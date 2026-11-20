#!/usr/bin/env python3
"""devmode global installer. Links devmode into each agent host so a `git pull`
updates every host at once, while loading as little as possible per turn.

  ./setup --host auto            every host whose config folder exists
  ./setup --host claude          Claude Code  (~/.claude/commands, agents, skills)
  ./setup --host codex           Codex        (~/.agents/skills)
  ./setup --host agy             Antigravity  (~/.gemini/config/skills)
  ./setup --host cursor          Cursor       (~/.cursor/skills; skipped by auto when Claude Code exists)
  ./setup --lean | --full        lean is the default; a later run keeps each host's mode
  ./setup --dry-run              print what would change, change nothing
  ./setup --check                report missing, foreign or stale links (exit 1 on a problem)
  ./setup --report               estimated per-turn listing cost of what is installed
  ./setup --uninstall --host X   remove only links that point into this repo

What loads on every turn:
  Claude Code lean   the /devmode router + the devmode-orchestrator agent. The leaf
                     skills are linked but hidden (disable-model-invocation), so they
                     cost nothing per turn and still run as /<name>. Role agents are
                     not linked; the orchestrator reads them by path.
  Claude Code full   lean + the role agents as named agent types.
  Codex/agy lean     the devmode router skill only (these hosts list every installed
                     description). full links every leaf skill too.

~/.devmode is a real folder: links into this repo (repo, skills, agents, references)
plus the user's global memories.jsonl, which uninstall never deletes. It never
overwrites a real file or a link it does not own; a clash is reported and skipped.
"""
import argparse
import json
import os
import re
import sys

HOSTS = ("claude", "codex", "agy", "cursor")
MODES = ("lean", "full")
HOME_LINKS = {"repo": "", "skills": "skills", "agents": ".agents", "references": "references"}

# ------------------------------------------------------------------ pure core


def inventory(repo):
    """What this repo can install: (kind, name, source path)."""
    items = []
    sk = os.path.join(repo, "skills")
    for n in sorted(os.listdir(sk)):
        if os.path.isfile(os.path.join(sk, n, "SKILL.md")):
            items.append(("leaf", n, os.path.join(sk, n)))
    items.append(("router-cmd", "devmode", os.path.join(repo, "integrations", "conductor-beads", "commands", "devmode.md")))
    items.append(("router-skill", "devmode", os.path.join(repo, ".agents", "skills", "devmode")))
    items.append(("orchestrator", "devmode-orchestrator",
                  os.path.join(repo, "integrations", "conductor-beads", "agents", "devmode-orchestrator.md")))
    ad = os.path.join(repo, ".agents")
    for f in sorted(os.listdir(ad)):
        if f.endswith(".md"):
            items.append(("role", f[:-3], os.path.join(ad, f)))
    return items


def host_dirs(host, home):
    if host == "claude":
        c = os.path.join(home, ".claude")
        return {"skills": os.path.join(c, "skills"), "commands": os.path.join(c, "commands"),
                "agents": os.path.join(c, "agents")}
    return {"skills": os.path.join(home, {"codex": ".agents/skills", "agy": ".gemini/config/skills",
                                          "cursor": ".cursor/skills"}[host])}


def desired(host, mode, items, home):
    """dest -> src for every link this host+mode wants."""
    d = host_dirs(host, home)
    out = {}
    for kind, name, src in items:
        if host == "claude":
            if kind == "leaf":
                out[os.path.join(d["skills"], name)] = src
            elif kind == "router-cmd":
                out[os.path.join(d["commands"], "devmode.md")] = src
            elif kind == "orchestrator":
                out[os.path.join(d["agents"], name + ".md")] = src
            elif kind == "role" and mode == "full":
                out[os.path.join(d["agents"], name + ".md")] = src
        else:
            if kind == "router-skill":
                out[os.path.join(d["skills"], "devmode")] = src
            elif kind == "leaf" and mode == "full":
                out[os.path.join(d["skills"], name)] = src
    return out


