# Attribution

devmode's core process is original, but several skills and enhancements were
**adapted** from third-party open-source projects after an evaluation pass. We
reframed each in the devmode voice and wired it to devmode's existing skills —
these are not verbatim copies. Credit and licenses below.

All sources marked MIT permit reuse and modification with attribution; this file
provides it. Where a source is not OSI-licensed, only *ideas/patterns* were
reused (no files copied), as noted.

| devmode artifact | Adapted from | Project | License |
|------------------|--------------|---------|---------|
| `skills/systematic-debugging` | `systematic-debugging` | [obra/superpowers](https://github.com/obra/superpowers) | MIT © Jesse Vincent |
| `skills/verification-before-completion` | `verification-before-completion` | obra/superpowers | MIT |
| `skills/subagent-driven-development` | `subagent-driven-development` (+ delegation discipline from cowwoc/cat) | obra/superpowers; cowwoc/cat | MIT; source-available (ideas only) |
| `skills/grill-me` (fault taxonomy, information-gain) | `clarify` | [ryanthedev/code-foundations](https://github.com/ryanthedev/code-foundations) | MIT |
| `skills/design-patterns` | `gof-design-patterns` | ryanthedev/code-foundations | MIT |
| `skills/architecture-boundaries` | `ca-architecture-boundaries` | ryanthedev/code-foundations | MIT |
| `.agents/complexity-reviewer` (prover/verifier, Done-When evidence) | `post-gate-agent` | ryanthedev/code-foundations | MIT |
| `skills/testing-principles` (anti-patterns) | `test-driven-development/testing-anti-patterns` | obra/superpowers | MIT |
| `skills/testing-principles` (AC↔test traceability), `skills/feedback-loops` (gate ladder, ratchet) | `df-ac-coverage`, `commands/df/verify` | [saidwafiq/deepflow](https://github.com/saidwafiq/deepflow) | MIT |
| `skills/feedback-loops` (gate taxonomy + the decision-coverage gate), `skills/testing-principles` (the edge-coverage probe — per-edge covered/dismissed/backstop/unresolved verdict), `skills/security-hardening` (the *vet-before-you-add* package-legitimacy / slopsquat awareness) | `references/gates` + the gate suite (decision-coverage, edge-coverage, package-legitimacy) | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) → now [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) | MIT |
| `skills/authoring-skills` | `writing-skills` + `skill-judge` + `skill-auditor` | obra/superpowers; [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit); [glittercowboy/taches-cc-resources](https://github.com/glittercowboy/taches-cc-resources) | MIT |
| `skills/delegate-to-cli` | `codex` / `gemini` skills | softaworks/agent-toolkit | MIT |
| `skills/code-review` | `requesting-code-review` + `receiving-code-review` (+ panel lanes from claude-conductor) | obra/superpowers; rbarcante/claude-conductor | MIT; Apache-2.0 |
| `.agents/tdd-implementer` (evidence-gated handoff), `skills/verification-before-completion` (evidence packs), `skills/testing-principles` ("not observed ≠ absent") | `worker-report.v1`, evidence scripts, unknown-data contract | [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness) | MIT |
| `integrations/.../hooks/guardrails.py` (+ test) — deterministic PreToolUse gates-as-code | R-rule guardrail engine (`go/internal/guardrail`) — *patterns only, not the Go binary* | Chachamaru127/claude-code-harness | MIT |
| Domain skills: `frontend-ui-engineering`, `api-design`, `security-hardening`, `performance-optimization`, `browser-testing`, `ci-cd-automation`, `documentation`, `git-workflow`, `migration`, `shipping`, `context-engineering`, `source-of-truth` | the corresponding `agent-skills` skills (generalized off their web stack; coverage-gate reconciled to devmode's base) | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | MIT |
| `skills/accessibility`, `skills/ux-design` | authored for devmode; a11y from `references/accessibility-checklist.md` (agent-skills) | addyosmani/agent-skills (a11y ref) + devmode-original (ux-design) | MIT |
| `skills/ux-design` (the **2:1 proximity ratio** — within-group spacing ≤ half the between-group spacing, making the qualitative proximity rule mechanically checkable) | the DESIGN-LANGUAGE proximity rule (concept only — none of the React/Tailwind/Vite component library, JSON tokens, Framer-Motion "seeds" engine, brand skins, or `npx` installer) | [bitjaru/styleseed](https://github.com/bitjaru/styleseed) | MIT © 2026 StyleSeed Contributors |
| `scripts/audit_skills.py` — description-overlap detector + trigger-word lint | `scripts/detect_dupes.sh` (Jaccard) + `scripts/lint.sh` (trigger/length) | [khendzel/skills-janitor](https://github.com/khendzel/skills-janitor) | MIT |
| `skills/discovery` — codebase reverse-engineering for `/devmode adopt` | Scout/Soul/Detective/Architect prompt pipeline + 🟢/🟡/🔴 confidence scale | [sandeco/reversa](https://github.com/sandeco/reversa) | MIT |
| `skills/doc-contracts` — hierarchical AGENTS.md doc-contract tree (pre-edit traversal + post-edit doc pass) | the `AGENTS.md` framework file | [agent0ai/dox](https://github.com/agent0ai/dox) | MIT |
| `skills/prototyping` — throwaway spike → capture → delete; `skills/context-engineering` (handoff: reference-don't-duplicate, suggested-skills, redact, temp-dir) | `prototype` + `handoff` skills | [mattpocock/skills](https://github.com/mattpocock/skills) | MIT © Matt Pocock |
| `/devmode do` — the plain-English task-router mode (Route→…→Deliver, evidence-gated) in `commands/devmode.md` | the `/do` command | [notque/vexjoy-agent](https://github.com/notque/vexjoy-agent) | MIT |
| `integrations/.../hooks/session_resume.py` — SessionStart warm-resume hook | the SessionStart lifecycle-hook pattern | [notque/claude-code-starter-kit](https://github.com/notque/claude-code-starter-kit) | MIT |
| `integrations/llm-wiki/` — the `/devmode wiki` module (LLM-maintained markdown knowledge base: 3 layers, 7 page types, ingest/query/lint) | the *LLM Wiki* pattern (concept only — no app/code) | [Andrej Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | gist (concept) |
| `skills/minimal-code` + `/devmode lean` — the lazy-senior-dev minimalism ladder, safety floor, intensity levels, deliberate-simplification comment, audit/review lenses | the `ponytail` skill (concept/prose only — none of its Node hooks or multi-agent packaging) | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | MIT © Dietrich Gebert |
| `skills/visual-explainers` | — devmode-original — (the `visualize`/`show_widget` usage is environment-specific; the legibility/theming/a11y rules are tool-agnostic) | (none) | — |
| `skills/frontend-ui-engineering` (brief-inference, design dials, concrete AI-tell bans, consistency locks, motivated motion + reduced-motion, mechanical pre-flight, image-first prototyping, audit-first redesign) + `skills/verification-before-completion` (output-completeness: no `// …` truncation; count + pause cleanly) | the `taste-skill` / `redesign-skill` / `output-skill` skills | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | MIT |
| `skills/code-review` (immutable gate-independence — the implementer never self-certifies a critical quality/security gate) + `skills/minimal-code` (search-first / reuse-before-create) | the vNext gate contract + the "Pattern Discovery Protocol" | [bybren-llc/safe-agentic-workflow](https://github.com/bybren-llc/safe-agentic-workflow) | MIT © J. Scott Graham / ByBren LLC |
| `skills/discovery` (the **readiness read** — test-safety-net + operational readiness → a recommended first move) + `skills/security-hardening` (the *scan-before-you-share* secrets reflex) | the pre-scaffold `genome` analysis + the `validate` credential-exposure gate (concepts only — none of the WASM kernel / witness-signing / multi-host infra) | [ruvnet/agent-harness-generator](https://github.com/ruvnet/agent-harness-generator) (MetaHarness) | MIT |
| `skills/verification-before-completion` (declare-and-confirm the task's concrete deliverables before "done") | the task-contract `requiredArtifacts`/`expectedOutputs` gate (concept only — none of the MCP server / runtime / tree-sitter / replay engine) | [vinilana/dotcontext](https://github.com/vinilana/dotcontext) | MIT |
| `skills/grill-me` + `skills/design-critique` (perspective-guided, cite-everything external grounding: diverse personas → grounded multi-turn questioning → surface unknown-unknowns — folded into existing skills, **no** new `/devmode research` command) | STORM / Co-STORM's methodology (concept only — none of the dspy/retriever app) | [stanford-oval/storm](https://github.com/stanford-oval/storm) | MIT |
| `skills/code-review` ("comprehension debt", maker/checker), `skills/subagent-driven-development` (worktree isolation) | the *loop-engineering* essays | [Osmani](https://addyosmani.com/blog/loop-engineering/) · [Autocomplete](https://medium.com/autocomplete-real-world-ai/wtf-is-a-agentic-coding-loop-and-how-to-build-one-58eedb7cbcae) · [Greyling](https://cobusgreyling.medium.com/loop-engineering-62926dd6991c) | essays (concepts) |
| `skills/code-review` (the *green-by-deletion* tripwire — a fix that disables/comments the very test it was meant to satisfy is an automatic finding) | the `loop-verifier` "no-cheating" gate (concept only — none of the npm CLIs / MCP server / scheduler / readiness-score) | [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | MIT |
| `skills/self-scorecard`, `scripts/scorecard.py`, `scripts/dashboard.py` | — devmode-original — | (none) | — |
| `skills/goal-brief`, `scripts/goal_brief.py` | — devmode-original — (emits Claude Code `/goal` & `/plan` commands; the commands are referenced, not vendored) | (none) | — |
| `integrations/conductor-beads` (STATE.md memory pattern) | `templates/state.md` | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) → now [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) | MIT |
| `.agents/code-quality-analyzer`, `.agents/security-scanner`, `.agents/test-coverage-analyzer` (parallel review panel) | `agents/code-quality-analyzer`, `agents/security-scanner`, `agents/test-coverage-analyzer` | [rbarcante/claude-conductor](https://github.com/rbarcante/claude-conductor) | Apache-2.0 |
| `integrations/.../templates/track/decisions.md` (ADR), INTEGRATION WARM START handoff | `protocols/decision-capture`, `commands/implement` | rbarcante/claude-conductor | Apache-2.0 |
| `skills/grill-me` (structured A/B/C/D/E choices) | `templates/askuserquestion-patterns` | rbarcante/claude-conductor | Apache-2.0 |
| `skills/impact-analysis`, `skills/ubiquitous-language` (why-per-edge) | `data-structure-protocol` (`dsp-cli` impact ops) | [k-kolomeitsev/data-structure-protocol](https://github.com/k-kolomeitsev/data-structure-protocol) | Apache-2.0 |
| `skills/confidence-check` | `confidence-check` | [SuperClaude-Org/SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) | MIT |
| `skills/design-critique` | `spec-panel` / `business-panel-experts` | SuperClaude-Org/SuperClaude_Framework | MIT |
| `.agents/*` ("Will / Will not" boundary sections) | agent frontmatter convention | SuperClaude-Org/SuperClaude_Framework | MIT |

## Notes

- **Apache-2.0 sources** (`rbarcante/claude-conductor`,
  `k-kolomeitsev/data-structure-protocol`) permit reuse and modification; this
  file preserves the required attribution. We adapted *patterns and prose*
  (review-agent roles, ADR/decision-capture, impact-analysis technique) — no
  source code was copied verbatim.
- **cowwoc/cat** is under a source-available *commercial* license (CAT Source-
  Available License v1.0), not OSI open-source. We reused only *concepts* (the
  subagent-delegation discipline), not files; individual/derivative use is
  permitted under its Indie terms. If you ship a commercial team product, review
  its license.
- **get-shit-done** (by TÂCHES) is MIT but **archived** (2026-06-26); the
  maintained successor is **`open-gsd/gsd-core`** (MIT). We mined prose patterns
  only — the gate taxonomy + STATE.md memory from the original, and (from gsd-core)
  the **edge-coverage probe** (`testing-principles`), the **decision-coverage gate**
  (`feedback-loops`), and the **package-legitimacy / slopsquat awareness**
  (`security-hardening`, as a one-line *practice* — none of gsd-core's external
  `slopcheck` tool or registry calls); we did not depend on its code/engine. ("GSD
  Redux" was the early provisional name, since renamed to gsd-core.)
- **NguyenSiTrung/Conductor-Beads** (Apache-2.0) is the upstream toolkit the
  integration *mounts*: `install.sh --with-conductor` clones it at install time
  into the target project. **No Conductor-Beads code is vendored in this repo**;
  the integration's own templates/adapters were written for devmode (with the
  ADR/panel patterns adapted from `rbarcante/claude-conductor`, attributed above).
- The original viral skill that inspired devmode's `grill-me` traces to
  obra/superpowers' `brainstorming`; both descend from the same lineage.
- **mattpocock/skills** (MIT © Matt Pocock) is devmode's **sibling**: both were
  distilled from Matt Pocock's *"Claude Code for real engineers"* talk and share
  the same thesis and four failure modes. We adapted two skills (`prototype`,
  `handoff`) and credit the shared lineage; devmode generalized the thesis into a
  tool-agnostic process rather than a TypeScript/web skill set.
- The **loop-engineering essays** (Osmani; Autocomplete/Real-World-AI; Greyling)
  are prose, not code — we reused *concepts* (maker/checker split, comprehension
  debt, worktree isolation, "design loops, don't prompt turn-by-turn"); they
  validated devmode's existing architecture more than they changed it. The
  **`cobusgreyling/loop-engineering`** *repo* (MIT) turns that essay into npm CLIs +
  an MCP server + a scheduler — all of which devmode refuses (app/runtime,
  human-in-the-loop by design); the one markdown-shaped delta its `loop-verifier`
  added beyond the essay is the **green-by-deletion** tripwire now in `code-review`.
  (Its Loop Readiness Score is a 0–100 rubric already covered by `self-scorecard`'s
  0–10; its `loop-constraints.md` is enforced harder by devmode's deterministic hooks.)
- **Evaluated and absorbed nothing** (recorded so they aren't re-litigated):
  **`safishamsi/graphify`** (MIT) — a tree-sitter parser + NetworkX/Neo4j graph
  engine + MCP server; the graph-as-markdown methodology is already devmode's
  (`ubiquitous-language` dep-map, `impact-analysis` blast-radius + why-per-edge,
  parser-free `discovery`, the `llm-wiki` [[wikilink]] graph), and the parser/graph-DB
  is the class devmode refuses. **`affaan-m/ecc`** (MIT) — an app-heavy sibling
  (continuous-learning JSONL runtime, a Node security scanner, a council panel);
  every novel piece is an app/DB/runtime and every markdown idea is already covered
  (`design-critique`, `minimal-code`, `discovery`, the supersede-the-ADR spine,
  `verification-before-completion`).
- **Andrej Karpathy's *LLM Wiki* gist** is the concept behind the
  `integrations/llm-wiki/` module. We implemented it as **pure, app-free
  markdown** (3 layers, 7 canonical page types, ingest/query/lint) — deliberately
  **not** tied to any specific wiki app or database; no third-party code was used,
  only the published pattern.
- **DietrichGebert/ponytail** (MIT) is the source of the `minimal-code` skill and
  the `/devmode lean` mode — its "lazy senior dev" minimalism ladder, the
  lazy-not-negligent safety floor, the intensity levels, the deliberate-
  simplification comment, and the benchmark evidence. We absorbed the **concept**
  as a single markdown skill; we did **not** port its Node lifecycle hooks, MCP
  server, or 14-agent platform packaging (devmode is markdown + Python-stdlib).
- **Leonxlnx/taste-skill** (MIT) is a rich frontend "anti-slop" skill set. A second,
  deeper pass folded its craft into the existing `frontend-ui-engineering` skill
  (deepening the module, not adding one): the brief-inference declaration, the
  deliberate design dials (variance / motion / density), the concrete AI-tell bans,
  the consistency locks (one accent / radius / theme), motivated-motion +
  reduced-motion, the mechanical pre-flight, the image-first "prototype the look",
  and the audit-first redesign protocol. Its `output-skill` (no `// …` truncation;
  count deliverables; pause cleanly under a token limit) became a rule in
  `verification-before-completion`. Concept/prose only — no JS/CLI code reused, and
  taste-skill's Tailwind/React-specific class names are illustrative, not prescribed
  (devmode stays tool-agnostic).
- **bybren-llc/safe-agentic-workflow** (MIT) is a SAFe multi-agent team harness.
  Its core safety ideas (blocking gates, evidence-over-trust, independent review,
  stop-the-line before work) already exist in devmode; we absorbed the two sharper
  framings — **immutable gate independence** (a critical quality/security gate is
  never self-certified by the implementer) in `code-review`, and the **Pattern
  Discovery Protocol** (search the repo for prior art / reuse before creating) as a
  rung in `minimal-code`. We did **not** adopt its 11 SAFe roles, 24 commands, or
  tmux "dark factory" (devmode stays lean).
- **ruvnet/agent-harness-generator** (MetaHarness, MIT) is a *factory* for branded
  agent harnesses — overwhelmingly **infrastructure devmode deliberately rejects**
  (a Rust/WASM kernel, Ed25519 witness-signing, SBOM/SLSA provenance, multi-host
  adapters, a model router, "Darwin" self-mutation, a marketplace). We absorbed only
  two **process** ideas that fit devmode's markdown, app-free base: its pre-scaffold
  `genome` readiness analysis became the qualitative **readiness read** in
  `discovery` (test-safety-net + operational readiness → a recommended first move,
  tagged 🟢🟡🔴 — *not* its 0–100 score, which devmode rejects as gameable), and its
  `validate` credential-exposure gate reinforced the **scan-before-you-share**
  secrets reflex in `security-hardening` (kept as a *practice* — the `guardrails.py`
  hook already denies writes to secret paths; a fuzzy content-scanner in the hook
  would trade false positives for little real gain). We took none of the kernel,
  signing, provenance, host adapters, router, or self-evolving machinery.
- **vinilana/dotcontext** (MIT) is a TypeScript app (MCP server + CLI + runtime).
  Almost all of it — the declarative policy engine, the replay / failure-signature
  datasets, the tree-sitter/LSP semantic maps, the 17-tool bidirectional sync — is
  the *runtime* devmode deliberately refuses (markdown + Python-stdlib only). We
  absorbed exactly one markdown-shaped idea: its task contract's *declare-then-check
  the required deliverables* discipline, folded into `verification-before-completion`.
  No app/code reused.
- **stanford-oval/storm** (MIT) is Stanford OVAL's STORM / Co-STORM — a Python/dspy
  app that writes cited, Wikipedia-style reports via *perspective-guided question
  asking* (diverse personas → grounded multi-turn questioning → outline → cited
  synthesis; Co-STORM adds a moderator for *unknown unknowns*). devmode can't vendor
  the app, and an equivalent `deep-research` skill already exists, so we **did not**
  add a `/devmode research` command. We folded the *methodology* into `grill-me`
  (ground a knowledge gap with diverse, cited web investigation before guessing) and
  `design-critique` (a lens grounds with a citation, not a hunch) — mapped onto
  primitives devmode already has (subagent fan-out, evidence-over-assertion).

- **bitjaru/styleseed** (MIT © 2026 StyleSeed Contributors) is a "design engine +
  methodology" for AI coding tools — a hybrid of a substantive markdown knowledge
  base and a **web app** (48 React components, JSON design tokens, a Vite scaffold,
  a Framer-Motion "seeds" animation engine, 7 brand skins, 15 `/ss-*` slash-skills,
  an `npx` installer). We absorbed exactly one tool-agnostic, markdown-shaped idea:
  the **2:1 proximity ratio** (within-group spacing ≤ half the between-group
  spacing), folded into `ux-design` to make its existing qualitative proximity rule
  mechanically checkable — the ratio only, none of the web-flavored pixel form-ladder.
  We took **none** of the React/Tailwind component library, tokens, motion engine,
  skins, or installer (all app/runtime devmode refuses). Rejected as already-covered:
  the "10 coherence axes" table (a longer restatement of `frontend-ui-engineering`'s
  consistency locks, plus framework-specific values), an ordered "why does this look
  off?" diagnosis probe (its dimensions already live in `frontend-ui-engineering`'s
  tell table + pre-flight scan — a second overlapping checklist would be bloat), and
  `ss-score`'s weighted 0–100 visual rubric (collides with `self-scorecard`'s 0–10
  process scorecard and is keyed to Tailwind-specific deductions). Its single-accent
  / one-radius / one-theme locks, emoji-as-icons ban, all-states rule, contrast and
  reduced-motion rules are already at or below devmode's `frontend-ui-engineering` /
  `ux-design` / `accessibility` coverage.
- **Evaluated and absorbed nothing — context-labs/halo** (HALO / `halo-engine`, MIT
  by classification; the exact copyright string was unreadable — LICENSE/LICENSE.md
  returned 404 on GitHub — so treat the holder as unconfirmed): an **app + runtime +
  trace-parser**, precisely the class devmode refuses. It is a specialized LLM "RLM"
  agent runtime that ingests OpenTelemetry/OpenInference JSONL trace spans, explores
  them with a bundled toolkit (a Deno JS sandbox + ripgrep), and emits a findings
  report — shipped as a desktop app (`curl | sh`), a Typer CLI (`pip install
  halo-engine`), and a Python streaming API, depending on openai / openai-agents /
  pydantic / numpy / pandas. The OTel/OpenInference JSONL schema + `setup_tracing()`
  is a data format + a vendored instrumentation module (a parser/observability
  integration, not a document). Its one on-philosophy idea — the 5-step diagnose →
  verify → minimal-change → re-measure loop, and its `halo-loop` maxims ("treat
  engine output as evidence not a directive", "the tool can't see your repo — verify
  every path claim before editing", "make the minimal-blast-radius edit") — is fully
  covered already by `self-scorecard`, `verification-before-completion`,
  `systematic-debugging`, `impact-analysis`, `code-review`, `delegate-to-cli`, and
  `minimal-code`. Nothing markdown-shaped and net-new; honest skip.

If you are an author here and want a correction to this attribution, please open
an issue.
