# Wayfinding: an effort bigger than one session

Some ideas are too big for one session to grill and too foggy to plan: the way
from here to the **destination** isn't visible yet. Don't charge at the
destination. Chart the way as a **map of decision tickets** and resolve them one
at a time until nothing is left to decide. Wayfinding produces decisions, not
deliverables: when the pull to just build it appears, you have reached the edge
of the map, and it's time to hand off to `write-prd`.

## Name the destination first

Grill until you can state, in one or two lines, what reaching the end looks like:
a spec to hand off, a decision to lock, or a change made in place. The
destination fixes the scope, so it is settled before anything else. Then grill
again **breadth-first** across the whole space to surface the open decisions. If
no fog appears (the way is already clear and fits one session), you don't need a
map: return to the normal grill.

## The map is an index, not a store

One map (a Conductor track's `spec.md`, or a `bd` epic) with four sections:

- **Destination**: the one or two lines above.
- **Decisions so far**: one line per resolved ticket, a gist plus a pointer. A
  decision lives in exactly one place, its ticket; the map never restates it.
- **Not yet specified**: the fog, see below.
- **Out of scope**: work ruled beyond the destination, one line each with why.

Refer to every ticket by its name (its title), never by a bare id.

## Tickets are questions

Each ticket's body is one question, sized to one session, with blocking edges to
the tickets it waits on (`bd` dependencies). Each is one of:

- **Research** (agent alone): a fact outside the repo a decision waits on;
  resolved by a background subagent (`research.md` in this folder) whose findings
  cite primary sources.
- **Prototype** (with the user): a cheap artifact to react to when "how should it
  look or behave" is the question (`prototyping`).
- **Grilling** (with the user): the default; a conversation. The agent never
  answers the user's side of it.
- **Task**: manual work that must happen before a decision can be made (sign up
  for a service to judge its API, move data to see its shape). The agent does it
  when it can; otherwise it hands the user a precise checklist.

A session **claims** a ticket (assigns it) before any work, so parallel sessions
skip it. The **frontier** is the open, unblocked, unclaimed tickets.

## Fog of war

Don't chart what you can't see yet. **Fog or ticket?** The test is whether you
can state the question precisely now, not whether you can answer it now. A sharp
question is a ticket even while blocked; a dim one goes in **Not yet specified**,
coarser than a ticket, never pre-sliced. Fog only gathers toward the destination:
work beyond it is **Out of scope**, never fog, and it returns only if the
destination is redrawn.

## Work the map

One ticket per session (research tickets excepted, they can fan out):

1. Load the map, not every ticket body. Take the ticket the user names, or the
   first on the frontier, and claim it.
2. Resolve it as its type says; fetch related tickets only as needed.
3. Record the answer on the ticket, close it, and add its one line to
   **Decisions so far**.
4. Create the tickets the answer made specifiable, clearing that patch of fog. A
   ticket the answer shows to sit past the destination is closed into **Out of
   scope**, not resolved. A decision that invalidates other tickets updates or
   removes them.

The map is done when no tickets and no fog remain: the way is clear.
