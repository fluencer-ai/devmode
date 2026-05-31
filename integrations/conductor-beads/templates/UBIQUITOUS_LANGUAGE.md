# Ubiquitous language

> A living glossary of the domain terms used identically in conversation, in the
> AI's reasoning, and in the code. **Keep it open while planning and grilling.**
> Update it in the same change whenever a concept appears or a definition
> sharpens — a stale glossary is worse than none.
>
> The **In code as** column is what makes the language *ubiquitous*: it ties each
> domain word to the concrete type, function, module, table, or event.
>
> Built/maintained with the `ubiquitous-language` skill. Promote new terms here
> from track `learnings.md` / `patterns.md` (see the knowledge flywheel).

## <Sub-domain name>

| Term | Definition | In code as | Notes / invariants |
|------|------------|-----------|--------------------|
| <Term> | <precise definition: the concept, its boundaries> | `<Type / module / fn>` | <invariant that's always true> |

## Module map
> The module boundaries are part of the language — you and the AI both need to
> know this map well. List each deep module, its responsibility, and its public
> interface. This is what lets `spec.md` be specific about which modules and
> interfaces change. Keep it current as modules are consolidated
> (`improve-codebase-architecture`).

| Module | Responsibility | Public interface | Core/shell | Critical? |
|--------|----------------|------------------|-----------|-----------|
| `<Module>` | <what it owns / decides> | `<key signatures / endpoints / events>` | <pure core fn(s) / I/O shell> | <yes/no> |

---

### Conflicts & synonyms to resolve
- <concept>: used as `<X>` in <place>, `<Y>` in <place> → standardize on `<...>`

### Relationships
- <A> belongs to <B>; <B> has many <A>.
