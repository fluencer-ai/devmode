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
                     description). full links every leaf skill too. Codex also gets
                     the devmode-orchestrator agent the router delegates to.

~/.devmode is a real folder: links into this repo (repo, skills, agents, references)
plus the user's global memories.jsonl, which uninstall never deletes. It never
overwrites a real file or a link it does not own; a clash is reported and skipped.
A link is ours to remove only when it points into this repo AND it was recorded in
install.json or carries the name of what it points to (a personal alias stays).
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
    codex_orch = os.path.join(repo, ".codex", "agents", "devmode-orchestrator.toml")
    if os.path.isfile(codex_orch):
        items.append(("codex-orchestrator", "devmode-orchestrator", codex_orch))
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
    d = {"skills": os.path.join(home, {"codex": ".agents/skills", "agy": ".gemini/config/skills",
                                       "cursor": ".cursor/skills"}[host])}
    if host == "codex":
        d["agents"] = os.path.join(home, ".codex", "agents")
    return d


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
            elif kind == "codex-orchestrator" and host == "codex":
                out[os.path.join(d["agents"], name + ".toml")] = src
    return out


def _named_like(dest, target):
    """Our links carry the name of what they point to (tdd -> skills/tdd)."""
    return os.path.basename(dest) == os.path.basename(target.rstrip(os.sep))


def plan(want, current, repo, managed=()):
    """Diff wanted links against the filesystem snapshot.

    `current` maps a path to ("link", target) | ("real", None) for every entry in
    the host folders. `managed` holds the links a previous run recorded. Returns
    (actions, notes): actions are ("link", src, dest), ("relink", src, dest) or
    ("unlink", dest); notes are human-readable skips."""
    owned = lambda t: t is not None and (t == repo or t.startswith(repo + os.sep))  # noqa: E731
    managed = set(managed)
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
        if path in managed or _named_like(path, state[1]):
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
    """The recorded install, {"hosts": {}} when there is none, or None when the
    file is not one this installer wrote (then nothing may write over it)."""
    path = state_path(home)
    if not os.path.lexists(path):
        return {"hosts": {}, "links": {}}
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    try:
        with open(path) as fh:
            st = json.load(fh)
    except Exception:
        return None
    if not isinstance(st, dict) or not isinstance(st.get("hosts"), dict):
        return None
    st.setdefault("links", {})
    return st


