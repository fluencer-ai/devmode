---
name: grill-me
description: >-
  Grill: relentless interview that reaches a shared design concept before any
  plan, spec, or code exists. Use when the user describes a feature, change, or
  product idea, when a request is too vague to plan without guessing, or when the
  user asks to be grilled.
disable-model-invocation: true
---

# Grill me

No one knows exactly what they want, not the user, not you. The gap between
what's in the user's head and what you build is the single biggest source of
wasted work. This skill closes that gap by reaching a **shared design concept**
(Frederick Brooks' term): the invisible, agreed-upon theory of what is being
built. It is not a document. You cannot save it to a file. It lives in the
shared understanding between you and the user, and you only get there by asking.

The mistake to avoid is rushing to create an asset. The instinct to produce a
plan immediately feels productive, but a plan written before alignment just
freezes a guess. Interview first. The conversation you generate here is the raw
material that later becomes a PRD or a set of issues, but the alignment is the
point, not the document.

## How to grill

Interview the user relentlessly about every aspect of the idea until you reach
genuine shared understanding. Treat yourself as a friendly adversary whose job
is to surface every hidden assumption.

Walk the **design tree**: every design decision opens branches, and branches
depend on each other. Don't fire questions randomly. Pick a branch, resolve the
decisions on it, and follow the dependencies those decisions create before
moving to the next branch. A decision about storage might depend on a decision
about data volume, which depends on a decision about who the users are: chase
that chain to the bottom.

Ask about, at minimum:

- **Purpose & users.** Who is this for? What problem does it solve? What
  happens if it doesn't exist?
- **Scope boundaries.** What is explicitly *not* part of this? What's the
  smallest version that delivers value?
- **Behavior & edge cases.** What happens on the happy path? On failure? On
  empty input? At the limits?
- **Constraints.** Performance, security, compliance, deadlines, existing
  systems it must fit into.
- **Data & state.** What is the shape of the data? What's the source of truth?
  What can change and when?
- **Trade-offs.** Where decisions conflict, make the tension explicit, then say
  which side you'd pick and why. A neutral menu with no opinion is abdication
  dressed up as balance. *Ask* when the call is the user's (product, priorities,
  taste); *decide* when it's an engineering call and defend it until shown wrong.
- **Success.** How will we both know this is done and correct?

## Classify what's unclear, then ask the right kind of question

Not all gaps are the same; the *type* of gap determines the *kind* of question.
Before firing a question, classify the fault:

- **Intention fault**: the real goal isn't recoverable. ("Make it better":
  better how, for whom? "Can you check if X is possible?" often means "do X".)
  → Ask for the underlying outcome.