def plan(want, current, repo):
    """Diff wanted links against the filesystem snapshot.

    `current` maps a path to ("link", target) | ("real", None) for every entry in
    the host folders. Returns (actions, notes): actions are ("link", src, dest),
    ("relink", src, dest) or ("unlink", dest); notes are human-readable skips."""
    owned = lambda t: t is not None and (t == repo or t.startswith(repo + os.sep))  # noqa: E731
    actions, notes = [], []
    for dest, src in sorted(want.items()):
        state = current.get(dest)
        if state is None:
            actions.append(("link", src, dest))
        elif state[0] == "link" and state[1] == src:
            continue
        elif state[0] == "link" and owned(state[1]):
            actions.append(("relink", src, dest))
        elif state[0] == "link":
            notes.append(f"skip {dest}: links elsewhere ({state[1]})")
        else:
            notes.append(f"skip {dest}: a real file or folder already exists")
    for path, state in sorted(current.items()):
        if path in want or state[0] != "link" or not owned(state[1]):
            continue
        actions.append(("unlink", path))  # ours, but not wanted in this mode (or stale)
    return actions, notes


_DESC = re.compile(r"^description:\s*(.*?)(?=^[\w-]+:|\Z)", re.M | re.S)


def frontmatter(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}, ""
    if not text.startswith("---"):
        return {}, ""
    fm = text.split("---", 2)[1]
    m = _DESC.search(fm)
    desc = " ".join(m.group(1).replace(">-", " ").replace("|", " ").split()).strip("'\"") if m else ""
    return {"hidden": bool(re.search(r"^disable-model-invocation:\s*true\s*$", fm, re.M))}, desc


def listing_cost(host, want):
    """Estimated characters the host puts in every turn for these links."""
    chars, rows = 0, []
    for dest, src in sorted(want.items()):
        f = src if src.endswith(".md") else os.path.join(src, "SKILL.md")
        meta, desc = frontmatter(f)
        if host == "claude" and meta.get("hidden"):
            continue  # Claude Code drops hidden skills from the listing
        n = len(os.path.basename(dest)) + len(desc) + 4
        chars += n
        rows.append((os.path.basename(dest), n))
    return chars, rows


# ------------------------------------------------------------------ shell


def snapshot(dirs):
    cur = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            p = os.path.join(d, n)
            cur[p] = ("link", os.readlink(p)) if os.path.islink(p) else ("real", None)
    return cur


def state_path(home):
    return os.path.join(home, ".devmode", "install.json")


def load_state(home):
    try:
        with open(state_path(home)) as fh:
            return json.load(fh)
    except Exception:
        return {"hosts": {}}


def save_state(home, st, dry):
    if dry:
        return
    os.makedirs(os.path.dirname(state_path(home)), exist_ok=True)
    with open(state_path(home), "w") as fh:
        json.dump(st, fh, indent=2, sort_keys=True)


def ensure_home(home, repo, dry, out):
    base = os.path.join(home, ".devmode")
    if os.path.islink(base):
        if os.path.realpath(base) == os.path.realpath(repo):
            out("  converting ~/.devmode from a repo link to a folder")
            if not dry:
                os.unlink(base)
        else:
            out(f"  skip ~/.devmode: it links elsewhere ({os.readlink(base)})")
            return False
    elif os.path.exists(base) and not os.path.isdir(base):
        out("  skip ~/.devmode: a real file is in the way")
        return False
    if not dry:
        os.makedirs(base, exist_ok=True)
    want = {os.path.join(base, k): os.path.join(repo, v) if v else repo for k, v in HOME_LINKS.items()}
    cur = snapshot([base]) if os.path.isdir(base) else {}
    cur = {p: s for p, s in cur.items() if os.path.basename(p) in HOME_LINKS}
    acts, notes = plan(want, cur, repo)
    apply(acts, dry, out)
    for n in notes:
        out("  " + n)
    return True


def apply(actions, dry, out):
    for act in actions:
        if act[0] in ("link", "relink"):
            _, src, dest = act
            out(f"  {'would ' if dry else ''}{act[0]} {os.path.basename(dest)}")
            if not dry:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if act[0] == "relink":
                    os.unlink(dest)
                os.symlink(src, dest)
        else:
            out(f"  {'would ' if dry else ''}unlink {os.path.basename(act[1])}")
            if not dry:
                os.unlink(act[1])


