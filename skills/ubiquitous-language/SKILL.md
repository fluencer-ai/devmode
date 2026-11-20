---
name: ubiquitous-language
description: >-
  Ubiquitous language: build and sharpen a shared glossary of domain terms used
  identically by the user, the AI, and the code. Use when starting on an
  unfamiliar codebase or domain, when output drifts from the plan, or when terms
  in conversation and code disagree.
disable-model-invocation: true
---

# Ubiquitous language

Verbose, drifting AI output usually isn't a reasoning problem — it's a language
problem. When you and the model don't share precise terms for the domain, the
model pads its thinking with circumlocution and translates intent through fuzzy
synonyms, so the implementation drifts from the plan. This is the same gap a
developer hits with a domain expert in microchips or insurance or logistics:
without shared vocabulary, every exchange is a lossy translation.

Domain-Driven Design's answer is a **ubiquitous language**: a single set of
terms, defined once, used everywhere — in conversation with the user, in the
AI's reasoning, and in the code itself. When the language is shared, the model
thinks more tightly and the code it produces lines up with what was planned.

## What to produce

Create or update a `UBIQUITOUS_LANGUAGE.md` (or the project's equivalent) at
the repo root, starting from `assets/glossary-template.md`. Create it lazily,
when the first term is resolved. It is a living glossary, organized by
sub-domain, of the terms that matter. Use markdown tables so it stays scannable:

```markdown
## <Sub-domain name>

| Term | Definition | In code as | Notes / invariants |
|------|------------|-----------|--------------------|
| Subscription | A customer's ongoing paid access to a plan | `Subscription` aggregate | Always has exactly one active Plan; a cancelled Subscription is kept, never erased. _Avoid_: membership |
| Seat | One assignable license within a subscription | `Seat` entity | A seat is assigned or free; never both |
| Dunning | The retry process after a failed payment | `DunningRun` | Max 4 attempts over 14 days |
```

The `In code as` column is what makes the language *ubiquitous* — it ties each
domain word to the concrete type, function, or module that represents it, so
the term means the same thing in a meeting and in a file.

**The glossary holds no implementation details.** A definition says what the
concept IS, in one or two sentences; an invariant states a domain rule. Storage
choices, algorithms, field mechanics, and design decisions do not belong here:
the glossary is not a spec, a scratch pad, or a decision log. The `In code as`
column carries only the identifier's name. The module map is the one
architecture section, and it stays separate (below).

## How to build it

1. **Scan the codebase first.** Read module names, type names, key function
   names, database tables, and existing docs. The vocabulary already in use is
   the starting point — capture it before inventing anything.
2. **Extract the real terms.** Pull out the nouns and verbs that carry domain
   meaning. Skip generic plumbing (`Controller`, `Service`, `Helper`) and general
   programming concepts (timeouts, error types) unless they carry a meaning
   unique to this project.
3. **Define each precisely.** A good definition names the concept, its
   boundaries, and any invariant that's always true of it. Ambiguity here is the
   bug you're trying to kill.
4. **Resolve synonyms and conflicts.** If the code says `User` in one place and
   `Account` in another for the same thing, flag it and pick one. Be opinionated:
   keep the best word and list the others as _Avoid_. Divergent terms for one
   concept are a smell worth surfacing to the user.
5. **Note relationships.** Where one term is defined in relation to another
   (a Seat belongs to a Subscription), say so — that's the domain model leaking
   through, which is exactly what you want.

## Sharpen it during the session

The glossary is built in conversation, not after it. While planning or grilling:

- **Challenge against the glossary.** When the user uses a term that conflicts
  with an existing entry, call it out at once: "The glossary defines cancellation
  as X, but you seem to mean Y. Which is it?"
- **Sharpen fuzzy language.** For a vague or overloaded term, propose the precise
  canonical one: "By account, do you mean the Customer or the User?"
- **Challenge claims against the code.** When the user states how something
  works, check whether the code agrees, and surface a contradiction: "The code
  cancels whole Orders, but you just said partial cancellation is possible. Which
  is right?"
- **Stress-test slippery boundaries with a scenario.** A flat table defines each
  term in isolation, so it hides the ambiguities that live *between* related
  terms. Invent an edge case that forces the user to be precise. Where a
  definition alone hasn't settled the argument, keep a 3–5 line exchange in the
  glossary next to the terms it clarifies:

  > **Dev:** When a customer places an Order, do we create the Invoice then?
  > **Expert:** No — an Invoice is only generated once a Shipment is confirmed. A
  > single Order can produce several Invoices if items ship separately.
  > **Dev:** So a Shipment cancelled before dispatch has no Invoice?
  > **Expert:** Right — the Invoice is tied to the Shipment, not the Order.

- **Write it down inline.** Update the glossary the moment a term is resolved;
  don't batch.

## Don't let a primitive delete the domain concept

Reusing a primitive one layer down — a token, a link, a session, a cache key — is
a virtue right up until it erases the thing the feature is actually about. The
trap is fusing a **property the feature requires** (email-binding, single-use,
consent) with an **implementation that happens to carry it today** (an auth link,
a signed URL, a session). Once fused, the reuse looks automatically correct, and
you borrow an *ephemeral* artifact to stand in for a *durable* domain record.

Separate the two: **name the property, then ask whether the primitive *models* it
or merely *coincides* with it today.** An auth link is not an invitation; a cache
key is not a job; a session is not an audit trail.

The tell is **lifecycle**. When the concept must be revoked, resent, expired on
its own clock, run several at once, or record who accepted and when, that
lifecycle *is* a domain term — it belongs in the glossary as a first-class entry
with its own status invariant (e.g. `requested → active / declined`), not smuggled
into a primitive that can't hold those states. Adding a well-chosen, durable term
is the *deep* move here — the counterweight to reuse (`minimal-code`), not a
contradiction of it.

## The module map: the architecture side of the language

Module names are part of the language too, so the same file carries a **module
map**: each deep module, its responsibility, its public interface, and its
dependencies. It is the architecture view and stays in its own section, clearly
apart from the glossary tables, so interfaces never leak into term definitions.
Building or updating the module map? Read `module-map.md` in this folder.

## Offer ADRs sparingly

Glossary work surfaces decisions. Offer an ADR only when it clears the bar in
`documentation` (which also owns the format):

1. **Hard to reverse**: changing your mind later has a meaningful cost.
2. And a future reader will ask "why this way?", because it is **surprising
   without context** or it was **a real trade-off** among genuine alternatives.

If it is cheap to reverse, skip the ADR. A resolved term goes in the glossary,
not an ADR.

## How to use it

- **Keep it open during planning and grilling.** Reference its exact terms when
  you talk to the user and when you write the PRD. Consistency compounds.
- **Use the terms in code and tests.** Type names, test descriptions, and
  variable names should echo the glossary. This is what keeps the language from
  drifting back into vagueness.
- **Update it as the domain evolves.** When a new concept appears or a
  definition sharpens, edit the glossary in the same change. A stale glossary is
  worse than none.
- **Feed it to the AI explicitly.** When delegating implementation, point the
  agent at the glossary so its reasoning starts from your vocabulary, not its
  own paraphrase.

`grill-me` surfaces terms worth defining, and `write-prd` writes in this
language.
