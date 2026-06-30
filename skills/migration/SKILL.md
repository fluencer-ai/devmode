---
name: migration
description: >-
  Change or replace existing systems safely — strangler-fig, adapter/anti-
  corruption layers, feature flags, expand-contract schema changes, and clean
  deprecation with a window. Use when replacing a module/service/library,
  migrating a database schema, deprecating an API, or doing a large rename; when
  the user says "migrate", "deprecate", "replace X with Y", "rewrite this",
  "upgrade the framework". The goal: never a risky big-bang cutover — incremental,
  reversible, with the old and new coexisting until the switch is safe.
---

# Deprecation & migration

The riskiest change is the big-bang replacement: rewrite everything, flip the
switch, pray. Safe migration is the opposite — the old and new **coexist**, you
move traffic/usage incrementally, and every step is reversible. Before touching
anything, know the blast radius ([`impact-analysis`](../impact-analysis/SKILL.md)).

## Patterns

- **Strangler fig** — wrap the old system; route new functionality (and then,
  piece by piece, existing functionality) to the new implementation until the old
  one is fully "strangled" and can be deleted. Incremental, never big-bang.
- **Adapter / anti-corruption layer** — a thin boundary that translates between
  old and new models so the new design isn't polluted by the old one's quirks
  (and callers don't change yet). Pairs with
  [`architecture-boundaries`](../architecture-boundaries/SKILL.md).
- **Feature flags** — ship the new path dark, flip per-cohort, and **roll back by
  flipping the flag** instead of deploying. Decouples deploy from release.
- **Expand–contract (parallel change) for data/contracts** — (1) *expand*: add
  the new field/table/endpoint, write to both; (2) *migrate*: backfill + move
  readers to the new; (3) *contract*: remove the old once nothing reads it. No
  step is breaking on its own.

## Deprecation with a window

- **Announce, don't yank.** Mark deprecated, keep it working, log/warn on use,
  give consumers a migration path and a date ([`documentation`](../documentation/SKILL.md),
  [`api-design`](../api-design/SKILL.md)).
- **Track real usage** before removing — "not observed" ≠ "unused"; confirm with
  data, then remove.
- **Then delete** — finish the job; a half-done migration leaves *two* systems to
  maintain, the worst of both.

## Kill zombie code

- A migration isn't done until the old path is **deleted**, not just unused.
  Dead-but-present code misleads readers and the AI, and rots.
- Watch the **churn rule:** if a file/area is being rewritten repeatedly, that's
  a signal the design is wrong — stop and reconsider
  ([`improve-codebase-architecture`](../improve-codebase-architecture/SKILL.md)),
  don't migrate it again.

## Process

1. **Impact-analysis** the blast radius (who depends on the thing).
2. Pick the pattern (strangler / adapter / flag / expand-contract).
3. Pin behavior with tests at the boundary *before* moving anything (tests green
   throughout — old and new must agree during coexistence).
4. Migrate incrementally; keep each step reversible.
5. Confirm the old path is unused (with data), then **delete it**.

## Red flags

- Big-bang cutover with no rollback.
- Removing the old path before confirming (with data) nothing uses it.
- A schema change that's breaking in a single step (skip expand-contract).
- A migration declared "done" with the old code still present (zombie).
- Re-migrating an area that keeps churning instead of fixing its design.
