# The devmode manual — structured development in the AI age

> A practical guide, in English, to using this set of skills and agents
> and building software with AI without falling into the "specs-to-code" trap.

> 🇧🇷 **Versão em português:** [`MANUAL-PT-BR.md`](MANUAL-PT-BR.md).

This manual teaches you **how to use** the process in this folder. If you want to
understand the *why* behind each piece, read [`references/foundations.md`](references/foundations.md).
If something is going wrong and you don't know which skill to reach for, go
straight to [`references/failure-modes.md`](references/failure-modes.md).

---

## 1. The core idea (read this first)

There is a myth that in the AI age **"code is cheap"**: you would just write a
specification, generate the code, and never look at it again. In practice that
fails — you recompile and the code gets *worse* every round. devmode's thesis is
the opposite:

> **Code is not cheap. Bad code is the most expensive thing there is today.**
> A codebase that is hard to change stops the AI from delivering its value.

The division of roles that holds it all together:

- **The AI is the tactics** — an excellent programmer "on the shop floor", fast
  and precise, but **with no strategy**.
- **You are the strategy** — the shared design concept, the module boundaries,
  the interfaces, and the continuous investment in design.

The whole process exists to supply the AI with the strategy it does not have.
**Never let the tactics set the direction.**

---

## 2. The map of the pack

Inside `devmode/` there are four kinds of piece:

| Piece | What it is | Where it lives |
|------|---------|-----------|
| **42 skills** | 21 *process* + 18 *domain* + 3 *meta* (`self-scorecard`, `discovery`, `goal-brief`) | `skills/<name>/SKILL.md` |
| **8 agents** | Subagents that embody the roles in the process (including the review panel) | `.agents/*.md` |
| **2 references** | Theoretical foundations and a diagnostic guide | `references/*.md` |
| **templates + script** | Templates (PRD, glossary) + the pack auditor (`scripts/audit_skills.py`) | `skills/*/assets/`, `scripts/` |

And [`CLAUDE.md`](CLAUDE.md) ties it all together: it is the manifesto + the
workflow table. Several skills were **adapted** from MIT projects — credits in
[`ATTRIBUTION.md`](ATTRIBUTION.md).

### The 21 process skills, grouped by phase

```
1. ALIGN        grill-me ............... shared design concept (+ fault taxonomy, A/B/C options)
2. LANGUAGE     ubiquitous-language .... one vocabulary + module map (+ a why per dependency)
3. SPECIFY      write-prd .............. a PRD explicit about modules and interfaces
                divergent-ideation ..... generate a wide candidate set before choosing
                design-critique ........ review the design/PRD through several lenses before coding
4. ARCHITECT    functional-core-imperative-shell . separate pure logic from I/O (module level)
                architecture-boundaries .......... system boundaries (rules vs. infrastructure)
                design-interface-delegate-impl. .. design the interface, delegate the implementation
                design-patterns .................. GoF patterns — only when they deepen the module
5. IMPLEMENT    confidence-check ....... readiness gate BEFORE coding
                feedback-loops ......... types, compiler, tests, browser + gate ladder
                tdd .................... small test-first steps
                testing-principles ..... what/how/how much to test (+ anti-patterns)
                subagent-driven-dev .... delegate to subagents w/ two-stage review
                delegate-to-cli ........ delegate to an external CLI (gray box)
                systematic-debugging ... root cause before any fix
                verification-before-completion . evidence before saying "done"
                code-review ............ review panel → act on the findings → re-verify
6. REFACTOR     impact-analysis ........ blast radius (who depends on it) before touching
                improve-codebase-architecture .... consolidate shallow modules into deep ones

META            authoring-skills ....... write/audit the skills themselves (scripts/audit_skills.py)
```

### Pairs that support each other

The process has duos designed to reinforce one another:

- **`functional-core-imperative-shell` ↔ `testing-principles`** — the
  architecture (pure core / shell) makes the code easy to test; the principles
  tell you *where* to put the boundary.
- **`functional-core-imperative-shell` ↔ `architecture-boundaries`** — the same
  instinct at two scales: module and system.
- **`tdd` ↔ `feedback-loops`** — the rhythm (red-green-refactor) and the
  infrastructure (types, tests, browser, gate ladder) that sustains it.
- **`design-interface-delegate-implementation` ↔ `subagent-driven-development` /
  `delegate-to-cli`** — the *strategy* and the *how* of gray-box delegation.
