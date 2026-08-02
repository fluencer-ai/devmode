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


CODEX_READ_ONLY_AGENTS = {
    "complexity-reviewer",
    "code-quality-analyzer",
    "security-scanner",
    "test-coverage-analyzer",
}


def _toml_string(text: str, key: str) -> str | None:
    match = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"\s*$', text, re.M)
    return match.group(1) if match else None


def audit_codex_agents() -> list[str]:
    """Validate project-scoped Codex adapters and their canonical sources."""
    errors: list[str] = []
    codex_dir = os.path.join(ROOT, ".codex", "agents")
    if not os.path.isdir(codex_dir):
        return [".codex/agents: missing Codex agent adapters"]

    base_agents = {
        f[:-3] for f in os.listdir(os.path.join(ROOT, ".agents"))
        if f.endswith(".md")
    }
    expected = base_agents | {"devmode-orchestrator"}
    found = {f[:-5] for f in os.listdir(codex_dir) if f.endswith(".toml")}
    for name in sorted(expected - found):
        errors.append(f".codex/agents/{name}.toml: missing adapter")
    for name in sorted(found - expected):
        errors.append(f".codex/agents/{name}.toml: no canonical Claude agent")

    print(f"{DIM}Auditing {len(found)} Codex agent adapters…{OFF}")
    for name in sorted(found):
        path = os.path.join(codex_dir, f"{name}.toml")
        rel = os.path.relpath(path, ROOT)
        text = open(path, encoding="utf-8").read()
        configured_name = _toml_string(text, "name")
        if configured_name != name:
            errors.append(f"{rel}: name '{configured_name}' != file '{name}'")
        if not _toml_string(text, "description"):
            errors.append(f"{rel}: missing description")
        instructions = re.search(r'^\s*developer_instructions\s*=\s*"""(.+?)"""', text, re.M | re.S)
        if not instructions or not instructions.group(1).strip():
            errors.append(f"{rel}: missing developer_instructions")

        source = (os.path.join(".claude", "agents", "devmode-orchestrator.md")
                  if name == "devmode-orchestrator"
                  else os.path.join(".agents", f"{name}.md"))
        if source not in text:
            errors.append(f"{rel}: does not reference canonical source {source}")
        elif not os.path.isfile(os.path.join(ROOT, source)):
            errors.append(f"{rel}: canonical source missing: {source}")

        sandbox = _toml_string(text, "sandbox_mode")
        if name in CODEX_READ_ONLY_AGENTS and sandbox != "read-only":
            errors.append(f"{rel}: review-only adapter must set sandbox_mode = \"read-only\"")
        print(f"  {GREEN}✓{OFF} {name}")
    return errors


def audit_codex_skills(root: str = ROOT) -> list[str]:
    """Every skill must be *reachable from Codex*, not just present.

    `audit_codex_agents` guards the Codex agent surface; the Codex **skill**
    surface had no guard at all. A skill added to `skills/` without its
    `.agents/skills/` link is invisible to Codex while the audit still exits 0.
    The Claude side cannot desync from itself (`skills/` is its own discovery
    root), so the asymmetry is real and one-directional.
    """
    errors: list[str] = []
    skills_dir = os.path.join(root, "skills")
    codex_dir = os.path.join(root, ".agents", "skills")
    if not os.path.isdir(skills_dir):
        return []
    names = sorted(n for n in os.listdir(skills_dir)
                   if os.path.isdir(os.path.join(skills_dir, n)))
    print(f"{DIM}Checking Codex skill view ({len(names)} links + launcher)…{OFF}")
    for name in names:
        rel = f".agents/skills/{name}"
        link = os.path.join(codex_dir, name)
        expected = os.path.join("../../skills", name)
        if not os.path.islink(link):
            errors.append(f"{rel}: missing link — '{name}' is invisible to Codex")
            continue
        actual = os.readlink(link)
        if actual != expected:
            errors.append(f"{rel}: links to '{actual}', expected '{expected}'")
        elif not os.path.isfile(os.path.join(link, "SKILL.md")):
            errors.append(f"{rel}: link resolves to no SKILL.md")
    for extra in ("SKILL.md", "agents/openai.yaml"):
        if not os.path.isfile(os.path.join(codex_dir, "devmode", *extra.split("/"))):
            errors.append(f".agents/skills/devmode/{extra}: launcher file missing")
    flag = f"{RED}✗{OFF}" if errors else f"{GREEN}✓{OFF}"
    print(f"  {flag} {len(names)} skills reachable from Codex, {len(errors)} problem(s)")
    return errors


