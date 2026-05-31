# Tech stack

> Deliberate technology choices. Changes here must be documented *before*
> implementation (see `workflow.md`). Prefer choices that strengthen feedback
> loops — static types, fast tests, a real runtime the AI can observe.

## Languages & runtimes
- <e.g. TypeScript (strict), Node 20>

## Frameworks & key libraries
- <...>

## Feedback-loop tooling (devmode-critical)
> The faster and more legible these are, the higher your speed limit.
- **Static types:** <e.g. TypeScript strict mode — non-negotiable where available>
- **Compiler / linter:** <command, runs on every change>
- **Test runner:** <command, kept fast; e.g. `CI=true npm test`>
- **Browser / runtime access:** <for UI, how the agent observes real output>

## Data & persistence
- <datastore, source of truth, migrations approach>

## Conventions
- Module layout: deep modules with functional core / imperative shell split
- Naming follows `UBIQUITOUS_LANGUAGE.md`

## Constraints
- <performance, compliance, deployment targets, etc.>
