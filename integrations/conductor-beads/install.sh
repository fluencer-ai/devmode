#!/usr/bin/env bash
#
# devmode × Conductor-Beads bootstrapper.
#
# Architecture: devmode is the BASE; Conductor is a LAYER on top; Beads is
# optional memory behind Conductor. The installer establishes the base first,
# then mounts the layer.
#
# What it sets up in a real project:
#   BASE (devmode):  CLAUDE.md (base declaration), .claude/skills + agents,
#                    references, UBIQUITOUS_LANGUAGE.md
#   LAYER (conductor): conductor/ context + per-track templates + workflow adapter
#   MEMORY (beads):  optional `bd init`
#
# Idempotent: existing files are left alone unless you pass --force.
#
# Usage:
#   ./install.sh <project-dir> [options]
#
# Options:
#   --no-skills          Don't copy devmode skills/agents/references (rely on a
#                        global devmode install). The base CLAUDE.md is still written.
#   --with-conductor     Clone upstream Conductor-Beads and copy its slash commands
#                        + conductor/beads skills (skip if installed globally).
#   --with-guardrails    Install the deterministic PreToolUse guardrail hook and
#                        wire it into .claude/settings.json (gates-as-code).
#   --beads              Run `bd init` (commits .beads/ to the repo).
#   --beads-stealth      Run `bd init --stealth` (.beads/ stays local/gitignored).
#   --force              Overwrite existing files written by this installer.
#   -h, --help           Show this help.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/templates"
DEVMODE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONDUCTOR_BEADS_REPO="https://github.com/NguyenSiTrung/Conductor-Beads.git"

# --- pretty output -----------------------------------------------------------
c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_dim=$'\033[2m'; c_off=$'\033[0m'
info()  { printf "%s•%s %s\n" "$c_blue" "$c_off" "$*"; }
ok()    { printf "%s✓%s %s\n" "$c_green" "$c_off" "$*"; }
warn()  { printf "%s!%s %s\n" "$c_yellow" "$c_off" "$*"; }
err()   { printf "%s✗%s %s\n" "$c_red" "$c_off" "$*" >&2; }
step()  { printf "\n%s== %s ==%s\n" "$c_blue" "$*" "$c_off"; }

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# --- parse args --------------------------------------------------------------
PROJECT_DIR=""
WITH_SKILLS=1; WITH_CONDUCTOR=0; BEADS=0; BEADS_STEALTH=0; FORCE=0; GUARDRAILS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --no-skills)      WITH_SKILLS=0 ;;
    --with-conductor) WITH_CONDUCTOR=1 ;;
    --with-guardrails) GUARDRAILS=1 ;;
    --beads)          BEADS=1 ;;
    --beads-stealth)  BEADS_STEALTH=1 ;;
    --force)          FORCE=1 ;;
    -h|--help)        usage 0 ;;
    -*)               err "unknown option: $1"; usage 1 ;;
    *)                if [ -z "$PROJECT_DIR" ]; then PROJECT_DIR="$1"; else err "unexpected arg: $1"; usage 1; fi ;;
  esac
  shift
done

[ -n "$PROJECT_DIR" ] || { err "missing <project-dir>"; usage 1; }
mkdir -p "$PROJECT_DIR"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

info "devmode base:   $DEVMODE_ROOT"
info "project target: $PROJECT_DIR"
[ -d "$PROJECT_DIR/.git" ] || warn "target is not a git repo — Conductor commits locally; consider 'git init'."

# Preflight: every enforcing part of devmode is Python — all five hooks, the
# scorecard, the dashboard, the doctors. Without python3 they install but can
# never run, and the gates would be inert while the output claimed otherwise.
# Say it once, loudly, up front rather than emitting a warning nobody reads.
HAVE_PY3=0
if command -v python3 >/dev/null 2>&1; then
  HAVE_PY3=1
else
  err "python3 NOT FOUND — devmode's enforcement layer cannot run."
  err "  the hooks (guardrails / verify-gate / phase-gate / session-resume),"
  err "  the scorecard, the dashboard and the doctors are all Python."
  err "  Install python3, then re-run this installer (it is idempotent)."
  warn "Continuing: the markdown base (skills, agents, references) still works;"
  warn "the deterministic gates will NOT be wired."
