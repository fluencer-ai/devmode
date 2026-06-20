# devmode — A development process for the AI age

> "Code is not cheap. Bad code is the most expensive it has ever been."

This directory holds a complete development process built on a single thesis:
**software fundamentals matter more now than they ever have.** AI is an
extraordinary *tactical* programmer — a sergeant on the ground who can make
changes faster than any human. But it has no strategy. Left alone, it produces
code that gets worse every iteration (software entropy), because it optimizes
the change in front of it, not the design of the whole system.

Your job — and the job of this process — is to supply the strategy: a shared
design concept, a shared language, deep and testable modules, and feedback
loops the AI can actually use. Do that, and AI thrives. Skip it, and you get
"specs-to-code" garbage: run the compiler again, get worse code, repeat.

## The core beliefs

1. **A good codebase is one that is easy to change.** Complexity (Ousterhout)
   is anything that makes a system hard to understand and modify. AI amplifies
   whatever you give it — a clean codebase compounds, a complex one collapses.
2. **No one knows exactly what they want.** The first job is requirements
   gathering: reaching a *shared design concept* (Brooks) with the AI before
   any code exists.
3. **Speak one language.** Verbosity and drift come from a language gap.
   A ubiquitous language (DDD) aligns thinking, planning, and implementation.
4. **The rate of feedback is your speed limit.** Don't outrun your headlights.
   Small, deliberate, test-first steps beat big bangs.
5. **Deep modules over shallow ones.** Lots of functionality behind a simple
   interface. Design the interface yourself; delegate the implementation.
6. **Invest in the design of the system every day** (Beck). Every change is a
   chance to improve the design, not just to add a feature.

## The workflow

Move top to bottom. Each step has a skill that does the work. You don't need
every step for every change — small changes can skip straight to TDD — but the
order is the spine of the process.

**The spine is a loop, not a one-way march.** Real projects re-enter it: when a
later phase (Review, or an ops/production signal) *invalidates an earlier
decision*, go back to the phase that owns it — usually **Specify** — and
**supersede the ADR** (write a new decision that references and overrides the old
one; keep the history) rather than patching around it in the shell. Re-run only
the affected phases for the delta. Record the re-entry as its own scored phase
(e.g. `Re-specify`) so the loop-back is visible in the trend, not hidden.

| Phase | Skill | What it gives you |
|-------|-------|-------------------|
| 1. Align | [`grill-me`](skills/grill-me/SKILL.md) | A shared design concept, reached by relentless interview before any asset exists |
| 2. Language | [`ubiquitous-language`](skills/ubiquitous-language/SKILL.md) | A glossary of domain terms shared by you, the AI, and the code |
| 3. Specify | [`write-prd`](skills/write-prd/SKILL.md) | A PRD that is explicit about which modules and interfaces change |
| 3. Specify | [`design-critique`](skills/design-critique/SKILL.md) | Pressure-test the design/PRD through several expert lenses before building |
| 4. Architect | [`functional-core-imperative-shell`](skills/functional-core-imperative-shell/SKILL.md) | A structure where pure logic is isolated from I/O — the foundation for testability |
| 4. Architect | [`architecture-boundaries`](skills/architecture-boundaries/SKILL.md) | System-level boundaries — business rules independent of infrastructure (the FCIS instinct, scaled up) |
| 4. Architect | [`design-interface-delegate-implementation`](skills/design-interface-delegate-implementation/SKILL.md) | Interfaces you design carefully; implementations you delegate and test as gray boxes |
| 4. Architect | [`design-patterns`](skills/design-patterns/SKILL.md) | GoF patterns chosen by smell or goal — used only when they make a module deeper, never as decoration |
| 5. Implement | [`confidence-check`](skills/confidence-check/SKILL.md) | A pre-flight readiness gate — do I know the goal, interface, constraints, and how I'll verify? |
| 5. Implement | [`feedback-loops`](skills/feedback-loops/SKILL.md) | Static types, compiler, fast tests, a real browser/runtime, and a verification gate ladder |
| 5. Implement | [`tdd`](skills/tdd/SKILL.md) | Small, deliberate, test-first steps that keep the AI inside its headlights |
| 5. Implement | [`testing-principles`](skills/testing-principles/SKILL.md) | Good decisions about unit size, what to mock, and which behaviors to test |
| 5. Implement | [`subagent-driven-development`](skills/subagent-driven-development/SKILL.md) | Execute a plan via fresh subagents per task with two-stage review — the *how* of gray-box delegation |
| 5. Implement | [`delegate-to-cli`](skills/delegate-to-cli/SKILL.md) | Offload a bounded task to an external model CLI as a verified gray box |
| 5. Implement | [`systematic-debugging`](skills/systematic-debugging/SKILL.md) | Root-cause-first discipline when anything breaks — no fix without investigation |
| 5. Implement | [`verification-before-completion`](skills/verification-before-completion/SKILL.md) | The gate before any "done" claim — fresh evidence, never confidence |
| 5. Implement | [`code-review`](skills/code-review/SKILL.md) | Run the review panel, act on every finding, re-verify — the author is blind to their own gaps |
| 6. Refactor | [`impact-analysis`](skills/impact-analysis/SKILL.md) | Map the blast radius — who depends on this, what breaks — before you change it |
| 6. Refactor | [`improve-codebase-architecture`](skills/improve-codebase-architecture/SKILL.md) | Shallow modules consolidated into deep ones — fighting entropy |