# The skill/agent totals are hand-written as prose in ~10 tracked files (README
# badges + "What's in the box" + the section headings, both manuals, INTEGRATION.md,
# the /devmode command and the orchestrator agent). audit_skills/audit_agents
# count the real folders but never checked those written numbers, so the docs
# could drift silently — a stale "38 skills" nearly shipped to the GitHub About.
#
# A digit glued to skills/agents is a TOTAL claim. The nouns cover English
# `skills`/`agents`, the README's `subagents`, and MANUAL-PT-BR.md's `agentes`.
COUNT_RE = re.compile(r"(\d+)\s+(skills|subagents|agentes|agents)\b", re.I)
# ...except a number qualified by a sub-category — "20 skills de processo",
# "18 skills de domínio" — is a partial count, not the grand total, so it is
# left out of the comparison.
BREAKDOWN_RE = re.compile(r"\s*(de\s+)?(process|processo|domains?|dom[íi]nio|meta)\b", re.I)
# A sub-count has no filesystem ground truth (nothing marks a skill "process" vs
# "domain"), so it can't be checked against reality — but every doc must at least
# agree with every other doc. A stale "20 skills de processo" survived a 41→42
# reconciliation precisely because the total check skips these; this catches the
# contradiction instead.
SUBCOUNT_RE = re.compile(
    r"(\d+)\s+(?:\*?skills?\*?\s+)?(?:de\s+)?\*?(process|processo|domains?|dom[íi]nio|meta)\*?\b", re.I)
# The README states each sub-count TWICE and in two shapes: the digit-first prose
# ("21 *process* + 18 *domain*") that SUBCOUNT_RE matches, and the section heading
# "<b>Process skills (21)</b>" where the digit trails the category. Only the first
# was collected, so a stale "(20)" heading sat one screen from a correct "21" and
# the audit still passed — exactly the drift this check exists to catch.
SUBCOUNT_TRAILING_RE = re.compile(
    r"\b(process|processo|domains?|dom[íi]nio|meta)\b[^()\n]{0,20}\((\d+)\)", re.I)
_CATEGORY = {"process": "process", "processo": "process", "domain": "domain",
             "domains": "domain", "domínio": "domain", "dominio": "domain", "meta": "meta"}


def subcount_conflicts(seen: dict[str, dict[int, list[str]]]) -> list[str]:
    """Return one error per sub-category whose written counts disagree across docs."""
    errors: list[str] = []
    for cat, by_value in sorted(seen.items()):
        if len(by_value) > 1:
            detail = "; ".join(f"{v} in {', '.join(locs[:3])}"
                               for v, locs in sorted(by_value.items()))
            errors.append(f"conflicting '{cat}' sub-counts across docs: {detail}")
    return errors


def collect_subcounts(rel: str, text: str, seen: dict[str, dict[int, list[str]]]) -> None:
    """Record every written per-category sub-count so conflicts can be reported."""
    for lineno, line in enumerate(text.splitlines(), 1):
        # An attribution/provenance row ("12 domain skills came from <source>") counts
        # what one upstream contributed, not what the pack holds — different claim,
        # so an external link on the line disqualifies it from the consistency check.
        if "](http" in line:
            continue
        for m in SUBCOUNT_RE.finditer(line):
            cat = _CATEGORY.get(m.group(2).lower())
            if cat:
                seen.setdefault(cat, {}).setdefault(int(m.group(1)), []).append(f"{rel}:{lineno}")
        for m in SUBCOUNT_TRAILING_RE.finditer(line):
            cat = _CATEGORY.get(m.group(1).lower())
            if cat:
                seen.setdefault(cat, {}).setdefault(int(m.group(2)), []).append(f"{rel}:{lineno}")


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
    seen_subcounts: dict[str, dict[int, list[str]]] = {}
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
            rel, body = os.path.relpath(mf, ROOT), open(mf, encoding="utf-8").read()
            errors += count_drift(rel, body, real_skills, real_agents)
            collect_subcounts(rel, body, seen_subcounts)
    errors += subcount_conflicts(seen_subcounts)
    flag = f"{RED}✗{OFF}" if errors else f"{GREEN}✓{OFF}"
    print(f"  {flag} {scanned} markdown files scanned, {len(errors)} count drift(s)")
    return errors