- **Premise fault**: an assumption in the request is wrong. ("Fix the race
  condition in the cache", when there is none; or it asks for something the
  system can't do.) → Surface and test the assumption *before* accepting the task.
- **Parameter fault**: required details are missing or conflicting. ("Build a
  login page": OAuth? email/password? SSO? "Simple but handle every edge case".)
  → Ask for the missing parameter or resolve the contradiction.
- **Expression fault**: the wording blocks a unique reading. ("Update that
  component", which? "Clean up the API": refactor, deprecate, or document?)
  → Disambiguate the term or referent.

Then note which *direction* the gap pulls: **semantic** (multiple meanings →
"A or B?"), **too broad** (huge scope → "which part matters most now?"), or **too
narrow** (oddly specific → "what's the broader outcome?").

## Choose questions by information gain

Don't ask "what should I ask?" Ask "what are the plausible interpretations, and
which question eliminates the most of them?"

1. Generate 2–4 competing interpretations of the request.
2. Find the axis on which they disagree.
3. Ask about that axis: the answer that collapses the most uncertainty.

This is the difference between dream-extraction and a checklist: each question
is chosen to resolve the largest open branch of the design tree, not to fill a
form. Explicitly check whether parts of the request *conflict* with each other:
inconsistencies are the hardest gaps to spot and the costliest to discover late.

**Offer A / B / C choices only for a truly discrete decision**, one with a small,
closed set of options (which auth provider, which of three layouts). Label each
with its trade-off in a phrase, add an "other / none of these" escape, and say in
one line why the decision is discrete. Everything else gets **one open question
with your recommended answer**: a menu on an open axis hides the option nobody
listed.

## Ask in rounds: work the frontier, not a drip

Serial one-question-at-a-time is slow and makes the user wait on you. Batch by
**frontier**: every decision whose prerequisites are *already settled*; the
questions you can ask now without guessing at answers you haven't heard yet. Ask
that whole frontier in one round: **number each question and give your recommended
answer**, then stop and wait. Word each question so that "yes" accepts your
recommendation ("Store sessions in Postgres, since it's already deployed?"), so a
user who agrees answers a whole round in one word. A question whose answer depends on another question
still open in this round belongs to the *next* round, not this one.

Each round's answers reshape the design tree: settled decisions push the frontier
outward and unblock what depended on them. Recompute and ask the next round.
You're done when **the frontier is empty**: every branch visited, nothing left
silently assumed.

(This is how "one branch at a time" is *paced*, not a contradiction of it: you
still finish a line of dependent decisions before opening an unrelated one; you
just don't drip-feed questions that were all answerable at the same moment.)

## Ground a knowledge gap before you guess

When a gap is shared ignorance (an unfamiliar library, protocol, or domain), not
the user's preference, investigate before you grill: read `research.md` in this
folder for the perspective-guided research technique.

## Too big for one session? Chart a map

When the idea is too big for one session and the way to it is still foggy, don't
grill it all at once: read `wayfinding.md` in this folder to chart it as a map of
decision tickets worked one per session.

## Rules of engagement

- **Check before you grill an incoming request.** Search the code for the
  behaviour by domain concept (not the request's wording) and read the ADRs and
  any out-of-scope notes: it may be done already, or ruled out before. For a
  reported bug, reproduce it first; for a proposed patch, run it. Grill only what
  survives, and say where you looked.

- **Ask a lot.** Real grilling means dozens of questions: keep going until the
  understanding is genuinely shared, not until you hit a quota. It is normal for
  this to run long.
- **One branch at a time.** Don't scatter. Finish resolving a line of
  dependent decisions before opening a new one, so the user can think clearly.
- **Facts are your job; decisions are theirs.** Never ask the user for something
  you could look up: the filesystem, the code, the docs, the dependency's actual
  API. Go find it (dispatch a subagent if it's slow) and don't block on it: only
  the questions *downstream* of that fact wait, so ask the rest of the round now.
  Asking the user to do your research is how an interview turns into a chore.
- **Surface assumptions, don't smuggle them.** Whenever you'd otherwise fill a
  gap by guessing, turn the guess into a question.
- **Disagree out loud: once.** When you believe the user's direction is wrong,
  say the unwelcome thing plainly, with the reason *and* an alternative, deferring
  to a plan you think is wrong to seem agreeable is negligence, not respect. On a
  judgment call (product, taste, priorities), if the user overrules you, do it
  their way, note the residual risk once, and don't relitigate. Correctness,
  security, and data-safety are the exception: never drop those to seem agreeable.
  Challenge, don't obstruct.
- **"Wait, what?"** When the user is lost (a confused reply, "what do you mean?",
  an answer to a question you didn't ask), stop the round. Re-pitch your last
  point in three lines of plain words in the project's ubiquitous language: the
  context they were missing, the point, the question. Then resume.
- **Reflect back.** Periodically summarize the design concept as you understand
  it so far and ask the user to correct it. This is how you confirm the concept
  is actually shared.
- **Don't write the asset yet.** Resist producing a plan, spec, or code until
  the user signals the concept is solid. When they do, hand the conversation to
  `write-prd` (large changes) or turn it directly into issues (small ones).

## When you're done

You've reached a shared design concept when you can restate the what, the why,
the boundaries, and the key trade-offs, and the user agrees without
corrections. At that point, stop grilling and offer to capture it, as a PRD,
as issues, or as a short summary the user can hand to an AFK agent.
