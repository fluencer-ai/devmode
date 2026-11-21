# Slice an approved PRD into tickets

An approved PRD (or a settled conversation) becomes implementation work as a set
of **tickets**: tracer-bullet vertical slices, each naming the tickets that
**block** it. In a Conductor project the tickets are the track's `plan.md` tasks;
with Beads they are `bd` issues and the blocking edges are `bd` dependencies.

## 1. Prefactor first

Explore the area in the ubiquitous language, respecting its ADRs, and look for a
prefactor that makes the change easy: "make the change easy, then make the easy
change". A prefactor is its own ticket and blocks the slices it unlocks.

## 2. Cut vertical slices

- Each slice cuts a narrow but **complete** path through every layer (schema, API,
  UI, tests): vertical, never one horizontal layer.
- A finished slice is demoable or verifiable on its own.
- Each slice fits one fresh context window (one `tdd-implementer` run).

Give each ticket its **blocking edges**: the tickets that must finish before it
starts. A ticket with no blockers can start now.

**A wide refactor is the exception.** One mechanical change whose blast radius
fans across the codebase (rename a column, retype a shared symbol) can't land
green as one slice. Sequence it as **expand–contract** (`migration`): expand (add
the new form beside the old), migrate call sites in batches sized by blast radius
(each batch a ticket blocked by the expand, CI green batch to batch), then
contract (delete the old form, blocked by every batch). When even the batches
can't stay green alone, they share an integration branch that all block one final
integrate-and-verify ticket; green is promised only there.

## 3. Quiz the user on the breakdown

Show a numbered list; for each ticket: **title**, **blocked by**, and **what it
delivers** (the end-to-end behaviour, from the user's side). Ask:

- Does the granularity feel right (too coarse, too fine)?
- Does each ticket depend only on tickets that genuinely gate it?
- Should any be merged or split?

Iterate until the user approves.

## 4. Write the tickets

Each ticket holds: what to build (behaviour, not a layer-by-layer list), its
acceptance criteria as checkboxes, and its blockers (or "none: can start now").
No file paths or code: they go stale fast. The one exception is the PRD's rule: a
prototype snippet that states a decision more precisely than prose, trimmed to
the decision-rich part and marked as from a prototype.

Work the **frontier**: any ticket whose blockers are all done. A purely linear
chain is just top to bottom; independent frontier tickets can run in parallel
(`subagent-driven-development`).
