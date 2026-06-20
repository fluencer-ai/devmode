---
description: Do ONE task, routed and gated. Plain-English in → classify → pick the right devmode skill(s)+agent → run a short evidence-gated pipeline (Understand → Plan → Execute → Verify → Deliver). The single-task sibling of /devmode (full project) and /devmode c (bare per-turn gates).
argument-hint: <a plain-English task, e.g. "debug this failing test" or "add a rate limit to the upload endpoint">
---

# /do — one task, routed and gated

`/do <task>` takes a single plain-English request, **routes** it to the right
devmode skill(s) and agent, and runs it through a short **evidence-gated
pipeline**. It is *not* a new engine — it reuses devmode's existing skills,
agents, and gates. It's the quick front door for one bounded task, between the
two you already have:

| Command | Scope | Use it for |
|---|---|---|
| `/devmode …` | a whole project, guided phase-by-phase | building/adopting a project through Align→Refactor |
| **`/do <task>`** | **ONE task, routed + gated** | **"just do this specific thing, correctly and verified"** |
| `/devmode c [comment]` | bare per-turn gates, no routing | ad-hoc ops/debug under the discipline this turn |

Pick `/do` when the work is a single, well-bounded task and the full phase
machine would be overkill — but you still want it routed to the right discipline
and *proven*, not asserted.

## The pipeline (do these in order, out loud, briefly)

1. **Route.** Classify the task and name what you'll use — the skill lane(s) and,
   if it helps, an agent. Examples:
   - bug / failure → `systematic-debugging` (+ `tdd` for the regression test)
   - new behavior → `tdd` + `testing-principles` (interface first via `design-interface-delegate-implementation`)
   - security/money/auth → `security-hardening` (the control checklist) — **reviewed in full, never gray-boxed**
   - refactor / rename → `impact-analysis` first, then the change
   - migration / deprecation → `migration` (strangler / expand–contract / delete the zombie)
   - unknown behavior to learn → `prototyping` (spike → capture → delete)
   - unclear ask → **stop and `grill-me`** before touching code

   State the route in one line: `Routing: <skill(s)> [+ <agent>]`.
2. **Understand.** If the task is ambiguous or the contract isn't obvious, ask the
   one or two questions that matter (don't quiz) or read the nearest doc contract
   (`doc-contracts` / the module map). Confirm you know the goal, the interface,
   the constraints, and **how you'll verify** — the `confidence-check` gate.
3. **Plan.** State the smallest change that does it and the check that proves it.
   For anything non-trivial, write the failing test first.
4. **Execute.** Make the change in small steps. Critical modules in full; give
   subagents constraints, not steps, if you delegate.
5. **Verify — evidence, not assertion.** Run the real check and **show the
   output** (`verification-before-completion`): tests green, the symptom gone, the
   build/exit code, the HTTP 200. The Stop gate (`verify_gate.py`) blocks a "done"
   with no fresh check after a rebuild/deploy/env change — override only with
   `VERIFY-OK: <reason>` when a check genuinely doesn't apply.
6. **Deliver.** State what changed, the evidence, and (one line) what you'd watch
   or do next. If the task turned out to be project-sized, say so and point to
   `/devmode`.

## Rules (the base wins, same as everywhere)

- **Root cause before any fix** — no change/rebuild before you can name the cause.
- **No "done" without fresh end-to-end evidence** — the gate enforces it.
- **Critical paths (auth/money/security) reviewed in full** — never gray-boxed.
- **Don't grow it into a project** — if it needs phases, hand off to `/devmode`.
- **Read what you produced** — accept no diff you can't explain (comprehension debt).

> The plain-English-router idea (Route → Plan → Execute → Verify → Deliver, with
> gates demanding evidence over assertions) is adapted from
> `notque/vexjoy-agent`'s `/do` command, MIT. devmode's `/do` reuses the existing
> skills/agents/gates — no new machinery.
