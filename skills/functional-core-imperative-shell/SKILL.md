---
name: functional-core-imperative-shell
description: >-
  Functional core, imperative shell: keep pure decisions apart from I/O in a
  module, and policy apart from infrastructure across a system. Use when
  structuring or refactoring a feature, when logic is tangled with DB, network,
  or framework calls, or when tests need heavy mocking.
disable-model-invocation: true
---

# Functional core, imperative shell

One instinct, two scales: **keep policy (decisions) independent of detail
(effects, I/O, frameworks).** Inside a module that is the functional core and
the imperative shell, covered below. Across a system it is the dependency rule:
layers, ports, and dependencies pointing inward, covered in `system-boundaries.md`.

Drawing system-level boundaries (layer direction, ports and adapters, parsing
input once at the edge, splitting modules by actor)? Read `system-boundaries.md`
in this folder.

Absorbed: `architecture-boundaries`. Its system-scale rules now live in
`system-boundaries.md` here.

## The module scale

Most code that's painful to test is painful because *decisions* and *effects*
are braided together: business logic interleaved with database reads, network
calls, clock reads, and writes. You can't exercise the logic without standing up
the world, so you reach for mocks, and the tests turn brittle and slow.

The functional-core / imperative-shell pattern (Gary Bernhardt) untangles this.
It splits a feature into two layers with a clear seam between them:

- **Functional core** — pure functions that hold all the interesting logic and
  decisions. Given inputs, they return outputs (or descriptions of what should
  happen). No I/O, no mutation of outside state, no clock, no randomness — same
  inputs always give the same outputs.
- **Imperative shell** — a thin outer layer that talks to the world: reads
  inputs (DB, network, files, time), hands them to the core, and carries out the
  decisions the core returns (writes, sends, logs). It has almost no branching
  logic of its own.

The shape: the shell **gathers** → the core **decides** → the shell **acts**.

This is the structural foundation that makes the rest of this process work. It's
why `tdd` and its testing principles (`testing-principles.md` in `tdd`) become easy rather than a mocking slog, and
the two support each other: this skill gives you a pure core to test, and good
testing principles tell you exactly where to put the seam.

## How to apply it

1. **Find the decisions.** What does this feature actually *decide*? Validation
   results, what to charge, which records to update, what response to return.
   That's the core.
2. **Find the effects.** What does it *do* to the world? Read the DB, call an
   API, read the clock, write a file, send an email. That's the shell.
3. **Push effects to the edges.** Restructure so the shell reads everything the
   core needs *up front*, calls the core with plain values, and then performs
   the effects the core asked for. The core never reaches out; it only computes.
4. **Make the core pure.** No hidden inputs. Pass the current time, random
   seeds, and configuration *in* as arguments rather than reading them inside.
   Purity is what makes the core deterministic and mock-free to test.
5. **Keep the shell dumb.** The shell should be so thin and so devoid of
   branching that there's little left to test in it beyond a few integration
   checks. Logic creeping into the shell is the main failure mode — pull it back
   into the core.

## Before / after

```text
# Before: decision and effect braided together (hard to test)
function renewSubscription(id) {
  const sub = db.load(id)                    // I/O
  if (sub.status !== "active") return        // logic
  if (now() > sub.endsAt) {                   // logic + clock
    const amount = sub.plan.price * sub.seats // logic
    payments.charge(sub.customer, amount)      // I/O
    db.save({ ...sub, endsAt: addMonth(now())})// logic + clock + I/O
  }
}

# After: shell gathers → core decides → shell acts
// core (pure): decide what should happen
function decideRenewal(sub, currentTime) {
  if (sub.status !== "active") return { kind: "noop" }
  if (currentTime <= sub.endsAt)  return { kind: "noop" }
  return {
    kind: "renew",
    charge: { customer: sub.customer, amount: sub.plan.price * sub.seats },
    newEndsAt: addMonth(currentTime),
  }
}

// shell (imperative): gather inputs, run core, carry out the decision
function renewSubscription(id) {
  const sub = db.load(id)
  const decision = decideRenewal(sub, now())
  if (decision.kind === "noop") return
  payments.charge(decision.charge.customer, decision.charge.amount)
  db.save({ ...sub, endsAt: decision.newEndsAt })
}
```

`decideRenewal` is tested with plain values and zero mocks — every edge case
(inactive, not yet due, due, multi-seat) is a one-line assertion. The shell gets
a couple of integration tests to confirm the wiring.

## Why this is a deep module

A core/shell feature is a textbook **deep module**: a lot of decision logic
hidden behind a simple, pure interface (`decideRenewal(sub, time) -> Decision`).
Callers — and tests — use that interface without caring how the decision is
made. That's exactly the interface you want to design carefully and then test
from the outside (see `design-interface-delegate-implementation`). You can
confidently delegate the *implementation* of the core to an AI, because its pure
interface plus exhaustive value-based tests pin the behavior with no ambiguity.

## Signals you've got it right

- The core has no `import` of your DB, HTTP, filesystem, or time library.
- Core tests have no mocks and run instantly.
- The shell is short, mostly straight-line, and boring to read.
- Adding a new edge case means adding a core test and a branch in the core —
  not touching any I/O.

If those aren't true, logic is leaking into the shell or effects are leaking
into the core; rebalance until the seam is clean. For an existing tangled
codebase, drive this with `improve-codebase-architecture`. Use both scales
together: pure cores inside, dependencies pointing inward outside.
