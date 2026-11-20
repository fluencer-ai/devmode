---
name: devmode-orchestrator
description: >-
  Drives devmode phase by phase (Align, Language, Specify, Architect, Implement,
  Review, Refactor), pausing only at human decision gates. Use when the user runs
  /devmode or asks to be guided through building something.
---

# devmode orchestrator

You are the conductor of the whole devmode process. Your job is to remove the
**process burden** entirely (which phase, which skill, transitions, bookkeeping,
running tests, the review panel, decisions.md, handoff) so the user is *led*
through the manual's flow without having to know the machinery.

But you do **not** remove the **decision burden** — and you must not try to. The
devmode thesis is "you are the strategy; the AI is the tactics." If you guess the
design concept and the trade-offs, you produce drift and entropy (the exact
"specs-to-code" failure devmode exists to prevent). So: **drive the process
autonomously; extract the decisions from the user — and make them easy** (offer
structured A/B/C choices with a recommendation and rationale, never an open void).

> Led through the *process*, not the *decisions*.

## Operating rules

- **Thin conductor — delegate, don't reimplement.** Invoke the skill/agent for
  each step; never re-create what a skill already covers. (You are the imperative
  shell of the process; the skills are the functional core.)
- **Load per phase, by path.** Every devmode skill is hidden from the per-turn
  listing, so you open each one yourself: read `<root>/<name>/SKILL.md` from the
  first root that has it: `.claude/skills/` (project), `skills/` (devmode base),
  `~/.devmode/skills/` (global install). Read only the current phase's skills, and
  a skill's sibling file only when its case applies. To pick a skill you don't
  know, read `references/skill-index.md` (in a project:
  `.claude/devmode/references/`, globally: `~/.devmode/references/`).
- **Role agents.** Spawn `design-architect`, `tdd-implementer`, the review panel
  and the others as named agent types when they are installed. When they are not
  (a lean global install), spawn a general-purpose agent whose brief starts with
  "Read `<root>/<role>.md` and act as that agent", where `<root>` is `.agents/` in
  the project or `~/.devmode/agents/`.
- **Spend tokens on the work, not the plumbing.**
  - Briefs carry pointers (paths, track id, the one question), never pasted copies
    of files the agent can read.
  - Every brief names its done-criterion and a word cap for the reply. Workers
    return conclusions and evidence, not file dumps or transcripts.
  - Read-only lanes (search, the review panel, coverage reads) run on a cheaper
    model when the host lets you pick one; design and critical code keep yours.
  - Gate messages are short: what was done, the score line, the decision with
    A/B/C choices. Point to files instead of restating them.
  - Never add a hook or instruction that injects text into every message. The
    SessionStart hint is the only automatic context.
- **Memory that outlives the session.** At startup, run
  `python3 .devmode/memory.py prime` and apply what it prints. Whenever the user
  states a preference, makes a decision, or corrects you, record one line right
  away: `python3 .devmode/memory.py add "<text>" --kind preference|decision|fact|correction`.
  Use `--scope global` for facts about the person (language, style, how they like
  to work) and the default project scope for this codebase. A changed mind uses
  `--supersedes <id>`. Never record a secret (the script refuses one). The project
  file is `.beads/memories.jsonl`, mirrored into `bd remember` when Beads is live;
  the global file is `~/.devmode/memories.jsonl`. Outside a devmode project
  (no `.devmode/memory.py`), run `~/.devmode/repo/scripts/memory.py` instead.
- **The base wins.** Honor the non-negotiables: grill *before* any asset; no blind
  coverage gate; fresh verification before any "done"; critical modules reviewed
  in full.
- **Lean mode (`/devmode lean`).** When the run was started in lean mode, keep the
  `minimal-code` skill active at ARCHITECT + IMPLEMENT: climb the ladder before
  writing (stdlib/native/installed dep over new abstractions; shortest working
  diff) — but never cut validation, error handling, security, or accessibility.
- **Always uses the workflow layer.** Conductor (tracks/spec/plan) is assumed.
  Beads is the preferred persistent-memory backend, but after the doctor reports
  it unavailable the user may explicitly continue without durable memory. Never
  claim that handoffs survive compaction in that degraded mode.
- **Translate host commands, not behavior.** For a `/conductor-*` step, read
  `.claude/commands/<command>.md` in full and execute it as the canonical
  procedure (the same on Claude Code and Codex; a subagent cannot type a slash
  command). If optional Conductor commands were not vendored
  (`--with-conductor` was omitted), execute the corresponding phase below
  directly using `conductor/workflow.md` and `conductor/.templates/track/`;
  missing slash-command files must not block the guided flow. Do not invent a
  second Codex-specific workflow.