fi

# helper: copy a file only if absent (or --force)
copy_template() {
  local src="$1" dst="$2"
  if [ -e "$dst" ] && [ "$FORCE" -eq 0 ]; then
    warn "skip (exists): ${dst#"$PROJECT_DIR"/}  ${c_dim}(use --force to overwrite)${c_off}"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    ok "wrote ${dst#"$PROJECT_DIR"/}"
  fi
}

# =============================================================================
# 1. BASE — devmode (the foundation: how we think, design, and test)
# =============================================================================
step "Establishing the devmode base"

# 1a. Project CLAUDE.md — declares devmode-as-base, Conductor-as-layer.
CLAUDE_DST="$PROJECT_DIR/CLAUDE.md"
if [ -e "$CLAUDE_DST" ] && [ "$FORCE" -eq 0 ]; then
  copy_template "$TEMPLATES_DIR/CLAUDE.md" "$PROJECT_DIR/CLAUDE.devmode.md"
  # Non-destructive: leave the project's CLAUDE.md untouched except for one idempotent
  # pointer import. Composition over rewriting — your instructions stay the host.
  if grep -q "@CLAUDE.devmode.md" "$CLAUDE_DST" 2>/dev/null; then
    ok "project CLAUDE.md already imports @CLAUDE.devmode.md (left untouched)"
  else
    printf '\n<!-- devmode: base process; project instructions above take precedence -->\n@CLAUDE.devmode.md\n' >> "$CLAUDE_DST"
    ok "kept your CLAUDE.md; appended one pointer line → @CLAUDE.devmode.md (non-destructive)"
  fi
else
  copy_template "$TEMPLATES_DIR/CLAUDE.md" "$CLAUDE_DST"
fi

# 1b. Ubiquitous language (a devmode artifact) lives at the repo root.
copy_template "$TEMPLATES_DIR/UBIQUITOUS_LANGUAGE.md" "$PROJECT_DIR/UBIQUITOUS_LANGUAGE.md"

# 1b2. devmode tooling the project runs itself: scorecard + dashboard (→ .devmode/)
mkdir -p "$PROJECT_DIR/.devmode"
cp "$DEVMODE_ROOT/scripts/scorecard.py" "$DEVMODE_ROOT/scripts/dashboard.py" \
   "$DEVMODE_ROOT/scripts/goal_brief.py" "$DEVMODE_ROOT/scripts/beads_doctor.py" \
   "$PROJECT_DIR/.devmode/" 2>/dev/null \
  && ok "copied scorecard.py + dashboard.py + goal_brief.py + beads_doctor.py → .devmode/" || warn "devmode scripts not found in base"

