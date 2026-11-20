---
name: visual-explainers
description: >-
  Visual explainers: an inline SVG diagram, HTML mockup, chart, or interactive
  explainer that is legible, themed, and accessible. Use when the user asks to
  see, diagram, or chart something, or when a structure, flow, or comparison reads
  faster as a picture.
disable-model-invocation: true
---

# Visual explainers

A picture earns its place when the *shape* of something — how layers nest, how a
request flows, how two options differ, how a number moved — is the point. The
model's default is prose; prose is the wrong medium for structure. This skill is
the knowledge an agent lacks by default: **when** to reach for a visual, and the
**discrete, easy-to-get-wrong mechanics** that decide whether the result is crisp
or garbage.

## The gap this closes

Left alone, agents fail visuals in two opposite ways:

1. **Under-reach** — answer a structural question with three paragraphs when one
   diagram would land instantly.
2. **Over-produce, badly** — emit an SVG with a viewBox too small (content
   clipped), arrows routed straight through unrelated boxes, labels sitting *on*
   the arrow lines, hardcoded `#333` text that vanishes in dark mode, ten boxes
   crammed across one row, and no accessibility hooks.

Both are knowledge gaps, not skill gaps. The rules below are the plugged
loopholes — most were learned the hard way, one clipped diagram at a time.

## When to reach for a visual (and when not)

Reach for it when the payload is **structure or magnitude**: system architecture,
nesting/containment, a sequence or decision flow, a side-by-side comparison, a
distribution or trend, a UI you're proposing. One focused visual beside a short
prose explanation beats either alone.

Do **not** decorate. A visual that just restates a sentence is noise. If you catch
yourself making a diagram because the answer feels bare, stop — bare prose that's
correct beats a diagram that adds nothing. And never produce *several* mediocre
visuals where one sharp one would do; the cost is the reader's attention.

## The protocol (show_widget / visualize tool)

1. **Load the design guidance first, silently.** Before your *first* `show_widget`
   call in a session, call the visualize `read_me` for the module(s) you need —
   `diagram`, `mockup`, `interactive`, `chart`, or `art`. It returns the CSS
   variables, color/text classes, sizing rules, and per-type guidance. **Do not
   narrate this call** — it's setup; just build the visual and present it.
2. **Route on the verb, not the noun.** Same subject, different visual:
   - *"what's the architecture / how is this organised"* → **structural diagram**
     (boxes nested/containing, labels, arrows).
   - *"walk me through / what are the steps / what's the flow"* → **flowchart**.
   - *"how does X actually work / explain X / I don't get X"* → **illustrative**
     (a visual metaphor, not a flowchart).
   - *"compare / which should I pick"* → side-by-side table or paired columns.
   - *"how did this number move / show the breakdown"* → **chart**.
   - *"what would the screen look like"* → **mockup** (HTML).
3. **Build, verify, present.** One visual per call. Put the explanation in your
   text response; put only labels in the visual.

## SVG diagram mechanics — the load-bearing rules

These are not style preferences; breaking them clips content or kills dark mode.

- **Canvas:** `<svg width="100%" viewBox="0 0 680 H" role="img">` with `<title>`
  and `<desc>` as the **first** children (screen readers announce them). The
  **680 is load-bearing** — it matches the container so SVG units render 1:1 with
  CSS pixels; all the "text fits in box" math assumes it. If content is naturally
  narrow, keep 680 and *center* the content (e.g. x=240..440); don't shrink the
  viewBox.
- **Height to fit:** after layout, `H = (bottom-most element, incl. text baseline)
  + ~20–40px`. Don't guess; don't leave a sea of empty space.
- **Safe area:** keep everything between x=40 and x=640.
- **Color only via the pre-built classes** (`c-blue`, `c-teal`, `c-amber`,
  `c-slate`, …) on shapes. They auto-adapt to light/dark. **Never** write a
  `<style>` color block and **never** hardcode hex on shapes — that's the #1 cause
  of "invisible in dark mode."
- **Every `<text>` carries a class** — `t` (14px label), `ts` (12px subtitle/arrow
  label), `th` (14px heading). Two font sizes only, 14 and 12. An unclassed
  `<text>` inherits the wrong font and may be invisible — that's the tell you
  forgot. Inside a `c-{color}` parent, the text classes auto-adjust to that ramp.
