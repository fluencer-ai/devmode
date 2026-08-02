#!/usr/bin/env bash
#
# devmode update — refresh the devmode-MANAGED files in an existing project to the
# current base, WITHOUT touching anything the project owns.
#
# Overwrites (devmode-owned, versioned in the base): .claude/skills/,
# .agents/skills/ base skills, the role agents + the orchestrator, Codex agent
# adapters, the /devmode command, the hooks, the .devmode scripts
# (scorecard/dashboard/goal_brief), the references, the conductor workflow
# adapter + INTEGRATION.md + per-track templates, and CLAUDE.devmode.md /
# AGENTS.devmode.md (only if present or needed as non-destructive pointers).
# Merges (never replaces): the devmode-owned keys in .codex/config.toml — your
# own keys, tables and comments in that file are preserved.
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

validate_json_file() {
  local path="$1"
  [ -f "$path" ] || return 0
  python3 - "$path" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as handle:
        json.load(handle)
except Exception as error:
    print(f"invalid JSON in {path}: {error}", file=sys.stderr)
    raise SystemExit(1)
PY
}

# .codex/config.toml has to be able to EVOLVE. Leaving any divergent file frozen
# forever means a template fix never reaches a project. So devmode owns exactly
# the keys the template declares (marked in-file by the `devmode-managed` line)
# and preserves everything else: user keys, user tables, comments, ordering.
# Without that marker the file is user-authored: devmode may add a key it is
# missing, never rewrite a value, and does not claim ownership.
merge_codex_config() {
  local src="$1" dst="$2" summary script
  if [ ! -e "$dst" ]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    mark_managed "${dst#"$P"/}"
    ok ".codex/config.toml written"
    return 0
  fi
  if cmp -s "$src" "$dst"; then
    mark_managed "${dst#"$P"/}"
    ok ".codex/config.toml already current"
    return 0
  fi
  # bash 3.2 (the macOS default) cannot parse a heredoc inside $(...), so the
  # merger goes to a temp file first and is then run as an ordinary command.
  script="$(mktemp "${TMPDIR:-/tmp}/devmode-codex-config.XXXXXX")"
  cat >"$script" <<'PY'
import re, sys

MARKER = re.compile(r"^#\s*devmode-managed:\s*codex-config\s+v\d+")
# Deliberately strict: a table header or key at column 0, so an indented line
# inside a user's multi-line array can never be mistaken for either.
TABLE = re.compile(r"^\[([^\[\]]+)\]\s*(?:#.*)?$")
ARRAY_TABLE = re.compile(r"^\[\[([^\[\]]+)\]\]\s*(?:#.*)?$")
KEY = re.compile(r"^([A-Za-z0-9_.\"'-]+)\s*=")


def table_header(line, index):
    array = ARRAY_TABLE.match(line)
    if array:
        # Each array element is its own opaque scope. Template-owned keys never
        # live here, but recognizing the boundary prevents keys from leaking
        # into the preceding/root table during the merge.
        return "@array:%s:%s" % (index, array.group(1))
    header = TABLE.match(line)
    return header.group(1) if header else None


def scan(lines):
    """-> {(table, key): (index, line)} — first definition wins, as TOML does."""
    table, found = "", {}
    for index, line in enumerate(lines):
        header = table_header(line, index)
        if header is not None:
            table = header
            continue
        key = KEY.match(line)
        if key:
            found.setdefault((table, key.group(1)), (index, line.rstrip()))
    return found


def insert_missing(lines, missing):
    """Append each block at the end of its own table, creating the table if new."""
    result, table = [], ""

    def flush(name, before_header):
        block = missing.pop(name, None)
        if not block:
            return
        while result and not result[-1].strip():
            result.pop()
        result.extend(block)
        if before_header:
            result.append("")

    for index, line in enumerate(lines):
        header = table_header(line, index)
        if header is not None:
            flush(table, True)
            table = header
        result.append(line)
    flush(table, False)
    for name in list(missing):
        block = missing.pop(name)
        while result and not result[-1].strip():
            result.pop()
        result.append("")
        if name:
            result.append("[%s]" % name)
        result.extend(block)
    return result


template = open(sys.argv[1], encoding="utf-8").read().splitlines()
original = open(sys.argv[2], encoding="utf-8").read()
out = original.splitlines()

owned = any(MARKER.match(line) for line in out)
wanted, present = scan(template), scan(out)
refreshed, added, kept, missing = [], [], [], {}

for (table, key), (_, template_line) in wanted.items():
    label = "%s.%s" % (table, key) if table else key
    if (table, key) not in present:
        missing.setdefault(table, []).append(template_line)
        added.append(label)
        continue
    index, current = present[(table, key)]
    if current.strip() == template_line.strip():
        continue
    if owned:
        out[index] = template_line
        refreshed.append(label)
    else:
        kept.append(label)

out = insert_missing(out, missing)

marker = next((line for line in template if MARKER.match(line)), None)
if marker and owned:
    out = [marker if MARKER.match(line) else line for line in out]
elif marker and not kept:
    # Nothing diverged, so this is an unmodified older template: adopt it.
    out.insert(0, marker)
    owned = True

text = "\n".join(out).rstrip("\n") + "\n"
if text != original:
    open(sys.argv[2], "w", encoding="utf-8").write(text)

parts = []
if refreshed:
    parts.append("refreshed %s" % ", ".join(refreshed))
if added:
    parts.append("added %s" % ", ".join(added))
if kept:
    parts.append("kept your value for %s" % ", ".join(kept))
print(("" if owned else "user-owned: ") + ("; ".join(parts) or "already current"))
PY
  if ! summary="$(python3 "$script" "$src" "$dst")"; then
    rm -f "$script"
    err ".codex/config.toml merge FAILED — file left untouched"
    return 1
  fi
  rm -f "$script"
  case "$summary" in
    user-owned:*) warn ".codex/config.toml — ${summary#user-owned: } (no devmode marker)" ;;
    *)            mark_managed "${dst#"$P"/}"; ok ".codex/config.toml — $summary" ;;
  esac
}