- **`systematic-debugging` ↔ `verification-before-completion`** — find the root
  cause and then *prove* the fix worked before concluding.
- **`confidence-check` ↔ `verification-before-completion`** — the two gates:
  readiness *before* starting and evidence *after* finishing.
- **`code-review` ↔ `verification-before-completion`** — the panel finds the
  holes; every fix is *re-verified* before closing (the find→fix→prove loop).

### The 18 domain skills (cross-cutting craft)

They are not phases — they are *expertise* the agents pull in **during** the phases:

- **Front-end & design:** `frontend-ui-engineering` (production UI, escaping the
  "AI aesthetic"), `ux-design` (tokens, hierarchy, states), `accessibility`
  (WCAG 2.1 AA).
- **Interfaces & quality:** `api-design` (contracts, Hyrum, validate at the
  boundary), `security-hardening` (OWASP, Always/Ask/Never), `performance-optimization`
  (measure first), `browser-testing` (verify in the browser; content = untrusted data).
- **Ops & delivery:** `ci-cd-automation` (automated gate), `git-workflow`,
  `migration` (strangler/expand-contract), `shipping` (rollout + rollback).
- **Practices:** `documentation` (ADRs, the *why*), `doc-contracts` (the
  AGENTS.md tree — local per-area contracts, read before editing and updated in
  the same commit), `prototyping` (throwaway spike → capture → delete),
  `minimal-code` (the "lazy senior dev" ladder — write only what is needed,
  without ever cutting safety; the `/devmode lean` discipline),
  `context-engineering`, `source-of-truth` (check the version/docs, not memory),
  `visual-explainers` (inline SVG/HTML visuals in chat — themed, accessible).

