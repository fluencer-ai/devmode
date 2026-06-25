#!/usr/bin/env python3
"""Audit the devmode skill pack for mechanical consistency.

Checks the invariants a script can verify objectively (the judgment calls live
in skills/authoring-skills/SKILL.md):

  - every skills/<name>/SKILL.md has YAML-ish frontmatter with `name` + `description`
  - frontmatter `name` matches its folder name
  - SKILL.md body stays under the line budget (progressive disclosure)
  - every .agents/<name>.md has frontmatter with `name` (matching the file) + `description`
  - every written "N skills"/"N agents" total in tracked markdown matches the
    real directory counts (so a stale "38 skills" can't ship to the README/About)
  - every relative markdown link in the repo resolves (excluding workspaces/ scratch)

Exit code 0 = clean; 1 = at least one hard failure. Soft issues (line budget)
are warnings and do not fail the run.

Usage:  python3 scripts/audit_skills.py
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, "skills")
LINE_BUDGET = 500
LINK_RE = re.compile(r"\]\(([^)]+)\)")

GREEN, RED, YELLOW, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def frontmatter(text: str) -> dict | None:
    """Parse the leading --- ... --- block into a flat key->value dict."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    data: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip()
        elif key and line.strip():  # folded/continued value (e.g. `>-` blocks)
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def audit_skills() -> list[str]:
    errors: list[str] = []
    if not os.path.isdir(SKILLS_DIR):
        return [f"no skills/ directory at {SKILLS_DIR}"]
    names = sorted(d for d in os.listdir(SKILLS_DIR)
                   if os.path.isdir(os.path.join(SKILLS_DIR, d)))
    print(f"{DIM}Auditing {len(names)} skills…{OFF}")
    for name in names:
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        rel = os.path.relpath(skill_md, ROOT)
        if not os.path.isfile(skill_md):
            errors.append(f"{rel}: missing SKILL.md")
            continue
        text = open(skill_md, encoding="utf-8").read()
        fm = frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: missing/!malformed frontmatter")
            continue
        if not fm.get("name"):
            errors.append(f"{rel}: frontmatter missing `name`")
        elif fm["name"] != name:
            errors.append(f"{rel}: name '{fm['name']}' != folder '{name}'")
        desc = fm.get("description", "")
        if not desc:
            errors.append(f"{rel}: frontmatter missing `description`")
        elif not re.search(r"\b(use when|when |trigger)", desc, re.I):
            # janitor-style trigger lint (soft): a good description says WHEN to fire
            print(f"  {YELLOW}~{OFF} {name}: description lacks a clear 'when…' trigger")
        body_lines = text.count("\n") + 1
        flag = f"{YELLOW}!{OFF}" if body_lines > LINE_BUDGET else f"{GREEN}✓{OFF}"
        warn = f"  {YELLOW}(over {LINE_BUDGET}-line budget){OFF}" if body_lines > LINE_BUDGET else ""
        print(f"  {flag} {name}  {DIM}{body_lines} lines{OFF}{warn}")
    return errors


def audit_agents() -> list[str]:
    """Validate .agents/*.md: frontmatter present, name matches filename, description."""
    errors: list[str] = []
    agents_dir = os.path.join(ROOT, ".agents")
    if not os.path.isdir(agents_dir):
        return errors
    files = sorted(f for f in os.listdir(agents_dir) if f.endswith(".md"))
    print(f"{DIM}Auditing {len(files)} agents…{OFF}")
    for f in files:
        rel = os.path.relpath(os.path.join(agents_dir, f), ROOT)
        fm = frontmatter(open(os.path.join(agents_dir, f), encoding="utf-8").read())
        stem = f[:-3]
        if fm is None:
            errors.append(f"{rel}: missing/malformed frontmatter")
        else:
            if not fm.get("name"):
                errors.append(f"{rel}: frontmatter missing `name`")
            elif fm["name"] != stem:
                errors.append(f"{rel}: name '{fm['name']}' != file '{stem}'")
            if not fm.get("description"):
                errors.append(f"{rel}: frontmatter missing `description`")
        print(f"  {GREEN}✓{OFF} {stem}")
    return errors


# The skill/agent totals are hand-written as prose in ~10 tracked files (README
# badges + "What's in the box" + the section headings, manual.md, INTEGRATION.md,
# the /devmode command and the orchestrator agent). audit_skills/audit_agents
# count the real folders but never checked those written numbers, so the docs
# could drift silently — a stale "38 skills" nearly shipped to the GitHub About.
#
# A digit glued to skills/agents is a TOTAL claim. The nouns cover English
# `skills`/`agents`, the README's `subagents`, and manual.md's PT-BR `agentes`.
COUNT_RE = re.compile(r"(\d+)\s+(skills|subagents|agentes|agents)\b", re.I)
# ...except a number qualified by a sub-category — "20 skills de processo",
# "18 skills de domínio" — is a partial count, not the grand total, so it is
# left out of the comparison.
BREAKDOWN_RE = re.compile(r"\s*(de\s+)?(process|processo|domains?|dom[íi]nio|meta)\b", re.I)


def count_drift(rel: str, text: str, real_skills: int, real_agents: int) -> list[str]:
    """Return one error per written skill/agent total that diverges from reality."""
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in COUNT_RE.finditer(line):
            if BREAKDOWN_RE.match(line[m.end():]):
                continue  # a sub-category count (e.g. "de processo"), not the total
            found = int(m.group(1))
            label, expected = (("skills", real_skills) if m.group(2).lower() == "skills"
                               else ("agents", real_agents))
            if found != expected:
                errors.append(
                    f"{rel}:{lineno}: wrote '{m.group(0)}' but there are "
                    f"{expected} {label} (found {found})")
    return errors


