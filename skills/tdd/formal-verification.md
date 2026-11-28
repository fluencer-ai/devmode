# Beyond examples: properties, models and proofs

An example test checks the cases someone thought of. Some bugs live only in the
cases nobody thought of: an unusual ordering of events, a race between two
requests, an input at the edge of an algorithm. For those, let a machine search
the space for you. AI makes this affordable: writing a spec or a property used
to take an expert days; now it takes an agent minutes, and the checker, not the
agent, decides whether it holds.

## Pick the target

Spend this effort where **a break would hurt users and ordinary tests rarely
reach**: payment and checkout flows, sync and offline logic, permission checks,
retries and idempotency, schedulers, parsers, money and date arithmetic. A
settings page does not need a model checker.

## Let the question pick the tool

| The question | Tool |
|---|---|
| "Can these steps happen in an order that breaks a rule?" (flows, protocols, concurrency, retries) | a model checker such as TLA+ (TLC) over a small spec of the flow |
| "Is this function correct for every input?" (an algorithm, a pure transform) | a proof in a language with a verifier (Lean, Dafny, or the language's own verifier) |
| "Does this hold for many inputs I can generate?" (most code) | property-based tests (Hypothesis, fast-check, QuickCheck and the like) |
| "Does it survive inputs nobody would write?" (parsers, file formats, public endpoints, a release) | fuzzing |

Property-based testing is the default: cheapest to start, runs in the normal
suite, and shrinks a failure to a small counterexample you can turn into a
plain regression test. It works for UIs too: generate sequences of user actions
and assert that the screen never reaches a state the rules forbid.

## Make sure the check can fail

A spec that always passes is decoration. Before trusting it:

- write each rule the reader agrees to as an invariant; never weaken a rule to
  make it hold (if it breaks, that is the finding);
- break the model or the code on purpose and watch the checker go red;
- keep the constants small (two users, three messages) so the search finishes;
  most ordering bugs show up in tiny worlds.

A finding stays a finding: report it with the path that reaches it, even if
the fix is out of scope.

## Be honest about scope

A model checks the model, not the code. Say what it leaves out (the network
layer, the UI, a third-party service) and keep a short coverage record next to
the spec: which rules are checked, which flows are modeled, and the commit the
model was last synced against. When the code changes in a modeled area, the
model is stale until someone re-syncs it; treat a stale model like a skipped
test.

## Show a statechart, in the reader's words

For a flow, the most useful artifact is often a picture the product owner can
read. From the model's state graph, draw a statechart (Mermaid works) where:

- each state is labeled with what the user sees or cares about ("Paying",
  "Offline, changes queued"), never a variable name;
- each arrow is labeled with what happens, as the user would say it ("you press
  pay", "the card is declined"), with any condition in brackets;
- states where a rule breaks are marked, and the legend names the rule;
- the chart stays small (about 20 arrows): merge states that behave the same,
  but never merge two states that break different rules.

Then replay each bug path against the **real** code (a test, a script, the
running app): a path the code cannot follow means the model is wrong, and a
path it can follow is a bug with a reproduction already written.

## Hand-off

For each check you added: the question it answers, the tool, the rules it
checks, what it leaves out, the command that reruns it, and every finding with
its path or counterexample.
