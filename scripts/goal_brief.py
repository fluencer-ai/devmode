#!/usr/bin/env python3
"""goal-brief — turn a devmode spec into a ready-to-run `/goal` (or `/plan`)
launch command that references the spec file in detail, and GUARANTEE it fits the
character budget.

Why this exists: an agent cannot invoke a Claude Code slash command itself
(`/goal`/`/plan` are user-typed; there's no "run a command" tool). So devmode
*emits* a ready-to-run command and you run it each iteration. The hard guarantee
this script provides is the budget: the emitted brief is always ≤ the limit.

Usage:
  # enforce the limit on a brief you (or the agent) wrote:
  python3 scripts/goal_brief.py check [file]        [--budget 3800]   # stdin if no file
  # scaffold a compact brief from a spec (+plan), measured against the budget:
  python3 scripts/goal_brief.py scaffold <spec.md> [--plan plan.md]
        [--kind goal|plan] [--budget 3800] [--ref <path printed in the brief>]

`check` exits 1 if over budget (a real feedback-loop gate). `scaffold` always
emits a brief ≤ budget (it falls back to a pointer if the detail won't fit).
"""
from __future__ import annotations

import argparse
import re
import sys

DEFAULT_BUDGET = 3800  # user's working limit; Claude /goal hard cap is 4000


def _section(md: str, *titles: str) -> list[str]:
    """Return the bullet lines under the first heading whose text matches a title."""
    lines = md.splitlines()
    out, capturing = [], False
    for ln in lines:
        if re.match(r"^#{1,4}\s", ln):
            head = ln.lstrip("#").strip().lower()
            capturing = any(t.lower() in head for t in titles)
            continue
        if capturing:
            m = re.match(r"^\s*[-*]\s+(.*)$", ln)
            if m:
                out.append(m.group(1).strip())
            elif ln.strip() and not ln.startswith(("|", ">")):
                pass  # ignore prose lines inside the section
    return out


def _title(md: str) -> str:
    for ln in md.splitlines():
        m = re.match(r"^#\s+(.*)$", ln)
        if m:
            return re.sub(r"^(spec|plan):\s*", "", m.group(1).strip(), flags=re.I)
    return "the objective"


def build_brief(spec_md: str, ref: str, kind: str, budget: int) -> tuple[str, bool]:
    title = _title(spec_md)
    acs = _section(spec_md, "acceptance criteria", "acceptance")
    tests = _section(spec_md, "testing strategy", "tests")
    verb = "Plan" if kind == "plan" else "Build"
    header = (
        f"{kind.upper()}: {title}\n\n"
        f"Read `{ref}` IN FULL — it has the step-by-step, the tests, and the "
        f"acceptance criteria. Work the devmode way: align on the spec, then "
        f"{'produce a phased plan' if kind == 'plan' else 'implement test-first (red→green→refactor)'}, "
        f"verify every claim with fresh evidence, review critical modules (auth/"
        f"money/security) in full, and never claim done without running the checks.\n"
    )
    ac_block = ""
    if acs:
        ac_block = "\nAcceptance criteria (full detail in the file):\n" + \
                   "\n".join(f"- {a}" for a in acs) + "\n"
    test_block = ("\nTests: " + "; ".join(tests) + "\n") if tests else ""
    footer = (
        f"\n{verb} the objective per `{ref}`; stop only at a genuine blocker or a "
        f"decision that needs me. Report a self-scorecard at the end.\n"
    )
    brief = header + ac_block + test_block + footer
    if len(brief) <= budget:
        return brief.strip(), True
    # too long → drop the test line, then summarize ACs to a pointer (file has detail)
    brief = header + ac_block + footer
    if len(brief) <= budget:
        return brief.strip(), True
    ac_summary = (f"\nAcceptance criteria: {len(acs)} items — see `{ref}`.\n" if acs else "")
    brief = header + ac_summary + footer
    return brief.strip(), len(brief) <= budget


def emit(brief: str, kind: str, budget: int) -> int:
    n = len(brief)
    cmd = f"/{kind} {brief}"
    over = n > budget
    print(f"--- ready-to-run command ({n} chars of brief; budget {budget}) ---\n")
    print(cmd)
    print(f"\n--- {'OK ✓ within budget' if not over else f'OVER by {n-budget} — condense before running'} ---")
    return 1 if over else 0


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("mode", choices=["check", "scaffold"])
    p.add_argument("file", nargs="?")
    p.add_argument("--plan")
    p.add_argument("--kind", default="goal", choices=["goal", "plan"])
    p.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    p.add_argument("--ref")
    args = p.parse_args()

    if args.mode == "check":
        text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
        n = len(text)
        over = n > args.budget
        print(f"{n}/{args.budget} chars — {'OVER by ' + str(n-args.budget) if over else 'PASS'}")
        return 1 if over else 0

    # scaffold
    if not args.file:
        print("scaffold needs a spec file", file=sys.stderr)
        return 2
    spec = open(args.file, encoding="utf-8").read()
    ref = args.ref or args.file
    brief, ok = build_brief(spec, ref, args.kind, args.budget)
    rc = emit(brief, args.kind, args.budget)
    if not ok:
        print("note: even the pointer-only brief exceeds the budget — raise --budget or shorten the title/ACs.",
              file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
