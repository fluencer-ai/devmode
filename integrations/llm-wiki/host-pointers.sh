# shellcheck shell=bash
#
# Shared host-instruction pointers for the Karpathy LLM Wiki.
#
# Sourced by install.sh and update.sh so the idempotency marker can never drift
# between them — a drifted marker would silently append a SECOND pointer to a
# wiki the installer had already wired up.
#
# Claude Code reads CLAUDE.md and supports the `@file` import syntax; Codex reads
# AGENTS.md and does NOT, so it gets the same instruction in prose.

WIKI_PTR_MARKER='<!-- LLM Wiki schema (read before ingest/query/lint) -->'
WIKI_CODEX_PTR='Before ingesting, querying, or linting this wiki, read `KARPATHY.md` in full and follow it.'

# ensure_codex_pointer <target-dir>
#
# Point Codex at the schema, non-destructively and idempotently: an existing
# project AGENTS.md stays the host and gains exactly one appended pointer.
# Sets CODEX_PTR_ACTION to created | appended | present.
ensure_codex_pointer() {
  local target="$1" agents="$1/AGENTS.md"
  if [ ! -f "$agents" ]; then
    printf '# %s\n\n%s\n%s\n' \
      "$(basename "$target")" "$WIKI_PTR_MARKER" "$WIKI_CODEX_PTR" > "$agents"
    CODEX_PTR_ACTION=created
  elif grep -Fq "$WIKI_PTR_MARKER" "$agents" 2>/dev/null; then
    CODEX_PTR_ACTION=present
  else
    printf '\n%s\n%s\n' "$WIKI_PTR_MARKER" "$WIKI_CODEX_PTR" >> "$agents"
    CODEX_PTR_ACTION=appended
  fi
}
