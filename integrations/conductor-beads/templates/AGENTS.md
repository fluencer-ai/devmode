# AGENTS.md -- Codex compatibility for devmode

This file is the Codex adapter for a devmode project. It must preserve the
Claude Code setup, not replace it.

## Source Of Truth

- The project's own instructions take precedence.
- `CLAUDE.md` or `CLAUDE.devmode.md` remains the canonical devmode manifest for
  the base process.
- `.claude/commands/devmode.md` remains the canonical guided command.
- `.agents/*.md` remain the canonical role-agent definitions.
- `.claude/agents/devmode-orchestrator.md` remains the canonical orchestrator
  definition.
- The Codex files in `.codex/` and `.agents/skills/devmode/` are compatibility
  adapters. If an adapter and its canonical source disagree, follow the
  canonical source and fix the adapter.

Before non-trivial work in this project, read the project instructions and the
devmode manifest. Before running the guided flow, invoke `/devmode` in Codex
Desktop or select `devmode` through `/skills` in CLI/IDE, then read
`.claude/commands/devmode.md`.

## Codex Surface Map

- Durable repo instructions: `AGENTS.md` or `AGENTS.devmode.md`.
- Base skills: Codex lists only the `devmode` launcher in `.agents/skills/`
  (lean, so the skill list stays one line). The launcher reads each leaf by
  path (`.claude/skills/<name>/SKILL.md`, index in
  `.claude/devmode/references/skill-index.md`). A project installed with
  `--codex-full` links every leaf instead.
- Guided front door: invoke `/devmode <args>` in Codex Desktop; in CLI/IDE,
  select the repo-shared `devmode` skill through `/skills`.
- Custom subagents: `.codex/agents/*.toml` adapts the existing role definitions
  for Codex subagents.
- Hooks: `.codex/hooks.json` runs `.codex/hooks/codex_hooks.py`. Codex project
  hooks only run after the project is trusted and the hook definitions are
  trusted in `/hooks`.
- Claude Code remains on the existing `.claude/` surface: do not remove,
  rewrite, or weaken those files while adding Codex support.

## Operating Contract

- Preserve user or project-owned files. Prefer additive pointers such as
  `CLAUDE.devmode.md` or `AGENTS.devmode.md` over flattening instructions into
  one file.
- Use the devmode loop from the manifest: Align, Language, Specify, Architect,
  Implement, Review, then Refactor as needed.
- For one bounded task, use the `do` lane from the devmode command instead of
  spinning up the full phase machine.
- For phase-driving guided work, delegate to the `devmode-orchestrator` custom
  agent instead of embodying the phase machine inline.
- No completion claim without fresh verification evidence that covers the
  changed behavior.

## Memory (every session, /devmode or not)

What the agent learns with the person lives in `.beads/memories.jsonl` (this
project) and `~/.devmode/memories.jsonl` (the person, every project):
append-only, never a secret (the script refuses one).

- **Start:** the SessionStart hook primes it. If nothing was primed, run
  `python3 .devmode/memory.py prime` and apply what it prints.
- **During:** when the person states a preference, makes a decision or corrects
  you, record one line at once:
  `python3 .devmode/memory.py add "<text>" --kind preference|decision|fact|correction`
  (add `--scope global` when it is about the person, not the project).
- **End:** before closing a conversation that settled something or left work
  open, record one `fact` line: what was agreed and what comes next.

## Gates And Overrides

When the devmode hooks are installed, Codex enforces the same gates as Claude
Code and exposes the same escape hatches. Each one is a conscious statement,
never a routine bypass:

- **`VERIFY-OK: <reason>`**: write it in your reply when the Stop verify gate
  fires after a rebuild/deploy/`.env` change that genuinely needs no end-to-end
  check.
- **`DEVMODE-OK: <reason>`**: write it in your reply when a phase-driving
  `/devmode` turn genuinely does not need the orchestrator.
- **`# DEVMODE-GUARDRAIL-OK`**: Codex has no interactive "ask", so the PreToolUse
  guardrail turns Claude's *ask* rules (destructive git, scoped `rm -rf`, reading
  a likely secret file) into a deny. **Ask the user first**, then re-run the
  command with that comment in it. Never add it pre-emptively: the deny is the
  confirmation prompt.

Rules that **deny** on both hosts (`sudo`, force-push, `--no-verify`, `rm -rf /`,
writes to `.git/`, `.env*`, `.ssh/`, `*.pem`) have no override. Do not route
around them; surface the reason to the user.

## Verification

After changing project code, run the verification command that covers the change
and report the actual evidence. After changing devmode itself, run the pack
audits from the devmode base repository.
