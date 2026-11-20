---
name: tdd
description: >-
  Test-first implementation in small red-green-refactor steps at agreed seams,
  plus the judgment on unit size, mocks, and which behaviors to assert. Use when
  writing or changing application logic, fixing a bug test-first, or deciding
  what and how to test.
disable-model-invocation: true
---

# Test-driven development

The rate of feedback is your speed limit. The classic AI failure mode is
**outrunning your headlights**: the model emits a large pile of code and only
*then* thinks to type-check or test it — by which point a small early mistake
has propagated everywhere. TDD fixes this structurally. It forces small,
deliberate steps where every step ends in a passing test, so feedback arrives
constantly and mistakes stay tiny.

TDD also does something subtler: writing the test first forces you to design
the interface from the *caller's* point of view before you write the
implementation. That pressure produces simpler, more usable interfaces — which
is exactly the design investment this whole process is about.

**Absorbed: `testing-principles`.** TDD sets the rhythm; the principles decide
unit size, what to mock, and which behaviors to assert. Deciding mock
boundaries, unit size, edge coverage, or whether a test is worth keeping? Read
`testing-principles.md` in this folder.

## Agree the seams first

A **seam** is the public boundary a test observes behavior through, without
reaching inside. Test only at seams the user has agreed.

- Before the first test, write down the seams you intend to test and confirm
  them with the user. No test is written at an unconfirmed seam.
- Give each proposed seam a one-line note: what a test there **catches** and
  what it **misses**. That note is how the user judges where testing effort
  lands (critical paths and complex logic, not every edge of every helper).
- If the right seam is itself unclear (how deep the module is, what the
  interface should expose), settle the interface first with
  `design-interface-delegate-implementation`.

Work from an approved PRD (`write-prd`) when one exists: its testing-strategy
section is the starting proposal for the seams.

## The loop: red → green → refactor

Do this one behavior at a time, at an agreed seam. Never skip the refactor
step — it's where the design investment happens.

1. **Red — write one failing test.** Pick the smallest next behavior. Write a
   test that asserts it and watch it fail *for the right reason* (the behavior
   is missing, not a typo). A test you never saw fail is a test you don't trust.
2. **Green — make it pass simply.** Write the least code that turns the test
   green. Resist building ahead of the test; the goal is a passing bar, not a
   finished feature.
3. **Refactor — improve the design.** With the test green as a safety net,
   clean up: remove duplication, sharpen names (use the `ubiquitous-language`),
   consolidate toward deep modules. Run the tests again. This is where you
   *invest in the design of the system*.

Repeat. Each cycle should be small enough that if the test fails unexpectedly,
the cause is obvious because you only changed one thing.

Refactor stays inside the loop on purpose. Some TDD guides move it out to the
review stage; devmode keeps it mandatory in every cycle, because deferring it
is how the design investment gets skipped.

## Why small steps matter with AI

The AI's instinct is to do too much at once — generate a whole feature, then
verify. That maximizes the blast radius of any error and makes failures hard to
localize. By gating every increment behind a test, you cap how far a mistake can
travel and you give the model a crisp, frequent signal. Slower-looking steps
produce faster real progress because you stop debugging giant tangles.

## Stack the feedback loops

TDD is one feedback loop; run it alongside static types, the compiler/linter,
fast test runs, and a real browser or runtime for UI and integration. Setting
these up and keeping them fast is `feedback-loops`. A slow suite lowers your
speed limit.

## How this connects to the rest

- TDD is dramatically easier in a codebase with simple, stable boundaries. A
  `functional-core-imperative-shell` split gives you pure logic that tests
  without mocks. If tests are painful to write, treat it as a design signal and
  consider `improve-codebase-architecture` before pushing harder.
- When a test fails for a reason you don't understand, switch to
  `systematic-debugging` (find the root cause) rather than guessing — and before
  claiming green, apply `verification-before-completion`.

## Working rules

- Test only at agreed seams; each seam carries its catches/misses note.
- One failing test at a time. See it fail before you make it pass.
- Don't write production code with no failing test demanding it.
- Keep the bar green between steps; never leave the suite red to "fix later".
- Refactor only on green, and treat it as mandatory, not optional polish.
