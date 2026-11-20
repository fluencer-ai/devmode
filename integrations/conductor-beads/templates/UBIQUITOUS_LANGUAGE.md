# Ubiquitous language

> A living glossary of the domain terms used identically in conversation, in the
> AI's reasoning, and in the code. **Keep it open while planning and grilling.**
> Update it in the same change whenever a concept appears or a definition
> sharpens — a stale glossary is worse than none.
>
> The **In code as** column is what makes the language *ubiquitous*: it ties each
> domain word to the concrete type, function, module, table, or event.
>
> The glossary holds no implementation details: say what each term IS, in one or
> two sentences, and keep storage, algorithms, and design decisions out. List
> rejected synonyms as _Avoid_.
>
> Built/maintained with the `ubiquitous-language` skill. Promote new terms here
> from track `learnings.md` / `patterns.md` (see the knowledge flywheel).

## <Sub-domain name>

| Term | Definition | In code as | Notes / invariants |
|------|------------|-----------|--------------------|
| <Term> | <precise definition: the concept, its boundaries> | `<Type / module / fn>` | <invariant that's always true>. _Avoid_: <synonyms> |

### Conflicts & synonyms to resolve
> Where the code uses different words for the same concept (e.g. `User` vs
> `Account`), record it here and pick one.

- <concept>: used as `<X>` in <place>, `<Y>` in <place> → standardize on `<...>`

### Relationships

- <A> belongs to <B>; <B> has many <A>.

---

## Module map (architecture, kept apart from the glossary)
> The module boundaries are part of the language — you and the AI both need to
> know this map well. List each deep module, its responsibility, and its public
> interface. This is what lets `spec.md` be specific about which modules and
> interfaces change. Keep it current as modules are consolidated
> (`improve-codebase-architecture`). Interfaces live here, never in the glossary
> tables above.

| Module | Responsibility | Public interface | Depends on (why) | Core/shell | Critical? |
|--------|----------------|------------------|------------------|-----------|-----------|
| `<Module>` | <what it owns / decides> | `<key signatures / endpoints / events>` | `<module>`: <why> | <pure core fn(s) / I/O shell> | <yes/no> |
