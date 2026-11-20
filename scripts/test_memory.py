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
        lines = memory.prime_lines([g], recs, limit=3, max_text=80)
        self.assertIn("About you", lines[1])
        self.assertIn("Reply in PT-BR", "\n".join(lines))
        project_items = [ln for ln in lines if "fact " in ln]
        self.assertEqual(len(project_items), 2)  # limit counts global too
        self.assertIn("fact 4", project_items[0])  # newest first
        self.assertTrue(all(len(ln) <= 110 for ln in project_items))

    def test_prime_lines_empty_is_empty(self):
        self.assertEqual(memory.prime_lines([], [], limit=5), [])

    def test_looks_secret(self):
        for bad in ("token sk-ant-api03-abcdefghijklmnop", "password: hunter2hunter2",
                    "AKIAABCDEFGHIJKLMNOP", "ghp_" + "a" * 36, "-----BEGIN RSA PRIVATE KEY-----"):
            self.assertTrue(memory.looks_secret(bad), bad)
        for ok in ("never commit .env files", "the API uses JWT", "keys live in 1Password"):
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
