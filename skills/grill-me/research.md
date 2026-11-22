# Perspective-guided research

Some gaps aren't in the *user's* head: they're shared ignorance: an unfamiliar
library, protocol, or domain; "what are the known failure modes of approach X?".
Quizzing a user who also doesn't know is useless, and guessing freezes a bad
premise (a *premise* or *parameter* fault that's really ignorance). When that
happens, **investigate before you grill**: a small grounded spike that writes
from research, not priors:

1. **Pick 3–5 distinct perspectives**, not one (e.g. a skeptic, an ops/SRE, a
   security reviewer, a maintainer, the official docs). Diverse viewpoints surface
   the *unknown unknowns* a single angle misses.
2. **Dispatch one fresh subagent per perspective**
   (`subagent-driven-development`), each
   given **only the question plus minimal context, never your running conversation
   or your own stated leaning**. When you're also the one synthesizing, feeding a
   voice your position makes it mirror that position back, destroying the very
   independence you dispatched it for. Each is issued web search/fetch and told to
   bring back **cited** findings: every claim carries a source or it doesn't count
   (`verification-before-completion`).
3. **Cross-examine**: where the perspectives disagree is where the real decision
   lives; surface the contradiction, don't average it away.
4. **Bring the cited findings back into the interview** to ground the next
   questions (and later the PRD/ADR). Keep them in a short markdown findings note.

This is a *technique inside the grill*, not a separate research mode: reach for
it the moment a gap turns out to be ignorance, not preference. (Run it ad hoc via
`/devmode do "research <question>"`.)
