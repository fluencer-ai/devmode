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
   "$DEVMODE_ROOT/scripts/goal_brief.py" "$PROJECT_DIR/.devmode/" 2>/dev/null \
  && ok "copied scorecard.py + dashboard.py + goal_brief.py → .devmode/" || warn "devmode scripts not found in base"

# 1c. devmode skills + agents + references (the base process itself).
if [ "$WITH_SKILLS" -eq 1 ]; then
  mkdir -p "$PROJECT_DIR/.claude/skills" "$PROJECT_DIR/.claude/agents" "$PROJECT_DIR/.claude/devmode/references"
  cp -R "$DEVMODE_ROOT/skills/." "$PROJECT_DIR/.claude/skills/"
  ok "copied $(find "$DEVMODE_ROOT/skills" -name SKILL.md | wc -l | tr -d ' ') devmode skills → .claude/skills/"
  cp "$DEVMODE_ROOT"/.agents/*.md "$PROJECT_DIR/.claude/agents/" 2>/dev/null && \
    ok "copied $(find "$DEVMODE_ROOT/.agents" -name '*.md' | wc -l | tr -d ' ') agents → .claude/agents/" || true
  cp "$DEVMODE_ROOT"/references/*.md "$PROJECT_DIR/.claude/devmode/references/" 2>/dev/null && \
    ok "copied references → .claude/devmode/references/" || true
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

# The guided front door: /devmode command + the orchestrator agent
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
if [ "$GUARDRAILS" -eq 1 ]; then
  step "Installing guardrails (gates-as-code)"
  mkdir -p "$PROJECT_DIR/.claude/hooks"
  copy_template "$SCRIPT_DIR/hooks/guardrails.py"      "$PROJECT_DIR/.claude/hooks/guardrails.py"
  copy_template "$SCRIPT_DIR/hooks/test_guardrails.py" "$PROJECT_DIR/.claude/hooks/test_guardrails.py"
  # Idempotently merge the PreToolUse hook into .claude/settings.json
  python3 - "$PROJECT_DIR/.claude/settings.json" <<'PY' && ok "wired PreToolUse guardrail into .claude/settings.json" || warn "could not merge settings.json — merge hooks/hooks.snippet.json by hand"
import json, os, sys
path = sys.argv[1]
cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guardrails.py"'
entry = {"matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit",
         "hooks": [{"type": "command", "command": cmd}]}
data = {}
if os.path.isfile(path):
    try: data = json.load(open(path))
    except Exception: data = {}
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
already = any(h.get("command") == cmd for g in pre for h in g.get("hooks", []))
if not already:
    pre.append(entry)
    json.dump(data, open(path, "w"), indent=2)
PY
  warn "guardrails block: sudo, force-push, --no-verify, rm -rf /, writes to .env/.git/secrets; ask: reset --hard, scoped rm -rf, reading secrets."
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
    warn "'bd' not found. Install: npm i -g @beads/bd  (then 'bd init')."
    warn "Beads is optional — set enabled:false in conductor/beads.json to run without it."
  fi
else
  info "skipping bd init (use --beads or --beads-stealth; or run it later)"
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
step "Done — next steps"
cat <<EOF
BASE established (devmode) · LAYER mounted (Conductor) · memory (Beads)

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
