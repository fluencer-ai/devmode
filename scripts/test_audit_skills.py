"""Tests for audit_skills' count-drift core — pure values, no mocks, no live tree.

Run:  python3 -m unittest test_audit_skills   (from the scripts/ directory)
"""
import unittest

from audit_skills import count_drift


def drift(text, skills=41, agents=8, rel="DOC.md"):
    return count_drift(rel, text, skills, agents)


class CountDriftTest(unittest.TestCase):
    # --- the happy path: written totals match reality -> silence ---
    def test_consistent_skills_and_agents_pass(self):
        self.assertEqual(drift("The pack ships 41 skills and 8 agents."), [])

    def test_consistent_across_lines(self):
        self.assertEqual(drift("41 skills\nsome prose\n8 agents\n"), [])

    # --- stale totals are flagged with file:line + expected/found ---
    def test_stale_skill_count_flagged(self):
        errs = drift("Now featuring 40 skills.", rel="README.md")
        self.assertEqual(len(errs), 1)
        self.assertIn("README.md:1", errs[0])
        self.assertIn("40", errs[0])       # the wrong number that was written
        self.assertIn("41", errs[0])       # the real count it should be
        self.assertIn("skills", errs[0])

    def test_stale_agent_count_flagged(self):
        errs = drift("a panel of 7 agents", rel="INTEGRATION.md")
        self.assertEqual(len(errs), 1)
        self.assertIn("INTEGRATION.md:1", errs[0])
        self.assertIn("7", errs[0])
        self.assertIn("8", errs[0])
        self.assertIn("agents", errs[0])

    def test_reports_correct_line_number(self):
        errs = drift("intro\nmore\n\n38 skills here", rel="x.md")
        self.assertEqual(len(errs), 1)
        self.assertIn("x.md:4", errs[0])

    def test_two_mentions_one_line_both_checked(self):
        errs = drift("we have 40 skills and 9 agents")
        self.assertEqual(len(errs), 2)

    # --- "subagents" / Portuguese "agentes" are agent-count claims too ---
    def test_subagents_noun_maps_to_agents(self):
        self.assertEqual(drift("8 subagents ship in .agents/"), [])
        self.assertEqual(len(drift("9 subagents ship in .agents/")), 1)

    def test_portuguese_agentes_checked(self):
        self.assertEqual(drift("Os 41 skills e 8 agentes."), [])
        self.assertEqual(len(drift("Os 41 skills e 9 agentes.")), 1)

    # --- breakdown sub-counts are NOT the total and must be ignored ---
    def test_breakdown_de_processo_not_flagged(self):
        self.assertEqual(drift("### As 20 skills de processo, agrupadas por fase"), [])

    def test_breakdown_de_dominio_not_flagged(self):
        self.assertEqual(drift("### As 18 skills de domínio (craft cross-cutting)"), [])

    def test_breakdown_skipped_but_total_on_same_line_still_checked(self):
        # the total is wrong; the trailing breakdown qualifier must not mask it
        errs = drift("**40 skills** | 20 skills de processo + 18 de domínio")
        self.assertEqual(len(errs), 1)
        self.assertIn("40", errs[0])


if __name__ == "__main__":
    unittest.main()
