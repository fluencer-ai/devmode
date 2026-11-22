# Changelog

## 2.0.0 (2026-11-20): lean by default

devmode v2 goes global without taxing every message. The process is unchanged;
what changed is how much of it the model has to carry on every turn.

### Cost per turn (descriptions the host lists every message)

| Host | v1 | v2 lean | How v2 gets there |
|---|---|---|---|
| Claude Code | ~6,200 tokens (43 skills + command + orchestrator) | ~110 tokens | leaves hidden; only `/devmode` and `devmode-orchestrator` listed |
| Codex | ~6,000 tokens (43 skill links + launcher) | ~105 tokens | only the `devmode` launcher and the `devmode-orchestrator` agent listed |
| Antigravity / Cursor | (not supported) | ~50 tokens | only the router skill listed |

Measured with `./setup --report` against a scratch HOME (4 chars ≈ 1 token).

### Added

- **`./setup`** (`scripts/devmode_setup.py`): global install for Claude Code,
  Codex, Antigravity, and Cursor. Creates `~/.devmode/` (links to the repo,
  skills, agents, references), links devmode into each host's user folders,
  and remembers the mode per host. Lean by default; `--full` adds the role
  agents (Claude) or every skill (other hosts). `--dry-run`, `--check`,
  `--report`, `--uninstall`. It only creates links into the repo and never
  overwrites a file or a foreign link.
- **Memory** (`scripts/memory.py`): what the orchestrator learns about the
  person and the project, in append-only JSONL. Project memory in
  `.beads/memories.jsonl` (created by the installer, mirrored to
  `bd remember` when Beads is live); global memory in
  `~/.devmode/memories.jsonl`. `forget` writes a tombstone and `--supersedes`
  replaces an entry, so history is kept. Secret-looking text is refused. The
  SessionStart hook (Claude and Codex) primes at most 8 lines (headers included) once per session, and only runs
  devmode's own `memory.py`.
- **Skill index** (`references/skill-index.md`, built by
  `scripts/build_skill_index.py`): the one-page map the orchestrator consults
  before reading a skill by path. The audit fails when it is stale.
- Installer flag **`--codex-full`**: link every skill into `.agents/skills`
  for Codex (kept across updates in `.devmode/codex-skills`).
- Orchestrator rules for **token economy**: brief subagents with pointers and a
  done-criterion, ask for conclusions only, use a cheaper model for read-only
  lanes, keep gates short, never inject text into every message.

### Changed

- **43 → 32 skills, no rule dropped.** Eleven overlapping skills were fused
  into sibling files of the skill that owns the case:

  | v1 skill | now |
  |---|---|
  | `architecture-boundaries` | `functional-core-imperative-shell/system-boundaries.md` |
  | `divergent-ideation` | `design-critique/divergent-ideation.md` |
  | `testing-principles` | `tdd/testing-principles.md` |
  | `confidence-check` | `verification-before-completion/confidence-check.md` |
  | `browser-testing` | `feedback-loops/browser-testing.md` |
  | `delegate-to-cli` | `subagent-driven-development/external-cli.md` |
  | `ux-design` | `frontend-ui-engineering/ux-design.md` |
  | `accessibility` | `frontend-ui-engineering/accessibility.md` |
  | `ci-cd-automation` | `shipping/ci-cd.md` |
  | `doc-contracts` | `documentation/doc-contracts.md` |
  | `source-of-truth` | `context-engineering/source-of-truth.md` |

- Every leaf skill has `disable-model-invocation: true` and a description of
  at most 300 characters (both enforced by the audit). You can still run any
  skill as `/<name>`.
- Skills absorbed newer upstream material (grilling, domain modeling, deep
  modules and design-it-twice, diagnosis loop, review smells, handoff and
  phase boundaries, writing for agents, retro, PR craft). New in v2:
  `write-prd/tickets.md` (slice an approved PRD into blocking-ordered
  tracer-bullet tickets, wide refactors as expand–contract),
  `grill-me/wayfinding.md` (chart an effort bigger than one session as a map
  of decision tickets), a check-before-you-grill rule in `grill-me` (already
  built? ruled out before? reproduce the bug first), and a guided script for
  launch steps only a human can do in `shipping`. Credits in `ATTRIBUTION.md`.
- `prototyping`: a finished spike moves off `main` to a `prototype/<name>`
  branch linked from its issue or ADR, instead of being deleted, so the
  evidence behind the decision stays one checkout away.
- Codex global install also links the `devmode-orchestrator` agent into
  `~/.codex/agents`. `./setup` records the links it made and removes only
  those (or links carrying devmode's own names); an unreadable state file
  stops it rather than being overwritten.
- The orchestrator loads skills per phase, by path, in this order:
  `.claude/skills/`, the base `skills/`, then `~/.devmode/skills/`. Role agents
  fall back to a general-purpose agent that reads the role file.
- Codex projects get only the `devmode` launcher in `.agents/skills` by default.
- The `/devmode` command and the orchestrator have one-line descriptions.

### Fixed (2026-11-21 audit)

- The installer's closing summary no longer claims "base skill links" for
  Codex on a default (lean) install; it reports leaf links only with
  `--codex-full`.
- Role agents now say how to open a `skills/<name>` reference (the leaves are
  hidden from the listing): by path, from the project, the base, or the global
  install. The project `AGENTS.md` / `CLAUDE.md` templates say the same instead
  of "Codex discovers them through `.agents/skills/`".
- `/devmode start`, `adopt`, `update` and `wiki` share one guard: work from the
  devmode base (the current directory, else `~/.devmode/repo`), so they run
  from any folder after a global install. The memory fallback follows it.
- The Codex launcher names where `skill-index.md` lives in each install.
- `argument-hint` lists `plan <objective>`; README credits name the sibling
  files that replaced the fused skills.

### Style (2026-11-22)

- No em dashes in the pack: docs, skills, agents, templates, scripts and their
  messages use a colon, comma, semicolon or parentheses instead.
  `scripts/audit_skills.py` now fails on any em dash, so it can't creep back.
  Installer checks still recognize project files written by older versions.

### Migration from v1

- **Projects:** run `/devmode update <folder>` (or
  `integrations/conductor-beads/update.sh <folder>`). It refreshes the managed
  skills, removes devmode's own copies of the 11 retired skills (a same-name
  skill you own is kept, with a warning), prunes devmode's own Codex leaf links
  unless the project chose `--codex-full`, and creates `.beads/memories.jsonl`
  when `conductor/` exists. Your memory file is never touched.
- **Global:** run `./setup --host auto` from the repo. A v1 `~/.devmode` that was
  a single symlink to the repo is converted into the v2 folder.
- References to a retired skill name now point to its sibling file; open the
  table above to find it.