MIRRORS = [
    (".claude/commands/devmode.md", "integrations/conductor-beads/commands/devmode.md"),
    (".claude/agents/devmode-orchestrator.md", "integrations/conductor-beads/agents/devmode-orchestrator.md"),
    (".codex/config.toml", "integrations/conductor-beads/templates/codex.config.toml"),
    (".codex/hooks/codex_hooks.py", "integrations/conductor-beads/hooks/codex_hooks.py"),
    (".claude/hooks/devmode_phase_gate.py", "integrations/conductor-beads/hooks/devmode_phase_gate.py"),
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


# A loaded file (skill, agent, command, deployed template) is re-read into context
# on every use, so upstream provenance in it is attention spent on something the
# agent cannot act on — and the pack lost that discipline twice before it was
# written down. Credit belongs in README.md / ATTRIBUTION.md, which is also where a
# licence's attribution condition is satisfied. Functional URLs (an XML namespace)
# are not provenance and are allowed.
PROVENANCE_RE = re.compile(
    r"https?://(?:www\.)?(?:github|gist\.github)\.com/"      # a source repo link
    r"|\bgithub\.com/[\w.-]+/[\w.-]+"                         # …or a bare owner/repo
    r"|\((?:MIT|Apache-2\.0|CC-BY[\w.-]*)\)"                  # "(MIT)"
    r"|,\s*(?:MIT|Apache-2\.0|CC-BY[\w.-]*)\b"                # ", MIT"
    r"|\bAdapted from\b|\bConsolidated from\b",               # the footer opener
    re.I)
LOADED_GLOBS = ("skills", ".agents", ".codex",
                os.path.join("integrations", "conductor-beads", "commands"),
                os.path.join("integrations", "conductor-beads", "agents"),
                os.path.join("integrations", "conductor-beads", "templates"),
                os.path.join("integrations", "llm-wiki", "templates"))


def audit_provenance() -> list[str]:
    """Fail if a context-loaded file carries upstream credit instead of the docs."""
    errors: list[str] = []
    scanned = 0
    for rel_root in LOADED_GLOBS:
        base = os.path.join(ROOT, rel_root)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fns in os.walk(base):
            for f in fns:
                if not f.endswith((".md", ".py", ".toml", ".json", ".yaml", ".yml")):
                    continue
                mf = os.path.join(dp, f)
                scanned += 1
                for lineno, line in enumerate(
                        open(mf, encoding="utf-8").read().splitlines(), 1):
                    m = PROVENANCE_RE.search(line)
                    if m:
                        errors.append(
                            f"{os.path.relpath(mf, ROOT)}:{lineno}: provenance in a "
                            f"loaded file ('{m.group(0)[:40]}') — move it to "
                            f"README.md / ATTRIBUTION.md")
    flag = f"{RED}✗{OFF}" if errors else f"{GREEN}✓{OFF}"
    print(f"  {flag} {scanned} loaded files scanned, {len(errors)} provenance leak(s)")
    return errors


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
    codex_agent_errors = audit_codex_agents()
    print()
    codex_skill_errors = audit_codex_skills()
    print()
    count_errors = audit_counts()
    print()
    mirror_errors = audit_mirrors()
    print()
    prov_errors = audit_provenance()
    print()
    audit_overlap()
    print()
    link_errors = audit_links()
    errors = (skill_errors + agent_errors + codex_agent_errors + codex_skill_errors
              + count_errors + mirror_errors + prov_errors + link_errors)
    print()
    if errors:
        print(f"{RED}✗ {len(errors)} issue(s):{OFF}")
        for e in errors:
            print(f"  {RED}-{OFF} {e}")
        return 1
    print(f"{GREEN}✓ skills + Claude/Codex agents are consistent "
          f"(frontmatter, adapters, names, counts, provenance, links).{OFF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
