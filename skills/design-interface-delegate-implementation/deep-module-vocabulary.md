# Deep-module vocabulary

The fixed architecture vocabulary for designing, deepening, and reviewing modules.
Use these terms exactly. Consistent language is the point: a substituted synonym
reopens the drift this pack exists to stop. Domain nouns come from the project's
`ubiquitous-language` glossary; these are the architecture nouns that sit beside
them.

## Terms

**Module**: anything with an interface and an implementation. Deliberately
scale-agnostic: a function, class, package, or tier-spanning slice.
_Avoid_: unit, component, service.

**Interface**: everything a caller must know to use the module correctly: the type
signature, but also invariants, ordering constraints, error modes, required
configuration, and performance characteristics.
_Avoid_: API, signature (both name only the type-level surface).

**Implementation**: what's inside a module, its body of code. Distinct from
**adapter**: a thing can be a small adapter with a large implementation (a
Postgres repository) or a large adapter with a small implementation (an in-memory
fake). Say "adapter" when the seam is the topic, "implementation" otherwise.

**Depth**: leverage at the interface, meaning the behavior a caller (or test) can
exercise per unit of interface they have to learn. **Deep**: a lot of behavior
behind a small interface. **Shallow**: the interface is nearly as complex as the
implementation.

**Seam**: a place where you can alter behavior without editing in that place; the
*location* where a module's interface lives. Where the seam goes is its own
design decision, separate from what goes behind it.
_Avoid_: boundary, for a module (it collides with the domain sense of a bounded
context). devmode keeps "boundary" only for system-scale layers, in
`system-boundaries.md` of `functional-core-imperative-shell`.

**Adapter**: a concrete thing that satisfies an interface at a seam. It names a
*role* (which slot it fills), not substance (what's inside).

**Leverage**: what callers get from depth: more capability per unit of interface
learned. One implementation pays back across N call sites and M tests.

**Locality**: what maintainers get from depth: change, bugs, knowledge, and
verification concentrate in one place instead of spreading across callers. Fix
once, fixed everywhere.

## Relationships

- A module has exactly one interface, the surface it presents to callers and tests.
- Depth is a property of a module, measured against its interface.
- A seam is where a module's interface lives.
- An adapter sits at a seam and satisfies the interface.
- Depth produces leverage for callers and locality for maintainers.

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module
  can be built from small, swappable parts; they just aren't part of the interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it
  was a pass-through. If complexity reappears across N callers, it was earning its
  keep.
- **The interface is the test surface.** Callers and tests cross the same seam.
  Testing *past* the interface means the module is the wrong shape.
- **One adapter means a hypothetical seam. Two adapters means a real one.**

## Rejected framings

- **Depth as the ratio of implementation lines to interface lines.** It rewards
  padding the implementation. Depth here is leverage.
- **"Interface" as a language's `interface` keyword or a class's public methods.**
  Too narrow: the interface includes every fact a caller must know.
- **"Boundary" for a module's edge.** Say seam or interface.
- **"Layer" or "wrapper" when you mean a module.** Say module; call it shallow if
  that's the complaint.
- **"Easier to maintain", "cleaner code" as a benefit.** Name the gain in these
  terms instead: locality (bugs concentrate in one module), leverage (one
  interface, N call sites), or a smaller interface.