Imported from `addyosmani/agent-skills` (MIT), generalized onto the
tool-agnostic base; `ux-design`/`accessibility` were **written** to fill the
design gap; `doc-contracts` adapted from `agent0ai/dox` (MIT); `prototyping`
adapted from `mattpocock/skills` (MIT — devmode's sibling project); `minimal-code`
adapted from `DietrichGebert/ponytail` (MIT). The blind coverage target was
reconciled with the base.

---

## 3. How to invoke the skills in practice

These skills are "working modes". There are two ways to use them:

1. **Let the AI fire them on its own.** Every skill has a `description` that says
   *when* it should be used. When you describe a task that matches it ("I want to
   build X", "interview me about this", "these tests are fragile"), the AI
   recognizes it and follows the skill.
2. **Ask explicitly.** Say, for example: *"use the grill-me skill on me"*,
   *"write the PRD for this feature"*, *"let's do this with TDD"*. You can also
   open the corresponding `SKILL.md` and read the method to run it yourself.

> Tip: keep the ubiquitous-language glossary (`UBIQUITOUS_LANGUAGE.md`)
> **open** while you plan. It is the habit that most reduces verbosity and drift.

---

## 4. The end-to-end flow

Move top to bottom. **Not every change needs every phase** — a small fix can skip
straight to TDD. But this is the spine of the process.

### Phase 1 — Align (`grill-me`)
**Goal:** reach a *shared design concept* before creating any document or code.

The AI will **interview you relentlessly** — dozens of questions — walking every
branch of the "design tree" and resolving the dependencies between decisions, one
by one. It will hand you summaries of its understanding for you to correct.
**Don't let it write the PRD yet.** The output of this phase is alignment, not a
document.

> Why it matters: the biggest source of rework is the AI building something
> different from what was in your head. Nobody knows exactly what they want until
> they are forced to articulate it.

### Phase 2 — Language (`ubiquitous-language`)
**Goal:** a single vocabulary used the same way in conversation, in the AI's
reasoning, and in the code.

The AI scans the codebase, extracts the domain terms, and assembles a
`UBIQUITOUS_LANGUAGE.md` (from the
[`template`](skills/ubiquitous-language/assets/glossary-template.md)). The
**"In code as"** column is what makes the language *ubiquitous*: every term points
to the type/module/function that represents it.

> The glossary is **not only about domain terms**: it also carries the **module
> map** (the deep modules and their public interfaces). You and the AI need to
> know that map well — a module boundary is a domain concept, with a name, a
> responsibility, and a contract. It is that map that lets the PRD be specific
> about *which modules and interfaces change*.

### Phase 3 — Specify (`write-prd`)
**Goal:** turn the aligned concept into a PRD written in the ubiquitous language.

The heart of the PRD is **not** the feature list — it is the section on **module
and interface changes**: signatures, types, real boundaries. This is where you
*invest in the design of the system* (Kent Beck). Use the
[`PRD template`](skills/write-prd/assets/prd-template.md).

### Phase 4 — Architect
**Goal:** define the structure before implementing.

- **`functional-core-imperative-shell`** — separate the *pure decision logic* (the
  core: no I/O, deterministic) from the *thin imperative shell* (reads inputs, calls
  the core, performs the effects). The pattern: **the shell collects → the core
  decides → the shell acts**. That makes the core trivial to test without mocks.
- **`design-interface-delegate-implementation`** — design the interface (the
  "contract") **yourself**, carefully, and **delegate the implementation** to the
  AI as a *gray box*: you verify from the outside, through the tests, without
  reading every line. Exception: **critical** modules (money, authentication,
  security) you review in full.

### Phase 5 — Implement
**Goal:** turn contracts into working, tested code.

- **`feedback-loops`** — make sure they exist and are *fast*: static types,
  compiler/linter, fast automated tests and, for frontend, **access to a real
  browser** so the AI can see the result. *The rate of feedback is your speed
  limit.*
- **`tdd`** — red (write a failing test) → green (make it pass with the minimum)
  → refactor (improve the design with the test protecting you). **One behavior at
  a time.**
- **`testing-principles`** — decide well: test at the **deepest stable
  boundary** (not every private function); **mock only what you don't control**
  (network, clock, disk, third parties); assert **behavior**, not
  implementation.

### Phase 6 — Refactor (`improve-codebase-architecture`)
**Goal:** fight entropy by consolidating **shallow modules** (many small blocks,
a complex interface, leaking internals) into **deep modules** (lots of
functionality behind a simple interface). Do it *before* complexity piles up —
and always with the tests green.

---

## 5. The agents (when to delegate to a subagent)

When a phase is big enough to deserve a context of its own, delegate to the
corresponding agent (in `.agents/`):

| Agent | Role | Use when |
|--------|-------|-----------|
| **`requirements-planner`** | Runs the grill, assembles the ubiquitous language, and writes the PRD | Start of a non-trivial feature |
| **`design-architect`** | Owner of the interfaces, boundaries, and the core/shell split | When deciding *how* to build |
| **`tdd-implementer`** | The tactical programmer: test first, small steps | Implementation behind a fixed contract |
| **`architecture-refactorer`** | Consolidates shallow modules into deep ones | Sprawling codebase / hard to navigate |
| **`complexity-reviewer`** | The entropy guard: reviews the diff for complexity and leads the panel | Before merging |
| **`code-quality-analyzer`** · **`security-scanner`** · **`test-coverage-analyzer`** | Review panel: specialized lanes (quality, security, test gaps) in parallel | After implementing, before the merge |

---

## 6. Quick diagnostic guide

Stuck? Match the symptom to the skill (condensed version of
[`references/failure-modes.md`](references/failure-modes.md)):

| Symptom | Skill |
|---------|-------|
| "The AI didn't do what I wanted" | `grill-me` |
| "The AI is too verbose / drifts from the plan" | `ubiquitous-language` |
| "It built it right, but it doesn't work" | `feedback-loops` + `tdd` |
| "It's broken / the test fails / I don't know why" | `systematic-debugging` |
| "It said it was done, but it wasn't" | `verification-before-completion` |
| "The AI does too much at once" | `tdd` |
| "The tests are fragile/slow/meaningless" | `testing-principles` |
| "Testing requires mocking everything" | `functional-core-imperative-shell` |
| "The AI gets lost in the code / a change breaks distant things" | `improve-codebase-architecture` |
| "What breaks if I touch this? / is it safe to remove?" | `impact-analysis` |
| "I don't know whether I'm ready to start coding" | `confidence-check` |
| "Does this design have holes? / what are we forgetting?" | `design-critique` |
| "Is it ready to merge? / what am I (the author) not seeing?" | `code-review` |
| "A change splashes into unrelated files / logic glued to infrastructure" | `architecture-boundaries` |
| "My brain can't keep up with the volume of code" | `design-interface-delegate-implementation` + `subagent-driven-development` |

> Golden rule of diagnosis: if you are always fighting a *late* symptom, suspect
> an *earlier* unresolved cause. A fragile test (5) is usually, in truth,
> tangled architecture (6/7); "it doesn't work" (3) is usually a lack of
> alignment (1/2).

---

## 7. A full example: renewing a subscription

Let's go from zero to code on a small feature, showing the whole process.

**1) Align (`grill-me`).** The AI interviews you: *"What happens if the card
fails? How many retries? Does it renew on the due date or before? Do you charge
per seat? What happens to a cancelled subscription?"* You answer, it reflects the
concept back, you agree.

**2) Language (`ubiquitous-language`).** It becomes a glossary:

