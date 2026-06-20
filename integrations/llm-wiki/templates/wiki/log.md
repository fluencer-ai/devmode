# Wiki log

> Append-only, chronological record of every operation (ingest, saved query, lint,
> refactor). One entry each: `## [YYYY-MM-DD] <op> | <title>`. Parse with
> `grep "^## \[" wiki/log.md | tail -10`. (No frontmatter on this file.)

## [SCAFFOLD] bootstrap | LLM Wiki initialized
Canonical Karpathy LLM-Wiki scaffolded (pure markdown): raw/{sources,assets} +
wiki/{entities,concepts,synthesis,sources,queries,comparisons} + index/log/overview.
Schema in KARPATHY.md. Drop external material in raw/sources/ and ask the LLM to
ingest it.
