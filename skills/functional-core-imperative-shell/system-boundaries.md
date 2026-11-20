# System boundaries (the core/shell instinct at system scale)

`SKILL.md` keeps decisions apart from effects inside one module. This file applies
the same instinct to the **system**: layers, components, and the direction of
dependencies between them. Read it when designing a system's shape, when a change
ripples across many unrelated files, or when business logic is welded to the
database, HTTP layer, or framework (clean architecture, hexagonal, ports and
adapters all name this).

## The dependency rule

**Source-code dependencies point inward, toward policy.** Business rules (the
*why* of the system) must not depend on infrastructure (the *how*: database, web
framework, UI, external services). Infrastructure depends on the business rules
through interfaces the business rules own, not the reverse.

```
   [ UI / HTTP ]    [ DB / files ]    [ 3rd-party APIs ]   ← details (volatile)
          \               |                 /
           ─────────▶ interfaces ◀──────────              (owned by the core)
                          │
                    [ business rules ]                     ← policy (stable)
```

This is why the functional core imports no DB/HTTP/clock: the same rule, one
module down. A framework is a *detail* you plug in, not the thing your logic is
built around. Keep it at the edge so you could swap it without touching policy.

## A boundary owns validity: parse, don't validate

A boundary controls more than dependency direction; it owns the **validity** of
what crosses it. Parse untrusted external input (manifests, args, remote targets,
API payloads) **once, at the boundary**, into a trusted domain type, then let
policy rely on canonical, already-valid states. The inner core should never re-ask
"is this well-formed / present / fresh?" because the type it received has already
answered that. Convert-and-narrow at the edge (return a domain type or an error)
instead of re-checking the same raw shape everywhere it flows.

**The smell that a boundary is missing:** the same defensive check scattered
across the code: repeated record/field checks, normalization in every function, a
readiness guard in every event handler, a stale-response guard at each call site.
Duplicated validity checks mean **no boundary owns validity**. Collapse them into
one parsing seam; downstream code then trusts the type.

(Structural validity, meaning well-formed, present, fresh, belongs at this seam.
Business-rule decisions, meaning *is this allowed?*, still belong in policy, the
functional core.)

## SRP is about actors, not "doing one thing"

> A module should be responsible to one, and only one, **actor**: a group of
> stakeholders who request changes.

The common misreading ("a function should do one thing") is too vague. The real
rule: if two *actors* share a class, a change requested by one can break the
other. Split by actor.

```
// Smell: one class serves three actors (accounting, HR, DBA)
class Employee { calculatePay(); reportHours(); save(); }

// Better: data + one module per actor
class EmployeeData {}                     // just the data
class PayCalculator   { pay(e) }          // accounting (CFO)
class HourReporter    { hours(e) }        // HR (COO)
class EmployeeStore   { save(e) }         // persistence (CTO/DBA)
```

When two pieces of code change for *different reasons by different people*, they
belong in different modules, even if they look similar today.

## How to draw the boundaries

1. **Identify policy vs. detail.** What are the business rules (would matter even
   if the app were paper)? What is plumbing (DB, framework, transport)?
2. **Put an interface at each boundary, owned by the inner side.** The core
   defines `repository` / `gateway` interfaces; infrastructure implements them.
   This is the imperative shell, scaled to the system. Introduce a port only where
   something actually varies across it (see the seam rules in
   `design-interface-delegate-implementation`).
3. **Point dependencies inward.** If an inner module imports an outer one, that's
   a violation: invert it with an interface.
4. **Split modules by actor.** Group code that changes for the same reason by the
   same stakeholder; separate code that changes for different reasons.
5. **Keep the boundaries in the module map** (see `ubiquitous-language`) so they
   are shared vocabulary and the PRD can reference them.

## Signals you've got it right

- You could swap the database or web framework without touching business rules.
- A feature change touches one component, not a scatter of unrelated files.
- The core has no `import` of the framework, ORM, or HTTP library.
- Tests of business rules need no infrastructure stood up.

## When it's wrong

- Business logic littered with SQL/HTTP calls: entanglement. Pull effects to the
  edge (the core/shell split in `SKILL.md`) and invert the dependency.
- A change "for marketing" keeps breaking "the accounting report": two actors in
  one module. Split by actor.
- Everything imports the framework: the framework became the architecture. Push
  it to the edge. If it's already pervasive, drive the fix with
  `improve-codebase-architecture`.
