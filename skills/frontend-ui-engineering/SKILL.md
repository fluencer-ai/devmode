---
name: frontend-ui-engineering
description: >-
  Build production-quality UI — component architecture, the state-management
  decision ladder, responsive layout, and escaping the generic "AI aesthetic."
  Use when building or reviewing front-end components, choosing where state
  lives, when a UI "looks AI-generated" (purple gradients, everything rounded),
  when the user mentions "build the UI", "this component", "React/Vue/Svelte",
  "make it look good", "responsive", "design system". Pair with ux-design (visual
  decisions) and accessibility (a11y is not optional).
---

# Front-end UI engineering

Front-end is where "works" and "is good" diverge most: a component can pass its
tests and still be unusable, inaccessible, or instantly recognizable as
AI-slop. This skill is the production bar. It's framework-shaped (React/Vue/
Svelte/etc.) but the decisions below are framework-agnostic.

## Escape the "AI aesthetic"

AI-generated UIs have a tell. Recognize and avoid the defaults:

| AI default | Why it's a problem | Production quality |
|------------|--------------------|--------------------|
| Purple/indigo everything, gradient overload | Generic, off-brand, dated | A real, restrained palette; gradients sparingly and on purpose |
| Drop-shadow on every element | Visual noise, no hierarchy | Elevation only where it signals layering |
| Everything `rounded-2xl` | No intent, toy-like | Radius scale tied to component role |
| Centered single-column for everything | Wastes space, no rhythm | Real layout: grid, alignment, density |
| Emoji as icons | Inconsistent, unprofessional | A proper icon set |

The fix isn't "more polish" — it's *intent*: every visual choice should map to a
design decision (see [`ux-design`](../ux-design/SKILL.md)), not a library default.

## The state-management decision ladder

Most front-end complexity is misplaced state. Put state at the *lowest* level
that works; climb only when forced:

1. **Local component state** — used by one component. Start here.
2. **Lifted state** — shared by a few siblings → lift to the nearest common parent.
3. **Context / provider** — cross-cutting, low-frequency (theme, current user).
   Not for high-frequency updates (re-render storms).
4. **URL state** — anything that should survive refresh/sharing (filters, tab,
   page). The URL is underused state.
5. **Server state** — data that lives on the server → a query/cache layer
   (dedupe, caching, invalidation), *not* hand-rolled in a global store.
6. **Global client store** — last resort, for genuinely global client-only state.

Pushing server data into a global store is the most common mistake — it
re-implements caching badly. Treat the server as the source of truth and cache it.

## Component architecture

- **Deep components, simple props** — the [`deep module`](../improve-codebase-architecture/SKILL.md)
  idea applied to UI: a small, clear prop interface hiding internal complexity.
  Avoid prop-drilling and 15-prop "god components."
- **Separate the functional core** — keep formatting/derivation/decision logic
  pure and testable, away from rendering and effects
  ([`functional-core-imperative-shell`](../functional-core-imperative-shell/SKILL.md)).
- **Composition over configuration** — prefer composable pieces to one component
  with a boolean for every variant.
- **Name in the [`ubiquitous language`](../ubiquitous-language/SKILL.md).**

## Non-negotiables

- **Accessibility is part of "done", not a later pass** — semantic elements,
  labels, keyboard operability, focus management. See
  [`accessibility`](../accessibility/SKILL.md).
- **Responsive by default** — design mobile-up; test the real breakpoints.
- **Loading / empty / error states exist** — the happy path is a third of the UI;
  design the other two-thirds.
- **Look at it run** — verify in a real browser ([`feedback-loops`](../feedback-loops/SKILL.md),
  [`browser-testing`](../browser-testing/SKILL.md)); screenshots and the DOM are
  the feedback loop for UI.

## Red flags

- A `<div onClick>` where a `<button>` belongs (kills keyboard + a11y).
- State lifted to global "to be safe."
- A component that renders, fetches, transforms, and decides — split it.
- "It looks fine to me" with no browser check across breakpoints.

> Adapted from `addyosmani/agent-skills` (`frontend-ui-engineering`), MIT.
> Generalized off its React/Vite specifics to fit devmode's tool-agnostic base.
