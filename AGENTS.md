# AGENTS.md -- Codex compatibility for devmode

This file is the Codex adapter for this repository. It must preserve the Claude
Code setup, not replace it.

## Source Of Truth

- `CLAUDE.md` remains the canonical devmode manifest: beliefs, workflow, usage
  rules, and project discipline.
- `.claude/commands/devmode.md` remains the canonical guided command.
- `.agents/*.md` remain the canonical role-agent definitions for the base pack.
- `.claude/agents/devmode-orchestrator.md` remains the canonical orchestrator
  definition.
- The Codex files in `.codex/` and `.agents/skills/devmode/` are compatibility
  adapters. If an adapter and its canonical source disagree, follow the
  canonical source and fix the adapter.

Before non-trivial work in this repo, read `CLAUDE.md`. Before running the
guided flow, invoke `/devmode` in Codex Desktop or select `devmode` through
`/skills` in CLI/IDE, then read `.claude/commands/devmode.md`.

## Codex Surface Map

- Durable repo instructions: `AGENTS.md` or `AGENTS.devmode.md`.
- Base skills: Codex discovers them through `.agents/skills/`.
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

- Keep the base repo clean. Experiments and smoke projects belong under
  `workspaces/`; bring back only proven learnings.
- Preserve user or project-owned files. For existing projects, prefer additive
  pointers such as `CLAUDE.devmode.md` or `AGENTS.devmode.md` over flattening
  instructions into one file.
- Use the devmode loop from `CLAUDE.md`: Align, Language, Specify, Architect,
  Implement, Review, then Refactor as needed.
- For one bounded task, use the `do` lane from the devmode command instead of
  spinning up the full phase machine.
- For phase-driving guided work, delegate to the `devmode-orchestrator` custom
  agent instead of embodying the phase machine inline.
- No completion claim without fresh verification evidence that covers the
  changed behavior.

## Gates And Overrides

The Codex hooks enforce the same gates as Claude Code and expose the same escape
hatches. Each one is a conscious statement, never a routine bypass:

- **`VERIFY-OK: <reason>`** — write it in your reply when the Stop verify gate
  fires after a rebuild/deploy/`.env` change that genuinely needs no end-to-end
  check.
- **`DEVMODE-OK: <reason>`** — write it in your reply when a phase-driving
  `/devmode` turn genuinely does not need the orchestrator.
- **`# DEVMODE-GUARDRAIL-OK`** — Codex has no interactive "ask", so the PreToolUse
  guardrail turns Claude's *ask* rules (destructive git, scoped `rm -rf`, reading
  a likely secret file) into a deny. **Ask the user first**, then re-run the
  command with that comment in it. Never add it pre-emptively — the deny is the
  confirmation prompt.

Rules that **deny** on both hosts (`sudo`, force-push, `--no-verify`, `rm -rf /`,
writes to `.git/`, `.env*`, `.ssh/`, `*.pem`) have no override. Do not route
around them; surface the reason to the user.

## Verification

After changing the pack, run:

```bash
python3 scripts/audit_skills.py
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 -m unittest discover -s integrations/conductor-beads/hooks -p 'test_*.py'
```
