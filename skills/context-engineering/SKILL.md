---
name: context-engineering
description: >-
  Context engineering: what goes into the agent's window, and grounding it in
  authoritative sources rather than memory. Use when context is cluttered or the
  thread is lost, at a phase boundary or handoff, when briefing a subagent, or when
  coding against a library or API.
disable-model-invocation: true
---

# Context engineering

An agent's output quality is bounded by what's in its working context. Too little
and it guesses; too much and the signal drowns in noise and it loses the thread.
Context is a budget to *curate*, not fill. This is the discipline of deciding
what the agent sees, when, where it comes from, and how it survives across
sessions.

Calling a library, framework, or API, or code doesn't behave as you "remember"?
Read `source-of-truth.md` in this folder: the installed version and the official
docs outrank memory.

Absorbed: `source-of-truth` now lives here as `source-of-truth.md`.

## Load the right thing at the right time (progressive disclosure)

- **Load on demand, not up front.** Pull the specific file/skill/reference for
  the current step; don't preload everything "to be safe." (This is why skills
  themselves use progressive disclosure: metadata always, body on trigger,
  references as needed.)
- **Place durable instructions at the latest reliable point.** Every standing or
  global instruction spends attention and narrows choices for *every* task, not
  just the one that needs it. Keep the persistent channel (CLAUDE.md, the agent
  brief) to outcome + acceptance + authority; surface narrow policy at the decision
  point where it actually applies, not up front.
- **Prefer the stable summary over the raw pile.** A tight design concept, the
  module map (`ubiquitous-language`), and the relevant interface beat twenty whole
  files. Reach for the detail only when you need it.
- **Curate for subagents.** When delegating (`subagent-driven-development`), hand
  the worker *exactly* the task text + context it needs, never your whole
  session history. Constructing a clean, minimal brief is the point.

## Primary and secondary sources

A **primary source** is the thing itself: the file, the diff, the ADR, the
installed library, the session as it happened. A **secondary source** is a summary
of one: a handoff doc, a compact summary, a subagent's report, your memory of a
file. Every context move except continuing in place turns primary into secondary,
and summaries are lossy.

- Know which one you are holding. Act on a load-bearing claim (a signature, a
  decision, a test result) only after checking it against its primary source.
- A fresh session seeded from a summary is confidently wrong about whatever the
  summary flattened. Re-read the primary before you build on it.

## Keep the working set tight

- **Stay in the smart zone.** Reasoning stays sharp only in the early part of the
  window (roughly the first ~150k tokens on current frontier models) and degrades
  past it. Don't push on a degraded context: at the nearest phase boundary, run the
  decision below.
- **Notice the smells:** re-reading the same files, output drifting from the
  goal, "what were we doing?" mid-task: these mean the working set is wrong
  (too cluttered or missing the key thing).
- **Summarize and drop.** Replace a long exploration with its conclusion; you
  don't need the search transcript once you have the answer.
- **One concern at a time.** A focused context for a focused task; don't carry
  five half-finished threads at once.
- **Park distractions, don't chase them.** When a second concern intrudes mid-task
  ("the retry logic probably has this same bug"), it's a *later*-task, not a
  *now*-task. Log it verbatim to durable memory with a one-line **anchor** so it
  reads cold after compaction (the task you're mid-way through · the file/area
  "this"/"here" points at · `branch@sha`) filled only from coordinates you already
  hold. Then ack in one line and resume *at the same pace*: don't act on it, don't
  open its files, and **don't cut corners on the current task to "get to" it.**

## Token economy

- **Pointers over copies.** Name the file, ADR, or issue by path; don't paste it.
- **Short delegate briefs.** Task, acceptance, the nearest contract, and the paths
  to read. Nothing the worker can look up itself.
- **Conclusions-only returns.** Ask a subagent for the answer and the evidence that
  settles it, not a transcript of what it read.
- **Cheapest capable model for read-only lanes.** Search, inventory, and scan
  lanes rarely need the strongest model; judgement and design do.
- **No re-pasting.** A file already in context is not read or pasted again unless
  it changed.

## Phase boundaries

A **phase** is a chunk of work inside a session (the grill, the implementation,
the review). Decide at the **boundary** between two phases, never mid-phase:
mid-phase you either continue or split the rest into subagents. At the boundary,
work down this list; the first yes wins.

1. **Continue** in this session when the next phase needs this one as a primary
   source (grill to implementation is the standard case) or there is smart-zone
   room left for it. It costs nothing and loses nothing, so rule it out first.
2. **Clear** when everything here is disposable for what comes next. Cheapest
   move, but one-way: clear a relevant context and the *why* behind the work is
   gone.
3. **Handoff** only when the work must move: to another harness (Claude to
   Codex), another directory or repo, or another person, or to fork a side task
   found mid-phase. If nothing is travelling, you don't need one.
4. **Subagent** when the next task is scoped tightly enough to run without
   steering (an automated review is the standard case). This session stays
   untouched.
5. **Compact** last, when the context is relevant, nothing moves, and you must stay
   in the loop. Pass it an instruction naming the next phase so the summary keeps
   what that phase needs.

Compacting summarizes earlier turns in place and the verbatim history is lost, so
compact only at an intentional break *between* phases. Whatever you pick, keep the
durable intent current first (below), so a clear or compact can resume cold.

## Durable intent and handoff docs

Long tasks outlive a single window. Keep a note that **carries intent, not just
status** (the design concept, the current position, the single next step, open
decisions) in durable memory (Beads notes / a `STATE.md` digest). A fresh session
should resume *cold* from it, not re-derive the plan. (This is the WARM START
habit in the Conductor integration.) A handoff doc, and that note, also:

- **Points to artifacts, doesn't duplicate them**: link the PRD/plan/ADR/issue/
  diff by path, don't paste their contents (that's the whole token win).
- **Names the next skills**: a short "suggested skills" line tells the resuming
  agent what to reach for first (e.g. "resume at IMPLEMENT via `tdd`").
- **Redacts secrets/PII**, never carry API keys, tokens, or personal data into a
  handoff doc; scrub them out.
- **Lives where the next session looks**: durable memory the loop reads on start
  (Beads / `STATE.md`), or the OS temp dir for a one-off agent-to-agent pass,
  not buried in chat scrollback.
- **Forks: it doesn't continue in place.** A handoff opens a *fresh* session that
  reads the doc, so the verbatim history survives *in the doc*.
- **Test the handoff in a fresh session.** A document's existence proves only that
  it was written, not that it works. Before trusting a handoff or durable note,
  open a cold session and confirm it actually retrieves the route and changes
  behavior; fix what the fresh agent misses.

## Process

1. For the current step, identify the *minimum* context that makes it doable.
2. Load that, from primary sources; resist loading more "just in case."
3. When delegating, build the subagent's brief deliberately and minimally.
4. Summarize finished sub-threads down to their conclusions.
5. At each phase boundary, run the five-step decision; keep durable intent current
   before you run out of room.

## Red flags

- Preloading the whole codebase/all skills before starting.
- Pasting a worker your entire history instead of a curated brief.
- The agent re-reading files it already saw, or losing the goal on a long task.
- Pushing work on a degraded context, or compacting mid-phase.
- Reaching for compact (or a handoff) first, before ruling out continue and clear.
- Acting on a summary's claim without checking its primary source.
- Trusting a handoff you never verified from a cold start (writing it ≠ it works).
- Chasing a passing thought mid-task (or rushing the current task to reach it)
  instead of parking it verbatim and resuming.
- Stopping a long task with no durable note (the next session starts from zero).
