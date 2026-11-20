---
name: subagent-driven-development
description: >-
  Gray-box delegation: run a plan's tickets as a dependency graph, one fresh
  subagent or external model CLI per ticket in its own worktree, each verified
  from outside. Use when executing an approved plan or PRD, when offloading a
  bounded task to another model, or when parallel tasks need isolation.
disable-model-invocation: true
---

# Subagent-driven development

This is the *operational mechanism* for the strategy in
`design-interface-delegate-implementation`: design the interface yourself, then
delegate the implementation as a **gray box** verified from the outside. That
skill says *why*; this one says *how* — dispatch a fresh worker per ticket,
review its output on two axes, merge, and keep your own context for coordination.

**Why a fresh worker per ticket:** you construct exactly the context each ticket
needs — it never inherits your session's history, so it stays focused and you
preserve your own context for orchestration. **Core loop:** ready ticket → fresh
implementer in its own worktree → Spec and Standards review → merger → next
ready tickets.

**Absorbed: `delegate-to-cli`.** The worker can also be an external model CLI;
it is the same gray-box contract, verified the same way. Delegating to another
model's CLI? Read `external-cli.md` in this folder.

## When to use it

- You have a plan/PRD whose tasks are well-enough specified that an isolated
  agent can execute each one.
- You're staying in **this session** (no parallel-session handoff).

If tasks are tightly coupled, or the design isn't settled, stop and `grill-me` /
`write-prd` first.

## Token economy

- **Briefs carry pointers and a done-criterion.** Point at the spec, the ticket,
  the exploration notes, and prior commits by path or SHA; don't paste copies of
  anything the worker can read. State the one check that means "done".
- **Workers return conclusions, not file dumps,** within a word cap you state in
  the brief (e.g. "report under 300 words": status, what changed, the evidence).
  You inspect the diff yourself; the report only has to tell you where to look.

## The process

1. **Read the plan once and build the ticket graph.** Tickets are not a list of
   steps: record which ticket blocks which. The **ready set** is every ticket
   whose blockers are all merged.
2. **(Optional) Explore first.** One exploration subagent gathers what the
   tickets need (relevant files, external docs) and saves markdown notes in a
   directory **outside the repo**, so every later worker can read them by path
   and implementers stay focused on implementing.
3. **Create the integration branch** the whole plan lands on.
4. **Per ready ticket, dispatch an implementer** in **its own worktree on its own
   branch**, based on the integration branch tip. Run the ready set concurrently.
   The brief: pointers to the ticket and notes, the interface/contract it must
   hit, the constraints/invariants, and the done-criterion — *not* the
   implementation steps. The implementer confirms its worktree base (resets onto
   the integration tip if not), works test-first (`tdd`), self-reviews, commits,
   and merges the integration tip into its branch before reporting.
5. **Answer questions before it builds.** A good implementer asks up front;
   answer clearly, then let it proceed.
6. **Review on two axes, in parallel** (separate fresh subagents, per
   `code-review`): **Spec** (matches the ticket, nothing missing, nothing extra)
   and **Standards** (deep modules, names in the `ubiquitous-language`, no
   shallow-module sprawl, tests at agreed seams). Report them separately; both
   must be clean. Issues → implementer fixes → re-review.
7. **Verify, then merge.** Apply `verification-before-completion` to the diff
   (don't trust the agent's "success" report). A **merger subagent** merges the
   ticket branch into the integration branch, resolves conflicts there, and runs
   the suite on the integrated result.
8. **Recompute the ready set** after each merge and dispatch the newly unblocked
   tickets.
9. **After all tickets**, run the full `code-review` over the integration branch
   (`complexity-reviewer` leads the lanes); fix its findings in one fresh
   implementer and re-verify before calling it done.
10. **Clean up** every implementer worktree.

## Handling implementer status

Implementers report one of four states — never ignore an escalation:

- **DONE** → only if it came with an **evidence-backed self-review** (each claim
  + the actual command output, per the `tdd-implementer`'s evidence-gated
  handoff). A "DONE" with empty/fabricated evidence bounces back *before* you
  spend a reviewer on it. Then proceed to review.
- **DONE_WITH_CONCERNS** → read the concerns; address correctness/scope ones
  before review; note observations and continue.
- **NEEDS_CONTEXT** → supply what's missing and re-dispatch.
- **BLOCKED** → diagnose: more context? more capable model? task too large
  (split it)? plan wrong (escalate to the human)? Never force the same model to
  retry unchanged.

## Parallelize with isolation, not luck

The fresh-implementer / separate-reviewer split *is* the maker/checker discipline
of loop engineering — never let the model that wrote the code be the one that
grades it. Concurrency comes from the ready set, safety from isolation: one
worktree (or branch/clone) per ticket so parallel writes can't collide, and one
merger that integrates after each ticket passes review. Dispatching parallel
implementers into the *same* working tree on overlapping files is the classic
conflict — isolation, not hope, is what makes the fan-out safe.

## Model selection (cost/speed)

Use the least powerful model that can do the role:
- 1–2 files with a complete spec → fast/cheap model (most tasks are mechanical).
- Multi-file integration / debugging → standard model.
- Architecture, design, or review judgment → most capable model.

## Delegation discipline (the gray-box contract)

- **Fix the interface and the tests first** — that's what lets you *not* read
  every line. A gray box is only safe when its boundary is pinned.
- **Critical modules are never gray boxes.** Money, auth, security, irreversible
  effects → review in full regardless of the worker's report.
- **Give constraints, not steps.** Prescribing how throws away the agent's
  tactical strength.
- **Keep the review axes separate.** A clean Standards pass must not mask a
  Spec gap (over- or under-building), and the reverse.

## Red flags

- Skipping either review axis, or proceeding with unfixed issues.
- Dispatching a ticket whose blockers aren't merged yet.
- Dispatching multiple implementers in parallel into the same working tree.
- Pasting file contents into a brief instead of a pointer, or a brief with no
  done-criterion or word cap.
- Exploration notes written inside the repo, where they pollute the diff.
- Trusting self-review as a substitute for an independent review.
- Letting an agent's "success" stand in for inspecting the diff.
