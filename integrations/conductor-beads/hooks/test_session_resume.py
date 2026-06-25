"""Tests for session_resume.py — the SessionStart hook that prints a compact
warm-resume hint from .devmode/scorecard.json, and FAILS OPEN (prints nothing,
exit 0) on any missing or malformed input.

It reads `$CLAUDE_PROJECT_DIR/.devmode/scorecard.json` (a list of phase entries)
and emits the hint to stdout. So we drive it as a black box: point
CLAUDE_PROJECT_DIR at a crafted project dir and assert the hint shape on a good
scorecard, and silence on bad/absent state.

Run:  python3 -m unittest test_session_resume   (from this directory)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "session_resume.py")


def entry(phase, scores=None, summary=None, recommendations=None):
    e = {"phase": phase}
    if scores:
        e["scores"] = {k: {"score": v} for k, v in scores.items()}
    if summary:
        e["summary"] = summary
    if recommendations:
        e["recommendations"] = recommendations
    return e


FULL_SCORES = {"correctness": 8, "design": 7, "testing": 9, "safety": 8, "clarity": 8}  # avg 8.0


class SessionResumeTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_scorecard(self, content):
        d = os.path.join(self.root, ".devmode")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "scorecard.json"), "w", encoding="utf-8") as fh:
            fh.write(content if isinstance(content, str) else json.dumps(content))

    def add_track(self, name):
        d = os.path.join(self.root, "conductor", "tracks", name)
        os.makedirs(d)
        with open(os.path.join(d, "spec.md"), "w") as fh:
            fh.write("# spec")

    def run_hook(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        return subprocess.run([sys.executable, HOOK], input="",
                              capture_output=True, text=True, env=env)

    def assertSilent(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "",
                         f"fail-open expected (no output), got: {proc.stdout!r}")

    # --- the happy path: full hint shape ---
    def test_full_hint_shape(self):
        self.write_scorecard([entry(
            "Implement", scores=FULL_SCORES, summary="login core landed",
            recommendations={"correctness": "add a negative-path test"},
        )])
        self.add_track("auth-login")
        proc = self.run_hook()
        out = proc.stdout
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[devmode] Warm resume", out)
        self.assertIn("Last phase: Implement", out)
        self.assertIn("(8.0/10)", out)
        self.assertIn("login core landed", out)
        self.assertIn("Active track: auth-login", out)
        self.assertIn("Next (correctness): add a negative-path test", out)
        self.assertIn("Full picture", out)

    def test_uses_last_entry(self):
        self.write_scorecard([
            entry("Align", summary="old phase"),
            entry("Refactor", scores={k: 6 for k in FULL_SCORES}, summary="newest phase"),
        ])
        out = self.run_hook().stdout
        self.assertIn("Last phase: Refactor", out)
        self.assertIn("newest phase", out)
        self.assertIn("(6.0/10)", out)
        self.assertNotIn("old phase", out)

    def test_partial_scores_average_present_only(self):
        # _overall must average only the criteria present, not divide by five.
        self.write_scorecard([entry("Architect", scores={"correctness": 10, "design": 5})])
        out = self.run_hook().stdout
        self.assertIn("Last phase: Architect (7.5/10)", out)

    def test_entry_without_scores_omits_score(self):
        self.write_scorecard([entry("Align")])
        out = self.run_hook().stdout
        self.assertIn("Last phase: Align", out)
        self.assertNotIn("/10)", out)
        self.assertIn("Full picture", out)

    def test_minimal_entry_skips_track_and_next(self):
        self.write_scorecard([entry("Specify", scores={k: 7 for k in FULL_SCORES})])
        out = self.run_hook().stdout
        self.assertIn("Last phase: Specify (7.0/10)", out)
        self.assertNotIn("Active track", out)
        self.assertNotIn("Next (", out)
        self.assertIn("Full picture", out)

    # --- fail-open: missing / malformed / empty state prints nothing ---
    def test_fail_open_missing_scorecard(self):
        # no .devmode/scorecard.json at all
        self.assertSilent(self.run_hook())

    def test_fail_open_malformed_json(self):
        self.write_scorecard("not valid json {{{")
        self.assertSilent(self.run_hook())

    def test_empty_list_prints_nothing(self):
        self.write_scorecard([])
        self.assertSilent(self.run_hook())


if __name__ == "__main__":
    unittest.main()
