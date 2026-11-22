---
name: migration
description: >-
  Migration: replace or change a live system incrementally and reversibly
  (strangler fig, adapters, flags, expand-contract). Use when replacing a module,
  service, or library, changing a schema, deprecating an API, or doing a large
  rename.
disable-model-invocation: true
---

# Deprecation & migration

The riskiest change is the big-bang replacement: rewrite everything, flip the
switch, pray. Safe migration is the opposite: the old and new **coexist**, you
move traffic/usage incrementally, and every step is reversible. Before touching
anything, know the blast radius (`impact-analysis`).

## Patterns

- **Strangler fig**: wrap the old system; route new functionality (and then,
  piece by piece, existing functionality) to the new implementation until the old
  one is fully "strangled" and can be deleted. Incremental, never big-bang.
- **Adapter / anti-corruption layer**: a thin boundary that translates between
  old and new models so the new design isn't polluted by the old one's quirks
  (and callers don't change yet). Pairs with
  `system-boundaries.md` in `functional-core-imperative-shell`.
- **Feature flags**: ship the new path dark, flip per-cohort, and **roll back by
  flipping the flag** instead of deploying. Decouples deploy from release.
- **Expand–contract (parallel change) for data/contracts**: (1) *expand*: add
  the new field/table/endpoint, write to both; (2) *migrate*: backfill + move
  readers to the new; (3) *contract*: remove the old once nothing reads it. No
  step is breaking on its own.

## Deprecation with a window

- **Announce, don't yank.** Mark deprecated, keep it working, log/warn on use,
  give consumers a migration path and a date (`documentation`,
  `api-design`).
- **Track real usage** before removing, "not observed" ≠ "unused"; confirm with
  data, then remove.
- **Then delete**: finish the job; a half-done migration leaves *two* systems to
  maintain, the worst of both.

## Kill zombie code

- A migration isn't done until the old path is **deleted**, not just unused.
  Code is prompt material for the next agent: leave the retired pattern and its
  replacement side by side and *both* read as precedent, so the next AI
  cargo-cults whichever it lands on: worse than double maintenance, it poisons
  every future change in the area. Incremental *cutover* still holds (move
  behavior in reversible steps), but a pattern you've decided to retire gets its
  whole discoverable population fixed in one coherent pass, so only one form
  remains to copy.
- **Ratchet the retired form out.** After deleting it, add a check that fails if
  it reappears (a lint rule, a CI grep, or a test), so a later agent can't
  silently reintroduce it (the ratchet spirit of
  `feedback-loops`, aimed at the deprecated
  pattern). Enable the rule, repair every violation, and lock it in the same change.
- Watch the **churn rule:** if a file/area is being rewritten repeatedly, that's
  a signal the design is wrong: stop and reconsider
  (`improve-codebase-architecture`),
  don't migrate it again.

## Process

1. **Impact-analysis** the blast radius (who depends on the thing).
2. Pick the pattern (strangler / adapter / flag / expand-contract).
3. Pin behavior with tests at the boundary *before* moving anything (tests green
   throughout: old and new must agree during coexistence).
4. Migrate incrementally; keep each step reversible.
5. Confirm the old path is unused (with data), then **delete it**.

## Red flags

- Big-bang cutover with no rollback.
- Removing the old path before confirming (with data) nothing uses it.
- A schema change that's breaking in a single step (skip expand-contract).
- A migration declared "done" with the old code still present (zombie).
- Re-migrating an area that keeps churning instead of fixing its design.
- A retired pattern left side by side with its replacement (both become precedent
  for the next AI), or deleted with no ratchet to keep it from creeping back.
