#!/usr/bin/env bash
#
# llm-wiki update — refresh the SCHEMA/how-to docs of a deployed Karpathy LLM Wiki
# to the current base, WITHOUT touching the knowledge the LLM has built.
#
# Overwrites only files recorded as devmode-owned by the installer. KARPATHY.md
# is always schema-owned. Legacy installs are recognized by exact template match.
# NEVER touches (your knowledge): wiki/index.md, wiki/log.md, wiki/overview.md,
# wiki/entities|concepts|synthesis|sources|queries|comparisons/*, raw/sources/*, CLAUDE.md.
#
# Host instruction files are never overwritten, only APPENDED to: AGENTS.md gets
# the Codex pointer backfilled, because wikis deployed before Codex support have
# none and would leave KARPATHY.md invisible to Codex. CLAUDE.md needs no backfill
# (every install wrote its @KARPATHY.md import), so it stays untouched.
#
# Usage:  ./update.sh <wiki-dir>
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPL="$SCRIPT_DIR/templates"
# shellcheck source=host-pointers.sh
. "$SCRIPT_DIR/host-pointers.sh"
c_green=$'\033[32m'; c_red=$'\033[31m'; c_blue=$'\033[34m'; c_yellow=$'\033[33m'; c_off=$'\033[0m'
ok()   { printf "%s✓%s %s\n" "$c_green" "$c_off" "$*"; }
warn() { printf "%s!%s %s\n" "$c_yellow" "$c_off" "$*"; }
err()  { printf "%s✗%s %s\n" "$c_red" "$c_off" "$*" >&2; }
step() { printf "\n%s== %s ==%s\n" "$c_blue" "$*" "$c_off"; }

usage() {
  cat <<'USAGE'
Usage: update.sh <wiki-dir>

Refresh a deployed Karpathy LLM Wiki's schema/how-to docs to the current base.

  <wiki-dir>    the deployed wiki to refresh (must contain KARPATHY.md)
  -h, --help    show this help

Overwrites installer-owned docs only (KARPATHY.md, the deployed README, and an
installer-owned raw/README.md) and backfills the idempotent Codex pointer in
AGENTS.md. Never touches wiki/ pages, raw/sources/, or CLAUDE.md.
USAGE
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

P="${1:-}"
[ -n "$P" ] || { err "usage: update.sh <wiki-dir>  (see --help)"; exit 1; }
[ -d "$P" ] || { err "no such directory: $P"; exit 1; }
P="$(cd "$P" && pwd)"
[ -f "$P/KARPATHY.md" ] || { err "$P has no KARPATHY.md — not an LLM Wiki. Run install.sh first."; exit 1; }
if ! { [ -f "$P/.llm-wiki/managed-files" ] && \
       grep -Fqx 'KARPATHY.md' "$P/.llm-wiki/managed-files"; } && \
   ! grep -Fqx '# KARPATHY.md — the LLM Wiki schema for this project' "$P/KARPATHY.md"; then
  err "refusing to overwrite project-owned KARPATHY.md; it is not a recognized LLM Wiki schema"
  exit 1
fi

MANAGED_DIR="$P/.llm-wiki"
MANAGED_FILES="$MANAGED_DIR/managed-files"
mkdir -p "$MANAGED_DIR"
touch "$MANAGED_FILES"
is_managed() { grep -Fqx "$1" "$MANAGED_FILES" 2>/dev/null; }
mark_managed() { is_managed "$1" || printf '%s\n' "$1" >> "$MANAGED_FILES"; }
refresh_if_owned() { # refresh_if_owned <template> <relative-path>
  local src="$1" rel="$2" dst="$P/$2"
  if is_managed "$rel" || { [ -f "$dst" ] && cmp -s "$src" "$dst"; }; then
    cp "$src" "$dst"
    mark_managed "$rel"
    ok "$rel refreshed"
    return 0
  fi
  return 1
}

step "Updating the LLM Wiki schema in $P (knowledge left untouched)"
# The schema maps each page type to a wiki/<dir>/. Refreshing KARPATHY.md without
# the folders it names would tell the LLM to write into directories that only
# fresh installs have — so re-scaffold the canonical tree first (mkdir -p is a
# no-op on an existing wiki and never touches a page).
mkdir -p "$P"/wiki/{entities,concepts,synthesis,sources,queries,comparisons} "$P"/raw/{sources,assets}
cp "$TPL/KARPATHY.md" "$P/KARPATHY.md"; ok "KARPATHY.md (schema) refreshed"
mark_managed "KARPATHY.md"

if [ -f "$P/.llm-wiki/README.md" ] || is_managed ".llm-wiki/README.md"; then
  cp "$TPL/README.md" "$P/.llm-wiki/README.md"
  mark_managed ".llm-wiki/README.md"
  ok ".llm-wiki/README.md (how-to) refreshed"
elif ! refresh_if_owned "$TPL/README.md" "README.md"; then
  cp "$TPL/README.md" "$P/.llm-wiki/README.md"
  mark_managed ".llm-wiki/README.md"
  warn "kept project-owned README.md; wrote wiki how-to to .llm-wiki/README.md"
fi

if [ -d "$P/raw" ] && ! refresh_if_owned "$TPL/raw/README.md" "raw/README.md"; then
  warn "kept project-owned raw/README.md"
fi

# Backfill the Codex host pointer (same marker as install.sh, so this is a no-op
# on a wiki that already has it). Project-owned AGENTS.md content is preserved.
ensure_codex_pointer "$P"
case "$CODEX_PTR_ACTION" in
  present)  ok "AGENTS.md already points Codex at KARPATHY.md" ;;
  appended) ok "appended the Codex KARPATHY.md pointer to your AGENTS.md (non-destructive)" ;;
  *)        ok "created AGENTS.md pointing Codex at KARPATHY.md" ;;
esac

step "Done — schema updated; your wiki/ knowledge + raw/sources untouched"
