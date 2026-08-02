# devmode × Conductor-Beads integration

**devmode is the base; Conductor is the layer on top; Beads is optional memory.**

```
   Beads        ← optional memory behind Conductor (survives compaction)
 ┌──────────┐
 │Conductor │   ← LAYER: organizes and persists the work (tracks, spec/plan, lifecycle)
 ├──────────┤
 │ devmode  │   ← BASE: how to think, design, and test (the source of truth)
 └──────────┘
```

- **devmode** (base) answers *"how to think and design so the AI produces good code"*.
- **Conductor** (layer) answers *"how to organize the work into tracks/spec/plan"*.
- **Beads** (memory) answers *"how to remember everything between sessions"*.

Remove Conductor and you still have a complete devmode project. Remove devmode
and Conductor becomes just a generic spec-first PM. **When the layer's defaults
conflict with the base, the base wins** — and devmode's skills were **not
modified** (they remain the tool-agnostic core). All the wiring lives here, in
the shell.

## What's here

| File | What for |
|---------|----------|
| `INTEGRATION.md` | The **map**: every devmode skill → Conductor phase → Beads action. Read it first. |
| `agents/devmode-orchestrator.md` | The **orchestrator**: drives the whole process phase by phase, pausing only at the decision gates. |
| `commands/devmode.md` | The **`/devmode`** slash command — the front door to guided mode. Includes **`/devmode c [comment]`** (Mode C-lite): a per-turn discipline trigger for ops/debug (root-cause-before-touching, evidence-before-done) without spinning up the phase machine. |
| `hooks/guardrails.py` (+ test) | **Guardrails (gates-as-code)**: a deterministic PreToolUse hook that blocks dangerous operations. Optional (`--with-guardrails`). |
| `hooks/verify_gate.py` | **Verify-gate (gates-as-code)**: a **Stop** hook that **blocks ending the turn** after a rebuild/docker build/deploy/restart/`.env` write with no end-to-end verification after it (override: write `VERIFY-OK: <reason>`). Deterministic enforcement of `verification-before-completion`. Optional (`--with-guardrails`). |
| `hooks/devmode_phase_gate.py` | **Phase-gate (gates-as-code)**: a **Stop** hook that (1) **auto-refreshes `devmode-dashboard.html`** from `.devmode/scorecard.json` (the dashboard can no longer go stale — it used to depend on remembering to run `dashboard.py`); and (2) **blocks ending a full `/devmode` turn** that **did not delegate** to the `devmode-orchestrator` agent (override: `DEVMODE-OK: <reason>`). Robust to the wrong cwd: it finds the project's `.devmode` through the transcript. Deterministic enforcement of the **ceremony** (delegation + dashboard) that prose alone loses under pressure. Optional (`--with-guardrails`). |
| `hooks/codex_hooks.py` | Codex adapter for the same gates: guardrails, verify-gate, phase-gate, and warm resume. It is wired into `.codex/hooks.json` when `--with-guardrails` is used. |
| `install.sh` | Bootstrap: establishes the **devmode base** and mounts the **Conductor layer** in a real project. |
| `templates/CLAUDE.md` | The **project CLAUDE.md**: declares devmode as the base and Conductor as the layer. It is what makes devmode the foundation. |
| `templates/AGENTS.md` + `templates/codex.config.toml` | Project adapters for Codex: durable instructions, skill links in `.agents/skills/`, agents in `.codex/agents/`, and hooks in `.codex/hooks.json`. |
| `templates/workflow.md` | Task-cycle adapter (defers to devmode's skills): TDD + FCIS + gray boxes + testing principles (replaces the ">80% coverage" target). |
| `templates/track/spec.md` | Track spec with `write-prd`'s module/interface rigor. |
| `templates/track/plan.md` | Phased plan (core → shell → critical), annotatable for Beads and parallel execution. |
| `templates/track/learnings.md` | The track's learnings journal (the Ralph flywheel); domain deltas flow back into the ubiquitous language. |
| `templates/product.md`, `tech-stack.md`, `tracks.md`, `patterns.md` | Project context, devmode-aware. |
| `templates/UBIQUITOUS_LANGUAGE.md` | Glossary + **module map** (devmode treats the map as part of the language). |
| `templates/beads.json` | Beads config. |

## How to try it on a real project

By default the installer **establishes the devmode base** (CLAUDE.md + AGENTS.md +
skills + agents + references + ubiquitous language) and then **mounts the
Conductor layer**.

### Option A — base + layer + commands + memory (full)
```bash
cd <devmode-repo>/integrations/conductor-beads
./install.sh /path/to/the/project --with-conductor --beads-stealth
```

### Option B — local devmode base + Conductor layer (no Beads)
```bash
./install.sh /path/to/the/project
```

### Option C — global base (skills not copied) + Conductor layer + memory
```bash
./install.sh /path/to/the/project --no-skills --beads-stealth
```

Flags:

| Flag | Effect |
|------|--------|
| *(default)* | Copies the devmode base once into `.claude/skills`, creates relative links in `.agents/skills` for Codex, and installs `CLAUDE.md`, `AGENTS.md`, and the agent adapters. |
| `--no-skills` | Does **not** copy skills/agents/references (uses a globally installed devmode). The base CLAUDE.md is still written, and future updates preserve this profile. |
| `--with-conductor` | Clones Conductor-Beads and copies its slash commands + the `conductor`/`beads` skills. Skip it if they are already global. |
| `--with-guardrails` | Installs the **four** deterministic hooks (gates-as-code) and wires them into `.claude/settings.json` and `.codex/hooks.json`: **PreToolUse** guardrails (blocks dangerous ops) + **Stop** verify-gate (requires an end-to-end verification after a rebuild/deploy/restart/`.env`) + **Stop** phase-gate (refreshes the dashboard and requires delegation to the orchestrator on a phase-driving `/devmode` turn) + **SessionStart** warm-resume (injects the last phase, score, and active track). |
| `--beads` / `--beads-stealth` | Runs `bd init` (normal / local-only). |
| `--force` | Overwrites files written by this installer. |

The script is **idempotent**: it overwrites nothing without `--force`. If the
project already has a `CLAUDE.md`, the base is written to `CLAUDE.devmode.md` and
the host file only receives the `@CLAUDE.devmode.md` pointer. If it already has
an `AGENTS.md`, the Codex base is written to `AGENTS.devmode.md` and the host
file only receives a textual pointer asking for that adapter to be read. In Codex
Desktop, invoke the repository skill directly as `/devmode <args>`; in CLI/IDE,
use `/skills` and select `devmode`. Both agents see the same files:
`.claude/skills/` holds the single physical copy and `.agents/skills/` contains
only relative links, plus the Codex launcher. Claude Code's existing `/devmode`
stays intact.

The installer records in `.devmode/managed-files` only the assets it actually
wrote. `update.sh` consults that manifest before updating, so a custom skill,
agent, reference, or script with the same name is not overwritten.

## Prerequisites and honest costs

- **Beads is optional.** Without it, the whole devmode + Conductor flow works —
  you only lose the persistent graph and survival across compaction.
  (`enabled:false` in `beads.json`, or simply don't run `bd init`.)
- **Beads CLI:** `npm i -g @beads/bd` (or brew/go). bd ≥ 1.0 uses **embedded Dolt**
  by default — `bd init` works on its own, with no server to bring up. (Only the
  optional `--server` mode needs an external `dolt sql-server`.) Verified on bd
  1.0.3: `bd init --stealth` initialized cleanly, with no separate server.
- The `conductor`/`beads`/`conductor-*` skills may **already exist globally** in
  your environment; in that case, don't use `--with-conductor`.

## The easiest way: guided mode

Claude Code:

```bash
/devmode "what you want to build"
```

Codex:

```bash
/devmode "what you want to build"
```

The **`devmode-orchestrator`** agent drives every phase (ALIGN → LANGUAGE →
SPECIFY → ARCHITECT → IMPLEMENT → REVIEW → REFACTOR), does all the mechanical
work, and **pauses only at your decision gates** (as A/B/C choices with a
recommendation). You are *led through the process*, but you keep deciding the
strategy.

## The combined flow (what the orchestrator does under the hood)

1. `/conductor-setup` + `bd init` → context + memory.
2. **`grill-me` BEFORE** creating the track (align the design concept).
3. `/conductor-newtrack` → `spec.md` with module/interface rigor (`write-prd`).
4. `/conductor-implement` → the TDD loop from `workflow.md` (FCIS, gray boxes,
   testing principles, feedback loops).
5. Phase verification → `feedback-loops` + the `complexity-reviewer` agent.
6. `/conductor-handoff` → Beads stores **the design concept + ubiquitous-language
   deltas**, not just the status.
7. `improve-codebase-architecture` at `refresh`/`archive` to contain entropy.

Full details: [`INTEGRATION.md`](INTEGRATION.md).

---

> **Credits:** the layer mounts the upstream toolkit
> [NguyenSiTrung/Conductor-Beads](https://github.com/NguyenSiTrung/Conductor-Beads)
> (Apache-2.0), cloned at install time with `--with-conductor` — never vendored
> here. ADR / review-panel patterns adapted from `rbarcante/claude-conductor`
> (Apache-2.0). Full map: [`ATTRIBUTION.md`](../../ATTRIBUTION.md).
