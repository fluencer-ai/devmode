#!/usr/bin/env python3
"""Tests for the Beads memory doctor's pure core (no bd install required)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from beads_doctor import diagnose


LIVE = {"bd_path": "/usr/local/bin/bd", "version": "bd version 1.0.3",
        "beads_dir": "/p/.beads", "ready_exit": 0, "ready_lines": 9,
        "counts": {"issues": 11, "memories": 0}, "config_enabled": True}


class Diagnose(unittest.TestCase):
    def test_fully_wired_project_is_live(self):
        live, rows, fix = diagnose(LIVE)
        self.assertTrue(live)
        self.assertEqual(fix, [])

    def test_missing_bd_is_not_live_and_says_how_to_install(self):
        # the reported production failure: bd was never installed
        live, rows, fix = diagnose({**LIVE, "bd_path": None, "version": None})
        self.assertFalse(live)
        self.assertTrue(any("install" in f.lower() for f in fix))

    def test_missing_beads_dir_is_not_live(self):
        live, _rows, fix = diagnose({**LIVE, "beads_dir": None, "ready_exit": None})
        self.assertFalse(live)
        self.assertTrue(any("bd init" in f for f in fix))

    def test_bd_installed_but_broken_in_this_project_is_not_live(self):
        # the subtler failure: binary present, unusable here
        live, _rows, fix = diagnose({**LIVE, "ready_exit": 1})
        self.assertFalse(live)
        self.assertTrue(any("not usable here" in f for f in fix))

    def test_lying_config_is_called_out_when_not_live(self):
        live, _rows, fix = diagnose({**LIVE, "bd_path": None, "config_enabled": True})
        self.assertFalse(live)
        self.assertTrue(any("lying" in f for f in fix))

    def test_no_config_complaint_when_already_disabled(self):
        _live, _rows, fix = diagnose({**LIVE, "bd_path": None, "config_enabled": False})
        self.assertFalse(any("lying" in f for f in fix))

    def test_empty_store_is_not_a_failure(self):
        # a fresh `bd init` has no export-state.json yet — that must stay green
        live, rows, _fix = diagnose({**LIVE, "counts": None})
        self.assertTrue(live)
        self.assertTrue(any(s == "!" for s, _, _ in rows))


if __name__ == "__main__":
    unittest.main()
