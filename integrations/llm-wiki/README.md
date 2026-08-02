# llm-wiki — the Karpathy LLM Wiki module for devmode

An **opt-in devmode module** that deploys a persistent, LLM-maintained markdown
knowledge base — Andrej Karpathy's *LLM Wiki* pattern — into a project (new or
existing). The LLM stops being a forgetful RAG retriever and becomes a
**disciplined wiki maintainer**: each source is *integrated* into an interlinked
graph of markdown, so knowledge **compounds** instead of being re-derived per query.

> **Pure markdown. No app, no database, no server.** Browse it in any editor;
> Obsidian follows the `[[wikilinks]]`. Independent of devmode's code process —
> it's a sibling *knowledge* base, not part of the Align→Refactor phase machine.
>
> Concept: [Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## What it scaffolds

```
<project>/
├── README.md              ← human how-to (or .llm-wiki/README.md on adopt)
├── KARPATHY.md            ← the SCHEMA: how the wiki is structured + maintained
├── CLAUDE.md              ← imports @KARPATHY.md for Claude Code
├── AGENTS.md              ← tells Codex to read KARPATHY.md
├── raw/                   ← layer 1: immutable external sources (human drops, LLM reads)
│   ├── sources/   assets/
│   └── README.md
└── wiki/                  ← layer 2: the LLM-maintained knowledge graph
    ├── index.md           ← the catalog (read first on every query)
    ├── log.md             ← append-only operation log
    ├── overview.md        ← the global picture (page type 1 of 7)
    └── entities/ concepts/ synthesis/ sources/ queries/ comparisons/   (types 2-7)
```

## Use it

Via the devmode command (recommended):

```text
/devmode wiki start <path>     # scaffold a fresh wiki project at <path>
/devmode wiki adopt <folder>   # add the wiki to an existing project (non-destructive)
/devmode update wiki <folder>  # refresh a deployed wiki's schema to the current base
```

Or directly:

```bash
integrations/llm-wiki/install.sh /path/to/project            # fresh
integrations/llm-wiki/install.sh /path/to/existing --adopt   # existing (audits, moves nothing)
integrations/llm-wiki/update.sh  /path/to/wiki               # refresh schema, keep knowledge
```

The installer is **idempotent and non-destructive** — fresh mode refuses a
non-empty target, and `--adopt` preserves project-owned files, stores its human
how-to at `.llm-wiki/README.md` when a host README exists, *audits* the repo, and proposes a
migration rather than moving anything automatically (migration is deliberate: the
human curates, the LLM compiles).

**Both hosts get activated, neither gets overwritten.** Claude Code reads an
idempotent `@KARPATHY.md` import appended to `CLAUDE.md`; Codex has no `@import`
syntax, so it gets the equivalent instruction in prose in `AGENTS.md`. `update.sh`
refreshes the schema and *backfills* that Codex pointer on wikis deployed before it
existed — never touching `wiki/` knowledge or `raw/sources/`.

## The loop, once deployed

1. **Read the schema** — the agent reads `KARPATHY.md` at session start.
2. **Ingest** — drop external material in `raw/sources/`; ask the LLM to ingest it
   (it writes a `wiki/sources/` summary and updates every affected page).
3. **Query** — ask questions; the LLM reads `wiki/index.md` first, drills in,
   answers with citations, and offers to save valuable answers as pages.
4. **Lint** — periodically ask for a health check (contradictions, stale claims,
   orphans, missing cross-refs).

The 7 page types, the frontmatter spec, and the full operation rules live in the
deployed `KARPATHY.md`.

## Why a separate module (not core devmode)

devmode's core is a tool-agnostic *software-development* process. The LLM Wiki is a
*knowledge-management* methodology — adjacent, but distinct. Keeping it as an
opt-in layer (like the Conductor-Beads integration) keeps the core focused while
making the capability one command away.

> Concept adapted from Andrej Karpathy's *LLM Wiki* gist (MIT-spirit, credited).
> devmode generalized it into a tool-agnostic, app-free markdown module. See the
> root [`ATTRIBUTION.md`](../../ATTRIBUTION.md).
