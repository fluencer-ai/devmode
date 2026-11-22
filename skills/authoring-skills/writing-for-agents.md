# Writing for agents

Read this when writing or restructuring the body of any document an agent
consumes: a skill, an agent definition, `CLAUDE.md` / `AGENTS.md`, or a doc
reached by a pointer. The packaging differs; the writing does not. The goal is
that the agent takes the same *process* every run.

## Context pointers

A **context pointer** is a line held in context that names out-of-context
material and the condition for reaching it. A skill description is one; a line in
`CLAUDE.md` naming a doc is another; "Read `ci-cd.md` when..." is a third. The
pointer's *wording*, not its target, decides when and how reliably the agent
reaches the material. A must-have target behind a weak pointer is a variance bug:
sharpen the wording first, and inline the material only if sharpening fails.

A pointer states what the material is and lists the **branches** that should
trigger it (a branch is a distinct case, so different runs take different paths).
Always-loaded pointers earn the hardest pruning:

- Front-load the leading word.
- One trigger per branch; synonyms for one branch are one branch written twice.
- Cut identity the body already carries.

## Information hierarchy

A document mixes **steps** (ordered actions) and **reference** (rules, facts,
definitions consulted on demand). Place each piece on a ladder ranked by how
immediately the agent needs it:

1. **In-file step:** what the agent does, in order.
2. **In-file reference:** consulted on demand; a flat peer-set of rules is fine.
3. **Disclosed reference:** a sibling file (or any external doc) behind a pointer,
   loaded only when the pointer fires.

Push too little down and the top bloats; push too much and you hide what the
agent needs. The branching test settles it: inline what every branch needs,
disclose what only some branches reach. Reference left inline among steps buries
them, and attending to a buried step becomes a coin-flip.

- **Co-location:** once a piece has its rung, keep a concept's definition, rules,
  and caveats under one heading. Scattering fragments one meaning across many
  places (distinct from duplication, which repeats it).
- **Sprawl:** a document too long even when every line is live and unique.
  Attention thins across the excess. Cure it with the ladder: disclose reference,
  and split by branch or sequence so each path carries only what it needs.

## Completion criteria

Every step ends on a criterion with two properties:

- **Clarity:** can the agent tell done from not-done? A vague bound invites
  **premature completion**, pulled by the visible steps still ahead. Sharpen the
  bound first. Only if it is irreducibly fuzzy *and* you observe the rush, hide the
  later steps by splitting the sequence across a real context boundary (a handoff
  or a subagent); an inline call leaves them in view and clears nothing.
- **Demand:** how much it requires. "Every modified model accounted for" drives
  more legwork than "produce a change list". Demand binds flat reference too:
  "every rule applied" is an exhaustiveness bar for a checklist.

The strongest criteria are both checkable and exhaustive.

## When to split

Splitting spends one of the two loads, so split only when the cut earns it:

- **By sequence:** when later steps tempt the agent to rush the current one.
  Merging sequences does the reverse and invites premature completion.
- **By invocation:** in devmode every leaf is user-invoked and reached through the
  router, so a split creates a new leaf only when it is a distinct case the router
  should name on its own. Otherwise split into a sibling file.

## Leading words

The cheapest way to steer behavior is to **recruit a concept the model already
holds**. A *leading word* is a compact term already in the model's pretraining
(`lesson`, `fog of war`, `tracer bullets`, `tight`, `red`) that the agent thinks
*with* while running the skill. Used as a repeated token (never restated as a
sentence), it accumulates meaning across the skill and anchors a whole region of
behavior for almost no tokens, because the priors come free.

It pays twice: in the body it anchors *execution* (the agent reaches for the same
behavior every time the word appears; the consistency a skill exists to buy); in
the description, and wherever the same word lives in your prompts, PRDs, and code,
it anchors *invocation*. devmode already runs on this (`grill`, `ratchet`,
`headlights`): name the concept, don't paraphrase it. Coin your own word only if
you then *define* it: a made-up term recruits no priors, so you pay in definition
tokens what a pretrained word gives free. And a word too weak to beat the default
(`be thorough` when the agent already is) is a **no-op**: the fix is a stronger
word (`relentless`), not more prose.

Hunt for restatements a leading word retires: a triad spelled out at three sites
("fast, deterministic, low-overhead" becomes *tight*), or a fuzzy gate that a
binary word makes observable (the loop goes *red* on the bug, or it doesn't).

## Pruning

- **Single source of truth:** each meaning lives in one place, so a behavior
  change is a one-place edit. Duplication costs tokens and inflates a meaning's
  rank on the ladder.
- **The environment is a source of truth too** (`package.json` scripts, config,
  the directory layout, `--help`). A document that restates it is a cache. Cache
  only what looking cannot find: the unwritten convention, the reason behind a
  choice, the gotcha no config confesses.
- **Relevance:** a line that never bears on the task, or has gone stale, is
  **sediment**. Shorter documents are easier to keep relevant.
- **No-ops:** test sentence by sentence whether it changes behavior versus the
  default. When it fails, delete the whole sentence rather than trimming words.
