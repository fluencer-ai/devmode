---
name: systematic-debugging
description: >-
  Find the root cause before proposing any fix, when facing a bug, test
  failure, build error, flaky test, performance problem, or any unexpected
  behavior. Use this the moment something doesn't work — especially under time
  pressure, when a "quick fix" looks obvious, or when a previous fix didn't
  stick — and when the user says "this is broken", "debug this", "the test
  fails", "why doesn't this work", "it crashes". Random fixes mask the real
  problem and create new bugs; this enforces root-cause-first discipline.
---

# Systematic debugging

Random fixes waste time and create new bugs. A quick patch on a symptom leaves
the real cause in place, where it resurfaces — often worse. Debugging is not
guessing-and-checking; it is investigation. This skill keeps you (and the AI,
which is strongly biased toward proposing a fix immediately) on the
root-cause-first path.

## The iron law

**No fix without a root-cause investigation first.** If you can't state *what*
is happening and *why*, you are not ready to change code. Proposing solutions
before tracing the cause is the failure mode this skill exists to prevent.

## The four phases — complete each before the next

### Phase 1 — Root-cause investigation
- **Read the error completely.** Stack traces, line numbers, codes — they often
  contain the answer. Don't skim past warnings.
- **Reproduce it reliably.** Exact steps; every time or intermittent? If you
  can't reproduce, gather more data — don't guess.
- **Check recent changes.** `git diff`, recent commits, new deps, config/env
  differences. What changed right before it broke?
- **Instrument the boundaries** in multi-component systems. Log what enters and
  exits each component (API → service → DB; CI → build → sign). Run once to see
  *where* it breaks, then investigate that component — don't theorize blind.
- **Trace the bad value backward.** Where does it originate? What passed it in?
  Keep going up the call stack to the source. Fix at the source, not the symptom.

### Phase 2 — Pattern analysis
- **Find working examples** of similar code in the same codebase.
- **Compare against the reference.** If you're following a pattern/library, read
  the reference implementation *completely* — don't adapt from a half-read.
- **List every difference** between working and broken, however small. "That
  can't matter" is how bugs hide.

### Phase 3 — Hypothesis and minimal test
- **State one hypothesis:** "I think X is the cause because Y." Be specific.
- **Test it with the smallest possible change.** One variable at a time.
- **Verify before continuing.** Worked → Phase 4. Didn't → form a *new*
  hypothesis; do **not** stack another fix on top.
- **When you don't know, say so** and investigate more. Don't pretend.

### Phase 4 — Fix the root cause
- **Write a failing test first** that reproduces the bug (lean on
  [`tdd`](../tdd/SKILL.md) and [`testing-principles`](../testing-principles/SKILL.md)).
- **One fix, addressing the root cause.** No "while I'm here" extras.
- **Verify with evidence** (see
  [`verification-before-completion`](../verification-before-completion/SKILL.md)):
  test passes, nothing else broke, the original symptom is gone.

### The 3-fix rule — question the architecture
If three fixes have failed — each revealing a new problem elsewhere, or each
needing "massive refactoring" — **stop**. This is not a failed hypothesis; it's
a wrong architecture. Surface it to your human partner and consider
[`improve-codebase-architecture`](../improve-codebase-architecture/SKILL.md)
instead of attempting fix #4.

## Red flags — stop and return to Phase 1

- "Quick fix now, investigate later" · "just try changing X" · "it's probably X"
- Proposing fixes before tracing data flow
- Changing multiple things at once
- "One more fix attempt" after 2+ failures
- "I don't fully understand but this might work"

## Common rationalizations

| Excuse | Reality |
|--------|---------|
| "It's simple, skip the process" | Simple bugs have root causes too — the process is fast for them. |
| "Emergency, no time" | Systematic is *faster* than guess-and-check thrashing. |
| "Try this first, investigate later" | The first fix sets the pattern. Do it right from the start. |
| "I'll test after I confirm the fix" | Untested fixes don't stick. The failing test proves the cause. |
| "Reference is long, I'll adapt it" | Partial understanding guarantees bugs. Read it fully. |
