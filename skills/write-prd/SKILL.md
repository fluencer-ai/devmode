---
name: write-prd
description: >-
  PRD writing: turn an aligned design concept into a spec that names which
  modules and interfaces change, and where the tests will sit. Use after
  alignment and before implementation, when the user asks for a PRD or spec, or
  when a change is too large to go straight to code without losing the design.
disable-model-invocation: true
---

# Write a PRD

A PRD here is not a wish list of features. It is where you **invest in the
design of the system** (Kent Beck: do this every day). "Specs-to-code" fails
because it divests from design — it describes behavior and lets the compiler
invent the structure, which decays a little more every run. A good PRD does the
opposite: it commits to *what behavior is needed* and *how the system's
structure changes to support it*, so implementation has a spine to follow. The
PRD must name module seams and interface changes, not just user-facing behavior.

Write the PRD only after the design concept is shared (see `grill-me`), and write
it in the project's `ubiquitous-language` glossary so the terms mean the same
thing here as in the code. Respect the existing ADRs in the area.

## Sketch the test seams first

Before writing, decide where the feature will be tested from the outside:

- **Prefer existing seams** to new ones.
- **Use the highest seam possible.** If a new seam is needed, propose it as high
  as you can.
- **Fewer seams is better; the ideal is one.** Each extra seam is another
  interface to keep stable and another place behavior can hide.

Check with the user that the seams match their expectations, then write the PRD
around them. The seams become the Testing strategy section and the interfaces
the `tdd` loop drives.

## Structure

Use this template (a ready-to-copy version lives at `assets/prd-template.md`).
Keep each section tight — a PRD earns its length by being specific, not long.

```markdown
# PRD: <feature name>

## Problem & purpose
What problem this solves, for whom, and why now. One short paragraph.

## Design concept
The agreed theory of the change in 3–5 sentences. The shared understanding
from grilling, stated plainly so a reader new to the conversation gets it.

## Scope
- In scope: ...
- Out of scope: ... (be explicit — boundaries prevent drift)

## Behavior
The observable behavior, written as concrete scenarios:
- Happy path: ...
- Edge cases: empty input, failure, limits, concurrency
- Errors: what the user/system sees when things go wrong

## Module & interface changes   <-- the heart of the PRD
For each affected module (named by module, never by file path):
- **<Module>** — purpose of the change. New or modified?
  - Interface: the public surface that changes (signatures, types, events,
    endpoints). Design this carefully — it's the contract you'll test against.
  - Implementation notes: only what constrains the design (invariants,
    performance, data shape). Leave routine implementation to the builder.
  - Seam: what crosses in and out, and what stays hidden inside.

## Data
Shapes, sources of truth, migrations, state transitions.

## Testing strategy
The test seams agreed above (ideally one, as high as possible), which
interfaces get verified from the outside, what to mock, and what "done and
correct" means. See `testing-principles.md` in `tdd`.

## Open questions / risks
Anything still unresolved, and what would resolve it.
```

## Why the module & interface section matters most

The AI is a strong tactical programmer but a weak strategist. If the PRD only
describes user-facing behavior, the AI invents the structure — and it tends
toward shallow modules and entropy. By naming the modules that change and
designing their **interfaces** here, you set the strategy and let the AI fill
the implementation. This is the same idea as
`design-interface-delegate-implementation`: the interface is yours, the
implementation can be delegated, because the interface plus tests pin the
behavior from the outside.

Be concrete about interfaces: real signatures, real types, real endpoint shapes
or event names. "Add a service to handle billing" is not a design; it's a
restatement of the feature. "`BillingGateway.charge(seatId, amount): Result<Receipt, ChargeError>`,
called only by the imperative shell, pure-validated by the functional core" is
a design.

**Name modules and interfaces, not file paths.** Paths go stale within days;
module names and contracts don't. Interface signatures belong; implementation
code doesn't. The one exception: when a prototype produced a snippet that states
a decision more precisely than prose (a state machine, a reducer, a schema, a
type shape), inline it in the relevant decision, trimmed to the decision-rich
part, and note that it came from a prototype.

## Working style

- Write in the ubiquitous language, and work from its **module map** — the
  PRD's module & interface section should reference the modules named there, and
  if the change adds or reshapes a module, update that map as part of this work.
  If a needed term isn't in the glossary, add it there too.
- Prefer the smallest design that satisfies the concept. Don't pre-build for
  hypothetical futures — that's its own form of entropy.
- Surface trade-offs rather than silently resolving them; if a decision is the
  user's to make, list it under open questions.
- **Make every resolved decision land.** A trade-off you settled (or an ADR) isn't
  done when it's *recorded* — it's done when the behavior or module/interface
  section actually reflects it. Before approving, confirm each decision is
  referenced somewhere downstream, not stranded in a log (the decision-coverage
  check in `feedback-loops`).
- Before approving a high-stakes PRD, pressure-test it with `design-critique` —
  review it through several expert lenses and surface the trade-offs while it's
  still cheap (on paper).
- When the PRD is approved, it becomes the brief for implementation — typically
  handed to `tdd` and the `tdd-implementer` agent. When it is more than one
  context's work, slice it into blocking-ordered tracer-bullet tickets first:
  read `tickets.md` in this folder.
