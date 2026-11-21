#!/usr/bin/env python3
"""Tests for scripts/devmode_setup.py, the global installer.

Every test runs against a fake repo and a temporary HOME. Nothing here touches the
real ~/.claude, ~/.agents or ~/.devmode. Run: python3 scripts/test_devmode_setup.py
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import devmode_setup as ds  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def skill(desc, hidden=True):
    flag = "disable-model-invocation: true\n" if hidden else ""
    return f"---\nname: x\ndescription: >-\n  {desc}\n{flag}---\nbody\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = os.path.realpath(self.tmp.name)
        self.repo, self.home = os.path.join(t, "devmode"), os.path.join(t, "home")
        for n in ("tdd", "grill-me"):
            write(os.path.join(self.repo, "skills", n, "SKILL.md"), skill(f"{n} discipline. Use when testing."))
        write(os.path.join(self.repo, "skills", "loud", "SKILL.md"), skill("visible one", hidden=False))
        cb = os.path.join(self.repo, "integrations", "conductor-beads")
        write(os.path.join(cb, "commands", "devmode.md"), "---\ndescription: Guided devmode.\n---\n")
        write(os.path.join(cb, "agents", "devmode-orchestrator.md"), "---\nname: o\ndescription: Drives devmode.\n---\n")
        write(os.path.join(self.repo, ".agents", "skills", "devmode", "SKILL.md"), skill("devmode router", hidden=False))
        write(os.path.join(self.repo, ".agents", "tdd-implementer.md"), "---\nname: t\ndescription: Writes tests.\n---\n")
        write(os.path.join(self.repo, ".codex", "agents", "devmode-orchestrator.toml"),
              'name = "devmode-orchestrator"\ndescription = "Drives devmode."\n')
        write(os.path.join(self.repo, "references", "skill-index.md"), "# index\n")
        os.makedirs(os.path.join(self.home, ".claude"))
        os.makedirs(os.path.join(self.home, ".codex"))
        self.log = []

    def tearDown(self):
        self.tmp.cleanup()

    def run_setup(self, *argv):
        self.log = []
        return ds.main(list(argv), home=self.home, repo=self.repo, out=self.log.append)

    def h(self, *parts):
        return os.path.join(self.home, *parts)


class InstallTest(Base):
    def test_claude_lean_links_router_orchestrator_and_hidden_leaves(self):
        self.assertEqual(self.run_setup("--host", "claude"), 0)
        self.assertTrue(os.path.islink(self.h(".claude", "commands", "devmode.md")))
        self.assertTrue(os.path.islink(self.h(".claude", "agents", "devmode-orchestrator.md")))
        self.assertFalse(os.path.lexists(self.h(".claude", "agents", "tdd-implementer.md")))
        self.assertEqual(sorted(os.listdir(self.h(".claude", "skills"))), ["grill-me", "loud", "tdd"])
        base = self.h(".devmode")
        self.assertTrue(os.path.isdir(base) and not os.path.islink(base))
        self.assertEqual(os.path.realpath(os.path.join(base, "skills")), os.path.join(self.repo, "skills"))

    def test_install_creates_a_private_global_memory_and_keeps_an_existing_one(self):
        old = os.umask(0o022)
        try:
            self.run_setup("--host", "claude")
        finally:
            os.umask(old)
        mem = self.h(".devmode", "memories.jsonl")
        self.assertEqual(0o600, os.stat(mem).st_mode & 0o777)
        with open(mem, "a", encoding="utf-8") as fh:
            fh.write('{"id": "m-0000000000"}\n')
        self.run_setup("--host", "claude")
        self.run_setup("--uninstall")
        with open(mem, encoding="utf-8") as fh:
            self.assertIn("m-0000000000", fh.read())

    def test_dry_run_creates_no_memory(self):
        self.run_setup("--host", "claude", "--dry-run")
        self.assertFalse(os.path.lexists(self.h(".devmode", "memories.jsonl")))

    def test_full_adds_role_agents_and_mode_is_kept(self):
        self.run_setup("--host", "claude", "--full")
        self.assertTrue(os.path.islink(self.h(".claude", "agents", "tdd-implementer.md")))
        self.run_setup("--host", "claude")  # no flag: keeps full
        self.assertTrue(os.path.islink(self.h(".claude", "agents", "tdd-implementer.md")))
        self.run_setup("--host", "claude", "--lean")
        self.assertFalse(os.path.lexists(self.h(".claude", "agents", "tdd-implementer.md")))

    def test_codex_lean_links_only_the_router(self):
        self.run_setup("--host", "codex")
        self.assertEqual(os.listdir(self.h(".agents", "skills")), ["devmode"])
        self.run_setup("--host", "codex", "--full")
        self.assertEqual(sorted(os.listdir(self.h(".agents", "skills"))), ["devmode", "grill-me", "loud", "tdd"])

    def test_never_overwrites_real_folders_or_foreign_links(self):
        write(self.h(".claude", "skills", "tdd", "SKILL.md"), "mine")
        os.makedirs(self.h(".claude", "commands"))
        os.symlink("/elsewhere/devmode.md", self.h(".claude", "commands", "devmode.md"))
        self.run_setup("--host", "claude")
        self.assertFalse(os.path.islink(self.h(".claude", "skills", "tdd")))
        self.assertEqual(os.readlink(self.h(".claude", "commands", "devmode.md")), "/elsewhere/devmode.md")
        self.assertTrue(any("links elsewhere" in ln for ln in self.log))
        self.assertTrue(any("real file or folder" in ln for ln in self.log))

    def test_dry_run_changes_nothing(self):
        self.run_setup("--host", "claude", "--dry-run")
        self.assertFalse(os.path.exists(self.h(".claude", "skills")))
        self.assertFalse(os.path.exists(self.h(".devmode")))

    def test_check_passes_then_flags_a_missing_link(self):
        self.run_setup("--host", "claude")
        self.assertEqual(self.run_setup("--check"), 0)
        os.unlink(self.h(".claude", "skills", "tdd"))
        self.assertEqual(self.run_setup("--check"), 1)
        self.assertTrue(any("needs link tdd" in ln for ln in self.log))

    def test_stale_link_into_repo_is_pruned(self):
        os.makedirs(self.h(".claude", "skills"))
        os.symlink(os.path.join(self.repo, "skills", "deleted-skill"), self.h(".claude", "skills", "deleted-skill"))
        self.run_setup("--host", "claude")
        self.assertFalse(os.path.lexists(self.h(".claude", "skills", "deleted-skill")))

    def test_a_malformed_state_file_stops_before_any_change(self):
        os.makedirs(self.h(".devmode"))
        for bad in ('{"hosts": {}, "links": []}', '{"hosts": {"claude": 3}}',
                    '{"hosts": {}, "links": {"claude": "x"}}', '{"hosts": {"mars": "lean"}}'):
            with open(self.h(".devmode", "install.json"), "w") as fh:
                fh.write(bad)
            self.assertEqual(1, self.run_setup("--host", "claude"), bad)
            self.assertFalse(os.path.lexists(self.h(".claude", "skills")), bad)

    def test_save_never_truncates_a_file_named_like_the_temp(self):
        os.makedirs(self.h(".devmode"))
        write(self.h(".devmode", "install.json.tmp"), "my notes\n")
        self.run_setup("--host", "claude")
        with open(self.h(".devmode", "install.json.tmp")) as fh:
            self.assertEqual("my notes\n", fh.read())
        self.assertEqual(["install.json", "install.json.tmp"],
                         sorted(f for f in os.listdir(self.h(".devmode")) if f.startswith("install")))

    def test_converts_a_repo_symlink_home(self):
        os.symlink(self.repo, self.h(".devmode"))
        self.run_setup("--host", "claude")
        self.assertFalse(os.path.islink(self.h(".devmode")))
        self.assertTrue(os.path.islink(self.h(".devmode", "repo")))

    def test_uninstall_keeps_memory_and_foreign_files(self):
        self.run_setup("--host", "claude")
        self.run_setup("--host", "codex")
        write(self.h(".devmode", "memories.jsonl"), "{}\n")
        write(self.h(".claude", "skills", "other", "SKILL.md"), "not ours")
        self.run_setup("--uninstall", "--host", "claude")
        self.assertTrue(os.path.islink(self.h(".devmode", "skills")))  # codex still uses it
        self.run_setup("--uninstall")
        self.assertEqual(os.listdir(self.h(".claude", "skills")), ["other"])
        self.assertFalse(os.path.lexists(self.h(".claude", "commands", "devmode.md")))
        self.assertEqual(os.listdir(self.h(".devmode")), ["memories.jsonl"])

    def test_report_counts_only_what_the_host_lists(self):
        self.run_setup("--host", "claude")
        self.run_setup("--report")
        line = next(ln for ln in self.log if ln.startswith("claude"))
        self.assertIn("devmode.md", line)
        self.assertIn("loud", line)  # not hidden, so it is listed
        self.assertNotIn("tdd", line)

    def test_codex_gets_the_orchestrator_agent_the_launcher_delegates_to(self):
        self.run_setup("--host", "codex")
        dest = self.h(".codex", "agents", "devmode-orchestrator.toml")
        self.assertEqual(os.readlink(dest),
                         os.path.join(self.repo, ".codex", "agents", "devmode-orchestrator.toml"))
        self.run_setup("--uninstall", "--host", "codex")
        self.assertFalse(os.path.lexists(dest))

    def test_a_personal_alias_into_the_repo_is_never_removed(self):
        os.makedirs(self.h(".claude", "skills"))
        alias = self.h(".claude", "skills", "apelido")
        os.symlink(os.path.join(self.repo, "skills", "tdd"), alias)
        self.run_setup("--host", "claude")
        self.run_setup("--host", "claude", "--full")
        self.run_setup("--uninstall", "--host", "claude")
        self.assertTrue(os.path.islink(alias))

    def test_a_refused_home_writes_no_state(self):
        os.makedirs(os.path.join(self.tmp.name, "elsewhere"))
        os.symlink(os.path.join(self.tmp.name, "elsewhere"), self.h(".devmode"))
        self.assertEqual(self.run_setup("--host", "claude"), 1)
        self.assertEqual(os.listdir(os.path.join(self.tmp.name, "elsewhere")), [])
        self.assertFalse(os.path.lexists(self.h(".claude", "skills")))

    def test_an_unreadable_state_file_is_never_overwritten(self):
        write(self.h(".devmode", "install.json"), "not json, someone else's file")
        self.assertEqual(self.run_setup("--host", "claude"), 1)
        with open(self.h(".devmode", "install.json")) as fh:
            self.assertEqual(fh.read(), "not json, someone else's file")
        self.assertEqual(self.run_setup("--uninstall"), 1)
        self.assertTrue(os.path.exists(self.h(".devmode", "install.json")))

    def test_check_flags_broken_or_misdirected_home_links(self):
        self.run_setup("--host", "claude")
        os.unlink(self.h(".devmode", "skills"))
        os.symlink(os.path.join(self.tmp.name, "nowhere"), self.h(".devmode", "skills"))
        self.assertEqual(self.run_setup("--check"), 1)
        self.assertTrue(any("~/.devmode" in ln and "skills" in ln for ln in self.log), self.log)

    def test_report_counts_only_what_is_actually_installed(self):
        self.run_setup("--host", "codex", "--report")
        line = next(ln for ln in self.log if ln.startswith("codex"))
        self.assertIn("not installed", line)

    def test_requires_a_host(self):
        with self.assertRaises(SystemExit):
            self.run_setup()

    def test_several_hosts_in_one_flag(self):
        self.assertEqual(0, self.run_setup("--host", "claude,codex", "--dry-run"))
        self.assertTrue(any(ln.startswith("claude") for ln in self.log), self.log)
        self.assertTrue(any(ln.startswith("codex") for ln in self.log), self.log)

    def test_a_repeated_host_flag_is_refused_not_overwritten(self):
        with self.assertRaises(SystemExit):
            self.run_setup("--host", "claude", "--host", "codex", "--dry-run")


class PlanTest(unittest.TestCase):
    def test_plan_is_pure_and_owned_only(self):
        repo = "/r"
        want = {"/h/a": "/r/skills/a", "/h/b": "/r/skills/b"}
        cur = {"/h/a": ("link", "/r/skills/a"), "/h/b": ("link", "/r/old/b"),
               "/h/c": ("link", "/r/skills/c"), "/h/d": ("link", "/other/d"), "/h/e": ("real", None)}
        acts, notes = ds.plan(want, cur, repo)
        self.assertEqual(acts, [("relink", "/r/skills/b", "/h/b"), ("unlink", "/h/c")])
        self.assertEqual(notes, [])

    def test_unlink_needs_our_name_or_a_record(self):
        cur = {"/h/alias": ("link", "/r/skills/tdd"), "/h/agents": ("link", "/r/.agents")}
        self.assertEqual(ds.plan({}, cur, "/r")[0], [])
        self.assertEqual(ds.plan({}, cur, "/r", managed={"/h/agents": "/r/.agents"})[0], [("unlink", "/h/agents")])

    def test_a_live_unrecorded_link_is_never_removed_or_redirected(self):
        alive = lambda t: True  # noqa: E731
        cur = {"/h/agents/design-architect.toml": ("link", "/r/.codex/agents/design-architect.toml"),
               "/h/skills/devmode": ("link", "/r/skills/tdd")}
        want = {"/h/skills/devmode": "/r/.agents/skills/devmode"}
        acts, notes = ds.plan(want, cur, "/r", alive=alive)
        self.assertEqual([], acts)
        self.assertTrue(any("skills/devmode" in n for n in notes), notes)
        recorded = {"/h/skills/devmode": "/r/skills/tdd", "/h/agents/design-architect.toml":
                    "/r/.codex/agents/design-architect.toml"}
        acts, _ = ds.plan(want, cur, "/r", recorded, alive=alive)
        self.assertEqual(sorted(acts), sorted([("relink", "/r/.agents/skills/devmode", "/h/skills/devmode"),
                                               ("unlink", "/h/agents/design-architect.toml")]))

    def test_a_record_for_another_target_is_not_ownership(self):
        cur = {"/h/x": ("link", "/r/skills/mine")}
        acts, _ = ds.plan({}, cur, "/r", {"/h/x": "/r/skills/x"}, alive=lambda t: True)
        self.assertEqual([], acts)

    def test_prefix_is_not_ownership(self):
        acts, _ = ds.plan({}, {"/h/x": ("link", "/r-other/x")}, "/r")
        self.assertEqual(acts, [])


if __name__ == "__main__":
    unittest.main()
