from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "integrations" / "conductor-beads" / "install.sh"
UPDATE = ROOT / "integrations" / "conductor-beads" / "update.sh"
TEXT_SUFFIXES = {".md", ".py", ".sh", ".toml", ".json", ".yaml", ".yml"}


class CodexCompatibilityTests(unittest.TestCase):
    def test_devmode_has_one_public_invocation(self) -> None:
        forbidden = "$" + "devmode"
        occurrences: list[str] = []

        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if ".git" in path.parts or "workspaces" in path.parts:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if forbidden in line:
                    occurrences.append(f"{path.relative_to(ROOT)}:{line_number}")

        self.assertEqual([], occurrences, "use /devmode everywhere: " + ", ".join(occurrences))

    def test_repo_codex_skill_view_is_links_plus_launcher(self) -> None:
        skill_names = sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir())
        codex_skills = ROOT / ".agents/skills"
        for name in skill_names:
            link = codex_skills / name
            self.assertTrue(link.is_symlink(), f"{link} must point at the canonical skill")
            self.assertEqual(Path("../../skills") / name, Path(os.readlink(link)))
            self.assertTrue((link / "SKILL.md").is_file())
        self.assertTrue((codex_skills / "devmode/SKILL.md").is_file())
        metadata = codex_skills / "devmode/agents/openai.yaml"
        self.assertTrue(metadata.is_file())
        self.assertIn('display_name: "devmode"', metadata.read_text(encoding="utf-8"))

    def test_install_and_update_share_skills_without_copying_them_twice(self) -> None:
        skill_names = sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir())

        with tempfile.TemporaryDirectory(prefix="devmode-codex-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assert_shared_skill_layout(project, skill_names)

            # Simulate the duplicated layout written by older versions.
            stale_link = project / ".agents" / "skills" / skill_names[0]
            stale_link.unlink()
            stale_link.mkdir()
            (stale_link / "stale-copy").write_text("duplicate", encoding="utf-8")

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assert_shared_skill_layout(project, skill_names)
            self.assertFalse((project / "AGENTS.devmode.md").exists())

    def test_update_collapses_exact_legacy_codex_skill_copies_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-codex-legacy-copy-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            skill_name = "tdd"
            codex_skill = project / ".agents/skills" / skill_name
            codex_skill.unlink()
            shutil.copytree(project / ".claude/skills" / skill_name, codex_skill)
            (project / ".devmode/managed-files").unlink()

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            self.assertTrue(codex_skill.is_symlink())
            self.assertEqual(Path("../../.claude/skills") / skill_name, Path(os.readlink(codex_skill)))

    def test_reinstalling_clean_project_does_not_create_manifest_adapters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-clean-") as temporary_dir:
            project = Path(temporary_dir)

            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            self.assertFalse((project / "CLAUDE.devmode.md").exists())
            self.assertFalse((project / "AGENTS.devmode.md").exists())
            self.assertNotIn(
                "<!-- devmode: base process;",
                (project / "CLAUDE.md").read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "<!-- devmode: Codex base process;",
                (project / "AGENTS.md").read_text(encoding="utf-8"),
            )

    def test_install_and_update_preserve_existing_claude_and_codex_assets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-host-") as temporary_dir:
            project = Path(temporary_dir)
            (project / "CLAUDE.md").write_text("host claude instructions\n", encoding="utf-8")
            (project / "AGENTS.md").write_text("host Codex instructions\n", encoding="utf-8")
            preserved = {
                project / ".claude/skills/tdd/SKILL.md": "host tdd skill\n",
                project / ".claude/agents/security-scanner.md": "host claude agent\n",
                project / ".agents/security-scanner.md": "host shared agent\n",
                project / ".codex/agents/security-scanner.toml": "name = 'host-agent'\n",
                project / ".devmode/scorecard.py": "# host scorecard\n",
                project / ".claude/devmode/references/foundations.md": "host reference\n",
            }
            for path, content in preserved.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            for path, content in preserved.items():
                self.assertEqual(content, path.read_text(encoding="utf-8"), f"installer clobbered {path}")
            claude = (project / "CLAUDE.md").read_text(encoding="utf-8")
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertTrue(claude.startswith("host claude instructions\n"))
            self.assertEqual(1, claude.count("@CLAUDE.devmode.md"))
            self.assertTrue(agents.startswith("host Codex instructions\n"))
            self.assertEqual(1, agents.count("<!-- devmode: Codex base process;"))

    def test_install_refuses_unrelated_manifest_adapter_collisions_atomically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-manifest-collision-") as temporary_dir:
            project = Path(temporary_dir)
            claude = project / "CLAUDE.md"
            agents = project / "AGENTS.md"
            claude.write_text("host Claude instructions\n", encoding="utf-8")
            agents.write_text("host Codex instructions\n", encoding="utf-8")
            (project / "CLAUDE.devmode.md").write_text("project-owned file\n", encoding="utf-8")
            (project / "AGENTS.devmode.md").write_text("project-owned file\n", encoding="utf-8")

            proc = subprocess.run(
                [str(INSTALL), str(project)], cwd=ROOT, capture_output=True, text=True
            )

            self.assertNotEqual(0, proc.returncode)
            self.assertIn("not a devmode adapter", proc.stderr)
            self.assertEqual("host Claude instructions\n", claude.read_text(encoding="utf-8"))
            self.assertEqual("host Codex instructions\n", agents.read_text(encoding="utf-8"))
            self.assertFalse((project / ".devmode/managed-files").exists())

    def test_update_refuses_unrelated_codex_adapter_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-update-adapter-collision-") as temporary_dir:
            project = Path(temporary_dir)
            (project / ".claude").mkdir()
            agents = project / "AGENTS.md"
            adapter = project / "AGENTS.devmode.md"
            agents.write_text("host Codex instructions\n", encoding="utf-8")
            adapter.write_text("project-owned file\n", encoding="utf-8")

            proc = subprocess.run(
                [str(UPDATE), str(project)], cwd=ROOT, capture_output=True, text=True
            )

            self.assertNotEqual(0, proc.returncode)
            self.assertEqual("host Codex instructions\n", agents.read_text(encoding="utf-8"))
            self.assertEqual("project-owned file\n", adapter.read_text(encoding="utf-8"))
            self.assertFalse((project / ".devmode/managed-files").exists())

    def test_optional_conductor_copy_preserves_host_commands_and_skills(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-conductor-source-") as source_dir, \
             tempfile.TemporaryDirectory(prefix="devmode-conductor-target-") as target_dir:
            source = Path(source_dir)
            target = Path(target_dir)
            for path, content in {
                source / ".claude/commands/conductor-custom.md": "upstream command\n",
                source / ".claude/commands/conductor-new.md": "new upstream command\n",
                source / ".claude/skills/conductor/SKILL.md": "upstream conductor skill\n",
                source / ".claude/skills/beads/SKILL.md": "upstream beads skill\n",
            }.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=devmode-test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "fixture",
                ],
                cwd=source,
                check=True,
            )

            custom_command = target / ".claude/commands/conductor-custom.md"
            custom_skill = target / ".claude/skills/conductor/SKILL.md"
            custom_command.parent.mkdir(parents=True, exist_ok=True)
            custom_skill.parent.mkdir(parents=True, exist_ok=True)
            custom_command.write_text("host command\n", encoding="utf-8")
            custom_skill.write_text("host conductor skill\n", encoding="utf-8")
            env = dict(os.environ, CONDUCTOR_BEADS_REPO=str(source))

            subprocess.run(
                [str(INSTALL), str(target), "--no-skills", "--with-conductor"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertEqual("host command\n", custom_command.read_text(encoding="utf-8"))
            self.assertEqual("host conductor skill\n", custom_skill.read_text(encoding="utf-8"))
            self.assertEqual(
                "new upstream command\n",
                (target / ".claude/commands/conductor-new.md").read_text(encoding="utf-8"),
            )
            self.assertTrue((target / ".agents/skills/conductor").is_symlink())

    def test_no_skills_still_installs_guided_codex_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-no-skills-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run(
                [str(INSTALL), str(project), "--no-skills"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertTrue((project / ".agents/skills/devmode/SKILL.md").is_file())
            self.assertTrue((project / ".agents/skills/devmode/agents/openai.yaml").is_file())
            self.assertTrue((project / ".claude/agents/devmode-orchestrator.md").is_file())
            self.assertTrue((project / ".codex/agents/devmode-orchestrator.toml").is_file())
            self.assertFalse((project / ".claude/skills/tdd").exists())

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertFalse((project / ".claude/skills/tdd").exists())
            self.assertTrue((project / ".agents/skills/devmode/SKILL.md").is_file())

    def test_custom_role_agent_does_not_receive_devmode_codex_adapter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-agent-collision-") as temporary_dir:
            project = Path(temporary_dir)
            custom_agent = project / ".agents/security-scanner.md"
            custom_agent.parent.mkdir(parents=True)
            custom_agent.write_text("host security agent\n", encoding="utf-8")

            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            self.assertEqual("host security agent\n", custom_agent.read_text(encoding="utf-8"))
            self.assertFalse((project / ".codex/agents/security-scanner.toml").exists())

    def test_codex_hook_scopes_and_reviewers_are_read_only(self) -> None:
        root_hooks = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual({"UserPromptSubmit", "PostToolUse", "Stop"}, set(root_hooks["hooks"]))
        self.assertEqual("Agent|spawn_agent", root_hooks["hooks"]["PostToolUse"][0]["matcher"])

        hooks = json.loads(
            (ROOT / "integrations/conductor-beads/hooks/codex.hooks.json").read_text(encoding="utf-8")
        )
        matcher = hooks["hooks"]["SessionStart"][0]["matcher"]
        self.assertIn("clear", matcher.split("|"))

        for name in ["complexity-reviewer", "code-quality-analyzer", "security-scanner", "test-coverage-analyzer"]:
            config = (ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8")
            self.assertIn('sandbox_mode = "read-only"', config, name)

    def test_update_rewrites_devmode_hook_in_place_and_preserves_custom_hooks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-hooks-") as temporary_dir:
            project = Path(temporary_dir)
            claude_settings = project / ".claude/settings.json"
            claude_settings.parent.mkdir(parents=True)
            claude_settings.write_text(
                '{"hooks":{"SessionEnd":[{"hooks":[{"type":"command","command":"custom-claude-end"}]}]}}',
                encoding="utf-8",
            )
            codex_hooks = project / ".codex/hooks.json"
            codex_hooks.parent.mkdir(parents=True)
            codex_hooks.write_text(
                '{"hooks":{"SessionEnd":[{"hooks":[{"type":"command","command":"custom-codex-end"}]}]}}',
                encoding="utf-8",
            )
            subprocess.run(
                [str(INSTALL), str(project), "--with-guardrails"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            hooks_path = project / ".codex/hooks.json"
            hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertIn("SessionEnd", hooks["hooks"])
            installed_claude = json.loads(claude_settings.read_text(encoding="utf-8"))
            self.assertIn("SessionEnd", installed_claude["hooks"])
            hooks["hooks"]["SessionStart"][0]["matcher"] = "startup|resume|compact"
            hooks_path.write_text(json.dumps(hooks), encoding="utf-8")

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            updated = json.loads(hooks_path.read_text(encoding="utf-8"))
            session_start = updated["hooks"]["SessionStart"]
            devmode_handlers = [
                (group, handler)
                for group in session_start
                for handler in group["hooks"]
                if ".codex/hooks/codex_hooks.py" in handler.get("command", "")
            ]
            self.assertEqual(1, len(devmode_handlers))
            self.assertEqual("startup|resume|clear|compact", devmode_handlers[0][0]["matcher"])
            self.assertIn("SessionEnd", updated["hooks"])

            for event, groups in updated["hooks"].items():
                count = sum(
                    ".codex/hooks/codex_hooks.py" in handler.get("command", "")
                    for group in groups
                    for handler in group.get("hooks", [])
                )
                if event != "SessionEnd":
                    self.assertEqual(1, count, event)

    def test_update_does_not_opt_project_into_devmode_hooks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-custom-hooks-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            custom_hook = project / ".claude/hooks/custom.py"
            custom_hook.parent.mkdir(parents=True)
            custom_hook.write_text("# host hook\n", encoding="utf-8")

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            self.assertEqual("# host hook\n", custom_hook.read_text(encoding="utf-8"))
            self.assertFalse((project / ".claude/hooks/guardrails.py").exists())
            self.assertFalse((project / ".codex/hooks.json").exists())

    def test_invalid_hook_json_is_preserved(self) -> None:
        for relative_path in (Path(".claude/settings.json"), Path(".codex/hooks.json")):
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory(prefix="devmode-invalid-json-") as temporary_dir:
                    project = Path(temporary_dir)
                    target = project / relative_path
                    target.parent.mkdir(parents=True)
                    invalid = "{ definitely not valid json\n"
                    target.write_text(invalid, encoding="utf-8")

                    proc = subprocess.run(
                        [str(INSTALL), str(project), "--with-guardrails"],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )

                    self.assertNotEqual(0, proc.returncode)
                    self.assertEqual(invalid, target.read_text(encoding="utf-8"))
                    self.assertFalse((project / ".devmode/managed-files").exists())
                    self.assertFalse((project / "CLAUDE.md").exists())

    def test_update_preserves_invalid_hook_json(self) -> None:
        for relative_path in (Path(".claude/settings.json"), Path(".codex/hooks.json")):
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory(prefix="devmode-update-invalid-") as temporary_dir:
                    project = Path(temporary_dir)
                    subprocess.run(
                        [str(INSTALL), str(project), "--with-guardrails"],
                        cwd=ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    target = project / relative_path
                    invalid = "{ still not valid json\n"
                    target.write_text(invalid, encoding="utf-8")
                    managed_script = project / ".devmode/goal_brief.py"
                    managed_script.write_text("# must survive failed preflight\n", encoding="utf-8")

                    proc = subprocess.run(
                        [str(UPDATE), str(project)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )

                    self.assertNotEqual(0, proc.returncode)
                    self.assertEqual(invalid, target.read_text(encoding="utf-8"))
                    self.assertEqual(
                        "# must survive failed preflight\n",
                        managed_script.read_text(encoding="utf-8"),
                    )

    def test_update_merges_codex_config_and_preserves_user_settings(self) -> None:
        """A devmode-owned config must evolve with the template without losing user keys."""
        with tempfile.TemporaryDirectory(prefix="devmode-codex-config-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            config = project / ".codex/config.toml"
            installed = config.read_text(encoding="utf-8")
            self.assertIn("devmode-managed: codex-config v", installed)

            # A project one template generation behind, carrying its own settings.
            drifted = [
                line
                for line in installed.splitlines()
                if not line.startswith("max_concurrent_threads_per_session")
            ]
            drifted = [
                line.replace("65536", "32768") if line.startswith("project_doc_max_bytes") else line
                for line in drifted
            ]
            drifted.insert(0, 'model_reasoning_effort = "high"')
            drifted += ["", "[mcp_servers.local]", 'command = "echo"']
            config.write_text("\n".join(drifted) + "\n", encoding="utf-8")

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            merged = config.read_text(encoding="utf-8")
            tables = self.toml_tables(merged)
            self.assertEqual('"high"', tables[""]["model_reasoning_effort"], "user key lost")
            self.assertEqual('"echo"', tables["mcp_servers.local"]["command"], "user table lost")
            self.assertEqual("65536", tables[""]["project_doc_max_bytes"], "template fix never landed")
            self.assertEqual("8", tables["agents"]["max_concurrent_threads_per_session"])
            self.assertEqual("true", tables["features"]["hooks"])
            for key in ("project_doc_max_bytes", "max_concurrent_threads_per_session"):
                self.assertEqual(1, len([l for l in merged.splitlines() if l.startswith(key)]), key)
            # A top-level key after a table header would silently join that table.
            first_table = next(i for i, l in enumerate(merged.splitlines()) if l.startswith("["))
            last_bare = max(
                i for i, l in enumerate(merged.splitlines()) if l.startswith("project_doc_max_bytes")
            )
            self.assertLess(last_bare, first_table, "top-level key drifted into a table")

    def test_update_keeps_values_in_a_user_owned_codex_config(self) -> None:
        """Without the ownership marker devmode may add missing keys, never rewrite values."""
        with tempfile.TemporaryDirectory(prefix="devmode-codex-config-user-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            config = project / ".codex/config.toml"
            config.write_text("project_doc_max_bytes = 1024\n", encoding="utf-8")

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            tables = self.toml_tables(config.read_text(encoding="utf-8"))
            self.assertEqual("1024", tables[""]["project_doc_max_bytes"], "user value overwritten")
            self.assertEqual("true", tables["features"]["hooks"], "missing devmode key not delivered")
            self.assertNotIn(
                "devmode-managed: codex-config v",
                config.read_text(encoding="utf-8"),
                "devmode claimed a config whose values it refused to own",
            )

    def test_codex_config_merge_respects_array_table_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-codex-array-table-") as temporary_dir:
            project = Path(temporary_dir)
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            config = project / ".codex/config.toml"
            config.write_text(
                '[[custom_tools]]\nname = "fixture"\nproject_doc_max_bytes = 1024\n',
                encoding="utf-8",
            )

            subprocess.run([str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)

            merged = config.read_text(encoding="utf-8")
            root_key = merged.index("project_doc_max_bytes = 65536")
            first_table = merged.index("[[custom_tools]]")
            self.assertLess(root_key, first_table)
            self.assertIn("project_doc_max_bytes = 1024", merged)

    def test_codex_config_merge_failure_fails_the_update(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-codex-config-failure-") as temporary_dir:
            project = Path(temporary_dir) / "project"
            subprocess.run([str(INSTALL), str(project)], cwd=ROOT, check=True, capture_output=True, text=True)
            config = project / ".codex/config.toml"
            before = config.read_text(encoding="utf-8")
            config.write_text(before.replace("65536", "32768"), encoding="utf-8")
            before = config.read_text(encoding="utf-8")

            fake_bin = Path(temporary_dir) / "bin"
            fake_bin.mkdir()
            fake_python = fake_bin / "python3"
            fake_python.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
            fake_python.chmod(0o755)
            env = dict(os.environ, PATH=f"{fake_bin}:{os.environ['PATH']}")

            proc = subprocess.run(
                [str(UPDATE), str(project)], cwd=ROOT, capture_output=True, text=True, env=env
            )

            self.assertNotEqual(0, proc.returncode)
            self.assertIn("python3 is required", proc.stderr)
            self.assertEqual(before, config.read_text(encoding="utf-8"))

    def test_summary_does_not_claim_custom_agents_when_project_disables_them(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-summary-config-") as temporary_dir:
            project = Path(temporary_dir)
            config = project / ".codex/config.toml"
            config.parent.mkdir(parents=True)
            config.write_text("[features]\nhooks = true\nmulti_agent = false\n", encoding="utf-8")

            proc = subprocess.run(
                [str(INSTALL), str(project), "--no-skills"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertNotIn("enabling hooks + custom agents", proc.stdout)
            self.assertIn("features.multi_agent", proc.stdout)

    def test_closing_summary_reports_only_what_was_installed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="devmode-summary-full-") as temporary_dir:
            full = subprocess.run(
                [str(INSTALL), temporary_dir, "--with-guardrails"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        with tempfile.TemporaryDirectory(prefix="devmode-summary-lean-") as temporary_dir:
            lean = subprocess.run(
                [str(INSTALL), temporary_dir, "--no-skills"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("base skill links", full.stdout)
        self.assertIn(".codex/hooks.json wired", full.stdout)
        self.assertNotIn(".codex/hooks.json NOT wired", full.stdout)

        self.assertNotIn("base skill links", lean.stdout)
        self.assertIn("--no-skills", lean.stdout)
        self.assertIn(".codex/hooks.json NOT wired", lean.stdout)

    def test_help_lists_every_option_the_installer_accepts(self) -> None:
        """The help window is a line range over the header — new options fall out of it."""
        help_text = subprocess.run(
            [str(INSTALL), "--help"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout
        for option in (
            "--no-skills",
            "--with-conductor",
            "--with-guardrails",
            "--beads",
            "--beads-stealth",
            "--force",
            "--help",
        ):
            self.assertIn(option, help_text, option)

    def test_codex_entrypoints_execute_the_conductor_command_procedures(self) -> None:
        launcher = (ROOT / ".agents/skills/devmode/SKILL.md").read_text(encoding="utf-8")
        adapter = (ROOT / ".codex/agents/devmode-orchestrator.toml").read_text(encoding="utf-8")
        for name, text in (("launcher", launcher), ("orchestrator adapter", adapter)):
            self.assertIn(".claude/commands/conductor-", text, name)
            self.assertIn("conductor/workflow.md", text, name)

    def test_root_hook_descriptions_explain_the_event_asymmetry(self) -> None:
        comment = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))["_comment"]
        description = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))["description"]
        for text in (comment, description):
            self.assertIn("UserPromptSubmit", text)
            self.assertIn("transcript", text)
            self.assertIn("opt-in", text)

    def test_codex_slash_support_is_claimed_only_where_it_is_verified(self) -> None:
        for relative in (".agents/skills/devmode/SKILL.md", "README.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("verified working in Codex Desktop", text, relative)
            self.assertIn("/skills", text, relative)

    @staticmethod
    def toml_tables(text: str) -> dict[str, dict[str, str]]:
        """Minimal TOML view: {table_name: {key: raw_value}}, top level under ''."""
        table, tables = "", {"": {}}
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                table = stripped[1:-1]
                tables.setdefault(table, {})
                continue
            key, separator, value = stripped.partition("=")
            if separator:
                tables.setdefault(table, {})[key.strip()] = value.strip()
        return tables

    def assert_shared_skill_layout(self, project: Path, skill_names: list[str]) -> None:
        codex_skills = project / ".agents" / "skills"
        for name in skill_names:
            link = codex_skills / name
            self.assertTrue(link.is_symlink(), f"{link} must share the Claude skill")
            self.assertEqual(Path("../../.claude/skills") / name, Path(os.readlink(link)))
            self.assertTrue((link / "SKILL.md").is_file())

        launcher = codex_skills / "devmode" / "SKILL.md"
        self.assertTrue(launcher.is_file())
        self.assertFalse(launcher.parent.is_symlink())


class GateParityTests(unittest.TestCase):
    """Both hosts must classify a `/devmode` argument string the same way.

    A drift here is silent: one host demands the orchestrator and the other lets
    the turn end, so the same project is gated differently depending on who runs it.
    """

    CLAUDE_GATE = ROOT / ".claude/hooks/devmode_phase_gate.py"
    CODEX_GATE = ROOT / ".codex/hooks/codex_hooks.py"

    # (argument string, inline?) — inline means "no orchestrator required".
    CASES = (
        ("", False),
        ("build me a todo app", False),
        ("c", True),
        ("c check the logs", True),
        ("do fix the bug", True),
        ("wiki start /tmp/x", True),
        ("update /tmp/x", True),
        ("update wiki /tmp/x", True),
        ("goal ship the beta", True),
        ("plan the migration", True),
        ("lean goal ship the beta", True),
        ("lean plan the migration", True),
        ("lean build a thing", False),
        # False-positive class: a bare idea that merely STARTS with a mode word.
        ("cleanup the dead config", False),
        ("commit the change", False),
        ("control flow refactor", False),
        ("documentation for the API", False),
        # `\b` also fires on punctuation — these are ideas, not modes.
        ("wiki-like docs feature", False),
        ("goal: ship the beta", False),
        ("update-notifier integration", False),
        ("plan/execute split", False),
    )

    @staticmethod
    def load(path: Path):
        import importlib.util

        spec = importlib.util.spec_from_file_location(f"gate_{path.stem}_{id(path)}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_both_hosts_classify_every_mode_identically(self) -> None:
        claude = self.load(self.CLAUDE_GATE)
        codex = self.load(self.CODEX_GATE)
        for args, inline in self.CASES:
            claude_inline = bool(claude.INLINE.match(args) or claude.LEAN_INLINE.match(args))
            codex_inline = bool(codex.INLINE_RE.match(args) or codex.LEAN_INLINE_RE.match(args))
            self.assertEqual(claude_inline, codex_inline, f"hosts disagree on {args!r}")
            self.assertEqual(inline, claude_inline, f"wrong classification for {args!r}")

    def test_codex_gate_recognises_the_picker_invocation(self) -> None:
        """Codex CLI/IDE reaches devmode through /skills, so the prompt may carry
        no leading slash. The gate must still demand the orchestrator."""
        codex = self.load(self.CODEX_GATE)
        for prompt in ("/devmode build a todo app", "devmode build a todo app"):
            self.assertTrue(codex._is_full_devmode_prompt(prompt), prompt)
        for prompt in ("/devmode c check the logs", "devmode c check the logs"):
            self.assertFalse(codex._is_full_devmode_prompt(prompt), prompt)
        self.assertFalse(codex._is_full_devmode_prompt("the devmode gate blocked me"))


class UpdateParityTests(unittest.TestCase):
    """`update.sh` must refresh everything `install.sh` established.

    Anything install wires and update forgets goes stale in place — the worst
    shape being a gate whose script is refreshed but never re-wired, so it looks
    installed and never runs.
    """

    def install(self, project: Path, *flags: str) -> None:
        subprocess.run(
            [str(INSTALL), str(project), *flags], cwd=ROOT, check=True, capture_output=True, text=True
        )

    def update(self, project: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(UPDATE), str(project)], cwd=ROOT, check=True, capture_output=True, text=True
        )

    @staticmethod
    def wired_commands(project: Path) -> set[str]:
        settings = json.loads((project / ".claude/settings.json").read_text(encoding="utf-8"))
        return {
            handler.get("command", "")
            for event in settings.get("hooks", {}).values()
            for group in event
            for handler in group.get("hooks", [])
        }

    def test_update_rewires_every_claude_gate_it_refreshes(self) -> None:
        """A project installed before a gate existed must gain it on update."""
        with tempfile.TemporaryDirectory(prefix="devmode-update-gates-") as temporary_dir:
            project = Path(temporary_dir)
            self.install(project, "--with-guardrails")

            # Simulate the older layout: only the PreToolUse guardrail was wired.
            settings = json.loads((project / ".claude/settings.json").read_text(encoding="utf-8"))
            settings["hooks"] = {
                "PreToolUse": [
                    {
                        "matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit",
                        "hooks": [
                            {
                                "type": "command",
                                "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guardrails.py"',
                            }
                        ],
                    }
                ]
            }
            (project / ".claude/settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

            self.update(project)

            wired = " ".join(sorted(self.wired_commands(project)))
            for script in ("guardrails.py", "verify_gate.py", "devmode_phase_gate.py", "session_resume.py"):
                self.assertTrue((project / ".claude/hooks" / script).is_file(), f"{script} not refreshed")
                self.assertIn(script, wired, f"{script} refreshed but never wired — the gate is inert")

            # Same fixture, second claim: a Codex-only user must be able to
            # self-verify their gate, the way test_guardrails.py lets a Claude
            # user verify theirs. Asserted here to avoid a third full install.
            self.assertTrue((project / ".claude/hooks/test_guardrails.py").is_file())
            self.assertTrue((project / ".codex/hooks/test_codex_hooks.py").is_file())

    def test_update_restores_the_conductor_and_beads_codex_links(self) -> None:
        """`--with-conductor` skills live outside the base's skills/, so the
        update loop over that directory can never reach them."""
        with tempfile.TemporaryDirectory(prefix="devmode-update-cb-") as temporary_dir:
            project = Path(temporary_dir)
            self.install(project)
            for name in ("conductor", "beads"):
                skill = project / ".claude/skills" / name
                skill.mkdir(parents=True, exist_ok=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: upstream skill\n---\n", encoding="utf-8"
                )
                link = project / ".agents/skills" / name
                if link.exists() or link.is_symlink():
                    link.unlink()

            self.update(project)

            for name in ("conductor", "beads"):
                link = project / ".agents/skills" / name
                self.assertTrue(link.is_symlink(), f"{name} unreachable from Codex after update")
                self.assertEqual(Path("../../.claude/skills") / name, Path(os.readlink(link)))

    def test_update_scripts_answer_help_like_the_installers(self) -> None:
        """`--help` must not be swallowed as a target directory."""
        for script in (UPDATE, ROOT / "integrations/llm-wiki/update.sh"):
            for flag in ("-h", "--help"):
                proc = subprocess.run([str(script), flag], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(0, proc.returncode, f"{script.name} {flag}: {proc.stderr}")
                self.assertIn("Usage:", proc.stdout, script.name)


class AuditCoverageTests(unittest.TestCase):
    """`.codex/agents/` is audited; the Codex *skill* surface must be too.

    A skill added to `skills/` without its `.agents/skills/` link is invisible to
    Codex while the audit still exits 0 — the Claude side cannot desync from
    itself, so only Codex needs the check.
    """

    @staticmethod
    def audit_module():
        import importlib.util

        path = ROOT / "scripts/audit_skills.py"
        spec = importlib.util.spec_from_file_location("devmode_audit_skills", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def build_tree(root: Path, names: tuple[str, ...]) -> None:
        for name in names:
            skill = root / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            link = root / ".agents/skills" / name
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(Path("../../skills") / name)
        launcher = root / ".agents/skills/devmode"
        (launcher / "agents").mkdir(parents=True)
        (launcher / "SKILL.md").write_text("---\nname: devmode\n---\n", encoding="utf-8")
        (launcher / "agents/openai.yaml").write_text('display_name: "devmode"\n', encoding="utf-8")

    def test_a_complete_codex_skill_view_passes(self) -> None:
        audit = self.audit_module()
        with tempfile.TemporaryDirectory(prefix="devmode-audit-ok-") as temporary_dir:
            root = Path(temporary_dir)
            self.build_tree(root, ("tdd", "grill-me"))
            self.assertEqual([], audit.audit_codex_skills(str(root)))

    def test_a_skill_without_its_codex_link_fails_the_audit(self) -> None:
        audit = self.audit_module()
        with tempfile.TemporaryDirectory(prefix="devmode-audit-missing-") as temporary_dir:
            root = Path(temporary_dir)
            self.build_tree(root, ("tdd", "grill-me"))
            (root / ".agents/skills/tdd").unlink()
            errors = audit.audit_codex_skills(str(root))
            self.assertEqual(1, len(errors), errors)
            self.assertIn("tdd", errors[0])

    def test_a_broken_or_copied_codex_link_fails_the_audit(self) -> None:
        audit = self.audit_module()
        with tempfile.TemporaryDirectory(prefix="devmode-audit-broken-") as temporary_dir:
            root = Path(temporary_dir)
            self.build_tree(root, ("tdd",))
            link = root / ".agents/skills/tdd"
            link.unlink()
            link.mkdir()
            (link / "SKILL.md").write_text("---\nname: tdd\n---\n", encoding="utf-8")
            errors = audit.audit_codex_skills(str(root))
            self.assertEqual(1, len(errors), errors)
            self.assertIn("tdd", errors[0])

    def test_a_missing_launcher_fails_the_audit(self) -> None:
        audit = self.audit_module()
        with tempfile.TemporaryDirectory(prefix="devmode-audit-launcher-") as temporary_dir:
            root = Path(temporary_dir)
            self.build_tree(root, ("tdd",))
            (root / ".agents/skills/devmode/agents/openai.yaml").unlink()
            errors = audit.audit_codex_skills(str(root))
            self.assertEqual(1, len(errors), errors)
            self.assertIn("openai.yaml", errors[0])

    def test_the_real_repo_passes_its_own_codex_skill_audit(self) -> None:
        audit = self.audit_module()
        self.assertEqual([], audit.audit_codex_skills(str(ROOT)))


if __name__ == "__main__":
    unittest.main()
