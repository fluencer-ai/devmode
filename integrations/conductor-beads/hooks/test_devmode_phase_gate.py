"""Tests for devmode_phase_gate.py — the Stop hook that enforces the devmode
ceremony. Two behaviors, both keyed off the transcript:

  1) DASHBOARD AUTO-REFRESH — a pure side effect that must NEVER block.
  2) ORCHESTRATOR DELEGATION — blocks ending a FULL `/devmode` turn (a
     phase-driving mode, i.e. NOT c/do/wiki/lean/update/goal/plan/adopt/start)
     that never spawned the `devmode-orchestrator` subagent. Override: DEVMODE-OK.

Like verify_gate, this is an I/O script, so we drive it as a black box: crafted
stdin (`transcript_path`, `cwd`) + crafted JSONL transcript via subprocess, and
assert block-vs-allow, mode recognition, the override, and that the dashboard
refresh path never raises a block.

Run:  python3 -m unittest test_devmode_phase_gate   (from this directory)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "devmode_phase_gate.py")


def user(text):
    """A real user prompt (string content, as Claude Code records slash commands)."""
    return {"type": "user", "message": {"role": "user", "content": text}}


def assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def devmode_cmd(args):
    """The command-tag form of a /devmode invocation with the given args."""
    return f"<command-name>/devmode</command-name>\n<command-args>{args}</command-args>"


def orchestrator_spawn():
    return {"type": "tool_use", "name": "Task",
            "input": {"subagent_type": "devmode-orchestrator", "prompt": "drive the phase"}}


def text_block(s):
    return {"type": "text", "text": s}


class PhaseGateTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_gate(self, transcript, cwd=None, stdin_extra=None):
        stdin = {"cwd": cwd or self.dir}
        if transcript is not None:
            tpath = os.path.join(self.dir, "transcript.jsonl")
            with open(tpath, "w", encoding="utf-8") as fh:
                for entry in transcript:
                    fh.write(json.dumps(entry) + "\n")
            stdin["transcript_path"] = tpath
        if stdin_extra:
            stdin.update(stdin_extra)
        return subprocess.run([sys.executable, HOOK], input=json.dumps(stdin),
                              capture_output=True, text=True)

    def make_project(self, name, dashboard_body):
        """A project dir with .devmode/scorecard.json + a stand-in dashboard.py."""
        proj = os.path.join(self.dir, name)
        os.makedirs(os.path.join(proj, ".devmode"))
        with open(os.path.join(proj, ".devmode", "scorecard.json"), "w") as fh:
            fh.write("[]")
        with open(os.path.join(proj, ".devmode", "dashboard.py"), "w") as fh:
            fh.write(dashboard_body)
        return proj

    def assertBlocked(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.strip(), "expected a block payload on stdout")
        self.assertEqual(json.loads(proc.stdout)["decision"], "block")

    def assertAllowed(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "",
                         f"expected no output (allow), got: {proc.stdout!r}")

    # --- block: a full /devmode turn with no orchestrator delegation ---
    def test_full_devmode_without_orchestrator_blocks(self):
        proc = self.run_gate([user(devmode_cmd("build a login form"))])
        self.assertBlocked(proc)

    def test_raw_input_full_form_blocks(self):
        # the other recognized form: the injected guided-mode body + "Raw input: **...**".
        body = "/devmode — guided mode\nRaw input: **build a dashboard**"
        proc = self.run_gate([user(body)])
        self.assertBlocked(proc)

    # --- allow: the orchestrator was spawned in the same turn ---
    def test_full_devmode_with_orchestrator_allows(self):
        proc = self.run_gate([
            user(devmode_cmd("build a login form")),
            assistant(orchestrator_spawn()),
        ])
        self.assertAllowed(proc)

    # --- allow: DEVMODE-OK override ---
    def test_devmode_ok_override_allows(self):
        proc = self.run_gate([
            user(devmode_cmd("build a login form")),
            assistant(text_block("Just answered a quick question. DEVMODE-OK: pure Q&A turn")),
        ])
        self.assertAllowed(proc)

    # --- allow: non-full modes run inline / have their own flows ---
    def test_nonfull_modes_allow(self):
        for args in ["c just an ops comment", "do add a health endpoint",
                     "wiki start ./kb", "lean build a thing", "update ./proj",
                     "goal ship it", "plan the thing", "adopt ./legacy",
                     "start newproj an idea", ""]:
            with self.subTest(args=args):
                proc = self.run_gate([user(devmode_cmd(args))])
                self.assertAllowed(proc)

    # --- allow: not a /devmode turn at all ---
    def test_non_devmode_turn_allows(self):
        proc = self.run_gate([user("hey, can you explain this function?")])
        self.assertAllowed(proc)

    # --- loop guard & robustness: always allow ---
    def test_stop_hook_active_allows(self):
        proc = self.run_gate([user(devmode_cmd("build a login form"))],
                             stdin_extra={"stop_hook_active": True})
        self.assertAllowed(proc)

    def test_malformed_stdin_allows(self):
        proc = subprocess.run([sys.executable, HOOK], input="not json{",
                              capture_output=True, text=True)
        self.assertAllowed(proc)

    # --- dashboard refresh: a side effect that must NEVER block ---
    def test_dashboard_refresh_runs_and_never_blocks(self):
        proj = self.make_project(
            "proj_ok",
            "import os, sys\n"
            "open(os.path.join(sys.argv[1], 'devmode-dashboard.html'), 'w').write('ok')\n",
        )
        # a plain, non-devmode turn: refresh fires purely as a side effect.
        proc = self.run_gate([user("just chatting")], cwd=proj)
        self.assertAllowed(proc)
        self.assertTrue(os.path.isfile(os.path.join(proj, "devmode-dashboard.html")),
                        "dashboard refresh should have produced the html artifact")

    def test_dashboard_refresh_failure_never_blocks(self):
        # a dashboard.py that crashes must be swallowed — the gate still allows.
        proj = self.make_project("proj_boom", "import sys\nsys.exit(2)\n")
        proc = self.run_gate([user("just chatting")], cwd=proj)
        self.assertAllowed(proc)

    def test_dashboard_refresh_runs_even_when_turn_blocks(self):
        # refresh (enforcement #1) is independent of delegation (enforcement #2):
        # a full /devmode turn with no orchestrator still blocks, AND the dashboard
        # is refreshed first — the block is about delegation, not the refresh.
        proj = self.make_project(
            "proj_block",
            "import os, sys\n"
            "open(os.path.join(sys.argv[1], 'devmode-dashboard.html'), 'w').write('ok')\n",
        )
        proc = self.run_gate([user(devmode_cmd("build a login form"))], cwd=proj)
        self.assertBlocked(proc)
        self.assertTrue(os.path.isfile(os.path.join(proj, "devmode-dashboard.html")),
                        "dashboard should refresh even on a turn that ends up blocked")


if __name__ == "__main__":
    unittest.main()