**Meta & self-evaluation:** [`authoring-skills`](skills/authoring-skills/SKILL.md)
maintains the pack (write skills test-first; `python3 scripts/audit_skills.py`
checks frontmatter, names, links, mirror-drift, and description overlap).
[`self-scorecard`](skills/self-scorecard/SKILL.md) makes the agent judge its own
work each phase — a 0–10 score on five criteria (Correctness, Design, Testing,
Safety, Clarity) tracked with deltas (`scripts/scorecard.py`) and a visual
overview (`scripts/dashboard.py` → a self-contained `devmode-dashboard.html`, no
server/registration: a KPI strip, a workflow pipeline of the phases, a per-phase
timeline, a score-trend sparkline, and a gates panel fed by `.devmode/gates.json`). [`discovery`](skills/discovery/SKILL.md) reverse-engineers
an existing codebase into the starting artifacts (used by `/devmode adopt`).
[`goal-brief`](skills/goal-brief/SKILL.md) turns a spec into a ready-to-run Claude
`/goal` or `/plan` command (≤3800 chars, budget-checked by
`scripts/goal_brief.py`) — opt-in, only via `/devmode goal`. Most skills are
adapted from MIT-licensed sources — see [`ATTRIBUTION.md`](ATTRIBUTION.md).

Several skills are paired on purpose, each supporting the other: a functional
core / imperative shell makes code trivial to test, and testing principles tell
you *where* to put the boundaries it exposes; `architecture-boundaries` is the
same instinct at the system scale that `functional-core-imperative-shell` applies
at the module scale; `design-interface-delegate-implementation` is the *strategy*
that `subagent-driven-development` and `delegate-to-cli` *operationalize*; and
`systematic-debugging` (find the root cause) feeds `verification-before-completion`
(prove the fix worked) before any "done".

## Domain skills

The process skills above are the *spine* (how to think/build, in any domain). The
**domain skills** are cross-cutting expertise the agents pull in *during* the
phases — they don't replace the spine, they fill it with craft for real
development. Reach for them whenever the work touches their area.

- **Front-end & design:** [`frontend-ui-engineering`](skills/frontend-ui-engineering/SKILL.md)
  · [`ux-design`](skills/ux-design/SKILL.md) · [`accessibility`](skills/accessibility/SKILL.md)
