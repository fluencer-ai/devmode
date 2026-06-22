#!/usr/bin/env bash
#
# devmode update — refresh the devmode-MANAGED files in an existing project to the
# current base, WITHOUT touching anything the project owns.
#
# Overwrites (devmode-owned, versioned in the base): .claude/skills/, the role
# agents + the orchestrator, the /devmode command, the hooks, the .devmode scripts
# (scorecard/dashboard/goal_brief), the references, the conductor workflow adapter
# + INTEGRATION.md + per-track templates, and CLAUDE.devmode.md (only if present).
#
# NEVER touches (project-owned): CLAUDE.md, UBIQUITOUS_LANGUAGE.md, conductor
# product/tech-stack/tracks/patterns/beads.json, your tracks/specs/code,
# .devmode/scorecard.json + gates.json, devmode-dashboard.html, user-added skills.
#
# Usage:  ./update.sh <project-dir>
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVMODE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TPL="$SCRIPT_DIR/templates"

c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_off=$'\033[0m'
ok()   { printf "%s✓%s %s\n" "$c_green" "$c_off" "$*"; }
warn() { printf "%s!%s %s\n" "$c_yellow" "$c_off" "$*"; }
err()  { printf "%s✗%s %s\n" "$c_red" "$c_off" "$*" >&2; }
step() { printf "\n%s== %s ==%s\n" "$c_blue" "$*" "$c_off"; }

P="${1:-}"
[ -n "$P" ] || { err "usage: update.sh <project-dir>"; exit 1; }
[ -d "$P" ] || { err "no such directory: $P"; exit 1; }
P="$(cd "$P" && pwd)"
[ -d "$P/.claude" ] || { err "$P has no .claude/ — not a devmode project. Run install.sh first."; exit 1; }

step "Updating devmode in $P (project files left untouched)"

# 1. skills — overwrite the base set (user-added skills are left in place)
mkdir -p "$P/.claude/skills"
cp -R "$DEVMODE_ROOT/skills/." "$P/.claude/skills/"
ok "skills → $(find "$DEVMODE_ROOT/skills" -name SKILL.md | wc -l | tr -d ' ') refreshed"

# 2. agents (role agents) + the orchestrator
mkdir -p "$P/.claude/agents"
cp "$DEVMODE_ROOT"/.agents/*.md "$P/.claude/agents/"
cp "$SCRIPT_DIR/agents/devmode-orchestrator.md" "$P/.claude/agents/devmode-orchestrator.md"
ok "agents + orchestrator refreshed"

# 3. the /devmode command
mkdir -p "$P/.claude/commands"
cp "$SCRIPT_DIR/commands/devmode.md" "$P/.claude/commands/devmode.md"
ok "/devmode command refreshed"

# 4. references
if ls "$DEVMODE_ROOT"/references/*.md >/dev/null 2>&1; then
  mkdir -p "$P/.claude/devmode/references"
  cp "$DEVMODE_ROOT"/references/*.md "$P/.claude/devmode/references/"
  ok "references refreshed"
fi

# 5. .devmode scripts — NEVER the data (scorecard.json / gates.json)
mkdir -p "$P/.devmode"
cp "$DEVMODE_ROOT"/scripts/scorecard.py "$DEVMODE_ROOT"/scripts/dashboard.py \
   "$DEVMODE_ROOT"/scripts/goal_brief.py "$P/.devmode/"
ok "scorecard.py + dashboard.py + goal_brief.py refreshed (scorecard.json untouched)"

# 6. hooks — only if the project already uses them; add the SessionStart resume if missing
if [ -d "$P/.claude/hooks" ]; then
  for h in guardrails test_guardrails verify_gate devmode_phase_gate session_resume; do
    cp "$SCRIPT_DIR/hooks/$h.py" "$P/.claude/hooks/$h.py"
  done
  ok "hooks refreshed (incl. session_resume)"
  # idempotently wire the SessionStart resume hook into settings.json
  if [ -f "$P/.claude/settings.json" ]; then
    python3 - "$P/.claude/settings.json" <<'PY' && ok "SessionStart resume wired in settings.json" || warn "could not wire session_resume — add it by hand"
import json, os, sys
path = sys.argv[1]
cmd = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/session_resume.py"'
try: data = json.load(open(path))
except Exception: data = {}
hooks = data.setdefault("hooks", {})
start = hooks.setdefault("SessionStart", [])
if not any(h.get("command") == cmd for g in start for h in g.get("hooks", [])):
    start.append({"hooks": [{"type": "command", "command": cmd}]})
    json.dump(data, open(path, "w"), indent=2)
PY
  fi
fi

# 7. conductor adapter (devmode-owned): workflow.md + INTEGRATION.md + per-track templates
if [ -d "$P/conductor" ]; then
  cp "$TPL/workflow.md"  "$P/conductor/workflow.md"
  cp "$SCRIPT_DIR/INTEGRATION.md" "$P/conductor/INTEGRATION.md"
  if [ -d "$P/conductor/.templates/track" ]; then
    cp "$TPL"/track/*.md "$P/conductor/.templates/track/"
  fi
  ok "conductor workflow adapter + INTEGRATION.md + track templates refreshed"
fi

# 8. CLAUDE.devmode.md — ONLY if the project uses the pointer variant. NEVER write CLAUDE.md.
if [ -f "$P/CLAUDE.devmode.md" ]; then
  cp "$TPL/CLAUDE.md" "$P/CLAUDE.devmode.md"
  ok "CLAUDE.devmode.md (base declaration) refreshed — your CLAUDE.md left untouched"
else
  warn "no CLAUDE.devmode.md (your CLAUDE.md holds devmode inline) — left untouched, as it should be"
fi

step "Done — devmode updated; project content untouched"
ok "Review with: git -C \"$P\" status  (only devmode-managed files should appear)"
