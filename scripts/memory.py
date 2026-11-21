#!/usr/bin/env python3
"""devmode memory: what the orchestrator learns about the user and the project.

Two append-only JSONL files are the source of truth:
  project  <root>/.beads/memories.jsonl     facts, decisions, preferences for THIS project
  global   $DEVMODE_HOME/memories.jsonl     the user's own preferences, every project
           (DEVMODE_HOME defaults to ~/.devmode)

Nothing is ever deleted. `forget` appends a tombstone and `--supersedes` replaces
an entry while keeping it in the file. Project entries are mirrored into
`bd remember` when Beads is live, so `bd prime` sees them too. The mirror is best
effort and the file stays the source.

  memory.py init                                   create .beads/memories.jsonl
  memory.py add "<text>" [--kind K] [--scope project|global] [--tags a,b] [--supersedes ID]
  memory.py list [--scope all|project|global] [--query Q] [--json]
  memory.py forget <id> [--reason R]
  memory.py prime [--limit N]                      compact block for a fresh context

Kinds: preference, decision, fact, correction. Secret-looking text is refused (exit 2).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

KINDS = ("preference", "decision", "fact", "correction")
SCOPES = ("project", "global")

# ---------------------------------------------------------------- pure core

_SECRET_RES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(password|passwd|senha|secret|token|api[_-]?key)\s*[:=]\s*\S{6,}", re.I),
    re.compile(r"\bauthorization\s*:\s*\S{6,}", re.I),
    re.compile(r"\bbearer\s+[A-Za-z0-9._~+/-]{16,}=*", re.I),
]
_ID_RE = re.compile(r"^m-[0-9a-f]{10}$")


def looks_secret(text: str) -> bool:
    """True when the text carries a credential. Memory must never hold one."""
    return any(r.search(text) for r in _SECRET_RES)


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def make_record(text, *, kind, scope, now, tags=None, source="devmode-orchestrator", supersedes=None):
    """Build one memory record. The id derives from the normalized text, so the
    same memory added twice folds into one entry."""
    text = " ".join(str(text).split())
    if not text:
        raise ValueError("memory text is empty")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {', '.join(SCOPES)}")
    mid = "m-" + hashlib.sha1(f"{scope}:{_norm(text)}".encode()).hexdigest()[:10]
    return {"v": 1, "id": mid, "ts": now, "scope": scope, "kind": kind, "text": text,
            "tags": list(tags or []), "source": source, "supersedes": supersedes}


def fold(lines):
    """Replay the append-only log into the live set, oldest first.

    A repeated id keeps its newest copy, a tombstone removes its id, and an entry
    with `supersedes` removes the entry it replaces. Malformed lines are skipped."""
    live = {}
    for rec in lines:
        if not isinstance(rec, dict) or not rec.get("id"):
            continue
        if rec.get("op") == "forget":
            live.pop(rec["id"], None)
            continue
        if not rec.get("text"):
            continue
        if rec.get("supersedes"):
            live.pop(rec["supersedes"], None)
        live.pop(rec["id"], None)  # re-insert so order follows the newest write
        live[rec["id"]] = rec
    return list(live.values())


def _clip(text, n):
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def prime_lines(global_live, project_live, *, limit=12, max_text=160):
    """The compact block injected into a fresh context: at most `limit` lines,
    headers included. Global entries come first, then project entries, newest
    first. When both scopes have entries, each keeps at least half the room, and
    room one scope does not use goes to the other."""
    newest = lambda rs: sorted(rs, key=lambda r: r.get("ts", ""), reverse=True)  # noqa: E731
    sections = [(t, newest(rs)) for t, rs in (("About you (global)", global_live),
                                               ("This project", project_live)) if rs]
    room = limit - 1 - len(sections)  # the title line + one header per section
    if not sections or room < len(sections):
        return []
    take = [min(len(rs), room // len(sections)) for _, rs in sections]
    for i, (_, rs) in enumerate(sections):  # hand the leftover room to whoever can use it
        take[i] = min(len(rs), take[i] + room - sum(take))
    out = ["[devmode] Memory: apply these, and record new ones with .devmode/memory.py add"]
    for (title, rows), n in zip(sections, take):
        out.append(f"  {title}:")
        for r in rows[:n]:
            out.append(f"   - [{r.get('kind', 'fact')}] {_clip(r['text'], max_text)}  ({r['id']})")
    return out


# ---------------------------------------------------------------- shell


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _path(scope, root):
    if scope == "global":
        home = os.environ.get("DEVMODE_HOME") or os.path.join(os.path.expanduser("~"), ".devmode")
        return os.path.join(home, "memories.jsonl")
    return os.path.join(root, ".beads", "memories.jsonl")


def _read(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return rows


def _touch_private(path):
    """Create the file owner-only (0600) without touching what is already in it."""
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    os.close(os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600))


def _append(path, rec):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def _bd(root, *args):
    """Mirror into Beads. Best effort: returns a short status, never raises."""
    if os.environ.get("DEVMODE_MEMORY_NO_BD") or not shutil.which("bd"):
        return "mirror skipped (bd not available)"
    try:
        p = subprocess.run(["bd", "-C", root, *args], capture_output=True, text=True, timeout=15)
        return "mirrored to bd" if p.returncode == 0 else "mirror skipped (bd returned an error)"
    except Exception:
        return "mirror skipped (bd did not answer)"


def cmd_init(a):
    path = _path("project", a.root)
    _touch_private(path)
    print(f"ok {os.path.relpath(path, a.root)}")
    return 0


def _refuse_secrets(*fields):
    """Every persisted field is screened, not just the text. True when refused."""
    if any(f and looks_secret(str(f)) for f in fields):
        print("refused: a field looks like a credential; memory never stores secrets", file=sys.stderr)
        return True
    return False


def cmd_add(a):
    if _refuse_secrets(a.text, a.tags, a.supersedes):
        return 2
    if a.supersedes and not _ID_RE.match(a.supersedes):
        print("error: --supersedes takes a memory id (m-xxxxxxxxxx)", file=sys.stderr)
        return 1
    try:
        rec = make_record(a.text, kind=a.kind, scope=a.scope, now=_now(),
                          tags=[t for t in (a.tags or "").split(",") if t], supersedes=a.supersedes)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    path = _path(a.scope, a.root)
    _append(path, rec)
    if a.scope == "project":
        status = _bd(a.root, "remember", rec["text"], "--key", f"devmode-{rec['id']}")
        if a.supersedes and a.supersedes != rec["id"]:  # the replaced key must leave bd too
            _bd(a.root, "forget", f"devmode-{a.supersedes}")
    else:
        status = "global (not mirrored)"
    print(f"ok {rec['id']} {a.scope} · {status}")
    return 0


def _live(scope, root):
    return fold(_read(_path(scope, root)))


def cmd_list(a):
    scopes = SCOPES if a.scope == "all" else (a.scope,)
    rows = [r for s in scopes for r in _live(s, a.root)]
    if a.query:
        q = _norm(a.query)
        rows = [r for r in rows if q in _norm(r["text"]) or q in [t.lower() for t in r.get("tags", [])]]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False))
    else:
        for r in rows:
            print(f"{r['id']}  {r['scope']:<7} {r['kind']:<10} {r['text']}")
    return 0


def cmd_forget(a):
    if _refuse_secrets(a.id, a.reason):
        return 2
    for scope in SCOPES:
        if any(r["id"] == a.id for r in _live(scope, a.root)):
            _append(_path(scope, a.root), {"v": 1, "op": "forget", "id": a.id, "ts": _now(),
                                           "reason": a.reason or ""})
            status = _bd(a.root, "forget", f"devmode-{a.id}") if scope == "project" else "global"
            print(f"ok forgot {a.id} · {status}")
            return 0
    print(f"error: no live memory {a.id}", file=sys.stderr)
    return 1


def cmd_prime(a):
    try:
        lines = prime_lines(_live("global", a.root), _live("project", a.root), limit=a.limit)
    except Exception:
        return 0  # a memory hint must never block a session
    if lines:
        print("\n".join(lines))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="memory.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))

    common(sub.add_parser("init"))
    sp = sub.add_parser("add")
    sp.add_argument("text")
    sp.add_argument("--kind", default="fact", choices=KINDS)
    sp.add_argument("--scope", default="project", choices=SCOPES)
    sp.add_argument("--tags")
    sp.add_argument("--supersedes")
    common(sp)
    sp = sub.add_parser("list")
    sp.add_argument("--scope", default="all", choices=("all",) + SCOPES)
    sp.add_argument("--query")
    sp.add_argument("--json", action="store_true")
    common(sp)
    sp = sub.add_parser("forget")
    sp.add_argument("id")
    sp.add_argument("--reason")
    common(sp)
    sp = sub.add_parser("prime")
    sp.add_argument("--limit", type=int, default=12)
    common(sp)
    a = p.parse_args(argv)
    a.root = os.path.abspath(a.root)
    return {"init": cmd_init, "add": cmd_add, "list": cmd_list,
            "forget": cmd_forget, "prime": cmd_prime}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
