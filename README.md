# devmode

> **A development process for the AI age.**
> *"Code is not cheap. Bad code is the most expensive it has ever been."*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Skills](https://img.shields.io/badge/skills-39-blue.svg)
![Agents](https://img.shields.io/badge/agents-8-blue.svg)
![Dependencies](https://img.shields.io/badge/runtime_deps-none-lightgrey.svg)

devmode is a complete, **tool-agnostic software development process** packaged as
39 skills, 8 subagents, deterministic guardrail hooks, a self-scoring system, and
a zero-setup visual dashboard — built for working *with* AI coding agents (Claude
Code and similar) without letting the codebase rot.

🇧🇷 **Português:** o manual completo em PT-BR está em [`manual.md`](manual.md).

---

## Table of contents

- [Why devmode exists](#why-devmode-exists)
- [What's in the box](#whats-in-the-box)
- [Quick start](#quick-start)
- [The workflow (a loop, not a march)](#the-workflow-a-loop-not-a-march)
- [The 39 skills](#the-39-skills)
- [The 8 agents](#the-8-agents)
- [Self-evaluation: scorecard & dashboard](#self-evaluation-scorecard--dashboard)
- [Enforcement: gates that bite](#enforcement-gates-that-bite)
- [The lab: workspaces & the Teamflow case study](#the-lab-workspaces--the-teamflow-case-study)
- [Repository layout](#repository-layout)
- [Foundations & reading list](#foundations--reading-list)
- [Acknowledgments & attribution](#acknowledgments--attribution)
- [License](#license)

---

## Why devmode exists

There's a popular belief that in the AI age **code is cheap** — generate it,
regenerate it, who cares. devmode is built on the opposite thesis: **software
fundamentals matter more now than they ever have.**

AI is an extraordinary *tactical* programmer — a sergeant on the ground who makes
changes faster than any human. But it has no *strategy*. Left alone it optimizes
the change in front of it, ignores the design of the whole, and produces code
that gets worse every iteration (software entropy). The result is the
"specs-to-code" death spiral: run the generator again, get worse code, repeat.

devmode supplies the strategy:

1. **A good codebase is one that is easy to change.** Complexity (Ousterhout) is
   anything that makes a system hard to understand and modify. AI amplifies
   whatever you give it — a clean codebase compounds, a complex one collapses.
2. **No one knows exactly what they want.** The first job is requirements
   gathering: reaching a *shared design concept* (Brooks) before any code exists.
3. **Speak one language.** A ubiquitous language (Evans/DDD) aligns thinking,
   planning, and implementation — verbosity and drift come from a language gap.
4. **The rate of feedback is your speed limit.** Small, deliberate, test-first
   steps beat big bangs. Don't outrun your headlights.
5. **Deep modules over shallow ones.** Lots of functionality behind a simple
   interface. Design the interface yourself; delegate the implementation.
6. **Invest in the design of the system every day** (Beck). Every change is a
   chance to improve the design, not just add a feature.

**You are the strategy. The AI is the tactics. Never let the tactics set the
direction.**

## What's in the box

| Piece | What it is | Where |
|---|---|---|
| **39 skills** | 20 *process* + 16 *domain* + 3 *meta* skills — each a focused, trigger-described practice | [`skills/`](skills/) |
| **8 agents** | Subagent role definitions, including a parallel 4-lane review panel | [`.agents/`](.agents/) |
| **Scripts** | Pack auditor, self-scorecard, HTML dashboard, `/goal` budget checker | [`scripts/`](scripts/) |
| **Guardrail hooks** | Deterministic PreToolUse + Stop gates + a SessionStart warm-resume (Python, stdlib only) | [`integrations/conductor-beads/hooks/`](integrations/conductor-beads/hooks/) |
| **Integration layer** | Conductor (tracks/spec/plan lifecycle) + Beads (persistent memory) mounted *on top of* the base | [`integrations/conductor-beads/`](integrations/conductor-beads/) |
| **References** | The principles behind the process + a failure-mode diagnostic table | [`references/`](references/) |
| **Manifest** | The process spine, beliefs, and usage rules (agent-facing) | [`CLAUDE.md`](CLAUDE.md) |
| **PT-BR manual** | Guia completo de uso em português | [`manual.md`](manual.md) |

Everything is Markdown + Python-stdlib. **No runtime dependencies, no server, no
registration, no build step.**

## Quick start

### A. Use the skills directly (lightest)

Copy (or symlink) `skills/` and `.agents/` into your agent's skill/agent
directories — for Claude Code, `.claude/skills/` and `.claude/agents/` in your
project. The skills are trigger-described: the agent pulls the right one when the
situation matches (e.g. it reaches for `systematic-debugging` when something
breaks, `grill-me` when requirements are vague).

### B. Install into a real project (recommended)

The installer establishes the devmode **base** and optionally mounts the
Conductor **layer** and **guardrails**:

```bash
git clone https://github.com/fluencer-ai/devmode.git && cd devmode
integrations/conductor-beads/install.sh /path/to/your/project --with-guardrails --beads-stealth
```

What you get in the project:

- `CLAUDE.md` (or a non-destructive `@CLAUDE.devmode.md` pointer appended to your
  existing one — your project's rules stay the host and take precedence),
- `.claude/skills/` + `.claude/agents/` (the full pack),
- `conductor/` (product/tech-stack/workflow/tracks + per-track `spec.md`/`plan.md`
  templates), `UBIQUITOUS_LANGUAGE.md`,
- `.devmode/` (scorecard.py, dashboard.py, goal_brief.py) + `devmode-dashboard.html`,
- with `--with-guardrails`: the deterministic hooks wired into `.claude/settings.json`.

Flags: `--no-skills` (rely on a global install) · `--with-conductor` (vendor the
upstream Conductor commands) · `--beads` / `--beads-stealth` (persistent task
memory, committed or local) · `--with-guardrails` · `--force`. Idempotent:
existing files are left alone unless you pass `--force`.

### C. Guided mode — `/devmode` (the front door)

The integration installs a `devmode-orchestrator` agent + `/devmode` command that
drives the whole phase machine for you, pausing only at human decision gates:

```text
/devmode start <name> <idea>   # scaffold a fresh workspaces/<name> project and guide it
/devmode adopt <folder>        # deploy devmode into an EXISTING codebase + run discovery
/devmode goal <objective>      # (opt-in) emit a ready-to-run Claude /goal or /plan command
/devmode <idea>                # guide/resume in the current project
/devmode c [comment]           # ad-hoc ops/debug turn with the gates applied (no phase machine)
```

At every gate it shows a self-scorecard and refreshes `devmode-dashboard.html`.
**Run it from the project directory** — the hooks key off the project root.

### D. One task, routed and gated — `/do`

For a single, well-bounded task (not a whole project), `/do <plain-English>`
**routes** it to the right skill(s)+agent and runs a short evidence-gated pipeline
(Understand → Plan → Execute → Verify → Deliver) — verified, not asserted:

```text
/do debug this failing quota test     # → systematic-debugging (+ tdd for the regression)
/do add a rate limit to /upload       # → security-hardening (control checklist) + tdd
```

`/do` is the single-task sibling of `/devmode` (full project) and `/devmode c`
(bare per-turn gates) — it reuses the existing skills/agents/gates, no new machinery.

## The workflow (a loop, not a march)

Move top to bottom; each phase has skills that do the work. Small changes can
skip straight to TDD — the order is the spine, not a bureaucracy.

| Phase | Skills | What it gives you |
|---|---|---|
| **1. Align** | `grill-me` | A shared design concept, reached by relentless interview *before any asset exists* |
| **2. Language** | `ubiquitous-language` | A glossary + module map shared by you, the AI, and the code |
| **3. Specify** | `write-prd` · `design-critique` | A PRD explicit about which modules/interfaces change, pressure-tested through expert lenses |
| **4. Architect** | `functional-core-imperative-shell` · `architecture-boundaries` · `design-interface-delegate-implementation` · `design-patterns` | Pure logic isolated from I/O; interfaces you design, implementations you delegate |
| **5. Implement** | `confidence-check` · `feedback-loops` · `tdd` · `testing-principles` · `subagent-driven-development` · `delegate-to-cli` · `systematic-debugging` · `verification-before-completion` · `code-review` | Small test-first steps, tight feedback, root-cause discipline, evidence before "done", independent review |
| **6. Refactor** | `impact-analysis` · `improve-codebase-architecture` | Blast radius mapped before changing; shallow modules consolidated into deep ones |

**The spine is a loop.** When a later phase (review, ops, production) invalidates
an earlier decision, go back to the phase that owns it — usually Specify — and
**supersede the ADR** (new decision referencing the old; history kept), re-run
only the affected delta, and record the re-entry as its own scored phase
(`Re-specify`). The dashboard badges these loop-backs (`↩ re-entry`) so they're
visible in the trend, not hidden.

## The 39 skills

Each skill is a `SKILL.md` with a trigger-rich description (when to fire) and a
compact, operational body. The pack is audited by
[`scripts/audit_skills.py`](scripts/audit_skills.py) — frontmatter, name↔folder,
line budgets, link integrity, mirror drift, description-overlap (Jaccard), and
trigger lint.

<details>
<summary><b>Process skills (20)</b> — the spine: how to think and build</summary>

| Skill | One line |
|---|---|
| [`grill-me`](skills/grill-me/SKILL.md) | Relentless requirements interview until a shared design concept exists |
| [`ubiquitous-language`](skills/ubiquitous-language/SKILL.md) | Glossary + module map; boundaries are part of the language |
| [`write-prd`](skills/write-prd/SKILL.md) | PRDs explicit about modules, interfaces, tests, and acceptance criteria |
| [`design-critique`](skills/design-critique/SKILL.md) | Pressure-test a design/PRD through several expert lenses before building |
| [`functional-core-imperative-shell`](skills/functional-core-imperative-shell/SKILL.md) | Pure decisions separated from I/O — the foundation of testability |
| [`architecture-boundaries`](skills/architecture-boundaries/SKILL.md) | Business rules independent of infrastructure, at system scale |
| [`design-interface-delegate-implementation`](skills/design-interface-delegate-implementation/SKILL.md) | Interfaces designed by hand; implementations delegated as verified gray boxes |
| [`design-patterns`](skills/design-patterns/SKILL.md) | GoF patterns chosen by smell/goal — only when they deepen a module |
| [`confidence-check`](skills/confidence-check/SKILL.md) | Pre-flight gate: do I know the goal, interface, constraints, verification? |
| [`feedback-loops`](skills/feedback-loops/SKILL.md) | Types, compiler, fast tests, real runtime — a verification gate ladder |
| [`tdd`](skills/tdd/SKILL.md) | Red → green in small deliberate steps that keep the AI inside its headlights |
| [`testing-principles`](skills/testing-principles/SKILL.md) | Unit size, what to mock, which behaviors to test, adversarial inputs |
| [`subagent-driven-development`](skills/subagent-driven-development/SKILL.md) | Fresh subagent per task + two-stage review — operationalized gray-boxing |
| [`delegate-to-cli`](skills/delegate-to-cli/SKILL.md) | Offload a bounded task to an external model CLI as a verified gray box |
| [`systematic-debugging`](skills/systematic-debugging/SKILL.md) | Root cause first — no fix without investigation |
| [`verification-before-completion`](skills/verification-before-completion/SKILL.md) | No "done" without fresh evidence; a green gate must have *covered the change* |
| [`code-review`](skills/code-review/SKILL.md) | Run the panel, act on every finding, re-verify; adopt the finding, verify the fix |
| [`impact-analysis`](skills/impact-analysis/SKILL.md) | Who depends on this? What breaks? Renames hit tests and substrings |
| [`improve-codebase-architecture`](skills/improve-codebase-architecture/SKILL.md) | Consolidate shallow modules into deep ones — fight entropy |
| [`authoring-skills`](skills/authoring-skills/SKILL.md) | Maintain the pack itself, test-first, audited |

</details>

<details>
<summary><b>Domain skills (16)</b> — cross-cutting craft pulled in during the phases</summary>

| Skill | One line |
|---|---|
| [`frontend-ui-engineering`](skills/frontend-ui-engineering/SKILL.md) | Production UI; escape the "AI aesthetic" |
| [`ux-design`](skills/ux-design/SKILL.md) | Tokens, hierarchy, states |
| [`accessibility`](skills/accessibility/SKILL.md) | WCAG 2.1 AA as a floor, not a feature |
| [`api-design`](skills/api-design/SKILL.md) | Contracts, Hyrum's law, validate at the boundary |
| [`security-hardening`](skills/security-hardening/SKILL.md) | OWASP, Always/Ask/Never tiers, and the **control checklist** (design controls adversarially *before* implementing) |
| [`performance-optimization`](skills/performance-optimization/SKILL.md) | Measure before optimizing |
| [`browser-testing`](skills/browser-testing/SKILL.md) | Verify in a real browser; page content is untrusted data |
| [`ci-cd-automation`](skills/ci-cd-automation/SKILL.md) | The gate ladder as an automated script |
| [`git-workflow`](skills/git-workflow/SKILL.md) | Atomic conventional commits, clean history |
| [`migration`](skills/migration/SKILL.md) | Strangler-fig, expand–contract, delete the zombie |
| [`shipping`](skills/shipping/SKILL.md) | PR-ready ≠ release-ready: checklist, staged rollout, rollback thresholds |
| [`documentation`](skills/documentation/SKILL.md) | ADRs for the *why*; supersede, don't mutate |
| [`doc-contracts`](skills/doc-contracts/SKILL.md) | Hierarchical AGENTS.md tree: local contracts walked before editing, updated in the same commit |
| [`prototyping`](skills/prototyping/SKILL.md) | Throwaway code that answers ONE question — a spike, then captured and deleted (never kept as production) |
| [`context-engineering`](skills/context-engineering/SKILL.md) | Curate the working set; minimal briefs; clean handoffs that survive compaction |
| [`source-of-truth`](skills/source-of-truth/SKILL.md) | Check the installed version and real docs, not training-data memory |

</details>

<details>
<summary><b>Meta skills (3)</b> — self-evaluation and adoption</summary>

| Skill | One line |
|---|---|
| [`self-scorecard`](skills/self-scorecard/SKILL.md) | The agent judges its own work each phase: 0–10 on Correctness, Design, Testing, Safety, Clarity — with deltas and trend |
| [`discovery`](skills/discovery/SKILL.md) | Reverse-engineer an existing codebase into the starting artifacts (🟢 confirmed / 🟡 inferred / 🔴 gap) — the `/devmode adopt` engine |
| [`goal-brief`](skills/goal-brief/SKILL.md) | Turn a spec into a ready-to-run Claude `/goal`/`/plan` command, budget-checked to ≤3800 chars |

</details>

## The 8 agents

| Agent | Role |
|---|---|
| [`design-architect`](.agents/design-architect.md) | The strategist — interfaces, module boundaries, core/shell split |
| [`requirements-planner`](.agents/requirements-planner.md) | Runs the grill, maintains the language, writes the PRD |
| [`tdd-implementer`](.agents/tdd-implementer.md) | The tactical programmer — failing test first, small steps, evidence-gated handoff |
| [`architecture-refactorer`](.agents/architecture-refactorer.md) | Hunts shallow modules, consolidates into deep ones |
| [`complexity-reviewer`](.agents/complexity-reviewer.md) | The entropy guard — leads the review panel |
| [`code-quality-analyzer`](.agents/code-quality-analyzer.md) | Review lane: readability, duplication, naming |
| [`security-scanner`](.agents/security-scanner.md) | Review lane: vulnerabilities, secret leakage, authz, control bypasses |
| [`test-coverage-analyzer`](.agents/test-coverage-analyzer.md) | Review lane: untested behaviors, edges, adversarial inputs |

The last three run **in parallel as fresh subagents** after implementation —
independent eyes that consistently catch what the author cannot see (see the
case study below).

## Self-evaluation: scorecard & dashboard

- **`scripts/scorecard.py`** — the agent records a 0–10 self-judgment on five
  criteria per phase (with a one-line summary and per-criterion notes); history
  lives in `.devmode/scorecard.json`, rendered with deltas and a trend.
- **`scripts/dashboard.py`** — generates a **single self-contained
  `devmode-dashboard.html`** (no server, no registration, no JS build): a KPI
  strip (overall, band, phases, tracks, tasks, ADRs, gates), a **workflow
  pipeline** of the seven phases (reached / current), a **per-phase timeline**
  with score deltas and **loop-back badges**, a score-trend **sparkline**, a
  **deterministic-gates panel** fed by `.devmode/gates.json` (emit it from your
  CI gate script), per-track progress, and carried-forward next actions.

```bash
python3 scripts/dashboard.py /path/to/project    # writes devmode-dashboard.html — just open it
```

## Enforcement: gates that bite

Prose guidance loses to pressure. devmode's non-negotiables are **deterministic
hooks** (Python stdlib, fail-open, with tests), wired by `--with-guardrails`:

| Hook | Event | What it does |
|---|---|---|
| [`guardrails.py`](integrations/conductor-beads/hooks/guardrails.py) | PreToolUse | **Blocks** `sudo`, force-push, `--no-verify`, `rm -rf` at root, writes to `.env`/`.git`/secrets; **asks** on `reset --hard`, scoped `rm -rf`, secret reads |
| [`verify_gate.py`](integrations/conductor-beads/hooks/verify_gate.py) | Stop | Blocks ending a turn after a rebuild/deploy/restart/`.env` change **with no fresh end-to-end check after it** — `verification-before-completion`, enforced |
| [`devmode_phase_gate.py`](integrations/conductor-beads/hooks/devmode_phase_gate.py) | Stop | Enforces the ceremony: auto-refreshes the dashboard from the scorecard and blocks a full `/devmode` turn that bypassed the orchestrator |
| [`session_resume.py`](integrations/conductor-beads/hooks/session_resume.py) | SessionStart | Injects a **warm-resume** hint (last phase, score, active track, next action) from `.devmode/scorecard.json` — read-only, fail-open (a fresh session starts where the loop left off) |

Conscious overrides exist (`VERIFY-OK: <reason>` / `DEVMODE-OK: <reason>`) — the
gates force the *decision* to skip to be explicit, never silent.

## The lab: workspaces & the Teamflow case study

The base stays clean; experiments live in **`workspaces/`** (gitignored scratch).
Copy the base in, run the experiment, **bring back only the learnings**.

The shipped process was battle-tested on **Teamflow**, a SaaS lab project driven
end-to-end through the full workflow — 6 tracks, 67 tests, every skill and agent
exercised. The independent review panel caught real bugs the implementer missed
**in every track**, including: a quota bypass via caller-supplied limits, a
quota-replay via a corrupt *future-dated* period, a CI glob that silently skipped
the new file (green gate, vacuous pass), a rotated key *born revoked*, and an
unauthorized-rotation DoS. Each finding was fixed, re-verified, and **distilled
back into the base skills** — most visibly the
[control checklist](skills/security-hardening/SKILL.md) (the track designed
against it up front survived review with zero findings) and the loop-back
discipline (a requirement change was absorbed by superseding an ADR, not by a
rewrite).

## Repository layout

```text
devmode/
├── CLAUDE.md                    # the manifest: beliefs, workflow table, usage rules
├── README.md                    # you are here
├── manual.md                    # full PT-BR manual
├── ATTRIBUTION.md               # per-artifact third-party credits
├── LICENSE                      # MIT
├── skills/                      # 39 skills (each: SKILL.md + optional assets/)
├── .agents/                     # 8 subagent definitions
├── .claude/                     # mirrors (commands/agents) so /devmode works here too
├── scripts/
│   ├── audit_skills.py          # pack auditor (consistency, links, overlap, budgets)
│   ├── scorecard.py             # per-phase 5-criteria self-scoring + trend
│   ├── dashboard.py             # self-contained HTML dashboard generator
│   └── goal_brief.py            # /goal–/plan brief scaffold + ≤3800-char budget check
├── references/
│   ├── foundations.md           # the principles + reading list
│   └── failure-modes.md         # symptom → skill diagnostic table
├── integrations/
│   └── conductor-beads/         # the layer: installer, hooks, templates, /devmode
└── workspaces/                  # gitignored experiment scratch (never the base)
```

## Foundations & reading list

The process is a synthesis of long-standing fundamentals, applied to AI-assisted
development (full essay: [`references/foundations.md`](references/foundations.md);
diagnostic table: [`references/failure-modes.md`](references/failure-modes.md)):

- *A Philosophy of Software Design* — John Ousterhout (complexity, deep modules)
- *The Pragmatic Programmer* — Hunt & Thomas (entropy, feedback, headlights)
- *The Design of Design* — Frederick P. Brooks (the shared design concept)
- *Domain-Driven Design* — Eric Evans (ubiquitous language)
- Kent Beck (TDD; invest in the design every day)
- Gary Bernhardt — "Boundaries" (functional core, imperative shell)

## Acknowledgments & attribution

devmode's core process is original, but many skills were **adapted** (reframed,
generalized, cross-wired — not copied verbatim) from excellent open-source
projects. Full per-artifact mapping with licenses:
[`ATTRIBUTION.md`](ATTRIBUTION.md). Thank you to all of them:

| Project | What devmode adapted | License |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | systematic-debugging, verification-before-completion, subagent-driven-development, code-review, testing anti-patterns, authoring-skills lineage | MIT |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 12 domain skills (generalized off their web stack) + the a11y checklist | MIT |
| [ryanthedev/code-foundations](https://github.com/ryanthedev/code-foundations) | grill-me's fault taxonomy, design-patterns, architecture-boundaries, the prover/verifier reviewer | MIT |
| [rbarcante/claude-conductor](https://github.com/rbarcante/claude-conductor) | the parallel review-panel lanes, ADR capture, structured-choice grilling | Apache-2.0 |
| [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness) | evidence-gated handoffs, "not observed ≠ absent", guardrail patterns | MIT |
| [saidwafiq/deepflow](https://github.com/saidwafiq/deepflow) | AC↔test traceability, the verify gate ladder | MIT |
| [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit) | delegate-to-cli, skill-judge ideas | MIT |
| [glittercowboy/taches-cc-resources](https://github.com/glittercowboy/taches-cc-resources) | skill-auditing ideas | MIT |
| [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | gate taxonomy, STATE.md memory pattern | MIT (archived) |
| [khendzel/skills-janitor](https://github.com/khendzel/skills-janitor) | description-overlap detection + trigger lint in the auditor | MIT |
| [sandeco/reversa](https://github.com/sandeco/reversa) | the discovery pipeline (Scout/Soul/Detective/Architect, 🟢🟡🔴) | MIT |
| [agent0ai/dox](https://github.com/agent0ai/dox) | the doc-contracts AGENTS.md tree (pre-edit traversal, post-edit pass) | MIT |
| [mattpocock/skills](https://github.com/mattpocock/skills) | **the sibling project** — same thesis & four failure modes; `prototyping` (spike) + the `context-engineering` handoff details | MIT |
| [notque/vexjoy-agent](https://github.com/notque/vexjoy-agent) | the `/do` plain-English task-router (Route→Plan→Execute→Verify→Deliver, evidence over assertions) | MIT |
| [notque/claude-code-starter-kit](https://github.com/notque/claude-code-starter-kit) | the SessionStart warm-resume hook (more lifecycle events; LLM-orchestrates / scripts-execute) | MIT |
| loop-engineering essays — [Osmani](https://addyosmani.com/blog/loop-engineering/), [Autocomplete](https://medium.com/autocomplete-real-world-ai/wtf-is-a-agentic-coding-loop-and-how-to-build-one-58eedb7cbcae), [Greyling](https://cobusgreyling.medium.com/loop-engineering-62926dd6991c) | the maker/checker split, "comprehension debt", worktree isolation reinforcements | (essays) |
| [k-kolomeitsev/data-structure-protocol](https://github.com/k-kolomeitsev/data-structure-protocol) | impact-analysis (reverse edges, why-per-edge) | Apache-2.0 |
| [SuperClaude-Org/SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) | confidence-check, design-critique panels, agent boundary sections | MIT |
| [NguyenSiTrung/Conductor-Beads](https://github.com/NguyenSiTrung/Conductor-Beads) | the upstream Conductor+Beads toolkit (cloned at install time with `--with-conductor`, never vendored here) | Apache-2.0 |
| [cowwoc/cat](https://github.com/cowwoc/cat) | subagent-delegation *concepts* only (no files) | source-available |

devmode and [mattpocock/skills](https://github.com/mattpocock/skills) are
**siblings**: both were distilled from the thesis in Matt Pocock's *"Claude Code
for real engineers"* talk — that AI is a brilliant tactician with no strategy, so
*you* must supply it. devmode generalized that thesis into a tool-agnostic process
(39 skills, agents, enforced gates, scorecard/dashboard) combined with the
reading list above.

## License

[MIT](LICENSE). Adapted skills retain their original attributions in
[`ATTRIBUTION.md`](ATTRIBUTION.md) — if you are an author there and want a
correction, please open an issue.
