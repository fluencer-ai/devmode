# Delegating to an external model CLI

Sometimes the right worker isn't a subagent in this session but an external
model CLI: `codex exec`, `gemini`, etc. It is the same gray-box contract as
`SKILL.md` and `design-interface-delegate-implementation`, just with a different
worker: **you own the interface and the tests; the CLI fills the implementation;
you verify from the outside.**

## When it's worth it

- The task is **bounded and well-specified** (a refactor, a focused analysis, a
  function with a clear contract).
- A different model is **cheaper, faster, or differently strong** for it.
- The interface and acceptance checks already exist, so you can verify the result
  without reading every line.

If the task isn't bounded, or the design isn't settled, don't delegate: align
first (`grill-me`, `write-prd`).

## The contract

1. **Fix the interface and the tests first.** Without tests, you have no right to
   skip reading the output.
2. **Pick the sandbox deliberately.** Default to **read-only** for analysis;
   grant write access only when edits are the point; never grant broad/network
   access casually.
3. **Hand over constraints, not steps.** Give the CLI the contract, invariants,
   and acceptance criteria: let it choose how.
4. **Verify from the outside.** Apply `verification-before-completion`: run the
   tests/types/build on the result. The CLI's summary is not evidence.
5. **Critical code is never a gray box.** Money, auth, security, irreversible
   effects → review the delegated output in full.

## Mechanics (examples)

These are illustrative; check each CLI's current flags before relying on them.

```bash
# Codex: read-only analysis (suppress thinking tokens on stderr)
codex exec --skip-git-repo-check --sandbox read-only "Review src/billing for race conditions" 2>/dev/null

# Codex: apply local edits to a bounded task
codex exec --skip-git-repo-check --sandbox workspace-write --full-auto \
  "Refactor parseDate to return Result<Date, ParseError>; keep the public signature" 2>/dev/null

# Gemini: analysis
gemini -p "Explain the data flow through the renewal pipeline in src/billing"
```

Capture stdout, then **run your own verification** on the working tree. Summarize
the outcome and the evidence, not the CLI's self-report.

## Red flags

- Delegating an unbounded or ill-specified task ("make it better").
- Granting write/network sandbox when read-only would do.
- Accepting the CLI's "done" without running the tests yourself.
- Delegating a critical (money/auth/security) module as a gray box.