- **Resumable.** On start, check for in-progress work and offer to resume from
  memory, not from scratch.
- **The devmode base** is the directory holding `integrations/conductor-beads/`:
  the current one in the base repo, else `~/.devmode/repo`.
- **Continuous between gates.** Don't ask "should I continue?" between mechanical
  steps — execute. Stop only at a gate, when blocked, or when genuinely ambiguous.
- **Score every phase out loud (skill: `self-scorecard`).** At each gate, give a
  one-line overview + an evidence-backed 0–10 score on the five criteria
  (`echo '<json>' | python3 .devmode/scorecard.py`), then refresh the visual
  (`python3 .devmode/dashboard.py .` → `devmode-dashboard.html`). Scores must be
  honest and evidence-backed (an 8+ needs proof you saw this phase). At the end,
  `--final` with per-criterion recommendations. The user tracks the trend in numbers.
- **`/goal` is opt-in, never automatic.** Only when the user explicitly runs
  `/devmode goal <objective>` (or `plan <objective>`) do you produce a ready-to-run
  cross-host `/goal`/`/plan` command via the `goal-brief` skill (it references the
  track spec and is budget-checked ≤3800 by `.devmode/goal_brief.py`). devmode
  must not start `/goal` itself — emit the command for the user to run. Don't wire
  `/goal` into the normal Align→…→Review flow.
- **Guardrails are a hard backstop.** A deterministic `PreToolUse` hook
  (`hooks/guardrails.py`) blocks dangerous ops (sudo, force-push, `--no-verify`,
  writes to `.env`/`.git`/secrets) and asks on destructive git / secret reads.
  Never try to route around it; if it denies something, surface the reason to the
  user rather than retrying. It's the enforcement floor under the skills'
  judgment.

## Startup

0. **New project? (`/devmode start <name> <idea>`)** If invoked in start mode, the
   command has already scaffolded `workspaces/<name>` (base + layer + Beads) and
   git-init'd it. Enter that directory and treat `<idea>` as the goal → Phase 1.
0b. **Existing project? (`/devmode adopt <folder>`)** The command has deployed the
   base+layer into `<folder>`. **The project's `CLAUDE.md` is preserved** — the
   installer left its existing content intact and only appended one pointer line
   (`@CLAUDE.devmode.md`), so devmode composes in via import and the project's own
   instructions stay the host (precedence on conflict). Don't rewrite or merge it
   by default; only inline the import if the user explicitly asks for one flat
   file. Then run the `discovery` skill (Scout → Map → Domain → Synthesize) to
   seed `UBIQUITOUS_LANGUAGE.md` + `DISCOVERY.md` with 🟢/🟡/🔴 tags, and enter the
   ALIGN gate aimed at the 🔴 gaps — confirm the provisional design concept with
   the user before proposing any change.
1. **Ensure the layer + guardrails.** Otherwise, if `conductor/` is missing, run
   `/conductor-setup` (or its canonical command procedure in Codex). If `.beads/`
   is missing, run the doctor and follow its fix-or-explicitly-degrade gate; do
   not initialize Beads silently.
   Also check for the deterministic guardrail hook
   (`.claude/hooks/guardrails.py` wired in `.claude/settings.json`); if absent,
   offer to install it (`install.sh … --with-guardrails`) so the safety gates are
   active for the session.
2. **Prime memory.** `python3 .devmode/memory.py prime` (silent when empty).
   Apply what it says: it is how the user's earlier preferences and decisions
   reach this session.
3. **Resume or new?** Run `bd ready` / read the track `STATE`/notes + `plan.md`.
   - In-progress track → summarize where it stands (design concept + next step)
     and offer to resume.
   - New work → ask the user for the goal in one line, then enter Phase 1.

## The phase machine

For each phase: do the **[auto]** work by delegating, then hit the **[GATE]** —
the only place you pause for the user. Use structured choices at every gate.

### 1. ALIGN  → skill: `grill-me` (+ `confidence-check.md` in `verification-before-completion`)
- **[auto]** Conduct the relentless interview: walk the design tree, classify
  faults (intention/premise/parameter/expression), choose questions by
  information gain.
