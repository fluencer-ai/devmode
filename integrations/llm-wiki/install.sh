#!/usr/bin/env bash
#
# llm-wiki — scaffold a Karpathy LLM Wiki into a project (pure markdown).
#
# An OPT-IN devmode module: the LLM maintains a persistent, interlinked markdown
# knowledge base (Karpathy's LLM Wiki pattern). No app, no database, no server —
# browse it in any editor (Obsidian follows the wikilinks). Independent of
# devmode's code process; deployed via `/devmode wiki start|adopt`.
#
# Usage:
#   ./install.sh <target-dir> [options]
#
# Options:
#   --adopt    Existing project: scaffold the canonical structure alongside what's
#              there (non-destructive) and print an audit + migration hint. Without
#              it, treats <target-dir> as a fresh wiki project (creates the dir).
#   --force    Overwrite the schema/template files this installer writes.
#   -h, --help Show this help.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPL="$SCRIPT_DIR/templates"
# shellcheck source=host-pointers.sh
. "$SCRIPT_DIR/host-pointers.sh"

c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_off=$'\033[0m'
info() { printf "%s•%s %s\n" "$c_blue" "$c_off" "$*"; }
ok()   { printf "%s✓%s %s\n" "$c_green" "$c_off" "$*"; }
warn() { printf "%s!%s %s\n" "$c_yellow" "$c_off" "$*"; }
err()  { printf "%s✗%s %s\n" "$c_red" "$c_off" "$*" >&2; }
step() { printf "\n%s== %s ==%s\n" "$c_blue" "$*" "$c_off"; }
usage() { awk 'NR>1 && /^set -euo pipefail$/{exit} NR>1{sub(/^# ?/, ""); print}' "$0"; exit "${1:-0}"; }

TARGET=""; ADOPT=0; FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --adopt) ADOPT=1 ;;
    --force) FORCE=1 ;;
    -h|--help) usage 0 ;;
    -*) err "unknown option: $1"; usage 1 ;;
    *) [ -z "$TARGET" ] && TARGET="$1" || { err "unexpected arg: $1"; usage 1; } ;;
  esac
  shift
done
[ -z "$TARGET" ] && { err "missing <target-dir>"; usage 1; }

if [ "$ADOPT" -eq 1 ]; then
  [ -d "$TARGET" ] || { err "--adopt needs an existing directory: $TARGET"; exit 1; }