- **Connectors:** stroke with a CSS variable, not a class —
  `stroke="var(--color-text-secondary)"`. Define one arrowhead `<marker>` and
  reuse it. Put arrow labels *beside* the line (offset ~10px), never on it.
- **Route arrows through gaps, not boxes.** Before drawing a vertical connector at
  x, confirm x falls in the gap *between* the boxes of the tier it crosses — an
  arrow spearing a box reads as a bug.

## The complexity budget (hard limits)

- **≤4 boxes per full-width tier** (~140px each). 5+ → shrink to ≤110px, wrap to
  two rows, or split into overview + detail diagrams.
- **≤2 color ramps.** If color encodes meaning (tiers, states), add a one-line
  legend; otherwise use a single neutral ramp. More than two ramps reads as
  confetti.
- **Box subtitles ≤5 words.** Detail goes in your prose, not the box. If you're
  writing a sentence inside a box, it's the wrong container.
- **Sentence case** on every label. No icons inside boxes (text only). No
  oversized step numbers or headings floating outside boxes.

## Layout math

Placing boxes and arrows by hand, or want a 3-tier skeleton to copy? Read
`svg-layout.md` in this folder (the anti-overlap recipe plus the skeleton).

## HTML widget mechanics (mockups, dashboards, interactive)

When the answer is a UI or needs interaction, output HTML (no `<html>/<head>/
<body>` wrapper):

- **All colors via CSS variables** (`--color-text-primary`,
  `--color-text-secondary`, `--color-bg-*`, `--border-radius-lg`, …). Never
  hardcode hex — same dark-mode rule as SVG.
- **Accessibility:** begin with a visually-hidden `<h2 class="sr-only">` that
  summarizes the widget in one sentence.
- **Host owns the frame:** transparent background, no top-level padding, no outer
  container with its own background — the card is provided for you.
- **Scripts run after streaming completes.** On Claude artifact surfaces, the
  globals `sendPrompt(text)` and `openLink(url)` can hand work back to chat or
  open the host's link-confirmation dialog. In Codex, use the native inline
  visualization/artifact surface and ordinary links; call those globals only
  after feature-detecting them. Handle filtering/sorting/toggling locally in JS.

## Two small parameters that matter

- **`title`** — a snake_case, *disambiguating* identifier (`oauth_login_flow`, not
  `diagram`); it's also the download filename.
- **`loading_messages`** — 1–4, ~5 words each, in the user's language. **Make them
  boring for serious topics** (illness, death, finance-in-distress, anything where
  the reader may be personally affected): describe what the code does, plainly.
  Playful is fine only for light subjects.

## Anti-patterns / red flags

| Smell | Why it's wrong | Fix |
|---|---|---|
| viewBox height guessed | content clips at the bottom | set H = lowest element + ~20–40 |
| changed viewBox width off 680 | text math + scaling break | keep 680; center narrow content |
| `<style>` color block / hardcoded hex | invisible in dark mode | use `c-*` classes / CSS vars only |
| `<text>` with no class | wrong/invisible font | always `t`, `ts`, or `th` |
| arrow crosses a box | reads as a bug | route through the gap; verify x |
| label sitting on the arrow line | unreadable | offset the label ~10px beside it |
| 6 boxes across one row | cramped, clipped | ≤4 per tier; wrap or split |
| 3+ color ramps | confetti, no meaning | ≤2 ramps + a legend |
| sentence inside a box | wrong altitude | ≤5-word subtitle; prose goes in chat |
| narrating the `read_me` call | breaks the seam | call it silently, then present |
| "click to learn more" but box is dense | broken promise | make the visual *actually* sparse |
| a visual that restates a sentence | decoration, noise | cut it; keep the prose |

## Verify before presenting

Re-read the SVG/HTML as if rendered on a near-black background: is every text
element readable? Does any shape or label cross the viewBox edge? Does every arrow
land in a gap? Is `H` tight? One `<svg>` per call — if the first attempt is wrong,
replace it entirely, never append a "fixed" copy after the broken one.

---

Pairs with `frontend-ui-engineering` (how the UI is built, its `ux-design.md` for
visual hierarchy, spacing, and color, and its `accessibility.md` for the
`role="img"`/`sr-only` discipline) and `documentation` (a diagram is
documentation that renders). The base rules here mirror the visualize tool's own design system;
they transfer to any SVG/HTML you hand-author.