| Term | Definition | In code as | Invariant |
|-------|-----------|-----------|-----------|
| Subscription | Continuous paid access to a plan | `Subscription` | Has exactly one active `Plan` |
| Seat | An assignable licence within the subscription | `Seat` | Is `assigned` or `free`, never both |
| Renewal | A charge that extends the period | `decideRenewal` | Only happens after the due date |

**3) Specify (`write-prd`).** In the interfaces section:
`decideRenewal(sub, currentTime) -> Decision` (pure core), called only by the
shell; `BillingGateway.charge(...)` is I/O and lives in the shell.

**4) Architect (`functional-core-imperative-shell`).** The shell collects → the
core decides → the shell acts:

```js
// CORE (pure): decides what should happen — testable without mocks
function decideRenewal(sub, currentTime) {
  if (sub.status !== "active") return { kind: "noop" }
  if (currentTime <= sub.endsAt) return { kind: "noop" }
  return {
    kind: "renew",
    charge: { customer: sub.customer, amount: sub.plan.price * sub.seats },
    newEndsAt: addMonth(currentTime),
  }
}

// SHELL (imperative): collects inputs, runs the core, performs the decision
function renewSubscription(id) {
  const sub = db.load(id)
  const decision = decideRenewal(sub, now())
  if (decision.kind === "noop") return
  payments.charge(decision.charge.customer, decision.charge.amount)
  db.save({ ...sub, endsAt: decision.newEndsAt })
}
```

**5) Implement (`tdd` + `testing-principles` + `feedback-loops`).** Every edge
case of `decideRenewal` becomes a one-line assertion, **with no mocks** (inactive,
not due yet, due, multiple seats). The shell gets 1–2 integration tests. Types and
tests run in seconds at every step.

**6) Decide the review (`design-interface-delegate-implementation`).** Because it
involves **money**, this module is critical → you review the implementation in
full (it is not a gray box).

**7) Refactor / review.** If the billing logic is scattered, the
`architecture-refactorer` consolidates it; the `complexity-reviewer` checks the
diff before the merge.

---

## 8. Habits and golden rules

- **Align before writing any asset.** The design concept comes first.
- **Keep the glossary open** and use the same terms in conversation, in the PRD,
  in the tests, and in the code.
- **Be specific about interfaces in the PRD** — real signatures and types, not
  "create a service for X".
- **One failing test at a time.** Watch it fail before making it pass. Never
  leave the suite red "for later".
- **Mock only what you don't control.** Mocking your own logic is a sign of a
  wrong boundary → apply core/shell.
- **A gray box only with tests that pin it down.** Without coverage you have not
  yet earned the right to stop reading the module. Critical modules are never
  gray boxes.
- **If a test hurts to write, that is a design signal** — refactor the
  architecture before piling up mocks.
- **Invest in the design every day.** Every change is a chance to improve the
  design, not just to add functionality.
- **You are the strategy; the AI is the tactics.**

---

## 9. Scaling to long work: Conductor-Beads

### `/devmode` modes, score, and dashboard

