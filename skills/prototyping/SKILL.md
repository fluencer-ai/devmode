---
name: prototyping
description: >-
  Prototyping: throwaway code that answers ONE design question, kept on a
  prototype branch as evidence. Use when an edge-case state machine needs
  checking, when several UI or API shapes compete, or when it is unclear whether a
  library or data source can do the job.
disable-model-invocation: true
---

# Prototyping (the spike)

A prototype is **throwaway code that answers a question.** Its only job is to turn
an unknown into a known cheaply, so the *real* design decision is made on evidence
instead of speculation. The question decides the shape. Once it's answered, the
answer folds into the real code and the prototype leaves `main` for its own
`prototype/<name>` branch, kept as a primary source. Leaving it on `main` is how a
spike rots into unowned production code.

This is the deliberate, bounded version of "let's just try it". It belongs
*before* the `write-prd`/`tdd` commit when an assumption is load-bearing and
unverified — a cheap input to a confident `design-critique`, not a substitute for
it.

## Identify the question first

A prototype with no question is just unowned code. State it in one line — "does
the quota reset correctly across a DST boundary?", "which of these three table
layouts reads best?", "can this API page beyond 10k rows?". The question picks the
shape:

- **Logic / behavior** → a tiny interactive harness (a script, a REPL, a terminal
  loop) that drives the thing through the edge cases that are hard to reason about
  on paper. **Surface the state after each step** so the behavior is visible.
- **Shape / interface** (UI or API) → build *several* radically different options
  side by side (toggle via a flag/param/route), so you're choosing between real
  alternatives, not defending the first one.

Picking the wrong branch wastes the whole spike — when ambiguous, default to a
logic harness for backend modules and a shape comparison for surfaces.

## Build it deliberately throwaway

- **Name it as a prototype** and colocate it near the code it validates, but keep
  it obviously separate (a `prototype/` or `spike-<question>` path) so no one
  mistakes it for production.
- **One command to run it** (`python spike_quota.py`, `npm run spike`, …),
  following the project's existing run conventions.
- **Strip everything not load-bearing for the question:** no tests, no error
  handling, no abstractions, no persistence — *unless persistence itself is the
  question* (then a scratch db/file is fine).

## Capture the answer, then move it off main

The deliverable of a spike is the **answer, not the code.** Write the verdict and
the question it settled where the decision lives — an ADR (`documentation`), the
issue, or a commit message. Fold the validated decision into production via `tdd`
(re-derived test-first, not pasted). Then:

1. Commit the prototype to a `prototype/<name>` branch cut from `main`.
2. Remove it from the working branch, so `main` keeps only the validated decision.
3. Leave a pointer to that branch on the issue or ADR, so the evidence behind the
   decision stays one checkout away.

A migration-style rule applies: a spike isn't done until it's promoted or moved to
its branch, never left to rot on `main` (`migration`: kill zombie code).

## Red flags

- A prototype with no written question (you'll learn nothing specific).
- A spike growing tests, abstractions, or a second feature — it's becoming
  production; stop and start it properly.
- "We'll just keep the prototype on main" — now you have untested, unowned production code.
- A prototype branch with no pointer from the issue or ADR (the evidence is lost).
- Pasting spike code straight into the codebase instead of re-deriving it test-first.
- Spiking what you could answer by reading the docs/source (`context-engineering`,
  source of truth) — don't prototype a known.
