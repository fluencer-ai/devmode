# The candidate report

Read this when building the report in step 3 of `SKILL.md`. The report shows the
deepening candidates so the user can pick one; the diagrams carry the weight,
prose stays sparse.

## Where it renders

Follow `visual-explainers` for the mechanics: theme-aware colors through its
classes and CSS variables (never hardcoded hex), the complexity budget, the
accessibility hooks. Render inline where the host has a visual surface. Otherwise
write one self-contained HTML file to the OS temp directory (never into the repo),
named `architecture-review-<timestamp>.html`, open it for the user, and give them
the absolute path. Keep it static: no app code, no interactivity beyond diagram
rendering.

## Layout

1. **Header**: repo name, date, and a compact legend (solid box = module, dashed
   line = seam, red arrow = leakage, thick dark box = deep module). No intro
   paragraph; go straight to the candidates.
2. **One card per candidate**, in the order below.
3. **Top recommendation**: one larger card with the candidate's name, one
   sentence on why it goes first, and an anchor link to its card.

## Candidate card

- **Title**: short, names the deepening ("Collapse the Order intake pipeline").
- **Badge row**: recommendation strength, plus a tag for the dependency category
  (`in-process`, `local-substitutable`, `ports & adapters`, `mock`):
  - `Strong`: the friction is real and the deepening clearly pays (teal/green ramp).
  - `Worth exploring`: plausible win, open questions remain (amber ramp).
  - `Speculative`: possible, weakly evidenced (slate ramp).
- **Modules and files involved**: a short monospaced list.
- **Before / after diagram**: the centerpiece, two columns side by side, about
  320px tall.
- **Problem**: one sentence. What hurts.
- **Solution**: one sentence, in plain English. What changes.
- **Wins**: bullets of at most 6 words, named in the vocabulary ("locality: bugs
  concentrate in one module", "leverage: one interface, N call sites", "delete 4
  shallow wrappers"). Never "easier to maintain" or "cleaner code".
- **ADR callout** (only if it applies): one line in an amber box, e.g. "contradicts
  ADR-0007, but worth reopening because…".

If the diagram needs a paragraph to be understood, redraw the diagram.

## Diagram patterns

Pick the one that fits each candidate and vary them across the report; identical
diagrams read as generic.

- **Dependency graph**: "X calls Y calls Z, and look at the mess". Color leakage
  edges red and the deep module dark. A sequence view works for "before: 6 round
  trips, after: 1".
- **Boxes and arrows**: modules as boxes, arrows routed through the gaps. Use it
  when the "after" should read as one thick-bordered deep module with its old
  pieces greyed out inside.
- **Cross-section**: stacked horizontal bands for the layers a call passes
  through. Before: 6 thin bands doing nothing. After: 1 thick band labeled with
  the consolidated responsibility.
- **Mass diagram**: two rectangles per module, interface and implementation.
  Before: nearly the same height (shallow). After: a short interface over a tall
  implementation (deep).
- **Call-graph collapse**: before, a tree of calls as nested boxes; after, the
  same tree collapsed into one box with the now-internal calls faded inside.

Module labels inside diagrams read as schematic: small, uppercase, sentence-short.

## Tone

Plain, concise, no hedging, no throat-clearing. If a sentence could be a bullet,
make it one; if a bullet could be cut, cut it. Fitting phrasings:

- "Order intake module is shallow: interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

If a term isn't in the vocabulary or the glossary, reach for one that is before
inventing a new one.
