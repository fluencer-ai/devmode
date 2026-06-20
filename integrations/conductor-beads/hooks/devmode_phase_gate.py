#!/usr/bin/env python3
"""devmode_phase_gate.py — devmode Stop hook that ENFORCES the devmode ceremony
that CLAUDE.md text alone loses under pressure (the "I skipped it" failure).

Two enforcements, both keyed off the transcript (deterministic, not vibes):

  1) DASHBOARD AUTO-REFRESH (side effect, never blocks): if a project's
     `.devmode/scorecard.json` is newer than its `devmode-dashboard.html`
     (or the HTML is missing), regenerate the dashboard via `.devmode/dashboard.py`.
     The agent can no longer "forget" to refresh it — the gate does it at turn end.

  2) ORCHESTRATOR DELEGATION on a full `/devmode` turn (blocks): if THIS turn's
     user prompt invoked `/devmode` in a phase-driving mode (i.e. NOT
     `c`/`do`/`goal`/`plan`/`adopt`/`start`) and NO `devmode-orchestrator` agent was
     spawned in the same turn, BLOCK ending the turn with a reminder to delegate.
     Conscious override: write `DEVMODE-OK: <reason>` in the reply.

Stop-hook protocol: JSON on stdin {transcript_path, stop_hook_active, cwd, ...}.
  - Block: print {"decision":"block","reason":"..."} to stdout, exit 0.
  - Allow: exit 0 with no output.
  - NEVER hard-fail: on any error, allow (exit 0) — a gate must not break sessions.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# /devmode invocation marker in a user message (command tag or injected body).
CMD_MARK = re.compile(r"<command-name>/?devmode</command-name>|/devmode\s+—\s+guided mode")
# Modes that do NOT require spinning up the orchestrator inline (per the command):
# `c` and `do` run inline; goal/plan/adopt/start are their own (non-phase-driving) flows.
NONFULL = re.compile(r"^(c|do|goal|plan|adopt|start)\b", re.IGNORECASE)
OVERRIDE = re.compile(r"DEVMODE-OK:", re.IGNORECASE)


def allow() -> None:
    sys.exit(0)


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def devmode_args(text: str) -> str:
    m = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"Raw input:\s*\*\*(.*?)\*\*", text, re.S)
    if m:
        return m.group(1).strip()
    return ""


def iter_blocks(entry):
    msg = (entry or {}).get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        return content
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return []


def find_project(file_blobs, cwd):
    """Locate the project dir that owns .devmode/scorecard.json — robust to the
    session being rooted somewhere else (the cwd-vs-project-root pitfall)."""
    cands = []
    if cwd:
        cands.append(cwd)
    for p in file_blobs:
        m = re.search(r"(.*?)/\.devmode/", p)
        if m:
            cands.append(m.group(1))
        m = re.search(r"(.*?)/devmode-dashboard\.html", p)
        if m:
            cands.append(m.group(1))
    seen = set()
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            if os.path.isfile(os.path.join(c, ".devmode", "scorecard.json")):
                return c
    return None


def refresh_dashboard(proj: str) -> None:
    try:
        sc = os.path.join(proj, ".devmode", "scorecard.json")
        html = os.path.join(proj, "devmode-dashboard.html")
        dash = os.path.join(proj, ".devmode", "dashboard.py")
        if not (os.path.isfile(sc) and os.path.isfile(dash)):
            return
        if os.path.isfile(html) and os.path.getmtime(html) >= os.path.getmtime(sc):
            return  # already fresh
        subprocess.run([sys.executable, dash, proj], cwd=proj, timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()
    if data.get("stop_hook_active"):
        allow()
    cwd = data.get("cwd") or os.getcwd()
    tpath = data.get("transcript_path")
    entries = []
    if tpath:
        try:
            for line in open(tpath, encoding="utf-8", errors="replace").read().splitlines():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    entries.append(None)
        except Exception:
            entries = []

    file_blobs = []
    prompt_idx = -1            # index of THIS turn's real user prompt
    prompt_is_devmode_full = False
    orch_idx = -1              # last devmode-orchestrator spawn
    override_idx = -1          # last DEVMODE-OK override (assistant)

    for i, e in enumerate(entries):
        if not e:
            continue
        typ = e.get("type")
        for b in iter_blocks(e):
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            txt = b.get("text") if isinstance(b.get("text"), str) else ""
            inp = b.get("input") if isinstance(b.get("input"), dict) else {}
            if bt == "tool_use":
                for v in (inp.get("file_path", ""), inp.get("command", "")):
                    if isinstance(v, str) and (".devmode" in v or "devmode-dashboard" in v):
                        file_blobs.append(v)
                if b.get("name") in ("Task", "Agent") and inp.get("subagent_type") == "devmode-orchestrator":
                    orch_idx = i
            elif bt == "text" and txt:
                if typ == "user":
                    # A real user prompt (tool_result blocks are not type 'text').
                    prompt_idx = i
                    if CMD_MARK.search(txt):
                        args = devmode_args(txt)
                        prompt_is_devmode_full = not (args == "" or NONFULL.match(args))
                    else:
                        prompt_is_devmode_full = False
                elif typ == "assistant" and OVERRIDE.search(txt):
                    override_idx = i

    # 1) keep the dashboard fresh — no excuses.
    proj = find_project(file_blobs, cwd)
    if proj:
        refresh_dashboard(proj)

    # 2) enforce orchestrator delegation on a full /devmode turn.
    if prompt_is_devmode_full and prompt_idx >= 0:
        delegated = orch_idx > prompt_idx
        overridden = override_idx > prompt_idx
        if not delegated and not overridden:
            block(
                "🚦 devmode gate: você rodou /devmode (modo de condução de fase) e está "
                "encerrando o turno SEM ter delegado ao agente devmode-orchestrator. "
                "Conduza a fase delegando: Task(subagent_type='devmode-orchestrator', ...) "
                "— não encarne o processo inline. Se a delegação realmente não se aplica "
                "neste turno, escreva no texto: DEVMODE-OK: <motivo>."
            )
    allow()


if __name__ == "__main__":
    main()
