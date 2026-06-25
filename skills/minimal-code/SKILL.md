---
name: minimal-code
description: >-
  Write only the code the task needs — climb a decision ladder before coding
  (does it need to exist? stdlib? native platform feature? installed dep? one
  line?) and stop at the first rung that holds, but NEVER cut validation, error
  handling, security, or accessibility. Use when implementing anything, when the
  user says "minimal", "simplest", "lazy", "YAGNI", "do less", "don't
  over-engineer", "shortest path", or complains about bloat, boilerplate,
  needless dependencies, or over-abstraction; and to audit/review existing code
  for over-engineering. The lazy senior dev: efficient, not careless.
---

# Minimal code (the lazy senior dev)

The best code is the code never written. Channel the senior who has seen every
over-engineered codebase and been paged at 3am for one: before writing anything,
climb the ladder and **stop at the first rung that holds.** The result is small
because it's *necessary*, not golfed — and it stays small *with every safety guard
intact*. This is the tactical counterpart to
[`improve-codebase-architecture`](../improve-codebase-architecture/SKILL.md):
that one consolidates shallow modules *after* the fact; this one stops the bloat
*before* it's written.

## The ladder

Stop at the first rung that holds — it's a reflex, not a research project:

1. **Does this need to exist at all?** Speculative need → skip it, say so in one
   line (YAGNI).
2. **Does this repo already do it?** *Search first* — grep for an existing helper,
   pattern, or utility before writing a new one. Reuse the codebase's own solution;
   don't re-solve a solved problem (and don't fork a second way to do one thing).
3. **Stdlib does it?** Use it.
4. **Native platform feature covers it?** `<input type="date">` over a picker lib,
   CSS over JS, a DB constraint over app code.
5. **Already-installed dependency solves it?** Use it — never add a new dependency
   for what a few lines do.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

Two rungs both work → take the higher one and move on. The first lazy solution
that works is the right one.

## Lazy, not negligent — the safety floor (never on the chopping block)

**Never** simplify away: input validation at trust boundaries, error handling
that prevents data loss, security measures, accessibility basics, or correctness
on edge cases. "Lazy" means writing *less* code, never the *flimsier* algorithm —
two stdlib options the same size, take the one that's right on the edges. A
security/money/auth control is the *last* place to cut (see
[`security-hardening`](../security-hardening/SKILL.md)'s control checklist).

## Rules

- **No unrequested abstractions** — no interface with one implementation, no
  factory for one product, no config for a value that never changes.
- **No scaffolding "for later"** — later can scaffold for itself. Fewest files;
  shortest working diff wins; deletion over addition; boring over clever (clever
  is what someone decodes at 3am).
- **Complex request?** Ship the lazy version and question the rest in the same
  breath: *"Did X; Y covers it. Need full X? Say so."* Never stall on an answer
  you can default.
- **Output discipline:** code first, then at most a few lines — *what you skipped,
  when to add it* (`[code] → skipped: X, add when Y`). If the explanation is
  longer than the code, delete the explanation — prose defending a simplification
  is complexity smuggled back in. (Explanation the user *asked* for — a report, a
  walkthrough, per-phase notes — is not debt; give it in full.)

## Mark deliberate simplifications — the `minimal:` comment

A shortcut reads as *intent, not ignorance* when you name it. Mark deliberate
simplifications with a comment that states the known ceiling and the upgrade path:

```python
# minimal: global lock; per-account locks if throughput matters
# minimal: O(n²) scan, fine at this n; index it past ~10k
```

These double as a **debt ledger**: periodically grep them
(`grep -rn "minimal:" .`) and decide which deferrals to pay down — tracked, not
forgotten. (The upstream convention is `ponytail:`; either is fine — pick one per
repo and be consistent.)

## Intensity

Dial it to the moment:

| Level | Behaviour |
|---|---|
| **lite** | Build what's asked, but name the lazier alternative in one line; the user picks. |
| **full** *(default)* | The ladder enforced — stdlib/native first, shortest diff, shortest explanation. |
| **ultra** | YAGNI extremist — ship the one-liner and challenge the rest of the requirement in the same response. |

`/devmode lean` runs a whole guided session at **full** by default (say "ultra"
to push harder, "lite" to only suggest).

## Audit & review through the ladder

The same ladder is a lens on code that *already exists*:

- **Audit (a whole area/repo):** rank what to **delete, simplify, or replace with
  stdlib/native** — reinvented stdlib, needless deps, speculative abstractions,
  dead "for later" scaffolding. Pairs with
  [`improve-codebase-architecture`](../improve-codebase-architecture/SKILL.md).
- **Review (a diff):** one line per finding — location, what to cut, the leaner
  form. This is a standing lens of the [`code-review`](../code-review/SKILL.md)
  panel, not just a one-off.

## Why it's worth it

Measured on a real agent editing a real repo, this discipline cut ~54% of the
code an unguided agent wrote (up to ~94% where it would over-build a date/color
picker into a component instead of reaching for a native `<input>`) — cheaper and
faster — **while keeping 100% of the safety guards.** Small-because-necessary,
not small-because-golfed. It is the direct embodiment of devmode's thesis: *code
is not cheap; the cheapest code is the line you didn't write.* Pairs with
[`tdd`](../tdd/SKILL.md) (write the minimum that passes the test) and
[`prototyping`](../prototyping/SKILL.md) (a spike answers the question with even
less).

## Red flags

- Writing a new helper for something the repo already has — *search before you
  write* (a second way to do one thing is complexity, not progress).
- Adding a dependency for what a few stdlib lines do.
- An interface/factory/config with exactly one use.
- Boilerplate or scaffolding "we'll need later."
- An explanation longer than the code it defends.
- Cutting validation/error-handling/security/a11y to "keep it minimal" — that's
  negligent, not lazy: stop and put them back.

> Adapted from [`DietrichGebert/ponytail`](https://github.com/DietrichGebert/ponytail)
> (the "lazy senior dev" minimalism skill — the ladder, the safety floor, the
> intensity levels, the deliberate-simplification comment, the audit/review
> lenses, and the benchmark evidence), MIT © Dietrich Gebert. Reframed in the
> devmode voice (markdown-only — none of ponytail's Node hooks / multi-agent
> packaging); applied via `/devmode lean`. The *search-first / reuse-before-create*
> rung is reinforced by the "Pattern Discovery Protocol" in
> `bybren-llc/safe-agentic-workflow` (MIT).