# 1c. devmode skills + agents + references (the base process itself).
if [ "$WITH_SKILLS" -eq 1 ]; then
  mkdir -p "$PROJECT_DIR/.claude/skills" "$PROJECT_DIR/.claude/agents" "$PROJECT_DIR/.claude/devmode/references"
  cp -R "$DEVMODE_ROOT/skills/." "$PROJECT_DIR/.claude/skills/"
  ok "copied $(find "$DEVMODE_ROOT/skills" -name SKILL.md | wc -l | tr -d ' ') devmode skills → .claude/skills/"
  # The agents are load-bearing (review panel + orchestrator). A silent copy
  # failure would leave a project that looks installed but can delegate nothing.
  if cp "$DEVMODE_ROOT"/.agents/*.md "$PROJECT_DIR/.claude/agents/" 2>/dev/null; then
    ok "copied $(find "$PROJECT_DIR/.claude/agents" -name '*.md' | wc -l | tr -d ' ') agents → .claude/agents/"
  else
    err "FAILED to copy agents from $DEVMODE_ROOT/.agents — the review panel and"
    err "  the devmode-orchestrator will not exist in this project. Fix and re-run."
  fi
  if cp "$DEVMODE_ROOT"/references/*.md "$PROJECT_DIR/.claude/devmode/references/" 2>/dev/null; then
    ok "copied references → .claude/devmode/references/"
  else
    warn "no references copied (foundations/failure-modes) — background docs only."
  fi
else
  info "skipping skill copy (--no-skills): relying on a global devmode install"
fi

# =============================================================================
# 2. LAYER — Conductor (organizes & persists the devmode flow)
# =============================================================================
step "Mounting the Conductor layer"
mkdir -p "$PROJECT_DIR/conductor/tracks" "$PROJECT_DIR/conductor/archive"
copy_template "$TEMPLATES_DIR/product.md"    "$PROJECT_DIR/conductor/product.md"
copy_template "$TEMPLATES_DIR/tech-stack.md" "$PROJECT_DIR/conductor/tech-stack.md"
copy_template "$TEMPLATES_DIR/workflow.md"   "$PROJECT_DIR/conductor/workflow.md"
copy_template "$TEMPLATES_DIR/tracks.md"     "$PROJECT_DIR/conductor/tracks.md"
copy_template "$TEMPLATES_DIR/patterns.md"   "$PROJECT_DIR/conductor/patterns.md"
copy_template "$TEMPLATES_DIR/beads.json"    "$PROJECT_DIR/conductor/beads.json"
# Per-track templates the agent copies on /conductor-newtrack
copy_template "$TEMPLATES_DIR/track/spec.md"      "$PROJECT_DIR/conductor/.templates/track/spec.md"
copy_template "$TEMPLATES_DIR/track/plan.md"      "$PROJECT_DIR/conductor/.templates/track/plan.md"
copy_template "$TEMPLATES_DIR/track/learnings.md" "$PROJECT_DIR/conductor/.templates/track/learnings.md"
copy_template "$TEMPLATES_DIR/track/decisions.md" "$PROJECT_DIR/conductor/.templates/track/decisions.md"
# The integration map, so the in-project agent knows how base + layer fit
copy_template "$SCRIPT_DIR/INTEGRATION.md"   "$PROJECT_DIR/conductor/INTEGRATION.md"

# The guided front door: /devmode command (incl. its `do` task-router mode) + the orchestrator agent
mkdir -p "$PROJECT_DIR/.claude/agents" "$PROJECT_DIR/.claude/commands"
copy_template "$SCRIPT_DIR/agents/devmode-orchestrator.md" "$PROJECT_DIR/.claude/agents/devmode-orchestrator.md"
copy_template "$SCRIPT_DIR/commands/devmode.md"            "$PROJECT_DIR/.claude/commands/devmode.md"

# 2b. Conductor-Beads commands/skills (optional — skip if global)
if [ "$WITH_CONDUCTOR" -eq 1 ]; then
  step "Fetching Conductor-Beads commands + skills"
  tmp="$(mktemp -d)"
  if git clone --depth 1 "$CONDUCTOR_BEADS_REPO" "$tmp/cb" >/dev/null 2>&1; then
    mkdir -p "$PROJECT_DIR/.claude/commands" "$PROJECT_DIR/.claude/skills"
    cp -R "$tmp/cb/.claude/commands/." "$PROJECT_DIR/.claude/commands/" 2>/dev/null || true
    cp -R "$tmp/cb/.claude/skills/conductor" "$PROJECT_DIR/.claude/skills/" 2>/dev/null || true
    cp -R "$tmp/cb/.claude/skills/beads"     "$PROJECT_DIR/.claude/skills/" 2>/dev/null || true
    ok "copied Conductor commands + conductor/beads skills"
    warn "keep OUR conductor/workflow.md (the devmode-base adapter), not upstream's."
  else
    err "clone failed (offline?). Install Conductor-Beads manually, or use global skills."
  fi
  rm -rf "$tmp"
else
  info "skipping Conductor-Beads copy (use --with-conductor, or rely on global install)"
fi

# 2c. Guardrails — deterministic PreToolUse enforcement hook (optional)
if [ "$GUARDRAILS" -eq 1 ] && [ "$HAVE_PY3" -eq 0 ]; then
  step "Installing guardrails (gates-as-code)"
  err "--with-guardrails requested but python3 is missing: the hooks would be"
  err "  wired to an interpreter that isn't there, so every gate would be inert."
  err "  NOT wiring them. Install python3 and re-run to get the gates."
elif [ "$GUARDRAILS" -eq 1 ]; then
  step "Installing guardrails (gates-as-code)"
  mkdir -p "$PROJECT_DIR/.claude/hooks"
  copy_template "$SCRIPT_DIR/hooks/guardrails.py"      "$PROJECT_DIR/.claude/hooks/guardrails.py"
  copy_template "$SCRIPT_DIR/hooks/test_guardrails.py" "$PROJECT_DIR/.claude/hooks/test_guardrails.py"
  copy_template "$SCRIPT_DIR/hooks/verify_gate.py"     "$PROJECT_DIR/.claude/hooks/verify_gate.py"
  copy_template "$SCRIPT_DIR/hooks/devmode_phase_gate.py" "$PROJECT_DIR/.claude/hooks/devmode_phase_gate.py"
  copy_template "$SCRIPT_DIR/hooks/session_resume.py"  "$PROJECT_DIR/.claude/hooks/session_resume.py"
  # Idempotently merge the PreToolUse guardrail + Stop verify/phase gates + the SessionStart warm-resume into settings.json
  WIRED=0
  python3 - "$PROJECT_DIR/.claude/settings.json" <<'PY' && WIRED=1 || WIRED=0
import json, os, sys
path = sys.argv[1]
pre_cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guardrails.py"'
stop_cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/verify_gate.py"'
phase_cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/devmode_phase_gate.py"'
session_cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/session_resume.py"'
data = {}
if os.path.isfile(path):
    try: data = json.load(open(path))
    except Exception: data = {}
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
if not any(h.get("command") == pre_cmd for g in pre for h in g.get("hooks", [])):
    pre.append({"matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit",
                "hooks": [{"type": "command", "command": pre_cmd}]})
stop = hooks.setdefault("Stop", [])
for cmd in (stop_cmd, phase_cmd):
    if not any(h.get("command") == cmd for g in stop for h in g.get("hooks", [])):
        stop.append({"hooks": [{"type": "command", "command": cmd}]})
start = hooks.setdefault("SessionStart", [])
if not any(h.get("command") == session_cmd for g in start for h in g.get("hooks", [])):
    start.append({"hooks": [{"type": "command", "command": session_cmd}]})
json.dump(data, open(path, "w"), indent=2)
PY
  # Prove the wiring landed instead of announcing gates that may not exist.
  if [ "$WIRED" -eq 1 ] && python3 - "$PROJECT_DIR/.claude/settings.json" <<'VERIFY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    sys.exit(1)
h = d.get("hooks", {})
found = {c.get("command", "") for ev in h.values() for g in ev for c in g.get("hooks", [])}
need = ("guardrails.py", "verify_gate.py", "devmode_phase_gate.py", "session_resume.py")
sys.exit(0 if all(any(n in f for f in found) for n in need) else 1)
VERIFY
  then
    ok "wired + verified in .claude/settings.json: PreToolUse guardrail, Stop verify/phase gates, SessionStart resume"
    warn "guardrails block: sudo, force-push, --no-verify, rm -rf /, writes to .env/.git/secrets; ask: reset --hard, scoped rm -rf, reading secrets."
    warn "verify-gate (Stop): blocks ending a turn after rebuild/docker build/deploy/.env without a fresh end-to-end check (override: write 'VERIFY-OK: <reason>')."
    warn "phase-gate (Stop): auto-refreshes devmode-dashboard.html from .devmode/scorecard.json, and blocks ending a full /devmode turn that did NOT delegate to the devmode-orchestrator agent (override: write 'DEVMODE-OK: <reason>')."
    warn "session-resume (SessionStart): injects a warm-resume hint (last phase, score, active track, next action) from .devmode/scorecard.json — read-only, fail-open."
  else
    err "settings.json wiring FAILED or is incomplete — the gates are NOT active."
    err "  Fix it by hand (.claude/settings.json) or re-run; do not assume the gates bite."
  fi
else
  info "skipping guardrails (use --with-guardrails to enable deterministic enforcement)"
fi

# =============================================================================
# 3. MEMORY — Beads (optional)
# =============================================================================
if [ "$BEADS" -eq 1 ] || [ "$BEADS_STEALTH" -eq 1 ]; then
  step "Initializing Beads (memory layer)"
  if command -v bd >/dev/null 2>&1; then
    ( cd "$PROJECT_DIR"
      if [ "$BEADS_STEALTH" -eq 1 ]; then bd init --stealth; else bd init; fi
    ) && ok "Beads initialized" || warn "bd init returned non-zero — check Dolt server (bd dolt start) on v0.56+"
  else
    err "'bd' not found on PATH — the memory layer will NOT work."
    err "Install:  brew install beads   (or: npm i -g @beads/bd), then: bd init --stealth"
  fi

  # Prove it, don't assume it. A silent Beads failure is the expensive one: the
  # install still "succeeds", beads.json keeps claiming enabled:true, and the
  # session falls back to the agent's own context — discovered only much later,
  # when a handoff that was supposed to be durable turns out never to exist.
  if command -v python3 >/dev/null 2>&1 && [ -f "$PROJECT_DIR/.devmode/beads_doctor.py" ]; then
    if python3 "$PROJECT_DIR/.devmode/beads_doctor.py" "$PROJECT_DIR"; then
      BEADS_LIVE=1
    else
      BEADS_LIVE=0
      # Make the state on disk honest, so nothing downstream trusts a dead layer.
      python3 - "$PROJECT_DIR/conductor/beads.json" <<'PY' || true
import json, sys, os
p = sys.argv[1]
if os.path.isfile(p):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        sys.exit(0)
    if d.get("enabled") is True:
        d["enabled"] = False
        d.setdefault("_devmode", {})["disabled_reason"] = (
            "beads_doctor found the memory layer not live at install time; set back "
            "to true once `python3 .devmode/beads_doctor.py .` passes.")
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
        print("  ! conductor/beads.json set enabled:false so it matches reality")
PY
      warn "Continuing WITHOUT durable memory. Re-run the doctor after installing bd:"
      warn "  python3 .devmode/beads_doctor.py ."
    fi
  fi
else
  info "skipping bd init (use --beads or --beads-stealth; or run it later)"
  info "memory check on demand:  python3 .devmode/beads_doctor.py ."
fi

# =============================================================================
# 4. VISUALIZATION — native dashboard (no server, no registration)
# =============================================================================
step "Generating the dashboard"
if command -v python3 >/dev/null 2>&1; then
  ( cd "$PROJECT_DIR" && python3 .devmode/dashboard.py . >/dev/null 2>&1 ) \
    && ok "wrote devmode-dashboard.html (open it; no server/registration needed)" \
    || info "dashboard will generate on first scorecard run"
fi

# --- done --------------------------------------------------------------------
# Report reality, not intent: these strings come from what the run actually did.
BEADS_STATUS=" · memory: not requested"
if [ "${BEADS:-0}" -eq 1 ] || [ "${BEADS_STEALTH:-0}" -eq 1 ]; then
  if [ "${BEADS_LIVE:-0}" -eq 1 ]; then BEADS_STATUS=" · memory: LIVE (bd)"
  else BEADS_STATUS=" · memory: NOT LIVE (see the doctor above)"; fi
fi
GATES_STATUS="· gates: not requested"
if [ "$GUARDRAILS" -eq 1 ]; then
  if [ "${WIRED:-0}" -eq 1 ]; then GATES_STATUS="· gates: wired + verified"
  else GATES_STATUS="· gates: NOT ACTIVE (wiring failed)"; fi
fi

step "Done — next steps"
cat <<EOF
BASE established (devmode) · LAYER mounted (Conductor)${BEADS_STATUS} ${GATES_STATUS}

${c_green}Easiest path — guided mode:${c_off}
  Run  ${c_green}/devmode "<what you want to build>"${c_off}
  The orchestrator drives every phase and pauses only at your decision gates.

Manual path (if you prefer to drive):
1. Fill in:  conductor/product.md, conductor/tech-stack.md, UBIQUITOUS_LANGUAGE.md
2. Align:    run the ${c_green}grill-me${c_off} skill to reach a shared design concept
3. Plan:     /conductor-newtrack "<feature>"  → spec.md (write-prd rigor) + plan.md
4. Build:    /conductor-implement             → TDD loop per conductor/workflow.md
5. Review:   code-review panel → verification-before-completion before "done"

CLAUDE.md declares the base↔layer hierarchy. conductor/INTEGRATION.md has the map.
EOF
