# SVG layout math and a copyable skeleton

Read this when you place boxes and arrows in an SVG diagram by hand (the
anti-overlap recipe), or want a 3-tier skeleton to start from.

Overlap and clipping come from eyeballing coordinates. Compute them:

- **Evenly spaced row of N boxes** across the safe width `W=600` (x=40..640) with
  gap `g`: `boxW = (W − (N−1)·g) / N`. For N=4, g=16 → boxW=138; the box x's are
  `40, 40+154, 40+308, 40+462` → right edge 640. ✔
- **Center a single box:** `x = 40 + (W − boxW)/2`.
- **Vertical rhythm:** give each tier a `y` and a fixed height; leave ~22–28px
  between a tier's bottom and the next arrow, and ~6–8px between an arrow head and
  the next box top. Track a running `y` so nothing collides.
- **Label baselines inside a box** `y..y+h`: single label at `y + h/2 + 5`; with a
  subtitle, label at `y + h·0.45`, subtitle at `y + h·0.72`.
- **The arrow-in-the-gap trick:** to drop a connector from a one-box tier into the
  *gap* of a four-box tier, place it at the center x only if that x lands between
  two boxes; with N=4, g=16, the center (x=340) sits in the gap between box 2
  (…332) and box 3 (348…). Verify, don't assume.

### Copyable skeleton — a 3-tier structural diagram

This is the exact pattern behind a clean "layers → filter → output" architecture
diagram. Adapt labels; keep the structure.

```svg
<svg width="100%" viewBox="0 0 680 300" role="img" xmlns="http://www.w3.org/2000/svg">
  <title>One-sentence what-this-shows</title>
  <desc>One sentence describing the flow for screen readers.</desc>
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="var(--color-text-secondary)"/>
    </marker>
  </defs>

  <!-- Tier 1: input (neutral outline) -->
  <rect x="40" y="40" width="600" height="48" rx="10" fill="none"
        stroke="var(--color-border-primary)" stroke-width="1.5"/>
  <text class="th" x="340" y="62" text-anchor="middle">Input layer</text>
  <text class="ts" x="340" y="79" text-anchor="middle">≤5-word subtitle</text>

  <line x1="340" y1="90" x2="340" y2="114" stroke="var(--color-text-secondary)"
        stroke-width="1.5" marker-end="url(#ah)"/>
  <text class="ts" x="350" y="106" text-anchor="start">verb</text>

  <!-- Tier 2: the filter (colored, ≤4 boxes; arrow above lands in a gap) -->
  <rect class="c-amber" x="40"  y="120" width="138" height="54" rx="10"/>
  <rect class="c-amber" x="194" y="120" width="138" height="54" rx="10"/>
  <rect class="c-amber" x="348" y="120" width="138" height="54" rx="10"/>
  <rect class="c-amber" x="502" y="120" width="138" height="54" rx="10"/>
  <text class="t" x="109" y="151" text-anchor="middle">Box one</text>
  <text class="t" x="263" y="151" text-anchor="middle">Box two</text>
  <text class="t" x="417" y="151" text-anchor="middle">Box three</text>
  <text class="t" x="571" y="151" text-anchor="middle">Box four</text>

  <line x1="340" y1="176" x2="340" y2="200" stroke="var(--color-text-secondary)"
        stroke-width="1.5" marker-end="url(#ah)"/>

  <!-- Tier 3: output (colored) -->
  <rect class="c-teal" x="40" y="206" width="600" height="48" rx="10"/>
  <text class="th" x="340" y="234" text-anchor="middle">Output layer</text>

  <!-- legend, if color encodes meaning -->
  <rect class="c-amber" x="40" y="270" width="14" height="14" rx="3"/>
  <text class="ts" x="60" y="281" text-anchor="start">what amber means</text>
  <rect class="c-teal" x="200" y="270" width="14" height="14" rx="3"/>
  <text class="ts" x="220" y="281" text-anchor="start">what teal means</text>
</svg>
```
