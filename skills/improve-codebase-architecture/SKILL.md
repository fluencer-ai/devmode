---
name: improve-codebase-architecture
description: >-
  Deepening refactor: find shallow modules, report candidates visually, grill the
  chosen one, then consolidate it behind a simple interface. Use when a codebase
  feels scattered or hard to change, when the AI keeps landing in the wrong code,
  or before building on an area whose structure is decaying.
disable-model-invocation: true
---

# Improve codebase architecture

A good codebase is one that is **easy to change** (Ousterhout: complexity is
anything that makes a system hard to understand and modify). Codebases drift
toward the opposite (software entropy) because every change optimizes the
change in front of it rather than the design of the whole. AI accelerates this:
it's very good at producing lots of small, shallow modules, and a codebase made
of them is hard for *both* humans and AI to navigate, so changes get slower and
buggier over time.

This skill reverses that drift by reshaping shallow modules into **deep
modules**. Speak the fixed vocabulary (module, interface, depth, seam, adapter,
leverage, locality) in every candidate and every message; the definitions and the
rejected terms are in `deep-module-vocabulary.md` of
`design-interface-delegate-implementation`. Domain nouns come from the
`ubiquitous-language` glossary: "the Order intake module", not "the
FooBarHandler" and not "the Order service".

## Shallow vs. deep modules

- **Shallow module:** little functionality behind a relatively complex
  interface. Lots of tiny blobs that expose many functions and leak their
  internals. A caller (or an AI) has to walk through many of them and understand
  all their dependencies to do anything, so it often fails to find the right
  one or misreads how they connect.
- **Deep module:** a lot of functionality hidden behind a *simple* interface.
  The complexity lives inside, where it's encapsulated. Callers use the
  interface and ignore the inside. You *can* open it, but you rarely need to.

The goal is **few large deep modules with simple interfaces**, not many small
shallow ones. The same code, reorganized behind clean seams, becomes navigable
and testable instead of scattered.

## The procedure

This is a repeatable, reversible refactor. Take small steps and keep tests green
throughout, never reshape architecture without a safety net.

1. **Map what exists.** Scope before you scan (YAGNI): deepening a module only
   pays off where future changes land, so weight the parts of the codebase that
   keep changing. Unless the user named a target, walk a good stretch of
   `git log` for hot spots (the files that keep coming up), and let those pull
   your attention first; if churn is scattered with no clear hot spot, widen the
   net. Read the glossary and the ADRs for the area first. Then explore (a fresh
   subagent keeps your context clean) and list the current modules, their
   interfaces, and their dependencies. Note where you feel friction:
   - understanding one concept means bouncing between many small modules;
   - an interface is nearly as complex as its implementation;
   - pure functions were extracted for testability, but the bugs hide in how
     they are called (no locality);
   - tightly coupled modules leak across their seams;
   - an area is untested, or hard to test through its current interface.
2. **Find candidate clusters.** Look for code that changes together, shares data,
   or serves one glossary concept but lives in separate shallow pieces. Apply the
   **deletion test** to anything that looks shallow: imagine deleting it. If the
   complexity simply vanishes, it was a pass-through: delete it, don't deepen it.
   If the complexity reappears, scattered across N callers, it was earning its keep
   and belongs behind one deep interface. Classify each candidate's dependencies
   with the four categories in `design-interface-delegate-implementation`; the
   category decides how the deepened module gets tested.
3. **Present the candidates as a visual report, then stop.** Render it with
   `visual-explainers`: one card per candidate with a before/after diagram and a
   recommendation badge (`Strong`, `Worth exploring`, or `Speculative`), ending in
   a top recommendation. Building the report? Read `html-report.md` in this
   folder. Respect existing ADRs: surface a candidate that contradicts one only
   when the friction is real enough to reopen it, and flag the conflict on its
   card. Do NOT propose interfaces yet. Ask: "Which of these would you like to
   explore?"
4. **Grill the one the user picks.** Run `grill-me` on it: constraints,
   dependencies, the shape of the deepened module, what sits behind the seam,
   which tests survive. Keep the domain model current as decisions land
   (`ubiquitous-language`): a deepened module named after a new concept gets a
   glossary entry, a sharpened term gets updated right there. If the user
   **rejects** the candidate with a load-bearing reason, offer an ADR (format in
   `documentation`): "Want me to record this so future architecture reviews don't
   re-suggest it?" Skip it for ephemeral reasons ("not now") or self-evident ones.
5. **Map the blast radius.** Before moving anything, run `impact-analysis` on the
   cluster you'll touch (who depends on it, what breaks, any cycles or orphans),
   so the refactor is bounded rather than a leap.
6. **Design the simple interface.** Decide the small interface that should
   remain: the contract callers need. Everything else becomes internal. Design
   this deliberately; it's the lid of the box (see
   `design-interface-delegate-implementation`, including its design-it-twice
   pass for a high-stakes interface).
7. **Pin behavior with tests at that interface.** Before moving code, add or
   confirm tests that exercise the intended interface, so the refactor is
   verifiable from the outside. Use `testing-principles.md` in `tdd` to choose the seam.
   **Replace, don't layer:** the old unit tests on the shallow modules become
   waste once interface tests exist. Delete them in step 9 rather than keeping
   both suites.
8. **Consolidate behind the seam.** Move the related code inside the new module,
   hide what was leaking, and reduce the interface to the designed one. Where
   logic and I/O are tangled inside the cluster, apply
   `functional-core-imperative-shell` so the deep module has a pure, testable
   heart.
9. **Re-point callers and delete the cruft.** Update call sites to the new
   interface and remove the now-dead shallow scaffolding and its tests. Don't
   leave compatibility shims or commented-out husks: that's entropy by another
   name.
10. **Run the loop again.** Tests green, types clean. Repeat on the next cluster.

## What "better" looks like

- Fewer modules, each doing more, each with a smaller interface.
- A new reader (or AI) can find the code for a concept in one place.
- Changing one concept touches one module, and the change doesn't ripple
  unexpectedly into others.
- Tests sit at stable interfaces, assert observable outcomes, and survive
  internal refactors. A test that must change when the implementation changes is
  testing past the interface.

## When to reach for this

- The AI repeatedly explores but lands in the wrong place or misjudges
  dependencies: a strong signal the structure is too shallow to navigate.
- A small change keeps breaking distant code (high coupling, leaked internals).
- Tests are brittle because they bind to scattered internals rather than an
  interface.
- You're about to build on top of an area: improve its architecture *first*, so
  you build on solid ground rather than compounding the entropy.

Do this *before* complexity compounds. The earlier you consolidate, the cheaper
it is, and the more of AI's bounty you can actually collect, because AI does
genuinely well in a clean, deep-module codebase.

**Related:** when the rot is system-level (logic welded to the framework/DB,
changes rippling everywhere), read `system-boundaries.md` in
`functional-core-imperative-shell`. When a cluster of conditionals-on-type or a
subclass explosion is the smell, a pattern from `design-patterns` may deepen the
module, but only if it reduces complexity, never as decoration.