def save_state(home, st, dry):
    """Atomic replace inside a real ~/.devmode folder; never follows a link."""
    if dry:
        return
    base = os.path.dirname(state_path(home))
    if os.path.islink(base) or not os.path.isdir(base):
        return
    tmp = state_path(home) + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=2, sort_keys=True)
    os.replace(tmp, state_path(home))


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
    memory = os.path.join(base, "memories.jsonl")
    if not os.path.lexists(memory):
        out(f"  {'would create' if dry else 'create'} memories.jsonl (private, empty)")
        if not dry:
            os.close(os.open(memory, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
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


def home_link_problems(home, repo):
    """~/.devmode links that are missing, broken, or point somewhere else."""
    base = os.path.join(home, ".devmode")
    bad = []
    for k, v in HOME_LINKS.items():
        p, want = os.path.join(base, k), os.path.join(repo, v) if v else repo
        if not os.path.islink(p) or os.readlink(p) != want or not os.path.exists(p):
            bad.append(k)
    return bad


def present(host, home):
    if host == "claude":
        return os.path.isdir(os.path.join(home, ".claude"))
    if host == "codex":
        return os.path.isdir(os.path.join(home, ".codex"))
    if host == "agy":
        return os.path.isdir(os.path.join(home, ".gemini", "config")) or \
            os.path.isdir(os.path.join(home, ".gemini", "antigravity"))
    return os.path.isdir(os.path.join(home, ".cursor")) and not os.path.isdir(os.path.join(home, ".claude"))


class _Once(argparse.Action):
    """Refuse a repeated flag instead of silently keeping the last value."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, "_seen_" + self.dest, False):
            parser.error(f"{option_string} given twice; list hosts with commas")
        setattr(namespace, "_seen_" + self.dest, True)
        setattr(namespace, self.dest, values)


def main(argv=None, home=None, repo=None, out=print):
    p = argparse.ArgumentParser(prog="setup", description="devmode global installer")
    p.add_argument("--host", default="", action=_Once,
                   help="auto, or one or more of claude,codex,agy,cursor (comma-separated)")
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
    if st is None:
        out(f"stop: {state_path(home)} is not an install record this setup wrote; "
            "move it aside and run again")
        return 1

    if a.host in ("", "auto"):
        if not a.host and not (a.check or a.report or a.uninstall):
            p.error("pass --host auto|claude|codex|agy|cursor")
        hosts = [h for h in HOSTS if present(h, home)] if a.host == "auto" else list(st["hosts"]) or \
            [h for h in HOSTS if present(h, home)]
    else:
        hosts = [h.strip() for h in a.host.split(",") if h.strip()]
        unknown = [h for h in hosts if h not in HOSTS]
        if unknown or not hosts:
            p.error(f"unknown host {a.host!r}")
        hosts = [h for h in HOSTS if h in hosts]
    if not hosts:
        out("no host folders found; pass --host explicitly")
        return 1

    items, status = inventory(repo), 0
    if not (a.check or a.report or a.uninstall) and not ensure_home(home, repo, a.dry_run, out):
        return 1  # a refused ~/.devmode means nothing is installed and nothing is recorded
    for h in hosts:
        mode = a.mode or st["hosts"].get(h) or "lean"
        want = desired(h, mode, items, home)
        cur = snapshot(host_dirs(h, home).values())
        managed = st["links"].get(h, [])
        if a.check:
            if h not in st["hosts"]:
                out(f"{h}: not installed")
                status = 1
                continue
            acts, notes = plan(want, cur, repo, managed)
            missing = home_link_problems(home, repo)
            for act in acts:
                out(f"  {h}: needs {act[0]} {os.path.basename(act[-1])}")
            for n in notes:
                out(f"  {h}: {n}")
            if missing:
                out(f"  {h}: ~/.devmode has missing or wrong links: {', '.join(missing)} (run setup again)")
            bad = len(acts) + len(notes) + len(missing)
            out(f"{h} ({mode}): {len(want)} wanted, {bad} problem(s)")
            status |= 1 if bad else 0
        elif a.report:
            installed = {d: s for d, s in want.items() if cur.get(d) == ("link", s)}
            if not installed:
                out(f"{h}: not installed · 0 tokens per turn")
                continue
            chars, rows = listing_cost(h, installed)
            listed = ", ".join(n for n, _ in rows) or "nothing"
            gap = f" · {len(want) - len(installed)} wanted entry(ies) missing" if len(installed) < len(want) else ""
            out(f"{h} ({mode}): ~{chars} chars ≈ {chars // 4} tokens per turn · listed: {listed}{gap}")
        elif a.uninstall:
            out(f"{h}: removing links into {repo}")
            acts, _ = plan({}, cur, repo, managed)
            apply(acts, a.dry_run, out)
            st["hosts"].pop(h, None)
            st["links"].pop(h, None)
        else:
            out(f"{h} ({mode})")
            acts, notes = plan(want, cur, repo, managed)
            apply(acts, a.dry_run, out)
            for n in notes:
                out("  " + n)
            st["hosts"][h] = mode
            if not a.dry_run:  # record exactly what we hold, so a later run can prune it
                st["links"][h] = sorted(d for d, s in want.items()
                                        if os.path.islink(d) and os.readlink(d) == s)
            out(f"  {len(want)} entries wanted, {len(acts)} change(s)")
    if a.uninstall and not st["hosts"]:
        base = os.path.join(home, ".devmode")
        if os.path.isdir(base) and not os.path.islink(base):
            home_links = {os.path.join(base, k) for k in HOME_LINKS}
            cur = {p: s for p, s in snapshot([base]).items() if p in home_links}
            apply(plan({}, cur, repo, home_links)[0], a.dry_run, out)
            if not a.dry_run:
                if os.path.isfile(state_path(home)) and not os.path.islink(state_path(home)):
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
