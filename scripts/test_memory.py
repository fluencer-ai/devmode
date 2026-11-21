#!/usr/bin/env python3
"""Tests for scripts/memory.py — the durable memory the orchestrator keeps.

Core (pure): make_record, fold, prime_lines, looks_secret. Shell: the CLI over a
temp project + temp global home. Run: python3 scripts/test_memory.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memory  # noqa: E402

NOW = "2026-11-20T12:00:00Z"


class CoreTest(unittest.TestCase):
    def test_record_shape(self):
        r = memory.make_record("Reply in PT-BR", kind="preference", scope="global",
                               tags=["lang"], source="devmode-orchestrator", now=NOW)
        self.assertEqual(r["v"], 1)
        self.assertTrue(r["id"].startswith("m-"))
        self.assertEqual((r["kind"], r["scope"], r["text"]), ("preference", "global", "Reply in PT-BR"))
        self.assertEqual(r["tags"], ["lang"])

    def test_id_is_stable_for_same_text(self):
        a = memory.make_record("x  y", kind="fact", scope="project", now=NOW)
        b = memory.make_record("X y", kind="fact", scope="project", now="2027-01-01T00:00:00Z")
        self.assertEqual(a["id"], b["id"])  # normalized text → same id → dedupe

    def test_rejects_unknown_kind_and_empty(self):
        with self.assertRaises(ValueError):
            memory.make_record("x", kind="gossip", scope="project", now=NOW)
        with self.assertRaises(ValueError):
            memory.make_record("   ", kind="fact", scope="project", now=NOW)

    def test_fold_dedupes_forgets_and_supersedes(self):
        a = memory.make_record("use pnpm", kind="preference", scope="project", now=NOW)
        a2 = dict(a, ts="2026-11-21T00:00:00Z")  # same id re-added → one entry, newest ts
        b = memory.make_record("deploys need an OK", kind="decision", scope="project", now=NOW)
        c = memory.make_record("use bun", kind="preference", scope="project", now=NOW, supersedes=a["id"])
        gone = {"v": 1, "op": "forget", "id": b["id"], "ts": NOW}
        live = memory.fold([a, b, a2, c, gone])
        self.assertEqual([r["text"] for r in live], ["use bun"])

    def test_fold_skips_garbage_lines(self):
        self.assertEqual(memory.fold([{"nope": 1}, "x", None]), [])

    def test_prime_lines_budget_and_order(self):
        recs = [memory.make_record(f"fact {i} " + "z" * 300, kind="fact", scope="project",
                                   now=f"2026-11-{10 + i:02d}T00:00:00Z") for i in range(5)]
        g = memory.make_record("Reply in PT-BR", kind="preference", scope="global", now=NOW)
        lines = memory.prime_lines([g], recs, limit=6, max_text=80)
        self.assertEqual(len(lines), 6)  # limit counts every emitted line, headers included
        self.assertIn("About you", lines[1])
        self.assertIn("Reply in PT-BR", "\n".join(lines))
        project_items = [ln for ln in lines if "fact " in ln]
        self.assertEqual(len(project_items), 2)
        self.assertIn("fact 4", project_items[0])  # newest first
        self.assertTrue(all(len(ln) <= 110 for ln in project_items))

    def test_prime_lines_keeps_room_for_both_scopes(self):
        gl = [memory.make_record(f"pref {i}", kind="preference", scope="global",
                                 now=f"2026-11-{10 + i:02d}T00:00:00Z") for i in range(8)]
        pl = [memory.make_record(f"decision {i}", kind="decision", scope="project",
                                 now=f"2026-11-{10 + i:02d}T00:00:00Z") for i in range(4)]
        for g, p in ((gl, pl), (gl[:4], pl)):
            lines = memory.prime_lines(g, p, limit=8)
            self.assertLessEqual(len(lines), 8)
            self.assertTrue(any("decision" in ln for ln in lines), lines)
            self.assertTrue(any("pref" in ln for ln in lines), lines)

    def test_prime_lines_gives_unused_room_to_the_other_scope(self):
        pl = [memory.make_record(f"decision {i}", kind="decision", scope="project", now=NOW)
              for i in range(10)]
        lines = memory.prime_lines([], pl, limit=8)
        self.assertEqual(len(lines), 8)
        self.assertEqual(sum("decision" in ln for ln in lines), 6)

    def test_prime_lines_empty_is_empty(self):
        self.assertEqual(memory.prime_lines([], [], limit=5), [])

    def test_looks_secret(self):
        for bad in ("token sk-ant-api03-abcdefghijklmnop", "password: hunter2hunter2",
                    "AKIAABCDEFGHIJKLMNOP", "ghp_" + "a" * 36, "-----BEGIN RSA PRIVATE KEY-----",
                    "send Authorization: Bearer abcdefghijklmnopqrstu",
                    "use bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"):
            self.assertTrue(memory.looks_secret(bad), bad)
        for ok in ("never commit .env files", "the API uses JWT", "keys live in 1Password",
                   "bearer tokens rotate daily"):
            self.assertFalse(memory.looks_secret(ok), ok)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "proj")
        self.home = os.path.join(self.tmp.name, "home")
        os.makedirs(os.path.join(self.root, ".beads"))
        self.env = dict(os.environ, DEVMODE_HOME=os.path.join(self.home, ".devmode"),
                        DEVMODE_MEMORY_NO_BD="1")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, ok=True):
        p = subprocess.run([sys.executable, os.path.join(HERE, "memory.py"), *args, "--root", self.root],
                           capture_output=True, text=True, env=self.env)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def test_init_creates_file(self):
        os.rmdir(os.path.join(self.root, ".beads"))
        self.run_cli("init")
        self.assertTrue(os.path.isfile(os.path.join(self.root, ".beads", "memories.jsonl")))
        self.run_cli("init")  # idempotent

    def test_add_list_forget_roundtrip(self):
        out = self.run_cli("add", "Run tests with -race", "--kind", "preference").stdout
        mid = out.split()[1]
        self.run_cli("add", "Reply in PT-BR", "--kind", "preference", "--scope", "global")
        listed = self.run_cli("list", "--json").stdout
        texts = sorted(r["text"] for r in json.loads(listed))
        self.assertEqual(texts, ["Reply in PT-BR", "Run tests with -race"])
        self.assertTrue(os.path.isfile(os.path.join(self.home, ".devmode", "memories.jsonl")))
        self.run_cli("forget", mid)
        texts = [r["text"] for r in json.loads(self.run_cli("list", "--json").stdout)]
        self.assertEqual(texts, ["Reply in PT-BR"])
        with open(os.path.join(self.root, ".beads", "memories.jsonl")) as fh:
            raw = fh.read().splitlines()
        self.assertEqual(len(raw), 2)  # kept the record: add + tombstone, nothing deleted

    def test_init_creates_a_private_file(self):
        old = os.umask(0o022)
        try:
            self.run_cli("init")
        finally:
            os.umask(old)
        mode = os.stat(os.path.join(self.root, ".beads", "memories.jsonl")).st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_refuses_secrets_in_every_persisted_field(self):
        fake = "sk-ant-api03-abcdefghijklmnop"
        self.assertEqual(self.run_cli("add", "fine", "--tags", f"a,{fake}", ok=False).returncode, 2)
        self.assertEqual(self.run_cli("add", "fine", "--supersedes", fake, ok=False).returncode, 2)
        mid = self.run_cli("add", "fine").stdout.split()[1]
        self.assertEqual(self.run_cli("forget", mid, "--reason", fake, ok=False).returncode, 2)
        with open(os.path.join(self.root, ".beads", "memories.jsonl")) as fh:
            self.assertNotIn(fake, fh.read())

    def test_supersedes_must_be_a_memory_id(self):
        self.assertEqual(self.run_cli("add", "fine", "--supersedes", "not an id", ok=False).returncode, 1)

    def test_supersede_also_forgets_the_old_key_in_bd(self):
        fake_bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(fake_bin)
        log = os.path.join(self.tmp.name, "bd.log")
        with open(os.path.join(fake_bin, "bd"), "w") as fh:
            fh.write(f'#!/bin/sh\necho "$@" >> "{log}"\n')
        os.chmod(os.path.join(fake_bin, "bd"), 0o755)
        self.env.pop("DEVMODE_MEMORY_NO_BD")
        self.env["PATH"] = fake_bin + os.pathsep + self.env["PATH"]
        old = self.run_cli("add", "use pnpm", "--kind", "decision").stdout.split()[1]
        new = self.run_cli("add", "use bun", "--kind", "decision", "--supersedes", old).stdout.split()[1]
        with open(log) as fh:
            calls = fh.read().splitlines()
        self.assertTrue(any(c.endswith(f"forget devmode-{old}") for c in calls), calls)
        self.assertTrue(any(f"--key devmode-{new}" in c for c in calls), calls)

    def test_refuses_secret(self):
        p = self.run_cli("add", "the key is sk-ant-api03-abcdefghijklmnop", ok=False)
        self.assertEqual(p.returncode, 2)
        self.assertFalse(os.path.getsize(os.path.join(self.root, ".beads", "memories.jsonl"))
                         if os.path.exists(os.path.join(self.root, ".beads", "memories.jsonl")) else 0)

    def test_prime_is_silent_without_memories(self):
        self.assertEqual(self.run_cli("prime").stdout, "")

    def test_prime_prints_block(self):
        self.run_cli("add", "Deploys wait for an explicit OK", "--kind", "decision")
        out = self.run_cli("prime").stdout
        self.assertIn("[devmode] Memory", out)
        self.assertIn("Deploys wait for an explicit OK", out)

    def test_query_filters(self):
        self.run_cli("add", "Use pnpm, never npm", "--kind", "preference")
        self.run_cli("add", "Billing module owns invoices", "--kind", "fact")
        rows = json.loads(self.run_cli("list", "--json", "--query", "pnpm").stdout)
        self.assertEqual([r["text"] for r in rows], ["Use pnpm, never npm"])


if __name__ == "__main__":
    unittest.main()