- **`/devmode start <name> <idea>`** — creates `workspaces/<name>` (base+layer+guardrails+Beads), `git init`, and starts at Phase 1.
- **`/devmode adopt <folder>`** — deploys devmode into an **existing project** and runs **discovery** (the `discovery` skill, reverse-engineering style): it sweeps the code, detects the stack, assembles the **module map** + glossary in `UBIQUITOUS_LANGUAGE.md` and a `DISCOVERY.md` (provisional design concept + architecture), with 🟢/🟡/🔴 tags — and the ALIGN phase attacks the 🔴 ones with you. If the folder already has a `CLAUDE.md`, the existing content stays intact and the installer appends only an idempotent `@CLAUDE.devmode.md` pointer (composition via native import; your instructions remain the host and take precedence). No rewriting; merging into a single file is optional, if you ask for it.
- **`/devmode update <folder>`** / **`/devmode update wiki <folder>`** — **updates** an existing project's *devmode-managed* files to the current base, **without overwriting anything the project owns**. The installer records in `.devmode/managed-files` only the paths it actually wrote; the update uses that manifest, preserves same-name collisions, and keeps the `--no-skills` profile. `.codex/config.toml` is **merged, not replaced**: only the keys devmode declares (marked in the file itself by the `devmode-managed` line) are updated — your keys, tables, and comments stay intact, and a file without that marker never has a value rewritten. The `update wiki` form refreshes `KARPATHY.md` and the how-tos the module owns, preserves the host's README, and appends only the idempotent Codex pointer to `AGENTS.md`; it never touches the knowledge in `wiki/` or `raw/sources/`. Review with `git -C <folder> status`.
- **`/devmode goal <objective>`** (opt-in) — generates a **ready-to-run `/goal` command** (≤3800 chars) that references `spec.md` in detail (step-by-step + tests + acceptance criteria), with the limit **guaranteed by a script** (`.devmode/goal_brief.py`). Use `plan <objective>` for a `/plan` (planning the goal — the `/plan ↔ /goal` recursion). By contract, devmode **does not start `/goal` on its own**; it **hands you the command** to run on each iteration. It is not baked into the normal flow — only when you ask.
- **`/devmode <idea>`** — guides/resumes in the current project.
- **`/devmode c [comment]`** — the **per-turn discipline trigger**: it applies
  devmode's gates to ad-hoc work (ops, debugging, a one-off question) **without**
  spinning up the phase machine. The turn's contract: root cause before any
  change, a backup before a risky operation, and **no "done" without fresh
  end-to-end evidence** (the `Stop` hook blocks the turn if it is missing). It is
  the lighter sibling of `/devmode do <task>`.
- **`/devmode lean <idea>`** / **`/devmode lean goal <objective>`** — runs with the
  **`minimal-code`** discipline (ponytail's "lazy senior dev" ladder) in the
  foreground: write only what the task needs (stdlib/native/one line),
  **without ever cutting** validation, error handling, security, or accessibility.
  The `lean goal` form emits a `/goal` with that directive baked in. (Adapted from
  `DietrichGebert/ponytail`, MIT.)
- **`/devmode do <task>`** — for **a single task** (not a project): it routes the
  sentence to the right skill(s)+agent and runs a short pipeline with evidence
  gates (Understand → Plan → Execute → Verify → Deliver). It is the single-task
  sibling of `/devmode` (whole project) and of `/devmode c` (per-turn gates);
  **every command starts with `/devmode`**, reusing the existing
  skills/agents/gates — no new machinery. (Concept adapted from the `/do` in
  `notque/vexjoy-agent`, MIT.)
- **`/devmode wiki start <path>`** / **`/devmode wiki adopt <folder>`** — deploys
  a **Karpathy LLM Wiki** (the opt-in `integrations/llm-wiki/` module): a
  knowledge base in **pure markdown** (no app, no database, no server) that the LLM
  *maintains* — every source is integrated into a graph of interlinked pages
  (ingest → query → lint over 7 types), so knowledge **accumulates** instead of
  being re-derived on every question. The deployed `KARPATHY.md` is the *schema*
  that makes the agent a disciplined maintainer. It runs **inline** (it is not the
  code phase machine). `start` requires a new/empty folder; `adopt` preserves the
  project's README and installs the how-to in `.llm-wiki/README.md`. `CLAUDE.md`
  and `AGENTS.md` activate the same schema in Claude Code and in Codex. Concept:
  Andrej Karpathy's *LLM Wiki* gist.

In **Codex Desktop** — the only surface where the slash form is **verified** —
invoke the repository skill directly as **`/devmode <args>`**. In CLI/IDE, skills
arrive through the official picker: use `/skills` and select `devmode` (we do not
promise the slash form there while Codex has no official support). The launcher
installed in `.agents/skills/devmode/` reads the same
`.claude/commands/devmode.md` file and adapts only the mechanism to `AGENTS.md`,
`.agents/skills/`, `.codex/agents/`, and `.codex/hooks.json`. The base skills have
a single physical copy in `.claude/skills/`; `.agents/skills/` contains relative
links to it. The Claude configuration stays intact.

> **Warm resume (SessionStart).** With `--with-guardrails`, a
> `session_resume.py` hook injects a short summary at the start of every session
> (last phase, score, active track, next action) read from
> `.devmode/scorecard.json` — read-only, fail-open. That way a new session
> **continues where the loop stopped** instead of starting from scratch (a
> pattern from `notque/claude-code-starter-kit`, MIT).

At **every phase**, the orchestrator shows a **score** (the `self-scorecard` skill): a summary of what was done + a 0–10 mark on 5 criteria (Correctness, Design, Testing, Safety, Clarity) with deltas (`.devmode/scorecard.py`), and it refreshes a **visual dashboard** (`.devmode/dashboard.py` → `devmode-dashboard.html`, no server, no registration). The dashboard carries a **KPI strip**, a **workflow pipeline** (the Align→Refactor phases, reached/current), a **per-phase timeline**, a **sparkline** of the score trend, and a **Gates panel** fed by `.devmode/gates.json` (emitted by a `ci/check.sh`). At the end, `--final` gives **per-criterion recommendations**. The dashboard is **zero-setup,
no server and no registration** — just open `devmode-dashboard.html`.

The 42 skills and 8 agents are the **tool-agnostic base** — they work on their
own. But when the work spans many sessions, devmode lacks a spine for
**orchestration** (tracks, status, dependencies) and for **persistent memory**
(one that survives conversation compaction). That is where the integration comes in:

> **devmode is the base; Conductor is the layer on top; Beads is the optional memory.**

The hierarchy is deliberate — Conductor **serves** the devmode flow, it does not
replace it. Remove Conductor and you still have a complete devmode project;
remove devmode and Conductor becomes a generic spec-first PM. **When the layer's
defaults conflict with the base, the base wins.** The wiring is isolated in
`integrations/conductor-beads/` (the shell), without touching the base skills.

To try it on a real project (the devmode base is installed by default):

```bash
cd integrations/conductor-beads
./install.sh /path/to/the/project --beads-stealth
```

The combined flow: `/conductor-setup` + `bd init` → **`grill-me` before**
`/conductor-newtrack` → a spec with module/interface rigor → `/conductor-implement`
following devmode's `workflow.md` (TDD + FCIS + gray boxes + testing principles,
**without** a blind coverage target) → the handoff stores the *design concept* in
the Beads notes, not just the status. Details:
[`integrations/conductor-beads/INTEGRATION.md`](integrations/conductor-beads/INTEGRATION.md).

