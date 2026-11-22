---
name: shipping
description: >-
  Shipping: CI gate ladder, PR evidence, pre-launch checklist, staged rollout and
  rollback. Use when setting up or fixing CI, writing a pull request, or preparing
  to release, tag, or deploy to production.
disable-model-invocation: true
---

# Shipping and launch

Passing tests means the code is *PR-ready*. Shipping asks a different question:
will it survive contact with production, and can you undo it if not? "Works on my
machine / in CI" and "safe in front of users" are two different bars; this skill
is the second one.

Setting up or fixing the CI pipeline that gates every change? Read `ci-cd.md` in
this folder.

Absorbed: `ci-cd-automation` now lives here as `ci-cd.md`.

## The pull request

A PR body proves the change, it doesn't narrate it. Keep prose brief and use the
project's ubiquitous language.

- **Summary:** the smallest view that makes the point: a diff-sketch, call tree,
  file tree, or diagram, placed next to the line it supports.
- **Evidence, before and after:** show the state before the change and after it.
  A screenshot pair is best for a visual change; otherwise the exact test or
  command output that failed before and passes now.
- **Door:** call every change a **one-way door** (destructive or hard to reverse:
  a data migration, a deleted API, a published contract) or a **two-way door**
  (cheap to roll back). A one-way door gets the full checklist below and a named
  rollback or recovery path.
- **Blast radius:** what else this can break (consumers, layout, mobile, data).

## Pre-launch checklist

Before releasing, confirm (with evidence, not assumption:
`verification-before-completion`):

- **The gate passed**: build/types/lint/tests green in CI (`ci-cd.md`);
  acceptance criteria met.
- **Reviewed**: the `code-review` panel signed off; critical paths
  (auth/money/security) reviewed in full.
- **Config & secrets**: prod config set, secrets present and *not* in the
  bundle/logs (`security-hardening`).
- **Migrations ready**: schema changes are expand-contract and reversible
  (`migration`); backups exist.
- **Observability**: logs, metrics, and alerts for the new path are in place, or
  you're flying blind.
- **Rollback plan**: you know *exactly* how to undo this (flag flip, redeploy
  previous, revert), and it's been thought through *before* you ship.

## Steps only a human can do

Some launch steps can't be automated by the agent: a third-party dashboard, a
credential to create, a CI secret to set, a one-off cutover. Don't re-explain
them in chat each time. Write a small guided script that walks the human through
them stage by stage: it opens each URL, says exactly what to click and copy,
reads secrets with hidden input, writes each value where it belongs (the env
file, the CI secret store), confirms before anything irreversible, and shows how
many stages remain. First read the repo (the env example file, the CI workflow's
secret references) for every value the script must produce, and never invent a
UI step you haven't checked. Verify it statically (`bash -n`, `shellcheck`)
rather than running it yourself, since it waits on a human. Delete it after the
run unless it should become the repo's documented setup path.

## Staged rollout

Don't expose 100% of users at once:

- **Flag / canary / percentage rollout**: release to a small cohort first, watch,
  then widen. Decouple deploy from release with a flag where you can.
- **Define rollback thresholds up front**: the concrete error-rate / latency /
  business-metric levels that trigger an automatic or immediate rollback. Decide
  them before launch, not during the incident.
- **Watch the right signals** during ramp, not just "is it up", but the metrics
  that show users are actually succeeding.

## After launch

- **Verify in prod**: exercise the real path; confirm the metrics, don't assume.
- **Tag + CHANGELOG** the release (`git-workflow`).
- **Capture learnings**: what surprised you? Feed it back (the `self-scorecard`
  retro, or an ADR).

## Red flags

- Shipping straight to 100% with no canary/flag and no rollback.
- "Tests pass, so ship", skipping the prod-readiness checklist.
- A PR with no before/after evidence, or a one-way door not called out as one.
- No monitoring/alerts on the new path (can't tell if it's failing).
- Rollback thresholds invented *during* the incident.
- A breaking schema/contract change shipped without expand-contract + backup.