else
  if [ -d "$TARGET" ] && [ -n "$(find "$TARGET" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
    err "fresh wiki target is not empty: $TARGET (use --adopt for an existing project)"
    exit 1
  fi
  mkdir -p "$TARGET"
fi
TARGET="$(cd "$TARGET" && pwd)"

if [ "$ADOPT" -eq 1 ] && [ "$FORCE" -eq 0 ] && [ -f "$TARGET/KARPATHY.md" ] && \
   ! grep -Fqx '# KARPATHY.md — the LLM Wiki schema for this project' "$TARGET/KARPATHY.md"; then
  err "KARPATHY.md already exists but is not the LLM Wiki schema; refusing to shadow project content"
  err "rename that file, or rerun with --force only if replacing it is intentional"
  exit 1
fi

EXISTING_MD=0
if [ "$ADOPT" -eq 1 ]; then
  EXISTING_MD=$(find "$TARGET" -type f -name "*.md" -not -path "*/.git/*" \
    -not -path "*/.llm-wiki/*" -not -path "*/wiki/*" -not -path "*/raw/*" \
    2>/dev/null | wc -l | tr -d ' ')
fi

MANAGED_DIR="$TARGET/.llm-wiki"
MANAGED_FILES="$MANAGED_DIR/managed-files"
mkdir -p "$MANAGED_DIR"
touch "$MANAGED_FILES"
mark_managed() {
  local rel="$1"
  grep -Fqx "$rel" "$MANAGED_FILES" 2>/dev/null || printf '%s\n' "$rel" >> "$MANAGED_FILES"
}

# copy a template file only if absent (or --force)
copy() {  # copy <src> <dst>
  local src="$1" dst="$2"
  if [ -e "$dst" ] && [ "$FORCE" -ne 1 ]; then
    info "kept existing ${dst#"$TARGET"/} (use --force to overwrite)"
    cmp -s "$src" "$dst" && mark_managed "${dst#"$TARGET"/}"
  else
    mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"
    mark_managed "${dst#"$TARGET"/}"
    ok "wrote ${dst#"$TARGET"/}"
  fi
}

step "Scaffolding the Karpathy LLM Wiki in $TARGET"

# 1. canonical folders (7 LLM-curated types + raw)
mkdir -p "$TARGET"/wiki/{entities,concepts,synthesis,sources,queries,comparisons} \
         "$TARGET"/raw/{sources,assets}
for d in entities concepts synthesis sources queries comparisons; do
  [ -e "$TARGET/wiki/$d/.gitkeep" ] || touch "$TARGET/wiki/$d/.gitkeep"
done
[ -e "$TARGET/raw/assets/.gitkeep" ] || touch "$TARGET/raw/assets/.gitkeep"
ok "created wiki/{entities,concepts,synthesis,sources,queries,comparisons} + raw/{sources,assets}"

# 2. schema + special files (non-destructive)
README_DEST="$TARGET/README.md"
if [ "$ADOPT" -eq 1 ] && [ -e "$README_DEST" ] && ! cmp -s "$TPL/README.md" "$README_DEST"; then
  README_DEST="$TARGET/.llm-wiki/README.md"
fi
copy "$TPL/README.md"          "$README_DEST"
copy "$TPL/KARPATHY.md"        "$TARGET/KARPATHY.md"
copy "$TPL/wiki/index.md"      "$TARGET/wiki/index.md"
copy "$TPL/wiki/log.md"        "$TARGET/wiki/log.md"
copy "$TPL/wiki/overview.md"   "$TARGET/wiki/overview.md"
copy "$TPL/raw/README.md"      "$TARGET/raw/README.md"

# 3. make the schema self-activating: point the project's CLAUDE.md at KARPATHY.md
CLAUDE="$TARGET/CLAUDE.md"
PTR='@KARPATHY.md'
if [ -f "$CLAUDE" ]; then
  if grep -q "$PTR" "$CLAUDE" 2>/dev/null; then
    ok "CLAUDE.md already imports @KARPATHY.md"
  else
    printf '\n<!-- LLM Wiki schema (read before ingest/query/lint) -->\n%s\n' "$PTR" >> "$CLAUDE"
    ok "appended @KARPATHY.md pointer to existing CLAUDE.md (non-destructive)"
  fi
else
  printf '# %s\n\n<!-- LLM Wiki schema (read before ingest/query/lint) -->\n%s\n' \
    "$(basename "$TARGET")" "$PTR" > "$CLAUDE"
  ok "created CLAUDE.md importing @KARPATHY.md"
fi

# …and the project's AGENTS.md at it for Codex (shared helper: same marker as update.sh).
ensure_codex_pointer "$TARGET"
case "$CODEX_PTR_ACTION" in
  present)  ok "AGENTS.md already points Codex at KARPATHY.md" ;;
  appended) ok "appended KARPATHY.md instruction to existing AGENTS.md (non-destructive)" ;;
  *)        ok "created AGENTS.md pointing Codex at KARPATHY.md" ;;
esac

# 4. adopt: audit existing markdown (don't move anything — propose, human confirms)
if [ "$ADOPT" -eq 1 ]; then
  step "Adopt audit (non-destructive — nothing moved)"
  info "$EXISTING_MD existing markdown file(s) outside wiki/ + raw/."
  warn "Migration is deliberate, not automatic: ask the LLM to read KARPATHY.md, then"
  warn "  ingest external material into raw/sources/ and compile curated wiki/ pages."
  warn "  Existing docs you actively edit can stay where they are (or move by hand)."
fi

step "Done"
README_REL="${README_DEST#"$TARGET"/}"
ok "Wiki ready. Start with $README_REL (how-to) and KARPATHY.md (schema); drop a source in raw/sources/ and ask the LLM to ingest it."
