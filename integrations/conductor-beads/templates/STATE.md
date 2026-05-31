# Project State

> A **file-based living memory** — a lightweight alternative to Beads when you
> don't want the `bd` CLI/Dolt dependency. Keep it under ~100 lines: it's a
> *digest* a fresh session reads first to recover position and design concept,
> not a log. Update it at every handoff (the devmode `grill-me` concept + the
> module map deltas belong here, not just status).
>
> Use this OR Beads, not both as source of truth. Beads gives a queryable
> dependency graph; STATE.md gives a zero-dependency human-readable digest.

## Design concept (the why — survives across sessions)
<3–5 sentences: the shared design concept reached while grilling. The single
most important thing to preserve, because status is recoverable but intent is not.>

## Current position
- **Track / focus:** <current track>
- **Phase:** <X of Y> — <phase name>
- **Status:** <ready to plan / planning / implementing / phase complete / blocked>
- **Last activity:** <YYYY-MM-DD> — <what happened, last commit SHA>

## Next step
<The single concrete next action a fresh session should take.>

## Key decisions
- <decision + rationale> (e.g. "RS256 over HS256 for key rotation")

## Ubiquitous-language / module-map deltas
<New terms, sharpened invariants, or module-map changes to fold into
UBIQUITOUS_LANGUAGE.md.>

## Open / blocked
- <anything waiting on a decision or external input>
