---
name: context-engineering
description: >-
  Curate what an agent has in its working context — load the right files at the
  right time, keep the working set tight, and hand off cleanly across sessions.
  Use when an agent is drowning in irrelevant context, losing the thread on long
  tasks, repeatedly re-reading the same files, approaching compaction, or when
  the user says "manage context", "it forgot", "too much in context", "hand off".
  Context is a scarce resource: what you load (and don't) determines the quality
  of the work.
---

# Context engineering

An agent's output quality is bounded by what's in its working context. Too little
and it guesses; too much and the signal drowns in noise and it loses the thread.
Context is a budget to *curate*, not fill. This is the discipline of deciding
what the agent sees, when, and how it survives across sessions.

## Load the right thing at the right time (progressive disclosure)

- **Load on demand, not up front.** Pull the specific file/skill/reference for
  the current step; don't preload everything "to be safe." (This is why skills
  themselves use progressive disclosure — metadata always, body on trigger,
  references as needed.)
- **Prefer the stable summary over the raw pile.** A tight design concept, the
  [`module map`](../ubiquitous-language/SKILL.md), and the relevant interface beat
  twenty whole files. Reach for the detail only when you need it.
- **Curate for subagents.** When delegating
  ([`subagent-driven-development`](../subagent-driven-development/SKILL.md)), hand
  the worker *exactly* the task text + context it needs — never your whole
  session history. Constructing a clean, minimal brief is the point.

## Keep the working set tight

- **Notice the smells:** re-reading the same files, output drifting from the
  goal, "what were we doing?" mid-task — these mean the working set is wrong
  (too cluttered or missing the key thing).
- **Summarize and drop.** Replace a long exploration with its conclusion; you
  don't need the search transcript once you have the answer.
- **One concern at a time.** A focused context for a focused task; don't carry
  five half-finished threads at once.

## Survive compaction (hand off cleanly)

Long tasks outlive a single context window. Before stopping or near compaction,
write a **handoff that carries intent, not just status** — the design concept,
the current position, the single next step, open decisions — into durable memory
(Beads notes / a `STATE.md` digest). A fresh session should resume *cold* from
it, not re-derive the plan. (This is the WARM START habit in the Conductor
integration.)

## Process

1. For the current step, identify the *minimum* context that makes it doable.
2. Load that; resist loading more "just in case."
3. When delegating, build the subagent's brief deliberately and minimally.
4. Summarize finished sub-threads down to their conclusions.
5. Hand off durable intent before you run out of room.

## Red flags

- Preloading the whole codebase/all skills before starting.
- Pasting a worker your entire history instead of a curated brief.
- The agent re-reading files it already saw, or losing the goal on a long task.
- Stopping a long task with no handoff (the next session starts from zero).

> Adapted from `addyosmani/agent-skills` (`context-engineering`), MIT —
> trimmed of Claude-Code-setup specifics to keep it tool-agnostic.
