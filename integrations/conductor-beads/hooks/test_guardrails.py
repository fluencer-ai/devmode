"""Tests for the guardrails functional core: pure values, no mocks.

Run:  python3 -m unittest test_guardrails   (from this directory)
"""
import unittest

from guardrails import evaluate


def bash(cmd):
    return evaluate("Bash", {"command": cmd})


def write(path):
    return evaluate("Write", {"file_path": path})


class GuardrailTest(unittest.TestCase):
    # deny rules
    def test_sudo_denied(self):
        self.assertEqual(bash("sudo rm x")[0], "deny")

    def test_force_push_denied(self):
        self.assertEqual(bash("git push --force origin main")[0], "deny")
        self.assertEqual(bash("git push -f")[0], "deny")

    def test_no_verify_denied(self):
        self.assertEqual(bash("git commit --no-verify -m x")[0], "deny")

    def test_rm_rf_root_denied(self):
        self.assertEqual(bash("rm -rf /")[0], "deny")

    def test_write_to_env_denied(self):
        self.assertEqual(write("config/.env")[0], "deny")

    def test_write_to_git_denied(self):
        self.assertEqual(write(".git/config")[0], "deny")

    # ask (warn) rules
    def test_reset_hard_asks(self):
        self.assertEqual(bash("git reset --hard HEAD~1")[0], "ask")

    def test_rm_rf_scoped_asks(self):
        self.assertEqual(bash("rm -rf build/")[0], "ask")

    def test_secret_read_asks(self):
        self.assertEqual(bash("cat .env")[0], "ask")

    # R05 reads the rm flags, not one spelling of them
    def test_rm_recursive_force_is_checked_in_any_flag_spelling(self):
        for cmd in ("rm -r -f build/", "rm -R -f build/", "rm -f -r build/", "rm --recursive --force build/"):
            self.assertEqual(bash(cmd)[0], "ask", cmd)
        for cmd in ("rm -r -f /", "rm --recursive --force ~", "rm -R -f *"):
            self.assertEqual(bash(cmd)[0], "deny", cmd)

    def test_rm_rf_denies_only_root_targets_and_asks_inside_home(self):
        for cmd in ("rm -rf ~", "rm -rf ~/", "rm -rf $HOME", "rm -rf /*", "rm -rf *", "rm -rf build/ ~"):
            self.assertEqual(bash(cmd)[0], "deny", cmd)
        for cmd in ("rm -rf ~/Projects/old-build", "rm -rf $HOME/old-build"):
            self.assertEqual(bash(cmd)[0], "ask", cmd)
        self.assertEqual(bash('echo "never run rm -rf /"')[0], "allow")

    # R07 uses the same secret-file rule as R06, plus .git and ~/.ssh
    def test_write_guard_uses_the_secret_file_rule(self):
        env = "." + "env"
        for path in (f"config/{env}", f"{env}.local", "keys/id_rsa", "certs/server.pem",
                     "credentials.json", "/home/me/.ssh/authorized_keys", "/home/me/.ssh/config"):
            self.assertEqual(write(path)[0], "deny", path)
        for path in (f"{env}.example", "docs/secrets-policy.md", "src/credentials_form.tsx"):
            self.assertEqual(write(path)[0], "allow", path)

    # quoted paths with spaces stay one argument; quoted text runs only where executed
    def test_quoted_paths_with_spaces_keep_their_program(self):
        env = "." + "env"
        self.assertEqual(bash(f'cat "Projetos pessoais/{env}"')[0], "ask")
        self.assertEqual(bash('rm -rf "My Folder/build"')[0], "ask")
        self.assertEqual(bash('cat "Projetos pessoais/nota.txt"')[0], "allow")

    def test_quoted_commands_are_opened_only_where_they_run(self):
        env = "." + "env"
        for cmd in (f'ssh host "cat {env}"', 'bash -c "rm -rf /Users/x/y"', f'sh -lc "cat {env}"',
                    f'docker exec app sh -c "cat {env}"', f'eval "cat {env}"',
                    f'watch "cat {env}"', f'watch -n 2 "cat {env}"', f'bash -ce "cat {env}"',
                    f'bash -ec "cat {env}"'):
            self.assertEqual(bash(cmd)[0], "ask", cmd)
        for cmd in (f'echo "cat {env}"', f'git commit -m "see {env} docs; cat later"'):
            self.assertEqual(bash(cmd)[0], "allow", cmd)

    # allow (the common case stays frictionless)
    def test_normal_bash_allowed(self):
        self.assertEqual(bash("git status")[0], "allow")
        self.assertEqual(bash("npm test")[0], "allow")

    def test_normal_write_allowed(self):
        self.assertEqual(write("src/auth/core.py")[0], "allow")

    def test_unknown_tool_allowed(self):
        self.assertEqual(evaluate("Read", {"file_path": ".env"})[0], "allow")  # reads aren't blocked here


if __name__ == "__main__":
    unittest.main()