def present(host, home):
    if host == "claude":
        return os.path.isdir(os.path.join(home, ".claude"))
    if host == "codex":
        return os.path.isdir(os.path.join(home, ".codex"))
    if host == "agy":
        return os.path.isdir(os.path.join(home, ".gemini", "config")) or \
            os.path.isdir(os.path.join(home, ".gemini", "antigravity"))
    return os.path.isdir(os.path.join(home, ".cursor")) and not os.path.isdir(os.path.join(home, ".claude"))


def main(argv=None, home=None, repo=None, out=print):
    p = argparse.ArgumentParser(prog="setup", description="devmode global installer")
    p.add_argument("--host", default="")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--lean", dest="mode", action="store_const", const="lean")
    g.add_argument("--full", dest="mode", action="store_const", const="full")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args(argv)
    home = home or os.path.expanduser("~")
    repo = repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    st = load_state(home)

    if a.host in ("", "auto"):
        if not a.host and not (a.check or a.report or a.uninstall):
            p.error("pass --host auto|claude|codex|agy|cursor")
        hosts = [h for h in HOSTS if present(h, home)] if a.host == "auto" else list(st["hosts"]) or \
            [h for h in HOSTS if present(h, home)]
    elif a.host in HOSTS:
        hosts = [a.host]
    else:
        p.error(f"unknown host {a.host!r}")
    if not hosts:
        out("no host folders found; pass --host explicitly")
        return 1

    items, status = inventory(repo), 0
    for h in hosts:
        mode = a.mode or st["hosts"].get(h) or "lean"
        want = desired(h, mode, items, home)
        cur = snapshot(host_dirs(h, home).values())
        if a.check:
            if h not in st["hosts"]:
                out(f"{h}: not installed")
                status = 1
                continue
            acts, notes = plan(want, cur, repo)
            missing = [k for k in HOME_LINKS if not os.path.islink(os.path.join(home, ".devmode", k))]
            for act in acts:
                out(f"  {h}: needs {act[0]} {os.path.basename(act[-1])}")
            for n in notes:
                out(f"  {h}: {n}")
            if missing:
                out(f"  {h}: ~/.devmode is missing {', '.join(missing)} (run setup again)")
            bad = len(acts) + len(notes) + len(missing)
            out(f"{h} ({mode}): {len(want)} wanted, {bad} problem(s)")
            status |= 1 if bad else 0
        elif a.report:
            chars, rows = listing_cost(h, want)
            listed = ", ".join(n for n, _ in rows) or "nothing"
            out(f"{h} ({mode}): ~{chars} chars ≈ {chars // 4} tokens per turn · listed: {listed}")
        elif a.uninstall:
            out(f"{h}: removing links into {repo}")
            acts, _ = plan({}, cur, repo)
            apply(acts, a.dry_run, out)
            st["hosts"].pop(h, None)
        else:
            out(f"{h} ({mode})")
            if not ensure_home(home, repo, a.dry_run, out):
                status = 1
                continue
            acts, notes = plan(want, cur, repo)
            apply(acts, a.dry_run, out)
            for n in notes:
                out("  " + n)
            st["hosts"][h] = mode
            out(f"  {len(want)} entries wanted, {len(acts)} change(s)")
    if a.uninstall and not st["hosts"]:
        base = os.path.join(home, ".devmode")
        if os.path.isdir(base) and not os.path.islink(base):
            apply(plan({}, snapshot([base]), repo)[0], a.dry_run, out)
            if not a.dry_run:
                if os.path.exists(state_path(home)):
                    os.remove(state_path(home))
                if os.listdir(base):
                    out("  kept ~/.devmode (it still holds your files, e.g. memories.jsonl)")
                else:
                    os.rmdir(base)
    elif not (a.check or a.report):
        save_state(home, st, a.dry_run)
    if a.dry_run:
        out("dry run: nothing changed")
    return status


if __name__ == "__main__":
    sys.exit(main())
