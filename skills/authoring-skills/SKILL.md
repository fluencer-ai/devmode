---
name: authoring-skills
description: >-
  Skill authoring: write, edit, and audit devmode SKILL.md files so they change
  behavior and stay consistent. Use when creating or editing a skill, agent, or
  steering file, when auditing the pack for drift or duplication, or when a skill
  is not followed.
disable-model-invocation: true
---

# Authoring skills

devmode *is* a skill pack, so maintaining the skills well is part of the work.
A skill is not a tutorial and not a story about how you once solved something:
it is a **knowledge-externalization mechanism**: edit a markdown file, and the
model's behavior changes on the next invocation, at zero training cost. The same
writing rules hold for every document an agent consumes: a skill, an agent
definition, `CLAUDE.md` / `AGENTS.md`, a doc reached by a pointer.

Writing the body itself (where each piece sits, splitting, leading words,
pruning)? Read `writing-for-agents.md` in this folder.

## The value test: knowledge delta

> **Good skill = expert-only knowledge − what the model already knows.**

A skill earns its place only by the *gap* it closes: decision trees, trade-offs,
edge cases, anti-patterns, domain-specific judgment: things experience teaches.
If the model already does it well without the skill, the skill is noise. Before
writing, ask: "what does an agent get *wrong* without this?" If the honest answer
is "nothing", don't write it.

## Write skills test-first (TDD for documentation)

Writing a skill is `tdd` applied to process docs:

1. **RED: watch it fail first.** Run a realistic pressure scenario *without* the
   skill and record the exact wrong behavior and the rationalizations the agent
   uses. If you didn't watch it fail, you don't know what the skill must teach.
2. **GREEN: write the minimal skill** that addresses those specific failures.
3. **REFACTOR: close loopholes.** Re-run; find the new rationalization the agent
   reaches for; plug it; re-verify. Repeat until it complies under pressure.

**Editing is not just adding.** When you change a skill that already works, a new
rule can dilute or quietly contradict guidance it already carried: the pack
accretes edits over many passes, so behavior it once handled can regress. Don't
stop at proving the new failure is fixed: re-run a scenario the skill *already*
handled to confirm you didn't break it, and try one *different*, unseen case in
the same class so the fix generalizes instead of overfitting the single scenario
you watched fail.

This is why the strongest skills (`systematic-debugging`,
`verification-before-completion`) carry rationalization tables and red-flag
lists: those are the plugged loopholes.

## The two loads

Every document and pointer you add spends one of two budgets:

- **Context load:** always-loaded material (a `CLAUDE.md` line, a visible skill's
  description) costs tokens and attention on every turn, whether it fires or not.
- **Cognitive load:** the human is the index of what exists and when to reach for
  it. Spend it where human judgement matters; remove it where it does not.

## Invocation: user-invoked vs model-invoked

- **Model-invoked** skills keep their description in the model's context so the
  agent can fire them on its own. That is permanent context load, paid for
  discoverability.
- **User-invoked** skills set `disable-model-invocation: true`. Only a human typing
  `/<name>`, or an agent told to read the file by path, reaches them. Zero context
  load.

**In devmode every leaf skill is user-invoked** (`disable-model-invocation: true`,
no exceptions). Only the `/devmode` router is visible; it names the leaves and the
orchestrator reads `skills/<name>/SKILL.md` by path. A new skill must not become
model-invoked: route to it from the router instead.

## Anatomy of a devmode skill

- **Frontmatter:** `name` (matches the folder), `description`, and
  `disable-model-invocation: true`. Keep any other existing keys.
- **Description is a context pointer.** The router and the human read it to
  decide when to open the skill, so its wording decides whether it gets reached.
  Shape: what it is in one clause, then "Use when <case>, <case>, or <case>." At
  most **300 characters** after whitespace collapses. Front-load the leading
  keyword. One trigger per distinct case; collapse synonyms into one. No example
  quote lists, no "pairs with" prose (that belongs in the body).
- **Body (imperative, target ~180 lines):** lead with the *why* (the problem and
  the principle), then the steps/decision rules, then anti-patterns/red flags.
  Explain reasoning rather than barking MUSTs: the model has good theory of mind
  and follows understood rules better than rote ones. **Steer by the positive.** A
  prohibition drags the forbidden behavior into context and makes it *more*
  available, so state the target: "write one-line comments", not "never write
  verbose comments". Keep a bare "don't" only as a guardrail you genuinely can't
  phrase positively, and even then pair it with what to do instead.
- **Completion criteria.** Every step ends on a checkable condition ("the
  frontier is empty", "every modified model accounted for"). A vague bound
  ("understanding reached") invites **premature completion**; the fix ladder is in
  `writing-for-agents.md`.
- **Sibling files for reference.** Material only some cases need goes into a
  sibling `.md` in the same folder, behind a one-line pointer that says *when* to
  read it ("Deciding mock boundaries? Read `testing-principles.md` in this
  folder."). Inline what every case needs. Bundled `assets/` and `scripts/` only
  when they pull their weight.
- **Cross-references:** name another skill as its bare name in backticks
  (`tdd`); the reader opens it by path. No relative `../x/SKILL.md` links. A
  sibling file is named relative to the skill folder.
- **Fusing skills:** when skill B folds into A, B's body moves to `A/<b-name>.md`
  with every rule kept, A gets a one-line "Absorbed: B" note, and B's folder is
  removed.

## Audit checklist

Run this when reviewing the pack (the script below automates the mechanical parts):

- **Frontmatter present & valid**: `name` matches the folder; the flag is set;
  `description` states what + when within 300 characters.
- **Knowledge delta is real**, not restating what the model already knows; apply
  the same test line by line (a line the model already obeys is a **no-op**), and
  settle no-op disputes by running the skill, not by debating the default.
- **Right altitude**: concrete enough to act on, general enough to reuse; not
  overfit to one example.
- **No sprawl, co-located**: a SKILL.md can be too long even when every line is
  live; move reference down to sibling files, and keep each concept under one
  heading (`writing-for-agents.md`).
- **No contradiction or duplication**: it doesn't fight another skill's advice
  or duplicate it (e.g. coverage targets vs. testing-principles; patterns-as-
  decoration vs. deep modules). Overlapping skills must scope against each other
  explicitly.
- **Consolidate, don't just patch**: removal, merge, and compression are
  first-class skill edits, not only addition. When a skill has been patched
  repeatedly and reads as accreted (stale, redundant, or conflicting rules),
  prefer a wholesale rewrite for coherence over one more append. This is
  `improve-codebase-architecture`'s shallow→deep instinct applied to the skill
  *document*.
- **Links resolve**: every relative link points at a real file.
- **No provenance inside the skill**: a skill carries only what it *does*. Where
  a rule came from (an upstream repo, its license, a URL) is metadata the agent
  can't act on, and a loaded file re-spends that attention on every task. Credit
  belongs in the human-facing docs (`README.md`, `ATTRIBUTION.md`), which is also
  where a licence's attribution *condition* is satisfied. Same rule for agents,
  commands, and deployed templates; the auditor enforces it.
- **Reasoning over MUSTs**: heavy ALL-CAPS rules are a yellow flag; reframe as
  explained principles.

## The audit script

`scripts/audit_skills.py` checks the mechanical invariants across the whole pack,
skills *and* agents (frontmatter, name↔folder/file match, line budget,
resolvable internal links, provenance), and prints a report. Run it after any
skill or agent change:

```bash
python3 scripts/audit_skills.py
```

Use it as the fast gate; use the checklist above for the judgment calls a script
can't make.
