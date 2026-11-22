---
name: design-critique
description: >-
  Design critique: widen the candidate set for an open decision, then
  pressure-test the chosen design, spec, or PRD through several expert lenses
  before code. Use when a hard-to-reverse decision has only one candidate, when a
  design or PRD is ready for review, or when the stakes are high.
disable-model-invocation: true
---

# Design critique

The cheapest place to fix a design is before it's code. This skill runs in two
passes, in order: **widen the candidate set, then pressure-test it.**

1. **Widen** (only when the decision is still open and hard to reverse: an
   architecture fork, an API/CLI/SDK surface, a naming scheme, a migration
   approach, a bug with no known root cause). A critique can tell you the chosen
   thing is weak, but it can't invent the alternative you never generated.
   Generating options? Read `divergent-ideation.md` in this folder.
2. **Pressure-test** the chosen design through the lenses below. A single
   reviewer (even a careful one) reviews from one angle; a strong design survives
   *several*. Surface where the lenses **disagree**, because the disagreements
   are where the real risk and the real decisions live.

Skip pass 1 when the design is already settled and only needs review.

Absorbed: `divergent-ideation`. Its generate-before-judge discipline is pass 1,
in `divergent-ideation.md` here.

This runs *before* implementation; the post-build code review is the
`complexity-reviewer` + the review-panel agents. Use it on a `write-prd` output
or a design reached via `grill-me`, before `subagent-driven-development`
executes it.

## The lenses

Review the design from each relevant lens; not every lens applies to every
design: pick the ones that matter and say why the others don't.

- **Simplicity (Ousterhout):** is this the simplest design that works? Where does
  complexity hide? Are the modules deep, the interfaces simple?
- **Change (Beck):** what's likely to change, and is the design easy to change
  there? Or is it rigid where the future will push?
- **Domain (Evans):** does it match the real domain model and the
  `ubiquitous-language` glossary? Any concept forced or missing?
- **Boundaries (Clean Arch):** are policy and detail separated? Does anything
  couple business rules to infrastructure (see `system-boundaries.md` in
  `functional-core-imperative-shell`)?
- **Failure & security:** what happens on bad input, partial failure, abuse?
  What's the worst case, and is it handled?
- **User/stakeholder:** does it actually solve the user's problem, or an adjacent
  one? Is the scope right?
- **Cost/operations:** what does it cost to build, run, and maintain? Cheaper
  alternative that's 80% as good?

## How to run it

1. **State the design** in one paragraph (the shared design concept) so every
   lens reviews the same thing.
2. **Apply each lens** in turn: its strongest concern, in one or two sentences.
   Be a critic, not a cheerleader: the job is to find weaknesses. When a lens
   leans on an external fact (a library's real behavior, a protocol's guarantees,
   a known failure mode), **ground it with a cited web check** rather than opining
   from priors: a perspective-expert with a source beats one with a hunch (the
   same grounding technique as `grill-me`).
3. **Surface the disagreements.** Where two lenses pull in opposite directions
   (simplicity vs. flexibility, speed vs. security, scope vs. cost), name the
   tension explicitly: don't average it away.
4. **Let the human decide the trade-offs.** Present the tensions as choices, with
   the consequence of each side. Trade-off resolution is the human's call.
5. **Produce a short verdict:** proceed / proceed-with-changes / rethink, plus the
   2–3 concrete changes or open questions that matter most, and for the decision
   you're endorsing, **name the condition that would make it wrong** (a user
   count, a price tier, a compliance need, a latency budget). A verdict with no
   stated invalidation condition can never be revisited on evidence; it just
   quietly ages.

## Keep it honest

- A critique that finds nothing is a failed critique: push harder or admit the
  design is genuinely solid *and say why*.
- Don't let the lenses become a checklist theater; each must produce a real
  concern or an explicit "no concern here, because…".
- This is *review*, not redesign: surface problems and trade-offs; let the
  `design-architect` and the human decide the fix.
- A hard-to-reverse decision reviewed with no alternative ever on the table:
  go back to pass 1.
