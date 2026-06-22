#!/usr/bin/env bash
#
# llm-wiki update — refresh the SCHEMA/how-to docs of a deployed Karpathy LLM Wiki
# to the current base, WITHOUT touching the knowledge the LLM has built.
#
# Overwrites (schema, devmode-owned): KARPATHY.md, the deployed README.md, raw/README.md.
# NEVER touches (your knowledge): wiki/index.md, wiki/log.md, wiki/overview.md,
# wiki/entities|concepts|synthesis|sources|queries|comparisons/*, raw/sources/*, CLAUDE.md.
#
# Usage:  ./update.sh <wiki-dir>
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPL="$SCRIPT_DIR/templates"
c_green=$'\033[32m'; c_red=$'\033[31m'; c_blue=$'\033[34m'; c_off=$'\033[0m'
ok()   { printf "%s✓%s %s\n" "$c_green" "$c_off" "$*"; }
err()  { printf "%s✗%s %s\n" "$c_red" "$c_off" "$*" >&2; }
step() { printf "\n%s== %s ==%s\n" "$c_blue" "$*" "$c_off"; }

P="${1:-}"
[ -n "$P" ] || { err "usage: update.sh <wiki-dir>"; exit 1; }
[ -d "$P" ] || { err "no such directory: $P"; exit 1; }
P="$(cd "$P" && pwd)"
[ -f "$P/KARPATHY.md" ] || { err "$P has no KARPATHY.md — not an LLM Wiki. Run install.sh first."; exit 1; }

step "Updating the LLM Wiki schema in $P (knowledge left untouched)"
cp "$TPL/KARPATHY.md"    "$P/KARPATHY.md";    ok "KARPATHY.md (schema) refreshed"
cp "$TPL/README.md"      "$P/README.md";      ok "README.md (how-to) refreshed"
[ -d "$P/raw" ] && { cp "$TPL/raw/README.md" "$P/raw/README.md"; ok "raw/README.md refreshed"; }

step "Done — schema updated; your wiki/ knowledge + raw/sources untouched"
