"""Tests for verify_gate.py — the Stop hook that blocks ending a turn after a
risky action (rebuild / docker build / deploy / .env write) until a fresh
end-to-end verification ran AFTER it.

Unlike guardrails (a pure core), this hook is an I/O script: it reads JSON on
stdin, follows `transcript_path` to a JSONL transcript, and prints a block
payload (or nothing) before exiting 0. So we test it as a black box exactly as
Claude Code invokes it — crafted stdin + crafted transcript via subprocess —
and assert the block-vs-allow decision and the VERIFY-OK override.

Run:  python3 -m unittest test_verify_gate   (from this directory)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "verify_gate.py")


def msg_entry(typ, *blocks):
    """One transcript line: a message of `typ` carrying the given content blocks."""
    return {"type": typ, "message": {"role": typ, "content": list(blocks)}}


def tool_use(name, **inp):
    return {"type": "tool_use", "name": name, "input": inp}


def tool_result(text):
    return {"type": "tool_result", "content": text}


def text_block(s):
    return {"type": "text", "text": s}


class VerifyGateTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_gate(self, transcript, stdin_extra=None):
        stdin = {}
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

    def assertBlocked(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.strip(), "expected a block payload on stdout")
        self.assertEqual(json.loads(proc.stdout)["decision"], "block")

    def assertAllowed(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "",
                         f"expected no output (allow), got: {proc.stdout!r}")

    # --- block: a risky action with no verification after it ---
    def test_docker_build_without_verify_blocks(self):
        proc = self.run_gate([msg_entry("assistant", tool_use("Bash", command="docker build -t app ."))])
        self.assertBlocked(proc)

    def test_docker_compose_up_without_verify_blocks(self):
        proc = self.run_gate([msg_entry("assistant", tool_use("Bash", command="docker compose up -d"))])
        self.assertBlocked(proc)

    def test_cli_rebuild_without_verify_blocks(self):
        proc = self.run_gate([msg_entry("assistant", tool_use("Bash", command="node cli.js rebuild"))])
        self.assertBlocked(proc)

    def test_env_write_without_verify_blocks(self):
        proc = self.run_gate([msg_entry("assistant", tool_use("Write", file_path="deploy/.env"))])
        self.assertBlocked(proc)

    def test_verify_before_risky_still_blocks(self):
        # verification must come AFTER the risky action — an earlier one doesn't count.
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="pytest -q")),
            msg_entry("assistant", tool_use("Bash", command="docker build -t app .")),
        ])
        self.assertBlocked(proc)

    # --- allow: a verification signal follows the risky action ---
    def test_pytest_after_risky_allows(self):
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="docker build -t app .")),
            msg_entry("assistant", tool_use("Bash", command="pytest -q")),
        ])
        self.assertAllowed(proc)

    def test_docker_ps_after_risky_allows(self):
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="docker compose up -d")),
            msg_entry("assistant", tool_use("Bash", command="docker ps")),
        ])
        self.assertAllowed(proc)

    def test_completed_evidence_in_tool_result_allows(self):
        # the verification signal can land in tool_result output, not just a command.
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="docker build -t app .")),
            msg_entry("user", tool_result("queued; moved to jobs/completed/abc.json — COMPLETED")),
        ])
        self.assertAllowed(proc)

    # --- override: VERIFY-OK lets the stop through ---
    def test_verify_ok_override_allows(self):
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="docker build -t app .")),
            msg_entry("assistant", text_block("Image is CI-only, nothing to run locally. VERIFY-OK: build is CI-only")),
        ])
        self.assertAllowed(proc)

    def test_verify_ok_is_case_insensitive(self):
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="docker build -t app .")),
            msg_entry("assistant", text_block("verify-ok: lowercase still counts")),
        ])
        self.assertAllowed(proc)

    # --- frictionless: no risky action at all ---
    def test_no_risky_action_allows(self):
        proc = self.run_gate([
            msg_entry("assistant", tool_use("Bash", command="git status")),
            msg_entry("assistant", tool_use("Bash", command="ls -la")),
        ])
        self.assertAllowed(proc)

    # --- loop guard & robustness: always allow ---
    def test_stop_hook_active_allows(self):
        # once we've blocked once and the model continued, let the stop through.
        proc = self.run_gate([msg_entry("assistant", tool_use("Bash", command="docker build -t app ."))],
                             stdin_extra={"stop_hook_active": True})
        self.assertAllowed(proc)

    def test_missing_transcript_path_allows(self):
        proc = self.run_gate(None)
        self.assertAllowed(proc)

    def test_malformed_stdin_allows(self):
        proc = subprocess.run([sys.executable, HOOK], input="not json{",
                              capture_output=True, text=True)
        self.assertAllowed(proc)


if __name__ == "__main__":
    unittest.main()
