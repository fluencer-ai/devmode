# A verification skill for the project

Tests tell you the code does what the tests say. They do not tell you the
running product does what the person asked. Closing that gap by hand every time
("start the server, log in, click through, look") is slow, so agents skip it.
The fix is to give the project its **own** verification skill: a short,
proven recipe plus a small tool that lets any agent launch the real thing,
drive it, and bring back evidence. When verification is cheap, it gets done on
every change; in a well-run AI project most of the tokens go to checking the
work, not to writing it.

## Interview the repo first

Before writing anything, answer five questions from the code and by trying
things, not from memory:

1. **Surface.** What does a user touch? A web page, a CLI, an API, a desktop or
   mobile app, a bot, a library.
2. **Run.** What exact command starts it locally, and what does it need
   (services, seed data, env names, ports)?
3. **Drive.** How can an agent act as the user? A real browser over the Chrome
   DevTools Protocol (CDP), an HTTP client, a PTY for a terminal app, a
   simulator, the library imported in a script.
4. **Observe.** Where does the truth show up? The rendered page, the console and
   network log, the response body, a row in the database, a file on disk.
5. **Isolate.** How does a run avoid touching real data? A scratch database, a
   temp folder, a test account, a port no one else uses.

Anything you could not answer is a gap: say so in the skill rather than guess.

## Write the skill (one file, six sections)

Put it where the project's skills live (for example
`.claude/skills/verify-<app>/SKILL.md`) with these sections:

- **Launch:** the commands to start the app in isolation, and how to know it is
  ready (a health URL, a log line), not a fixed sleep.
- **Doctor:** a quick check that the environment can run it at all (tools
  installed, ports free, services up), with the fix for each failure.
- **Drive:** how to act as the user, with the smallest working example.
- **Evidence:** what to capture and where it goes (screenshots, a short screen
  recording, the response, the log excerpt) so a reviewer can see the change
  working without rerunning it.
- **Cleanup:** stop what was started and remove scratch state. Evidence must
  **survive** cleanup: save it outside the folders you delete.
- **Helpers:** the small tool below, and the known gotchas.

## Build a small control tool

When driving the app takes more than two or three commands, wrap it in a tiny
CLI shipped with the skill (a script in its folder). Keep it deep and small:

- a handful of composable commands (`start`, `status`, `open <page>`,
  `shot <name>`, `stop`), not one command per scenario;
- `--dry-run` on anything that changes state;
- errors that say what to do next ("port 5173 is busy: run `ctl stop` or pass
  `--port`"), so a stuck agent recovers without asking;
- deterministic output that is cheap to read (short lines, stable names).

A deterministic tool beats a fleet of agents clicking around: build the lever
once, and every later check costs one command.

## Seed a feature map

Next to the skill, keep a feature map: one short page per feature an agent is
likely to change, each with four headings:

- **Sub-features:** the parts a change can break.
- **How to get to it:** the path from the user's point of view (which page,
  which menu, which command).
- **Driving it with the tool:** the exact commands.
- **Gotchas:** what bit someone before (a modal that eats the first click, a
  feature flag, a slow first load).

Start with the features the current change touches; the map grows as work
lands. A wrong entry is worse than none: fix it the moment it misleads you.

## Prove it once, end to end

The skill is not done until a fresh agent, given only the skill, has launched
the app, driven one real flow, captured evidence, and cleaned up, with the
evidence still on disk afterward. Record that run (date, commit, what was
driven) at the bottom of the skill.

## Evidence is the review

The skill's Evidence section is what makes the proof artifacts of
`verification-before-completion` cheap: every run leaves them on disk, ready to
hand to `code-review`.

## Keep it alive

When a run fails because the skill was wrong (a renamed page, a new required
service), fix the skill in the same change. A verification skill that drifts
from the product teaches every agent to stop trusting it.