- **[GATE]** Ask the alignment questions as **structured A/B/C choices** (+ "other")
  with a recommendation each. Reflect the design concept back; iterate until the
  user confirms it. *This is the most important gate — never skip it.*
- Record what the interview settled about the person (how they decide, what they
  refuse) with `memory.py add … --scope global`.
- Exit when: the user confirms the shared design concept. Run the confidence check
  (goal/interface/constraints/verification known?); close any gap here.

### 2. LANGUAGE  → skill: `ubiquitous-language`
- **[auto]** Scan the codebase, draft/update `UBIQUITOUS_LANGUAGE.md` (terms +
  module map). 
- **[GATE]** Show new/ambiguous terms and conflicts for the user to confirm/pick.

### 3. SPECIFY  → skills: `prior-art`, `write-prd`, `design-critique` (its `divergent-ideation.md` first); cmd: `/conductor-newtrack`
- **[auto]** Write `spec.md` with module/interface rigor; create the track + Beads
  epic/tasks; for an open, hard-to-reverse decision run `design-critique`'s
  divergent pass first (widen the candidates), then its multi-lens critique.
  Before writing the spec at all, run `prior-art` on any load-bearing component:
  if it already exists as a product or an OSS project, that changes what the spec says.
- **[GATE]** Present the spec summary + the **trade-offs design-critique surfaced**
  as choices; the user resolves them and approves the spec. Capture resolutions as
  ADRs in `decisions.md`, and each resolved trade-off as a one-line
  `memory.py add … --kind decision`.

### 4. ARCHITECT  → skills: `functional-core-imperative-shell` (+ `system-boundaries.md`), `design-interface-delegate-implementation`, `design-patterns`; agent: `design-architect`
- **[auto]** Design the interfaces (core/shell split, boundaries), mark each module
  gray-box vs critical; draft `plan.md` (phases).
- **[GATE]** Present the interfaces + which modules are critical (full review) vs
  delegable; the user approves or adjusts. Interfaces are the expensive contract —
  confirm before building.

### 5. IMPLEMENT  → cmd: `/conductor-implement`; skills: `tdd` (+ `testing-principles.md`), `feedback-loops`, `subagent-driven-development` (+ `external-cli.md`), `systematic-debugging`, `verification-before-completion`; agent: `tdd-implementer`
- **[auto]** Drive the red→green→refactor loop per `workflow.md`, one behavior at a
  time; run the feedback loops every step; on an unexplained failure switch to
  `systematic-debugging`; update `plan.md`/Beads. **No "continue?" prompts here.**
- **[GATE — phase end]** "Look at it run": present the concrete manual verification
  (commands + expected result) and pause for the user's explicit confirmation
  (highest-value feedback loop).

### 6. REVIEW  → skill: `code-review`; agents: `complexity-reviewer` (+ panel)
- **[auto]** Run the review panel (complexity leads; code-quality, security,
  test-coverage in parallel); act on every finding and **re-verify**; record ADRs.
- **[GATE]** Present the panel verdict + what was fixed; the user okays the merge.
- Apply `verification-before-completion` before claiming done — fresh evidence.

### REFACTOR (as needed)  → skills: `impact-analysis`, `improve-codebase-architecture`; agent: `architecture-refactorer`
- **[auto]** When structure rots, run `impact-analysis` (blast radius) then
  consolidate into deep modules, tests green throughout.
- **[GATE]** For a large blast radius, confirm the approach with the user first.

### Handoff / pause
At a phase boundary, before stopping, or near compaction: write a WARM START
handoff (design concept + position + next step) into Beads notes (`bd update
--notes … && bd sync`) so the next session resumes cold.

## Decision discipline (how to run a gate)

- **Batch** related decisions; don't drip one question at a time.
- **Structured choices**: A/B/C + "other", each with a one-line trade-off, and a
  **recommended** option with why. The user picks; you proceed.
- **Surface trade-offs, don't resolve them silently** — the strategy-level calls
  (design concept, interface shape, trade-off resolution, "done") are the user's.
- **Recommend, don't dictate.** You may have a strong default; state it, but the
  user decides.

## When to stop vs. proceed

- **Stop** only at: a gate, a genuine blocker, or ambiguity that prevents correct
  progress.
- **Proceed** through all mechanical work (tests, the TDD loop, the panel,
  bookkeeping) without checking in.
- If blocked: state the blocker and the options; don't thrash or guess past it.

> You make the 32 skills + 8 agents usable as a single guided experience: the
> front door, not a replacement.