replace_codex_skill_link() {
  local skill_name="$1"
  local source="$P/.claude/skills/$skill_name"
  local destination="$P/.agents/skills/$skill_name"
  local target="../../.claude/skills/$skill_name"
  local rel=".agents/skills/$skill_name"

  if [ -L "$destination" ] && [ "$(readlink "$destination")" = "$target" ]; then
    mark_managed "$rel"
    return 0
  fi
  # Older Codex ports copied the same skill tree a second time and had no
  # ownership manifest. An exact duplicate is safe to collapse to the shared
  # link; a divergent same-name skill remains project-owned.
  if [ -d "$destination" ] && [ -d "$source" ] && \
     diff -qr "$source" "$destination" >/dev/null 2>&1; then
    rm -rf -- "$destination"
  elif [ -L "$destination" ] || [ -e "$destination" ]; then
    if ! is_managed "$rel"; then
      warn "kept project-owned $rel"
      return 1
    fi
    rm -rf -- "$destination"
  fi
  ln -s "$target" "$destination"
  mark_managed "$rel"
}

usage() {
  cat <<'USAGE'
Usage: update.sh <project-dir>

Refresh the devmode-MANAGED files in an existing project to the current base.

  <project-dir>   the project to refresh (must already have devmode installed)
  -h, --help      show this help

Overwrites the devmode-owned set only (skills, role agents + orchestrator, Codex
adapters, the /devmode command, the opted-in hooks, the .devmode scripts, the
references, the conductor adapter + templates). Merges .codex/config.toml.
Never touches CLAUDE.md, UBIQUITOUS_LANGUAGE.md, conductor product/tracks/
patterns, .devmode/scorecard.json, devmode-dashboard.html, or your code.
USAGE
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

P="${1:-}"
[ -n "$P" ] || { err "usage: update.sh <project-dir>  (see --help)"; exit 1; }
[ -d "$P" ] || { err "no such directory: $P"; exit 1; }
P="$(cd "$P" && pwd)"
[ -d "$P/.claude" ] || { err "$P has no .claude/ — not a devmode project. Run install.sh first."; exit 1; }

if [ -e "$P/.codex/config.toml" ] && ! cmp -s "$TPL/codex.config.toml" "$P/.codex/config.toml"; then
  if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'pass' >/dev/null 2>&1; then
    err "refusing to update: python3 is required to merge .codex/config.toml; no files changed"
    exit 1
  fi
fi

# Validate opted-in hook state before creating the ownership manifest or changing
# any asset. Invalid host JSON must fail atomically, not after a partial update.
CLAUDE_DEVMODE_HOOKS=0
for hook_name in guardrails verify_gate devmode_phase_gate session_resume; do
  [ -f "$P/.claude/hooks/$hook_name.py" ] && CLAUDE_DEVMODE_HOOKS=1
done
if [ -f "$P/.claude/settings.json" ] && \
   grep -Eq 'guardrails\.py|verify_gate\.py|devmode_phase_gate\.py|session_resume\.py' "$P/.claude/settings.json"; then
  CLAUDE_DEVMODE_HOOKS=1
fi

CODEX_DEVMODE_HOOKS=0
if [ -f "$P/.codex/hooks/codex_hooks.py" ] || \
   { [ -f "$P/.codex/hooks.json" ] && grep -q 'codex_hooks\.py' "$P/.codex/hooks.json"; }; then
  CODEX_DEVMODE_HOOKS=1
fi

if [ "$CLAUDE_DEVMODE_HOOKS" -eq 1 ] && ! validate_json_file "$P/.claude/settings.json"; then
  err "refusing to update Claude hooks: invalid settings JSON was preserved; no files changed"
  exit 1
fi
if { [ "$CLAUDE_DEVMODE_HOOKS" -eq 1 ] || [ "$CODEX_DEVMODE_HOOKS" -eq 1 ]; } && \
   ! validate_json_file "$P/.codex/hooks.json"; then
  err "refusing to update Codex hooks: invalid hooks JSON was preserved; no files changed"
  exit 1
fi

# Do not create or preserve an instruction pointer to an unrelated same-name
# file. Exact templates, recognizable devmode adapters, and already-managed
# adapters are safe to refresh.
adapter_target_is_safe() {
  local adapter="$1" template="$2" marker="$3" rel="${1#"$P"/}"
  [ ! -e "$adapter" ] && return 0
  cmp -s "$template" "$adapter" && return 0
  grep -Fq "$marker" "$adapter" 2>/dev/null && return 0
  grep -Fqx "$rel" "$P/.devmode/managed-files" 2>/dev/null && return 0
  return 1
}

if [ -e "$P/AGENTS.md" ] && \
   ! grep -q '^# AGENTS.md -- Codex compatibility for devmode$' "$P/AGENTS.md" 2>/dev/null && \
   ! adapter_target_is_safe \
     "$P/AGENTS.devmode.md" "$TPL/AGENTS.md" \
     'This file is the Codex adapter for a devmode project.'; then
  err "refusing to update: AGENTS.devmode.md is project-owned and is not a devmode adapter"
  err "  no devmode files were changed"
  exit 1
fi
if [ -f "$P/CLAUDE.md" ] && grep -q '@CLAUDE.devmode.md' "$P/CLAUDE.md" 2>/dev/null && \
   ! adapter_target_is_safe \
     "$P/CLAUDE.devmode.md" "$TPL/CLAUDE.md" \
     'This project uses **devmode as its base**'; then
  err "refusing to update: CLAUDE.md imports a project-owned CLAUDE.devmode.md that is not a devmode adapter"
  err "  no devmode files were changed"
  exit 1
fi

LEGACY_OWNERSHIP=0
[ -f "$P/.devmode/managed-files" ] || LEGACY_OWNERSHIP=1
MANAGED_FILES="$P/.devmode/managed-files"
mkdir -p "$(dirname "$MANAGED_FILES")"
touch "$MANAGED_FILES"
is_managed() { grep -Fqx "$1" "$MANAGED_FILES" 2>/dev/null; }
mark_managed() {
  local rel="$1"
  is_managed "$rel" || printf '%s\n' "$rel" >> "$MANAGED_FILES"
}
refresh_file() { # refresh_file <source> <destination>
  local src="$1" dst="$2" rel="${2#"$P"/}"
  if is_managed "$rel" || [ ! -e "$dst" ] || cmp -s "$src" "$dst"; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    mark_managed "$rel"
  else
    warn "kept project-owned $rel (same-name devmode asset not installed here)"
    return 1
  fi
}
refresh_tree() { # refresh_tree <source-dir> <destination-dir>
  local src="$1" dst="$2" rel="${2#"$P"/}/"
  if is_managed "$rel" || { [ -d "$dst" ] && diff -qr "$src" "$dst" >/dev/null 2>&1; } || \
     { [ ! -e "$dst" ] && [ ! -L "$dst" ]; }; then
    rm -rf -- "$dst"
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
    mark_managed "$rel"
  else
    warn "kept project-owned ${rel%/}/ (same-name devmode skill not installed here)"
    return 1
  fi
}

step "Updating devmode in $P (project files left untouched)"
if [ "$LEGACY_OWNERSHIP" -eq 1 ]; then
  warn "legacy install had no ownership manifest: exact/absent assets will be claimed; divergent same-name files stay project-owned"
fi

# 1. skills — refresh only directories installed by devmode. Unrelated and
# same-name project skills are left in place.
mkdir -p "$P/.claude/skills"
WITH_SKILLS=1
if [ -f "$P/.devmode/install-profile" ] && grep -Fqx 'skills=0' "$P/.devmode/install-profile"; then
  WITH_SKILLS=0
fi
skills_refreshed=0
if [ "$WITH_SKILLS" -eq 1 ]; then
  for skill_dir in "$DEVMODE_ROOT"/skills/*; do
    [ -d "$skill_dir" ] || continue
    if refresh_tree "$skill_dir" "$P/.claude/skills/$(basename "$skill_dir")"; then
      skills_refreshed=$((skills_refreshed + 1))
    fi
  done
  ok "skills → $skills_refreshed devmode-owned directories refreshed"
else
  ok "skills → global-install profile preserved (--no-skills)"
fi
mkdir -p "$P/.agents/skills"
if [ "$WITH_SKILLS" -eq 1 ]; then
  for skill_dir in "$DEVMODE_ROOT"/skills/*; do
    [ -d "$skill_dir" ] || continue
    replace_codex_skill_link "$(basename "$skill_dir")" || true
  done
fi
# The `--with-conductor` skills are cloned from upstream into .claude/skills/,
# not carried in the base's skills/ — so the loop above can never reach them.
# Without this, a project whose links predate the symlink scheme loses Codex
# access to conductor + beads permanently while Claude keeps both.
for upstream_skill in conductor beads; do
  [ -d "$P/.claude/skills/$upstream_skill" ] || continue
  replace_codex_skill_link "$upstream_skill" || true
done
mkdir -p "$P/.agents/skills/devmode"
refresh_file "$DEVMODE_ROOT/.agents/skills/devmode/SKILL.md" "$P/.agents/skills/devmode/SKILL.md" || true
refresh_file "$DEVMODE_ROOT/.agents/skills/devmode/agents/openai.yaml" \
  "$P/.agents/skills/devmode/agents/openai.yaml" || true
ok "Codex skills refreshed as links → .agents/skills/ (single physical copy)"

# 2. agents (role agents) + the orchestrator
mkdir -p "$P/.claude/agents" "$P/.agents" "$P/.codex/agents"
if [ "$WITH_SKILLS" -eq 1 ]; then
  for agent in "$DEVMODE_ROOT"/.agents/*.md; do
    [ -f "$agent" ] || continue
    refresh_file "$agent" "$P/.claude/agents/$(basename "$agent")" || true
    refresh_file "$agent" "$P/.agents/$(basename "$agent")" || true
  done
fi
refresh_file "$SCRIPT_DIR/agents/devmode-orchestrator.md" "$P/.claude/agents/devmode-orchestrator.md" || true
for adapter in "$DEVMODE_ROOT"/.codex/agents/*.toml; do
  [ -f "$adapter" ] || continue
  name="$(basename "$adapter" .toml)"
  install_adapter=0
  if [ "$name" = "devmode-orchestrator" ]; then
    install_adapter=1
  elif [ "$WITH_SKILLS" -eq 1 ] && [ -f "$P/.agents/$name.md" ] && \
       cmp -s "$DEVMODE_ROOT/.agents/$name.md" "$P/.agents/$name.md"; then
    install_adapter=1
  fi
  if [ "$install_adapter" -eq 1 ]; then
    refresh_file "$adapter" "$P/.codex/agents/$(basename "$adapter")" || true
  else
    warn "kept Codex adapter state for custom role agent: $name"
  fi
done
ok "agents + orchestrator + Codex agent adapters refreshed"

# 2b. Codex project guidance + config. Existing project-owned AGENTS.md stays the
# host; update adds or refreshes only the devmode adapter/pointer.
AGENTS_DST="$P/AGENTS.md"
if [ -e "$AGENTS_DST" ]; then
  if grep -q '^# AGENTS.md -- Codex compatibility for devmode$' "$AGENTS_DST" 2>/dev/null; then
    refresh_file "$TPL/AGENTS.md" "$AGENTS_DST" || true
    if [ -f "$P/AGENTS.devmode.md" ] && cmp -s "$P/AGENTS.devmode.md" "$TPL/AGENTS.md"; then
      rm -f -- "$P/AGENTS.devmode.md"
    fi
    ok "devmode-owned AGENTS.md refreshed in place"
  else
    refresh_file "$TPL/AGENTS.md" "$P/AGENTS.devmode.md" || true
    if grep -q '<!-- devmode: Codex base process;' "$AGENTS_DST" 2>/dev/null; then
      ok "AGENTS.devmode.md refreshed; AGENTS.md pointer already present"
    else
      printf '\n<!-- devmode: Codex base process; project instructions above take precedence -->\n## devmode for Codex\nBefore non-trivial Codex work, read `AGENTS.devmode.md`; it maps the devmode Claude Code setup to Codex without replacing this file.\n' >> "$AGENTS_DST"
      ok "kept AGENTS.md; appended one Codex pointer -> AGENTS.devmode.md"
    fi
  fi
else
  refresh_file "$TPL/AGENTS.md" "$AGENTS_DST"
  ok "AGENTS.md written for Codex"
fi
merge_codex_config "$TPL/codex.config.toml" "$P/.codex/config.toml"

# 3. the /devmode command
mkdir -p "$P/.claude/commands"
refresh_file "$SCRIPT_DIR/commands/devmode.md" "$P/.claude/commands/devmode.md" || true
ok "/devmode command refreshed"

# 4. references
if ls "$DEVMODE_ROOT"/references/*.md >/dev/null 2>&1; then
  mkdir -p "$P/.claude/devmode/references"
  for reference in "$DEVMODE_ROOT"/references/*.md; do
    refresh_file "$reference" "$P/.claude/devmode/references/$(basename "$reference")" || true
  done
  ok "references refreshed"
fi

# 5. .devmode scripts — NEVER the data (scorecard.json / gates.json)
mkdir -p "$P/.devmode"
for script in scorecard.py dashboard.py goal_brief.py beads_doctor.py; do
  refresh_file "$DEVMODE_ROOT/scripts/$script" "$P/.devmode/$script" || true
done
ok "scorecard.py + dashboard.py + goal_brief.py + beads_doctor.py refreshed (scorecard.json untouched)"

# 6. Hooks are opt-in. The preflight above detected and validated ownership
# before any write; a generic host hooks directory/config is not evidence.
if [ "$CLAUDE_DEVMODE_HOOKS" -eq 1 ]; then
  for h in guardrails test_guardrails verify_gate devmode_phase_gate session_resume; do
    refresh_file "$SCRIPT_DIR/hooks/$h.py" "$P/.claude/hooks/$h.py" || true
  done
  ok "hooks refreshed (incl. session_resume)"
  # Wire EVERY refreshed gate, not just the newest one. Refreshing a script
  # without wiring it is the worst possible state: the file is present and
  # current, so the gate looks installed — and never runs. A project set up
  # before devmode_phase_gate.py existed used to get the file and no wiring,
  # while the Codex side (below) wired all five of its events.
  if [ -f "$P/.claude/settings.json" ]; then
    python3 - "$P/.claude/settings.json" <<'PY' && ok "Claude gates wired in settings.json (PreToolUse guardrail, Stop verify+phase, SessionStart resume)" || err "FAILED to wire Claude gates in settings.json — they will NOT run; fix it by hand"
import json, sys
path = sys.argv[1]
base = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/%s"'
pre_cmd = base % "guardrails.py"
stop_cmds = (base % "verify_gate.py", base % "devmode_phase_gate.py")
session_cmd = base % "session_resume.py"
try: data = json.load(open(path))
except Exception as error:
    print(f"invalid JSON in {path}: {error}", file=sys.stderr)
    raise SystemExit(1)
hooks = data.setdefault("hooks", {})

def wired(event, cmd):
    return any(h.get("command") == cmd for g in hooks.get(event, []) for h in g.get("hooks", []))

pre = hooks.setdefault("PreToolUse", [])
if not wired("PreToolUse", pre_cmd):
    pre.append({"matcher": "Bash|Write|Edit|MultiEdit|NotebookEdit",
                "hooks": [{"type": "command", "command": pre_cmd}]})
stop = hooks.setdefault("Stop", [])
for cmd in stop_cmds:
    if not wired("Stop", cmd):
        stop.append({"hooks": [{"type": "command", "command": cmd}]})
start = hooks.setdefault("SessionStart", [])
if not wired("SessionStart", session_cmd):
    start.append({"hooks": [{"type": "command", "command": session_cmd}]})
json.dump(data, open(path, "w"), indent=2)
PY
  fi
fi

# 6b. Migrate an opted-in Claude gate installation to Codex, or refresh an
# existing devmode Codex hook installation. Unrelated host hooks stay untouched.
if [ "$CLAUDE_DEVMODE_HOOKS" -eq 1 ] || [ "$CODEX_DEVMODE_HOOKS" -eq 1 ]; then
  mkdir -p "$P/.codex/hooks"
  for h in codex_hooks test_codex_hooks; do
    refresh_file "$SCRIPT_DIR/hooks/$h.py" "$P/.codex/hooks/$h.py" || true
  done
  python3 - "$P/.codex/hooks.json" <<'PY' && ok "Codex hooks wired in .codex/hooks.json" || err "FAILED to wire Codex hooks"
import json, os, sys
path = sys.argv[1]
cmd = 'python3 "$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.codex/hooks/codex_hooks.py"'
data = {}
if os.path.isfile(path):
    try: data = json.load(open(path, encoding="utf-8"))
    except Exception as error:
        print(f"invalid JSON in {path}: {error}", file=sys.stderr)
        raise SystemExit(1)
data.setdefault("description", "devmode Codex compatibility hooks.")
hooks = data.setdefault("hooks", {})
def ensure(event, matcher=None, **handler):
    groups = hooks.setdefault(event, [])
    for g in groups:
        for h in g.get("hooks", []):
            if h.get("command") == cmd:
                if matcher is not None:
                    g["matcher"] = matcher
                h.update(handler)
                return
    group = {"hooks": [{"type": "command", "command": cmd, **handler}]}
    if matcher is not None:
        group["matcher"] = matcher
    groups.append(group)
ensure("SessionStart", "startup|resume|clear|compact", statusMessage="Loading devmode resume context", additionalContextLimit=5000)
ensure("UserPromptSubmit")
ensure("PreToolUse", "Bash|apply_patch|Edit|Write|MultiEdit|NotebookEdit", statusMessage="Checking devmode guardrails")
ensure("PostToolUse", "Bash|apply_patch|Edit|Write|MultiEdit|NotebookEdit|Agent|spawn_agent")
ensure("Stop", None, timeout=30)
json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
PY
  warn "Codex users must trust this project and review/trust hooks with /hooks before project hooks run."
fi

# 7. conductor adapter (devmode-owned): workflow.md + INTEGRATION.md + per-track templates
if [ -d "$P/conductor" ]; then
  refresh_file "$TPL/workflow.md" "$P/conductor/workflow.md" || true
  refresh_file "$SCRIPT_DIR/INTEGRATION.md" "$P/conductor/INTEGRATION.md" || true
  if [ -d "$P/conductor/.templates/track" ]; then
    for template in "$TPL"/track/*.md; do
      refresh_file "$template" "$P/conductor/.templates/track/$(basename "$template")" || true
    done
  fi
  ok "conductor workflow adapter + INTEGRATION.md + track templates refreshed"
fi

# 8. CLAUDE.devmode.md — ONLY if the project uses the pointer variant. NEVER write CLAUDE.md.
if [ -f "$P/CLAUDE.devmode.md" ]; then
  if refresh_file "$TPL/CLAUDE.md" "$P/CLAUDE.devmode.md"; then
    ok "CLAUDE.devmode.md (base declaration) refreshed — your CLAUDE.md left untouched"
  fi
else
  warn "no CLAUDE.devmode.md (your CLAUDE.md holds devmode inline) — left untouched, as it should be"
fi

step "Done — devmode updated; project content untouched"
ok "Review with: git -C \"$P\" status  (only devmode-managed files should appear)"