- **Interfaces & quality:** [`api-design`](skills/api-design/SKILL.md)
  · [`security-hardening`](skills/security-hardening/SKILL.md)
  · [`performance-optimization`](skills/performance-optimization/SKILL.md)
  · [`browser-testing`](skills/browser-testing/SKILL.md)
- **Ops & delivery:** [`ci-cd-automation`](skills/ci-cd-automation/SKILL.md)
  · [`git-workflow`](skills/git-workflow/SKILL.md) · [`migration`](skills/migration/SKILL.md)
  · [`shipping`](skills/shipping/SKILL.md)
- **Practices:** [`documentation`](skills/documentation/SKILL.md)
  · [`doc-contracts`](skills/doc-contracts/SKILL.md)
  · [`prototyping`](skills/prototyping/SKILL.md)
  · [`context-engineering`](skills/context-engineering/SKILL.md)
  · [`source-of-truth`](skills/source-of-truth/SKILL.md)

Most are adapted from `addyosmani/agent-skills` (MIT), generalized off their web
stack to fit the tool-agnostic base; `ux-design` and `accessibility` are authored
to fill the design gap those packs leave. See [`ATTRIBUTION.md`](ATTRIBUTION.md).

## The agents

`.agents/` holds subagent definitions that embody the roles in this process.
Delegate to them when a phase is large enough to deserve a focused context:

- **`design-architect`** — the strategist. Owns interfaces, module boundaries,
  and the functional-core/imperative-shell split.
- **`requirements-planner`** — runs the grill, maintains the ubiquitous
  language, and writes the PRD.
- **`tdd-implementer`** — the tactical programmer. Writes failing tests first,
  takes small steps, keeps feedback loops tight.
- **`architecture-refactorer`** — hunts shallow modules and consolidates them
  into deep ones with simple interfaces.
- **`complexity-reviewer`** — the entropy guard. Reviews diffs for anything
  that makes the system harder to understand or change, and leads the review panel.
- **`code-quality-analyzer`**, **`security-scanner`**, **`test-coverage-analyzer`**
  — the review panel: specialized read-only lanes (code quality, security
  vulnerabilities, test gaps) dispatched in parallel after implementation.

## How to use this in practice

- Keep the ubiquitous language file open while planning. Reference its terms
  in the PRD, in tests, and in conversation with the AI.
- Design interfaces by hand or with the `design-architect`. You may leave
  *implementations* of non-critical deep modules largely to the AI — but only
  because the interface and tests pin the behavior from the outside.
- When something doesn't work, fix the design, not just the symptom. Reach for
  `improve-codebase-architecture` before complexity compounds.
- You are the strategy. The AI is the tactics. Never let the tactics set the
  direction.

## Background and diagnostics

- [`references/foundations.md`](references/foundations.md) — the principles
  behind the whole process (complexity, entropy, the design concept, ubiquitous
  language, functional core/shell, the strategy/tactics split) and the reading
  list they come from. Read this to understand *why* the skills are shaped this
  way.
- [`references/failure-modes.md`](references/failure-modes.md) — a diagnostic
  table mapping the concrete ways AI-assisted development goes wrong to the skill
  that fixes each one. Start here when something is going wrong and you're not
  sure which skill to reach for.

## Integrations

The skills above are the **tool-agnostic base**. When a project needs execution
orchestration and memory that survives across sessions, mount a layer on top of
that base — the base stays the source of truth:

- [`integrations/conductor-beads/`](integrations/conductor-beads/README.md) —
  **devmode is the base; Conductor is a layer; Beads is optional memory.**
  Conductor (tracks, spec/plan, lifecycle) organizes and persists the devmode
  flow; Beads (a dependency graph + notes that survive conversation compaction)
  backs it. Remove the layer and you still have a complete devmode project. When
  the layer's defaults conflict with the base, the base wins (e.g. no blind
  coverage gate; grill before creating a track). Run
  `integrations/conductor-beads/install.sh <project>` to establish the base and
  mount the layer in a real project; see
  [`INTEGRATION.md`](integrations/conductor-beads/INTEGRATION.md) for the
  skill-by-phase map. The layer also installs a **guided front door** — the
  `devmode-orchestrator` agent invoked via the `/devmode` command — which drives
  the whole phase machine for you and pauses only at human decision gates (it
  carries the *process*; you still make the *decisions*, made easy). Three modes:
  `/devmode start <name> <idea>` scaffolds a new `workspaces/<name>` project;
  `/devmode adopt <folder>` deploys devmode into an *existing* codebase and runs
  `discovery` on it; `/devmode goal <objective>` (opt-in) emits a ready-to-run
  Claude `/goal`/`/plan` command referencing the spec; `/devmode [idea]`
  guides/resumes in the current project. It shows a `self-scorecard` at every gate
  and refreshes `devmode-dashboard.html` (the zero-setup, no-server visualization).
  For ad-hoc ops/debug, **`/devmode c [comment]`** applies the gates *per-turn*
  (root-cause-first, evidence-before-done) without spinning up the phase machine —
  the cheap trigger for "don't abandon the discipline when things break". For a
  single bounded task, **`/devmode do <task>`** routes it to the right
  skill(s)+agent and runs a short evidence-gated pipeline — the single-task sibling
  (every entry point starts with `/devmode`).
- **Enforcement, not advice (the gates bite).** `--with-guardrails` wires the
  deterministic hooks into `.claude/settings.json`: a **PreToolUse guardrail**
  (`guardrails.py`, blocks dangerous ops); a **Stop `verify_gate.py`** that
  *blocks ending a turn* after a rebuild / `docker build` / deploy / restart / `.env`
  change with no fresh end-to-end check after it — making
  [`verification-before-completion`](skills/verification-before-completion/SKILL.md)
  enforced rather than advisory; and a **Stop `devmode_phase_gate.py`** that
  enforces the *ceremony* (the part most easily skipped under pressure): it
  **auto-refreshes `devmode-dashboard.html`** from `.devmode/scorecard.json` (so the
  dashboard can't go stale) and **blocks ending a full `/devmode` turn that did not
  delegate to the `devmode-orchestrator` agent** (embodying the phase machine inline
  is the failure mode this catches). It also wires a **SessionStart
  `session_resume.py`** that injects a warm-resume hint (last phase, score, active
  track, next action) so a fresh session picks up where the loop left off
  (read-only, fail-open). Conscious overrides: `VERIFY-OK: <reason>` /
  `DEVMODE-OK: <reason>` when a check genuinely doesn't apply. (CLAUDE.md text alone
  loses to pressure — that's *why* these are hooks, not prose.) **Run `/devmode`
  from the project dir**: hooks key off `$CLAUDE_PROJECT_DIR`, so a session rooted in
  the base repo leaves the *project's* guardrail/verify gates inert — the base repo
  now ships its own `.claude/settings.json` wiring the phase-gate so the ceremony
  still bites from here.

## Workspaces — experiment without touching the base

**This folder is the base. We reuse it across other projects, so it must stay
clean.** Never run experiments, smoke tests, or throwaway features directly in
the base — that risks polluting the very thing other projects depend on.

Instead, work in [`workspaces/`](workspaces/README.md):

1. **Copy the base into a workspace.** The fastest way is the installer, which
   copies the devmode base (CLAUDE.md, skills, agents, references) and mounts the
   Conductor layer into a fresh directory:
   `integrations/conductor-beads/install.sh workspaces/<experiment-name>`.
   (Or copy the whole folder by hand — just exclude `workspaces/` itself.)
2. **Do all the work inside that workspace.** Build features, run tests, try
   changes. The workspace is disposable scratch space.
3. **Bring back only the learnings.** When something proves out, port the
   *learning* — a sharpened skill, a fixed template, a new pattern — back into the
   base by hand. Never copy a whole experiment back wholesale.

`workspaces/` is **gitignored** (scratch is never committed). Treat anything in
it as throwaway; the source of truth always lives in the base files above.