def audit_counts() -> list[str]:
    """Fail if any prose skill/agent total drifted from the real directory counts."""
    real_skills = (sum(1 for d in os.listdir(SKILLS_DIR)
                       if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md")))
                   if os.path.isdir(SKILLS_DIR) else 0)
    agents_dir = os.path.join(ROOT, ".agents")
    real_agents = (sum(1 for f in os.listdir(agents_dir)
                       if f.endswith(".md") and f[:-3].lower() != "readme")
                   if os.path.isdir(agents_dir) else 0)
    print(f"{DIM}Checking written totals against {real_skills} skills / {real_agents} agents…{OFF}")
    errors: list[str] = []
    scanned = 0
    for dp, dn, fns in os.walk(ROOT):
        if "/workspaces" in dp or "/.git" in dp:
            dn[:] = [d for d in dn if d not in (".git",)]
            if "/workspaces" in dp:
                continue
        for f in fns:
            if not f.endswith(".md"):
                continue
            mf = os.path.join(dp, f)
            scanned += 1
            errors += count_drift(os.path.relpath(mf, ROOT),
                                  open(mf, encoding="utf-8").read(),
                                  real_skills, real_agents)
    flag = f"{RED}✗{OFF}" if errors else f"{GREEN}✓{OFF}"
    print(f"  {flag} {scanned} markdown files scanned, {len(errors)} count drift(s)")
    return errors


MIRRORS = [
    (".claude/commands/devmode.md", "integrations/conductor-beads/commands/devmode.md"),
    (".claude/agents/devmode-orchestrator.md", "integrations/conductor-beads/agents/devmode-orchestrator.md"),
]


def audit_mirrors() -> list[str]:
    """The lab's .claude/ copies of /devmode must stay identical to the integration source."""
    errors: list[str] = []
    print(f"{DIM}Checking {len(MIRRORS)} mirrored files…{OFF}")
    for copy, src in MIRRORS:
        cp, sp = os.path.join(ROOT, copy), os.path.join(ROOT, src)
        if not os.path.isfile(sp):
            errors.append(f"{src}: source missing")
            continue
        if not os.path.isfile(cp):
            errors.append(f"{copy}: mirror missing (copy from {src})")
            continue
        ok = open(cp, encoding="utf-8").read() == open(sp, encoding="utf-8").read()
        print(f"  {GREEN+'✓'+OFF if ok else RED+'✗'+OFF} {copy} == {src}")
        if not ok:
            errors.append(f"{copy} drifted from {src} (re-copy)")
    return errors


_STOP = set("the a an and or of to for in on with you your this that use when it is be as by from into not "
            "if then so do does done will would should can could may might per via not only also their its "
            "what which how why before after over under run runs running used using user agent skill skills "
            "devmode code change task work make made keep give given get gets are was were has have had".split())
_WORD = re.compile(r"[a-z][a-z][a-z]+")


def _keywords(text: str) -> set:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def audit_overlap(threshold: float = 0.40) -> list[str]:
    """Flag skill pairs whose descriptions overlap heavily — a duplication smell.

    Informational (prints, never fails the build): legitimately-related skills
    share vocabulary, so high overlap is a *review* signal, not an error. Adapted
    from skills-janitor's Jaccard description-overlap detector (MIT).
    """
    if not os.path.isdir(SKILLS_DIR):
        return []
    descs = {}
    for name in sorted(os.listdir(SKILLS_DIR)):
        p = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        fm = frontmatter(open(p, encoding="utf-8").read()) or {}
        kw = _keywords(fm.get("description", ""))
        if kw:
            descs[name] = kw
    names = list(descs)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = descs[names[i]], descs[names[j]]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= threshold:
                pairs.append((jac, names[i], names[j]))
    pairs.sort(reverse=True)
    if pairs:
        print(f"{YELLOW}~ description overlap (review for duplication):{OFF}")
        for jac, x, y in pairs:
            print(f"  {YELLOW}~{OFF} {jac:.0%}  {x}  ~  {y}")
    else:
        print(f"{DIM}No skill-description overlap above {threshold:.0%}.{OFF}")
    return []  # informational only — never fails the run


def audit_links() -> list[str]:
    errors: list[str] = []
    checked = 0
    for dp, dn, fns in os.walk(ROOT):
        if "/workspaces" in dp or "/.git" in dp:
            dn[:] = [d for d in dn if d not in (".git",)]
            if "/workspaces" in dp:
                continue
        for f in fns:
            if not f.endswith(".md"):
                continue
            mf = os.path.join(dp, f)
            text = open(mf, encoding="utf-8").read()
            for m in LINK_RE.finditer(text):
                target = m.group(1).strip()
                if target.startswith(("http", "#", "<", "mailto:")):
                    continue
                path = target.split("#")[0]
                if not path:
                    continue
                checked += 1
                resolved = os.path.normpath(os.path.join(os.path.dirname(mf), path))
                if not os.path.exists(resolved):
                    errors.append(f"{os.path.relpath(mf, ROOT)} -> {target} (broken)")
    print(f"{DIM}Checked {checked} relative markdown links.{OFF}")
    return errors


def main() -> int:
    print(f"\n{DIM}== devmode skill audit =={OFF}")
    skill_errors = audit_skills()
    print()
    agent_errors = audit_agents()
    print()
    count_errors = audit_counts()
    print()
    mirror_errors = audit_mirrors()
    print()
    audit_overlap()
    print()
    link_errors = audit_links()
    errors = skill_errors + agent_errors + count_errors + mirror_errors + link_errors
    print()
    if errors:
        print(f"{RED}✗ {len(errors)} issue(s):{OFF}")
        for e in errors:
            print(f"  {RED}-{OFF} {e}")
        return 1
    print(f"{GREEN}✓ skills + agents are consistent (frontmatter, names, counts, links).{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
