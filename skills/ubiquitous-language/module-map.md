# The module map

Read this when building or updating the module map section of
`UBIQUITOUS_LANGUAGE.md`.

The ubiquitous language is not only domain nouns and verbs. Whenever you plan or
touch code, you and the AI both need to know the **module map** — the deep
modules in the system and their public interfaces — and know it *well*. A module
is a domain concept: it has a name, a purpose, and a contract, and if that name
isn't shared, planning drifts exactly the way vocabulary drifts.

So the file carries an architecture section listing each deep module, what it's
responsible for, and its public interface. Keep it in its own section below the
glossary tables: this is the one place interfaces and signatures belong, and the
glossary entries stay free of them. Use the architecture vocabulary from
`deep-module-vocabulary.md` of `design-interface-delegate-implementation`
(module, interface, seam, adapter) when describing entries.

This map is what makes `write-prd` able to be specific about *which modules and
interfaces change*, and what lets you reason about the system as a handful of
boxes rather than thousands of lines (see
`design-interface-delegate-implementation`). Keep the map current as modules are
consolidated (`improve-codebase-architecture`) — a stale map misleads planning
more than no map at all. For a *non-obvious* dependency, record the **why** next
to the edge (module A uses B *because…*) — a dependency with a recorded reason is
what lets a future session (or the AI after compaction) judge whether it's
essential or accidental, and it powers `impact-analysis`.

| Module | Responsibility | Public interface | Depends on |
|--------|----------------|------------------|-----------|
| `Billing` | Decides and performs charges for renewals | `decideRenewal(sub, time) -> Decision`, `BillingGateway.charge(...)` | `Subscriptions`, payment provider |
| `Subscriptions` | Owns subscription + seat state and invariants | `load(id)`, `assignSeat(...)`, `cancel(...)` | datastore |
