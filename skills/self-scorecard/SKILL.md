---
name: self-scorecard
description: >-
  Self-scorecard: an evidence-backed 0-10 score on five criteria at each phase,
  tracked with deltas, plus a closing retro on the environment. Use at every
  phase boundary of a multi-step build, at the final gate, or when the user asks
  how the work is going.
disable-model-invocation: true
---

# Self-scorecard

The agent that builds is the worst judge of its own work — unless it's forced to
score itself against fixed criteria, with evidence, every step. This skill turns
"looks good" into **numbers you can track**: a short overview of what was done
plus a 0–10 score on five criteria, with the delta from the last phase, so you
can watch the agent's own judgment of the work rise (or fall) as it goes.

It is *self-assessment, grounded in evidence* — the score on Correctness must be
backed by an actual test run (see `verification-before-completion`), not a
feeling. Honesty is the whole point: a dishonest 9 is worse than an honest 5.

## The five criteria (0–10 each)

| Criterion | Scores high when… | Backed by |
|-----------|-------------------|-----------|
| **Correctness** | it works: tests pass, ACs met, fresh verification evidence | the actual test/build output |
| **Design** | deep modules, FCIS split, low complexity, easy to change | `functional-core-imperative-shell`, `improve-codebase-architecture` |
| **Testing** | behavior at stable boundaries, edges+invariants, no over-mock, ratchet | `testing-principles.md` in `tdd`, `tdd` |
| **Safety** | no secrets, input validated, guardrails respected, critical modules reviewed | `security-hardening`, the guardrails hook, `code-review` |
| **Clarity** | ubiquitous language, comments explain *why*, ADRs, readable | `ubiquitous-language`, `documentation` |

**Score bands:** <4 Weak · 4–6 Developing · 6–8 Solid · 8–9 Strong · 9+ Excellent.
Anchor your scores: a 10 means "I have evidence it's excellent here," not "no
problems came to mind." Reserve 8+ for things you've actually verified.

## How to run it (each phase)

1. **Gather evidence** for the phase — the test output, the diff, the review
   findings, the a11y/lint/audit results. Don't score from memory.
2. **Score each criterion 0–10** with a one-line, evidence-based note. Be
   harsh on what you haven't verified ("not observed" ≠ "fine").
3. **Render it** with the script (consistent format + delta + trend):
   ```bash
   echo '{ "phase":"Implement", "summary":"<what was done>",
     "scores": { "correctness":{"score":8,"note":"12/12 green"},
       "design":{"score":7,"note":"deep core/shell"},
       "testing":{"score":8,"note":"edges+invariants, no mocks"},
       "safety":{"score":6,"note":"guardrails on; auth review pending"},
       "clarity":{"score":7,"note":"UL used; 1 ADR missing"} } }' \
     | python3 scripts/scorecard.py
   ```
   It stores history in `.devmode/scorecard.json` and shows ▲/▼ deltas so the
   user tracks the trend across phases.
4. **Show the user the overview + scores.** This is the per-phase check-in.

## At the end — recommendations

When the work is done, run the **final** scorecard and attach
**recommendations per criterion** — the concrete next move that would raise the
weakest scores:

```bash
echo '{ "phase":"Review", "summary":"...", "scores":{...},
  "recommendations": {
    "safety":"add a no-leak test + review the auth path in full",
    "testing":"add the concurrency edge case",
    "clarity":"write the ADR for the storage choice" } }' \
  | python3 scripts/scorecard.py
python3 scripts/scorecard.py --final     # trend + recommendations
```

Recommendations are *judgment* (the script renders them; you author them). Aim
each at moving a specific criterion up a band, and point at the skill that does it.

## At the final gate: a short retro

The recommendations improve *this* work. The retro improves the **environment**
the next build starts from. Run it in the session it looks back on, before any
clear, reading the session itself (primary source), not your memory of it. List
only real candidates, most severe first, each with the one change it proposes:

- **Navigation:** where did finding a file or fact take too long? Propose a
  pointer (a `CLAUDE.md` line, a doc-contract index entry).
- **Checks:** which mistake could an automated check have caught? Look at the
  repo's existing check command and CI first: an unwired or broken check is the
  finding, not a new one.
- **Standards:** what did review miss, or flag that no rule covered?
- **Steering files:** what in `CLAUDE.md` / `AGENTS.md` should move into a check,
  a standard, or a skill?
- **Tool cost:** which tool calls were expensive or repeated for no new
  information?
- **No-ops:** which steering instructions changed nothing the agent would not do
  by default? Propose deleting them.

Classify each fault before proposing a fix. A **mechanical** fault (a fixed
pattern, a banned API, a file-location rule) becomes a **deterministic check**: a
lint rule, a hook, or a CI job, whichever the repo makes cheapest. A **judgement
call** (cross-file consistency, matching local style) becomes a written
**standard** for the reviewer. Default to the check. Proposals go to the user;
apply none without a yes.

## Honesty rules

- **Every 8+ needs evidence you actually saw this phase.** No optimistic scores.
- **Score down for unknowns.** Untested path → Testing/Correctness can't be high.
- **Don't game the trend.** If a phase regressed a criterion, show the ▼ — that's
  the signal that makes the scorecard worth anything.
- A criterion you can't yet assess (e.g. Correctness before any code) gets a low,
  honest score with the note "no code yet", not a placeholder high one.
