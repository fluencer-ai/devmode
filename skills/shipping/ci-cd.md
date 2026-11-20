# CI/CD and automation

Read this when setting up or improving CI, or when checks only run by hand (and so
get skipped). A check that relies on a human remembering to run it will eventually
be skipped. CI makes the `feedback-loops` automatic and non-optional: every push
runs the full gate ladder and reports back fast, so mistakes surface at the PR,
not in production.

## The pipeline as a gate ladder

Run cheapest-first, fail fast (mirrors the verification ladder in
`feedback-loops`):

1. **Build / compile** — exit 0.
2. **Types** — type-checker clean.
3. **Lint / format** — clean.
4. **Tests** — the suite green; cover contract/edges/invariants.
5. **Security** — dependency audit triage, secret scan (`security-hardening`).
6. **Budgets** — perf budgets, bundle size (`performance-optimization`).

Keep it **fast** (cache deps, parallelize, run only what's affected where
possible) — a slow pipeline gets bypassed, which defeats the purpose.

## No blind coverage gate

devmode rejects a **blind coverage percentage** as a pass/fail gate (it pushes
testing implementation details and over-mocking — see `testing-principles.md` in `tdd`). So
in CI:

- **Gate on behavior**, not on a coverage number: build/types/lint/tests-green,
  acceptance-criteria coverage, and the **ratchet** (pre-existing tests must stay
  green so a trivial new test can't mask a regression).
- Track coverage as a *reported diagnostic* if you like — but don't fail the
  build solely because a percentage dipped.
- The review panel (`code-review`) is for *judgment*; the pipeline is for the
  *machine-checkable* gates.

## Build and deploy discipline

- **One source of truth for build/deploy steps** — scripted, reproducible, not a
  README of manual commands.
- **Branch protection:** the gate must pass before merge; protected branches
  can't be force-pushed (the guardrails hook backs this locally too).
- **Deploy safely:** staged rollout where possible, health checks, an automated
  **rollback** path (the release side is `SKILL.md`).
- **Evidence:** CI produces the artifacts/logs that make a result trustworthy
  (`verification-before-completion`).

## Process

1. Identify the checks that already exist locally; automate exactly those first.
2. Add the gate ladder to CI (e.g. GitHub Actions), cheapest-first, fail-fast.
3. Make it fast (cache, parallelize, affected-only).
4. Wire branch protection so the gate is non-optional.
5. Add deploy + rollback only once the gate is trustworthy.

## Red flags

- A coverage-% gate as the primary merge blocker (against the base).
- A pipeline so slow people merge around it.
- Deploy steps that live only in someone's head / a manual checklist.
- No rollback path.
- Secrets in CI logs or committed workflow files.
