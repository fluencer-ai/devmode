---
name: verification-before-completion
description: >-
  Require fresh verification evidence before claiming any work is done, fixed,
  passing, or correct — and before committing, opening a PR, or moving to the
  next task. Use this whenever you're about to say "done", "fixed", "it works",
  "tests pass", "ready to merge", or express satisfaction ("great", "perfect").
  Also use before trusting a subagent's "success" report. Claiming completion
  without running the check is a correctness and trust failure, not efficiency.
---

# Verification before completion

Claiming work is complete without verifying it is not efficiency — it's a guess
dressed as a result, and it breaks trust the moment it's wrong. The AI is
especially prone to this: it changes code and reports success from confidence,
not evidence. This skill is the gate that converts "should work" into "verified
to work".

This is distinct from [`feedback-loops`](../feedback-loops/SKILL.md): feedback
loops are the checks you run *continuously while building*; this is the final
**gate before you make a completion claim**. They reinforce each other. It is
also the bookend to [`confidence-check`](../confidence-check/SKILL.md) — that
gate confirms you're *ready to start*; this one confirms you're *actually done*.

## The iron law

**No completion claim without fresh verification evidence.** If you have not run
the verifying command in this turn, you cannot claim the thing it would prove.

## The gate function

Before stating any status or expressing satisfaction:

1. **Identify** — which command proves this claim?
2. **Run** — execute the *full*, fresh command (not a partial check, not a
   remembered earlier run).
3. **Read** — the complete output; check the exit code; count failures.
4. **Verify** — does the output actually confirm the claim?
   - No → state the *actual* status, with evidence.
   - Yes → state the claim, *with* the evidence.
5. **Only then** make the claim.

Skipping any step is asserting, not verifying.

## What each claim actually requires

| Claim | Sufficient evidence | NOT sufficient |
|-------|--------------------|----------------|
| Tests pass | Test run output: 0 failures, this turn | "should pass", an earlier run |
| Linter/types clean | Tool output: 0 errors | "linter passed" (≠ compiler) |
| Build succeeds | Build command: exit 0 | logs "look fine" |
| Bug fixed | The original symptom retested: gone | code changed, assumed fixed |
| Regression test works | Red→green verified (revert fix → test FAILS → restore → passes) | test passes once |
| Subagent finished | The VCS diff / output inspected | the agent's "success" report |
| Requirements met | Line-by-line check against the spec/PRD | "tests pass, so it's done" |
| Gate is green | The gate actually *ran over the file you changed* | exit 0 (a glob/path may have skipped it) |

## Red flags — stop before you speak

- "should", "probably", "seems to", "looks correct"
- "Great!" / "Perfect!" / "Done!" *before* running the check
- About to commit / push / open a PR without verifying
- Trusting a subagent's success report without inspecting the diff
- "Just this once" · "I'm tired" · "partial check is enough"
- A **green gate that silently skipped the changed file** — a `**` glob that
  doesn't recurse (bash without `globstar`), an over-broad exclude, a path typo.
  A passing gate proves nothing about code it never executed; confirm the gate
  *covered your change*, not just that it exited 0.
- Different wording to dodge the rule — spirit over letter

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "Should work now" | Then running it costs nothing — run it. |
| "I'm confident" | Confidence is not evidence. |
| "Linter passed" | The linter doesn't compile or run the code. |
| "The agent said success" | Verify independently; agents over-report. |
| "Partial check is enough" | Partial proves nothing about the whole. |

## Attach the evidence (don't just assert it)

A claim is stronger — and re-checkable — when the *evidence travels with it*. When
you report completion, attach the actual output, not a summary: "tests pass
(`Ran 12 tests … OK`)", not "tests pass". For a release or a hand-off, assemble a
small **evidence pack**: the commands run, their output/exit codes, the commit
SHAs, and which acceptance criteria each proves. This is what lets a reviewer (or
a future you) trust the result without re-deriving it from memory — and it pairs
with the evidence-gated handoff the `tdd-implementer` returns.

## The bottom line

Run the command. Read the output. *Then* make the claim. Pair this with
[`systematic-debugging`](../systematic-debugging/SKILL.md) (verify the fix
worked) and [`tdd`](../tdd/SKILL.md) (the red→green evidence for regressions).

> Adapted from `obra/superpowers` (`verification-before-completion`), MIT.
> Reframed in the devmode voice; scoped against devmode's feedback-loops skill.
