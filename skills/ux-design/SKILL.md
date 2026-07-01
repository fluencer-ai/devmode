---
name: ux-design
description: >-
  Make deliberate visual and interaction design decisions — design tokens,
  visual hierarchy, layout, spacing rhythm, typography, and interaction states —
  so a UI looks intentional, not defaulted. Use when designing a screen or
  component's look-and-feel, building or extending a design system / token set,
  when the user says "design this", "make it look intentional", "what colors/
  spacing/typography", "design tokens", "visual hierarchy". The design layer
  above frontend-ui-engineering (how it's built) and accessibility (who can use it).
---

# UX & visual design

Front-end engineering answers *how it's built*; this answers *what it should
look and feel like, and why*. The goal is **intent**: every color, size, and
spacing value should trace to a decision, not a library default. Design is the
difference between "works" and "feels right."

## Design tokens — decisions, not magic numbers

Express the design as a small set of named tokens, then build only from them.
Hardcoded hex/px values scattered through components are the design equivalent of
shallow modules — impossible to change coherently.

- **Color:** a restrained palette — a brand/primary, a neutral ramp (not pure
  black/white), semantic colors (success/warn/error/info), and *enough* contrast
  (see [`accessibility`](../accessibility/SKILL.md)). Avoid the AI-default
  purple-gradient look.
- **Spacing:** one scale (e.g. 4-based: 4/8/12/16/24/32…). Consistent rhythm
  reads as "designed"; arbitrary margins read as "generated."
- **Typography:** a type scale (sizes + weights + line-heights), one or two
  families, deliberate measure (line length). Hierarchy comes from the scale,
  not random font sizes.
- **Radius / elevation / motion:** small scales tied to *role* (a card vs. a
  button vs. a modal), not applied uniformly.

## Visual hierarchy — guide the eye

A screen should answer "where do I look first?" instantly.

- **One primary action per view.** Make it visually dominant; demote the rest to
  secondary/tertiary. Two equal-weight CTAs = no hierarchy.
- **Size, weight, color, and space** create rank — use them intentionally, and
  use *fewer* of them per view (restraint reads as confidence).
- **Group by proximity and alignment.** Related things sit close and aligned;
  whitespace is structure, not waste. Make it checkable: keep within-group
  spacing at most half the between-group spacing (a ~2:1 gap), so grouping is
  visible, not implied. Uniform spacing everywhere destroys grouping — the #1
  spacing tell.
- **Density to match the task** — a dashboard and a landing page want opposite
  densities; choose deliberately.

## Interaction & states

A control isn't designed until all its states are:

- **Every interactive element:** default, hover, focus (visible!), active,
  disabled, loading. Missing focus states is both a UX and an
  [`accessibility`](../accessibility/SKILL.md) failure.
- **Every data view:** loading, empty (with a helpful next step), error
  (recoverable), and populated. The empty state is a design opportunity, not an
  afterthought.
- **Feedback & motion:** confirm actions; use motion to explain change (enter/
  exit, state transitions), briefly and purposefully — not decoration.
- **Forgiving by default:** confirm destructive actions, allow undo, preserve
  input on error.

## Process

1. **Start from the user's goal and content**, not a blank canvas — what must
   they accomplish, what's the most important thing on this screen?
2. **Set/extend the tokens** before styling components, so choices stay coherent.
3. **Establish hierarchy** (primary action, reading order) before polish.
4. **Design all the states**, not just the happy path.
5. **Critique it** — run [`design-critique`](../design-critique/SKILL.md) (and a
   real-browser look) before calling it done.

## Red flags

- Hardcoded colors/spacing instead of tokens → can't restyle coherently.
- Two or more competing primary actions → flat hierarchy.
- Only the happy/populated state designed.
- "Polish" added (shadows, gradients, rounding) without a hierarchy reason.
- Contrast or focus states ignored — that's an accessibility defect, not a taste call.

> Authored for devmode to fill the design/UX gap that imported skill packs leave
> (they fold design into front-end). Pairs with frontend-ui-engineering,
> accessibility, and design-critique.
