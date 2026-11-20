# PRD: <feature name>

> Write this in the project's ubiquitous language. Be specific — a PRD earns its
> length by being precise about module and interface changes, not by being long.
> Name modules and interfaces, never file paths. No implementation code; a
> prototype snippet only when it states a decision more precisely than prose.

## Problem & purpose
<What problem this solves, for whom, and why now. One short paragraph.>

## Design concept
<The agreed theory of the change in 3–5 sentences — the shared understanding
reached while grilling, stated so a reader new to the conversation gets it.>

## Scope
- **In scope:** <...>
- **Out of scope:** <... — be explicit; boundaries prevent drift>

## Behavior
- **Happy path:** <...>
- **Edge cases:** <empty input, boundaries, limits, concurrency>
- **Errors:** <what the user/system sees when things go wrong>

## Module & interface changes  ← the heart of the PRD
> For each affected module, named by module (no file paths). This is where you
> invest in the design of the system.

### <Module name> — <new | modified>
- **Purpose of the change:** <...>
- **Interface (the contract you'll test against):**
  - `<real signature / type / endpoint / event>`
  - `<...>`
- **Seam:** <what crosses in and out; what stays hidden inside>
- **Implementation notes (constraints only):** <invariants, performance budget,
  data shape — leave routine implementation to the builder>

### <Module name> — <new | modified>
- ...

## Data
<Shapes, sources of truth, migrations, state transitions.>

## Testing strategy
<The test seams agreed with the user before writing: existing seams first, as
high as possible, ideally one. Which interfaces get verified from the outside,
what to mock (only what you don't own), and what "done and correct" means.>

## Open questions / risks
- <Anything unresolved, and what would resolve it.>
- <Decisions that are the user's to make.>