> Beads is **optional**: without it the devmode + Conductor flow works just the
> same, only without the persistent graph. Low cost on bd ≥ 1.0: it uses
> **embedded Dolt** by default — `bd init` works with no server (verified on bd
> 1.0.3).

### Guided mode (`/devmode` / the `devmode` skill) — being led through the process

If you don't want to think about *which* skill to use and *when*, use the
orchestrator:

```bash
/devmode "what you want to build"
```

In Codex Desktop, use the same slash command:

```bash
/devmode "what you want to build"
```

The **`devmode-orchestrator`** agent (installed by `install.sh`) drives every
phase — ALIGN → LANGUAGE → SPECIFY → ARCHITECT → IMPLEMENT → REVIEW → REFACTOR —
doing all the mechanical work and **pausing only at your decision gates**, which
it presents as A/B/C choices with a recommendation. The golden rule: you are
**led through the *process*, but you keep deciding the *strategy*** (the design
concept, the trade-offs, approving the interface, saying "done"). It is a *thin
conductor* — it delegates to the deep skills, it never reimplements them.
Details: [`INTEGRATION.md`](integrations/conductor-beads/INTEGRATION.md) →
"Guided mode".

## 10. Going deeper

- [`CLAUDE.md`](CLAUDE.md) — the manifesto and the workflow table.
- [`AGENTS.md`](AGENTS.md) — the Codex adapter that points at the same sources of
  truth as Claude Code.
- [`references/foundations.md`](references/foundations.md) — the principles and
  the reading list (Ousterhout, Brooks, Beck, Evans, Hunt & Thomas, Bernhardt).
- [`references/failure-modes.md`](references/failure-modes.md) — the complete
  symptom → skill diagnostic.
- The `SKILL.md` files themselves in `skills/` — each explains its method and the why.

---

## Author

**Gabriel Sorrentino** — [LinkedIn](https://www.linkedin.com/in/gabriel-sorrentino/)
· [fluencerai.com](https://fluencerai.com) · <gabriel@fluencerai.com>
