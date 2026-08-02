from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GOAL_BRIEF = ROOT / "scripts/goal_brief.py"
WIKI_INSTALL = ROOT / "integrations/llm-wiki/install.sh"
WIKI_UPDATE = ROOT / "integrations/llm-wiki/update.sh"
COMMAND = ROOT / ".claude/commands/devmode.md"
ORCHESTRATOR = ROOT / ".claude/agents/devmode-orchestrator.md"


class GoalBriefCommandTests(unittest.TestCase):
    def test_scaffold_uses_optional_plan_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-goal-") as temporary_dir:
            project = Path(temporary_dir)
            spec = project / "spec.md"
            plan = project / "plan.md"
            spec.write_text(
                "# Spec: Search\n\n## Acceptance criteria\n- Finds exact matches\n",
                encoding="utf-8",
            )
            plan.write_text(
                "# Plan: Search\n\n## Phase 1\n- Add the search index boundary\n- Cover empty queries\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(GOAL_BRIEF),
                    "scaffold",
                    str(spec),
                    "--plan",
                    str(plan),
                    "--kind",
                    "plan",
                    "--ref",
                    "conductor/tracks/search/spec.md",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertIn("Add the search index boundary", proc.stdout)
            self.assertIn("Cover empty queries", proc.stdout)
            self.assertIn("/plan ", proc.stdout)

    def test_missing_spec_or_plan_fails_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-goal-missing-") as temporary_dir:
            project = Path(temporary_dir)
            spec = project / "spec.md"
            spec.write_text("# Spec: Existing\n", encoding="utf-8")
            cases = [
                ["scaffold", str(project / "missing.md")],
                ["scaffold", str(spec), "--plan", str(project / "missing-plan.md")],
            ]
            for args in cases:
                with self.subTest(args=args):
                    proc = subprocess.run(
                        [sys.executable, str(GOAL_BRIEF), *args],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, proc.returncode)
                    self.assertIn("not found", proc.stderr.lower())
                    self.assertNotIn("Traceback", proc.stderr)


class WikiCommandTests(unittest.TestCase):
    def test_wiki_adopt_refuses_unrelated_karpathy_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-schema-collision-") as temporary_dir:
            target = Path(temporary_dir)
            existing = target / "KARPATHY.md"
            existing.write_text("# Project-owned Karpathy notes\n", encoding="utf-8")

            proc = subprocess.run(
                [str(WIKI_INSTALL), str(target), "--adopt"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, proc.returncode)
            self.assertIn("refusing", proc.stderr.lower())
            self.assertEqual("# Project-owned Karpathy notes\n", existing.read_text(encoding="utf-8"))

    def test_wiki_start_refuses_nonempty_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-start-") as temporary_dir:
            target = Path(temporary_dir)
            (target / "keep.txt").write_text("host\n", encoding="utf-8")

            proc = subprocess.run(
                [str(WIKI_INSTALL), str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, proc.returncode)
            self.assertIn("--adopt", proc.stderr)
            self.assertFalse((target / "KARPATHY.md").exists())
            self.assertEqual("host\n", (target / "keep.txt").read_text(encoding="utf-8"))

    def test_wiki_adopt_and_update_preserve_host_docs_and_support_codex(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-adopt-") as temporary_dir:
            target = Path(temporary_dir)
            (target / "README.md").write_text("# Host README\n", encoding="utf-8")
            (target / "CLAUDE.md").write_text("# Host Claude\n", encoding="utf-8")
            (target / "AGENTS.md").write_text("# Host Codex\n", encoding="utf-8")
            (target / "notes.md").write_text("# Existing notes\n", encoding="utf-8")

            first = subprocess.run(
                [str(WIKI_INSTALL), str(target), "--adopt"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [str(WIKI_INSTALL), str(target), "--adopt"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("4 existing markdown file(s)", first.stdout)
            self.assertEqual("# Host README\n", (target / "README.md").read_text(encoding="utf-8"))
            self.assertTrue((target / ".llm-wiki/README.md").is_file())
            self.assertEqual(1, (target / "CLAUDE.md").read_text(encoding="utf-8").count("@KARPATHY.md"))
            self.assertEqual(1, (target / "AGENTS.md").read_text(encoding="utf-8").count("KARPATHY.md"))

            subprocess.run(
                [str(WIKI_UPDATE), str(target)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual("# Host README\n", (target / "README.md").read_text(encoding="utf-8"))
            self.assertIn("Your knowledge base", (target / ".llm-wiki/README.md").read_text(encoding="utf-8"))
            self.assertEqual("# Existing notes\n", (target / "notes.md").read_text(encoding="utf-8"))

    def test_wiki_start_creates_both_agent_instruction_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-fresh-") as temporary_dir:
            target = Path(temporary_dir) / "wiki"
            subprocess.run(
                [str(WIKI_INSTALL), str(target)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("@KARPATHY.md", (target / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn("KARPATHY.md", (target / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue((target / "README.md").is_file())

            (target / "AGENTS.md").unlink()
            subprocess.run(
                [str(WIKI_UPDATE), str(target)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("KARPATHY.md", (target / "AGENTS.md").read_text(encoding="utf-8"))

    def test_wiki_update_backfills_codex_pointer_for_a_pre_codex_wiki(self) -> None:
        """A wiki deployed before Codex support must gain AGENTS.md on update."""
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-legacy-") as temporary_dir:
            target = Path(temporary_dir) / "wiki"
            subprocess.run(
                [str(WIKI_INSTALL), str(target)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            # Simulate the pre-Codex deployment the update path has to migrate.
            (target / "AGENTS.md").unlink()
            claude_before = (target / "CLAUDE.md").read_text(encoding="utf-8")

            for _ in range(2):
                subprocess.run(
                    [str(WIKI_UPDATE), str(target)],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(1, agents.count("KARPATHY.md"))
            self.assertEqual(claude_before, (target / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_wiki_update_keeps_host_agents_content_and_stays_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-wiki-host-codex-") as temporary_dir:
            target = Path(temporary_dir)
            (target / "AGENTS.md").write_text(
                "# Host Codex\n\nProject rules that must survive.\n", encoding="utf-8"
            )
            (target / "CLAUDE.md").write_text("# Host Claude\n", encoding="utf-8")
            subprocess.run(
                [str(WIKI_INSTALL), str(target), "--adopt"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            for _ in range(2):
                subprocess.run(
                    [str(WIKI_UPDATE), str(target)],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Project rules that must survive.", agents)
            self.assertEqual(1, agents.count("KARPATHY.md"))
            # Claude Code's host file keeps exactly the one import the installer added.
            claude = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("# Host Claude", claude)
            self.assertEqual(1, claude.count("@KARPATHY.md"))

    def test_install_and_update_share_one_idempotency_marker(self) -> None:
        """Drifted markers would silently append a duplicate pointer on update."""
        for script in (WIKI_INSTALL, WIKI_UPDATE):
            with self.subTest(script=script.name):
                self.assertIn("host-pointers.sh", script.read_text(encoding="utf-8"))

    def test_wiki_help_lists_all_supported_options_without_shell_source(self) -> None:
        help_text = subprocess.run(
            [str(WIKI_INSTALL), "--help"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout
        for option in ("--adopt", "--force", "--help"):
            self.assertIn(option, help_text)
        self.assertNotIn("set -euo pipefail", help_text)


class CommandContractTests(unittest.TestCase):
    def test_orchestrator_does_not_require_optional_conductor_commands(self) -> None:
        orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
        self.assertIn("missing slash-command files must not block", orchestrator)
        self.assertIn("conductor/.templates/track/", orchestrator)

    def test_every_public_mode_has_an_explicit_contract(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        headings = [
            "Mode C-lite",
            "Mode Do",
            "Mode Wiki",
            "Mode Lean",
            "Mode Update",
            "Mode Start",
            "Mode Adopt",
            "Mode Goal",
            "Mode Resume",
        ]
        for heading in headings:
            self.assertIn(f"### {heading}", command)

    def test_start_contract_rejects_unsafe_or_incomplete_names(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        self.assertIn("^[a-z0-9][a-z0-9-]*$", command)
        self.assertIn("Refuse missing `<name>` or `<idea>`", command)

    def test_start_initializes_git_before_the_installer_runs_beads(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        start = command.index("### Mode Start")
        adopt = command.index("### Mode Adopt")
        section = command[start:adopt]
        self.assertLess(
            section.index('git -C "workspaces/<name>" init -q'),
            section.index('install.sh "workspaces/<name>"'),
        )

    def test_non_optional_mode_arguments_are_rejected_when_missing(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        for contract in (
            "Refuse a missing `<task>`",
            "Refuse a missing `<idea>` or `<objective>`",
            "Refuse a missing `<folder>`",
            "Refuse a missing `<objective>`",
        ):
            self.assertIn(contract, command)

    def test_goal_contract_passes_an_existing_plan_to_scaffold(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        self.assertIn("--plan conductor/tracks/<id>/plan.md", command)


if __name__ == "__main__":
    unittest.main()
