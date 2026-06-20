---
description: Guided devmode mode. `start <name> <idea>` scaffolds a new workspaces/<name> project; `adopt <folder>` deploys+discovers an existing one; `goal|plan <objective>` emits a ready-to-run Claude /goal or /plan command; `<idea>`/blank guides or resumes the current project.
argument-hint: start <name> <idea> | adopt <folder> | goal <objective> | <idea> | (blank to resume)
---

# /devmode — guided mode

**On a full `/devmode` invocation — Mode A (`start`), Mode C (`adopt`), Mode D
(`goal`/`plan`), or Mode B (a bare idea / blank resume) — your FIRST action MUST
be to DELEGATE to the `devmode-orchestrator` agent via the Task tool**
(`subagent_type: "devmode-orchestrator"`), briefing it with the current state and
the decision at hand. Do **not** embody the phase machine inline — *spawn the
orchestrator and relay its gate*. The orchestrator does the mechanical work and
pauses only at the human decision gates (easy structured A/B/C choices). The **ONE
exception is `/devmode c`** (Mode C-lite, below): it runs inline with the per-turn
gates and must NOT spin up the orchestrator.

This is **enforced, not advisory** (text alone gets ignored under pressure): the
`devmode_phase_gate.py` **Stop hook BLOCKS** ending a full `/devmode` turn that did
not spawn the orchestrator — override only with `DEVMODE-OK: <reason>` when
delegation genuinely doesn't apply (e.g. a one-line resume). The same hook
**auto-refreshes `devmode-dashboard.html`** from `.devmode/scorecard.json`, so the
dashboard can never go stale (it used to, because nothing forced the refresh).

> ⚠️ **Run `/devmode` from the project directory** (the one with `.devmode/`,
> `conductor/`, `.claude/`). If the session is rooted elsewhere (e.g. the devmode
> base repo), that project's `verify_gate.py`/`guardrails.py` hooks don't load
> (they key off `$CLAUDE_PROJECT_DIR`) and the ops-safety gates go inert.

Raw input: **$ARGUMENTS**

## Decide the mode from $ARGUMENTS

### Mode C-lite — `c [comentário]`  (first token is `c`)  ← CHECK THIS FIRST
The **per-turn discipline trigger**. Use for ops/debug/any ad-hoc work where the
heavy phase machine doesn't fit but the devmode *gates* must still apply. Do **NOT**
spin up the orchestrator, tracks, or phases. Parse everything after `c` as the task.

Apply this **operating contract** to the task this turn (it's why the gate exists —
CLAUDE.md alone gets ignored under pressure; here the gates are re-injected live and
the `Stop` hook `verify_gate.py` *enforces* the last one):

1. **Root cause before any change** (`systematic-debugging`). If something is broken,
   *investigate and state the root cause first*. No fix, rebuild, or config change
   before you can name the cause. Don't guess-and-rebuild.
2. **Risky op → backup first, then plan the check.** Before
   `rebuild`/`docker build`/`deploy`/`.env` changes: back up images + `.env`; never
   `--full`/`--super-power` (wrong-direction sync). Say how you'll verify *before* you act.
3. **No "done" without fresh end-to-end evidence** (`verification-before-completion`).
   Run a real check (a job reaching `completed/`, tests passing, a container log /
   HTTP 200) and *show it*. The `Stop` hook blocks the turn otherwise. If a check
   truly doesn't apply, write `VERIFY-OK: <reason>`.
4. **Honest self-read** — if you slipped on 1–3, say so plainly (`self-scorecard`).

Then do `[comentário]` under that contract. Keep the user *led, not quizzed*.

### Mode A — `start <name> <idea>`  (first token is `start`)
Scaffold a brand-new project under `workspaces/` and begin work in it. Parse the
**second** token as `<name>` (slugify: lowercase, spaces→`-`) and **everything
after** as `<idea>`.

1. **Guard:** confirm you're at the devmode repo root (the dir containing
   `integrations/conductor-beads/install.sh`). If not, tell the user to run it
   from the devmode repo. Refuse if `workspaces/<name>` already exists (suggest a
   new name or `/devmode` to resume).
2. **Scaffold (copy everything in):** run the installer to copy the devmode base
   (CLAUDE.md, 39 skills, 8 agents, references), mount the Conductor layer, drop
   the orchestrator + `/devmode` command, init Beads, and **wire the deterministic
   guardrails hook**:
   ```bash
   integrations/conductor-beads/install.sh "workspaces/<name>" --beads-stealth --with-guardrails
   ```
3. **Make it a working repo:** `git -C "workspaces/<name>" init -q` (Conductor
   commits locally). Announce the new project path.
4. **Begin:** treat `<idea>` as the goal, enter the new project
   (`workspaces/<name>`), and start **Phase 1 (ALIGN)** — the orchestrator's
   `grill-me` interview. From here, follow the orchestrator playbook end to end.

> `workspaces/` is gitignored scratch in the devmode repo — perfect for spinning
> up an isolated project without touching the base. Bring learnings back by hand.

### Mode C — `adopt <folder>`  (first token is `adopt`)
Deploy devmode into an **existing** codebase and discover it (do NOT scaffold a
blank project). Parse everything after `adopt` as `<folder>` (an absolute or
relative path to the target repo).

