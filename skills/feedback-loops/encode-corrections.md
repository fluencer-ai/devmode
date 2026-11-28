# Encode corrections as checks

A correction you only *say* is lost the next session. A correction you encode
as structure is gone for good: the mistake can no longer be made, by you, by
the AI, or by the next agent that has never seen this conversation. This file is
the procedure for turning "don't do that again" into something a machine
enforces.

## The reader you are designing for

Picture the agent that will touch this code next. It sees only the files it
opened. It copies the nearest example it finds. It takes the shortest path that
compiles and passes the tests. It has not read your docs, your ADRs, or the
chat where you explained the rule. Every fix below is judged by one question:
**would that agent still make the mistake?**

## When a mistake becomes a class

One slip is an incident; fix it and move on. The **second** time the same kind
of mistake appears (in review, in a bug, in a `correction` memory entry), it is
a class, and a class gets encoded. Signals that you are looking at a class:

- the same review comment written twice, on different changes;
- a `correction` recorded in memory (`memory.py add ... --kind correction`) that
  matches an earlier one;
- a bug whose root cause (`systematic-debugging`) is "someone used the old way".

## Fix at the highest level that works

Work down this list and stop at the first level that makes the mistake
impossible or loud. Each level down is weaker: it relies more on someone
noticing.

1. **Architecture.** Make the wrong thing unavailable. One owner per concept,
   one supported way to do it, internals hidden behind the module's interface,
   and the old way **deleted** (agents copy whatever exists; an old pattern left
   in the tree is an instruction to repeat it). Boundaries between directories
   are enforced by an import-graph lint, not by a README.
2. **Types.** Make the wrong thing fail to compile: a branded ID instead of a
   raw string, a closed union instead of a free-form status, a constructor that
   validates once at the boundary.
3. **A lint or CI check whose error names the fix.** "Do not call `fetch`
   directly; use `api.request` from `src/net` (it adds auth and retries)" beats
   "banned API". When the pattern is already common in the tree, fail only on
   **new** instances (a baseline file or a diff-only check) and burn the
   baseline down; a check that fails on day one gets disabled on day two.
4. **A test** that fails when the mistake comes back.
5. **Docs or prose, last.** A line in the project instructions is the weakest
   enforcer there is: it competes for attention with everything else in the
   context and loses under pressure. Use it only when nothing above fits, and
   say so in the rule table.

## Prove the check bites

A check you have never seen fail is a guess. Before you trust it:

- replay a **real past instance** of the mistake (the commit, the diff, the
  snippet from review) and watch the check go red;
- confirm the error message tells the next agent what to do instead;
- confirm the clean tree is green.

## Exceptions are visible and expire

Sometimes the rule must bend. When it does, the exception lives **on the
offending line**, not in a config file far away, and carries three things: the
reason, an expiry date, and who approved it (a human). An exception with no
reason or no date is a bug in the check.

## Keep the rule table

Keep one table, in the project (next to the lint config or in the docs the
project already has), with one row per encoded class:

| Mistake class | Enforcer | Level | Proven against |
|---|---|---|---|
| raw `fetch` outside `src/net` | `no-restricted-imports` rule | lint | commit that leaked the token |

Review it now and then. When a mistake can no longer happen at all (the old API
was deleted, the type makes it unrepresentable), drop the weaker enforcers for
it: a rule nobody can break is noise in the table and in the lint output.

## Hand-off

Report each class you encoded: the mistake in one sentence, the level you fixed
it at and why no higher level worked, the past instance you replayed, and the
row you added to the rule table.
