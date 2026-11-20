#!/usr/bin/env python3
"""Tests for scripts/build_skill_index.py: the map the orchestrator routes from.

Run: python3 scripts/test_build_skill_index.py
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_skill_index as idx  # noqa: E402


def skill(root, name, frontmatter, siblings=()):
    d = os.path.join(root, "skills", name)
    os.makedirs(d)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(f"---\n{frontmatter}\n---\n# {name}\n")
    for s in siblings:
        with open(os.path.join(d, s), "w", encoding="utf-8") as fh:
            fh.write("x\n")


class IndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_folded_description_and_siblings(self):
        skill(self.root, "tdd", "name: tdd\ndescription: >-\n  Test-first steps.\n  Use when coding.\n"
              "disable-model-invocation: true", siblings=("testing-principles.md",))
        text = idx.render(self.root)
        self.assertIn("- **tdd**: Test-first steps. Use when coding. Siblings: testing-principles.md.", text)
        self.assertIn("1 skills.", text)

    def test_quoted_description_and_no_siblings(self):
        skill(self.root, "grill-me", 'name: grill-me\ndescription: "Interview first."')
        self.assertIn("- **grill-me**: Interview first.\n", idx.render(self.root))

    def test_folders_without_skill_md_are_skipped_and_order_is_stable(self):
        skill(self.root, "zeta", "name: zeta\ndescription: z")
        skill(self.root, "alpha", "name: alpha\ndescription: a")
        os.makedirs(os.path.join(self.root, "skills", "notes"))
        rows = [ln for ln in idx.render(self.root).splitlines() if ln.startswith("- **")]
        self.assertEqual(["- **alpha**: a", "- **zeta**: z"], rows)

    def test_the_real_index_is_current(self):
        self.assertEqual(0, idx.main(["--check"]))


if __name__ == "__main__":
    unittest.main()