1. **Guard:** confirm `<folder>` exists and looks like a code repo. If it already
   has `conductor/` + `.claude/`, offer to refresh discovery instead of redeploy.
2. **Deploy the base+layer in place:** run the installer against the existing
   folder (it's idempotent — won't clobber files without `--force`):
   ```bash
   integrations/conductor-beads/install.sh "<folder>" --beads-stealth --with-guardrails
   ```
2b. **Existing `CLAUDE.md` is preserved, not rewritten.** The installer keeps the
   project's `CLAUDE.md` byte-for-byte and only **appends one idempotent pointer**
   — `@CLAUDE.devmode.md` — so the devmode base is composed in via Claude Code's
   native import, while the project's own instructions stay the host (and take
   precedence on conflict). **Default: leave it exactly like that** — don't merge.
   Just confirm to the user that their `CLAUDE.md` is untouched apart from the
   pointer line, and that `CLAUDE.devmode.md` holds the base. *Only if the user
   explicitly wants a single flat file* should you offer to inline the import
   (merge `CLAUDE.devmode.md` in, then drop it). (`/devmode start` writes the
   `CLAUDE.md` directly — no pointer needed.)
3. **Run discovery** (skill: `discovery`) on the codebase — Scout → Map → Domain
   → Synthesize. Produce, with 🟢/🟡/🔴 confidence tags:
   - seed `<folder>/UBIQUITOUS_LANGUAGE.md` (terms + module map),
   - `<folder>/DISCOVERY.md` (purpose, provisional design concept, architecture,
     risks/gaps).
4. **Resolve the gaps:** enter the **ALIGN** gate (`grill-me`) aimed at the 🔴
   gaps discovery surfaced — confirm the provisional design concept with the user
   *before* proposing any change. Discovery proposes; the human confirms.
5. From there, normal guided flow (the user states what they want to build/fix in
   the now-understood codebase).

### Mode D — `goal <objective>`  (first token is `goal`)  ·  also `plan <objective>`
Produce a ready-to-run Claude Code **`/goal`** command (≤3800 chars) that
references a detailed spec — the opt-in bridge to `/goal`/`/plan` (skill:
`goal-brief`). **devmode can't run `/goal` itself; it emits the command for you
to run each iteration.** This mode is **only** triggered by an explicit `goal`/
`plan` token — `/goal` is never wired into the normal flow.

1. **Ensure the objective doc exists** (the brief references it for the detail):
   if no spec covers `<objective>`, create one first — `grill-me` → `write-prd`
   → `/conductor-newtrack`, so `spec.md` carries the **step-by-step + tests +
   acceptance criteria**. Reuse the existing track `spec.md`/`plan.md` when present.
2. **Build + budget-check the brief** (skill: `goal-brief`):
   ```bash
   python3 .devmode/goal_brief.py scaffold conductor/tracks/<id>/spec.md \
     --kind goal --ref conductor/tracks/<id>/spec.md --budget 3800
   ```
   Refine it to reference the file in detail, then guarantee the limit:
   `printf '%s' "<brief>" | python3 .devmode/goal_brief.py check --budget 3800`
   (must say `PASS`). Use `--kind plan` to emit a `/plan` brief instead (plan the
   goal before executing it; the `/plan ↔ /goal` recursion).
3. **Emit the ready-to-run command** to the user (`/goal …` or `/plan …`), note
   it references `spec.md`, and re-emit an updated one whenever they ask (each
   iteration reflects the current spec/plan).

### Mode B — `<idea>` or blank  (no `start`/`adopt`/`goal`/`plan`)
Run/resume in the **current** project (don't scaffold):
- Blank → check `bd ready` + the track `plan.md`/notes; offer to resume from where
  it stands (design concept + next step).
- An idea → treat it as the goal and enter Phase 1 (ALIGN).

## Then drive the phase machine (all modes)

Delegate per phase; do mechanical work autonomously; stop only at gates:
ALIGN (grill-me + confidence-check) → LANGUAGE (ubiquitous-language) →
SPECIFY (write-prd + design-critique, /conductor-newtrack) → ARCHITECT
(FCIS / boundaries / interfaces) → IMPLEMENT (/conductor-implement: tdd,
testing-principles, feedback-loops, systematic-debugging) → REVIEW (code-review
panel) → REFACTOR (impact-analysis → improve-codebase-architecture) as needed.

At every gate: batched, structured A/B/C choices with a recommendation. Honor the
base-wins rules (grill before assets, no blind coverage gate, fresh verification
before "done", critical modules reviewed in full). Hand off warm (design concept
+ position + next step → Beads notes + `bd sync`) before stopping.

**Always show the score (skill: `self-scorecard`).** At each phase gate, give a
one-line overview of what was done and an evidence-backed 0–10 score on the five
criteria, rendered with the tracker so the user sees the trend:
`echo '<json>' | python3 .devmode/scorecard.py`. Then refresh the visual
dashboard: `python3 .devmode/dashboard.py .` (writes `devmode-dashboard.html` —
open it anytime; no server, no registration). At the end, run
`python3 .devmode/scorecard.py --final` with per-criterion **recommendations**.

Keep the user *led*, not quizzed: do the work, ask only what matters.
