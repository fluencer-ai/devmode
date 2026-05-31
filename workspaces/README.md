# workspaces/ — disposable experiment space

**The devmode base (everything outside this folder) is reused across projects and
must stay clean.** Never experiment in the base directly. Do it here.

## How to use

1. **Copy the base into a workspace** — easiest via the installer:
   ```bash
   integrations/conductor-beads/install.sh workspaces/<experiment-name>
   ```
   This copies the devmode base (CLAUDE.md, skills, agents, references) and mounts
   the Conductor layer into `workspaces/<experiment-name>/`.

2. **Work inside that workspace.** Build features, run tests, break things. It's
   throwaway.

3. **Bring back only the learnings.** Port a sharpened skill, a fixed template, or
   a new pattern into the base **by hand**. Never copy a whole experiment back.

## Rules

- Everything here is **gitignored** (see `.gitignore`) — scratch is never committed.
- The source of truth is always the base, never a workspace copy.
- One workspace per experiment; delete it when done.
