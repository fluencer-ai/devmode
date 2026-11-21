#!/usr/bin/env python3
"""devmode session-resume — a SessionStart hook that injects a *warm* resume
context so a fresh session doesn't start cold (context-engineering: survive
compaction; loop-engineering: maintain external state and resume from it).

It reads the project's own durable state (`.devmode/scorecard.json` + the active
conductor track) and prints a compact pointer to stdout, which Claude Code adds
to the session's starting context. It also prints the memory block from
`.devmode/memory.py prime` (the user's preferences + this project's decisions),
capped at a few lines. This runs once per session, never per message. Pure read,
fail-OPEN: any problem → print nothing, exit 0 (a resume hint must never block a
session).
"""
import glob
import json
import os
import subprocess
import sys

MEMORY_LIMIT = 8  # lines of memory per session start; the rest stays one `list` away

CRITERIA = ["correctness", "design", "testing", "safety", "clarity"]


def _overall(entry):
    s = entry.get("scores", {})
    vals = [s[c]["score"] for c in CRITERIA if c in s]
    return round(sum(vals) / len(vals), 1) if vals else None


def is_devmode_memory(script):
    """Run only devmode's own memory tool, never a same-named project file."""
    try:
        with open(script, encoding="utf-8", errors="replace") as fh:
            return '"""devmode memory:' in fh.read(400)
    except OSError:
        return False


def memory_block(root):
    """The `memory.py prime` output, or [] when there is no memory or no script."""
    script = os.path.join(root, ".devmode", "memory.py")
    if not is_devmode_memory(script):
        return []
    try:
        p = subprocess.run([sys.executable, script, "prime", "--root", root,
                            "--limit", str(MEMORY_LIMIT)],
                           capture_output=True, text=True, timeout=5)
    except Exception:
        return []
    return p.stdout.strip().splitlines() if p.returncode == 0 else []


def resume_block(root):
    try:
        with open(os.path.join(root, ".devmode", "scorecard.json")) as fh:
            hist = json.load(fh)
    except Exception:
        return []  # no devmode state here — nothing to resume
    if not isinstance(hist, list) or not hist or not isinstance(hist[-1], dict):
        return []
    last = hist[-1]
    lines = ["[devmode] Warm resume — pick up where the loop left off:"]
    o = _overall(last)
    lines.append(f"  • Last phase: {last.get('phase', '?')}"
                 + (f" ({o}/10)" if o is not None else "")
                 + (f" — {last['summary']}" if last.get("summary") else ""))
    # active track: the most recently touched track dir with a spec
    tracks = [d for d in glob.glob(os.path.join(root, "conductor", "tracks", "*"))
              if os.path.isdir(d) and os.path.exists(os.path.join(d, "spec.md"))]
    if tracks:
        latest = max(tracks, key=os.path.getmtime)
        lines.append(f"  • Active track: {os.path.basename(latest)}")
    recs = last.get("recommendations") or {}
    for c in CRITERIA:
        if recs.get(c):
            lines.append(f"  • Next ({c}): {recs[c]}")
            break
    lines.append("  • Full picture: open devmode-dashboard.html (refresh: python3 .devmode/dashboard.py .)")
    return lines


def main():
    root = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    try:
        lines = resume_block(root) + memory_block(root)
    except Exception:
        return 0
    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
