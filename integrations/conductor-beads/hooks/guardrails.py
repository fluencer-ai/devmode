#!/usr/bin/env python3
"""devmode guardrails: a deterministic PreToolUse hook (gates-as-code).

devmode's skills *persuade* via prompts; this hook *enforces* a small set of
safety rules deterministically, so a few dangerous operations are blocked even
when prompt guidance drifts. Adapted (lean, stdlib-only) from the R-rule engine
in Chachamaru127/claude-code-harness (MIT).

Design (devmode-style): `evaluate()` is a **pure functional core** (tool name +
input → decision), tested directly; `main()` is the **imperative shell** (read
the hook JSON from stdin, print the permission decision). Fail-open: any error
or unparseable input → allow (a buggy guard must never block honest work).

Decisions: "allow" (silent), "ask" (user confirms), "deny" (blocked).
Wire it via Claude Code PreToolUse hooks (see hooks.snippet.json).
"""
from __future__ import annotations

import json
import re
import sys
from typing import Tuple

# --- R05/R06 v2: ask only when a command really reads a secret or deletes outside temp.
# v1 asked on any cat/head/tail plus the word "secret" or a dotenv name anywhere (heredocs, greps).
import os as _os
import shlex as _shlex

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n[ \t]*\2[ \t]*(?=\n|$|\))", re.S)
_READERS = {"cat", "less", "more", "head", "tail", "bat", "strings", "xxd", "od", "hexdump", "nl", "tac", "grep", "egrep",
            "fgrep", "rg", "ag", "sed", "awk", "jq", "yq", "base64", "diff", "sort", "uniq", "cut", "cp", "scp", "openssl",
            "pbcopy", "tee", "dotenv", "python", "python3", "node", "ruby", "perl"}
_PREFIX = {"env", "command", "builtin", "nohup", "time", "exec", "xargs", "nice", "caffeinate", "sudo", "then", "do",
           "else", "if", "while", "until", "!", "{", "timeout"}
_SEP = set(";|&()\n")
_TEMP = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/", "/.trash/")


def secret_path(arg: str) -> bool:
    """A path whose contents are a secret: .env files, private keys, credential stores."""
    a = arg.strip("'\"").lower()
    base = _os.path.basename(a.rstrip("/"))
    if re.fullmatch(r"\.env(rc)?([._-][\w.-]+)?", base):
        return not re.search(r"\.(example|sample|template|dist|exemplo|modelo)$", base)
    if base.endswith((".pem", ".key", ".p12", ".pfx", ".keystore", ".jks")) or re.fullmatch(r"[\w.-]+\.env", base):
        return True
    if re.fullmatch(r"id_(rsa|dsa|ecdsa|ed25519)([._-][\w.-]+)?", base) and not base.endswith(".pub"):
        return True  # the key and its copies (id_rsa.backup, id_ed25519-old), never the public half
    if re.fullmatch(r"(credentials?|secrets?)([_-][a-z0-9]+)*(\.(prod|production|staging|stage|dev|development|local|test))*"
                    r"(\.(json|ya?ml|toml|env|txt|ini|conf))?", base):
        return True  # secrets-production.yaml, credentials.prod.json; not secrets-policy.md or credentials_form.tsx
    if "/.ssh/" in "/" + a and not base.endswith((".pub", "known_hosts", "config", "authorized_keys")) \
            and base not in ("", ".ssh"):
        return True
    return base in ("auth.json", ".netrc", ".pgpass", ".npmrc", ".pypirc", "token", "tokens.json")


def _words(cmd: str, fundo: int = 0):
    """Tokens of the command. Heredoc bodies (text, not commands) are dropped; quoted remote commands
    (`ssh host '...'`, `bash -c "..."`) are opened so their inner commands are checked too."""
    text = _HEREDOC.sub("<<TEXT ", cmd)
    try:
        lx = _shlex.shlex(text, posix=True, punctuation_chars="();<>|&\n")
        lx.whitespace, lx.whitespace_split = " \t\r", True
        toks = list(lx)
    except ValueError:
        return [t for t in re.split(r"[\s;|&()]+", text) if t]
    out, head, prev, shell = [], None, None, False
    for t in toks:
        if t and set(t) <= _SEP:
            head, shell = None, False
        elif head is None and not (re.match(r"^\w+=", t) or t in _PREFIX):
            head = _os.path.basename(t)
        shell = shell or _os.path.basename(t) in _SHELLS  # `docker exec c sh -c "..."` runs it too
        if fundo < 4 and t != cmd and _runs_as_command(head, prev, t, shell):
            out += [";"] + _words(t, fundo + 1) + [";"]
        else:
            out.append(t)  # a quoted path or message stays ONE argument of its program
        prev = t
    return out


_SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "su"}
_REMOTE = {"ssh", "watch", "eval"}


def _runs_as_command(head, prev, tok, shell) -> bool:
    """A quoted string is opened as a command only where something executes it:
    `bash -c "..."`, `su -c "..."`, `eval "..."`, `ssh host "..."`, `watch "..."`."""
    if not (" " in tok or "\n" in tok or ";" in tok or "|" in tok) or head is None:
        return False
    if shell and prev is not None and re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", prev):
        return True
    return head in _REMOTE and prev is not None or head == "eval"


def simple_commands(cmd: str):
    cur, res = [], []
    for t in _words(cmd) + [";"]:
        if t and set(t) <= _SEP:
            w = cur
            while w and (re.match(r"^\w+=", w[0]) or w[0] in _PREFIX):
                w = w[1:]
            if w:
                res.append(w)
            cur = []
        else:
            cur.append(t)
    return res


def reads_secret(cmd: str) -> bool:
    """True when some simple command prints, copies or loads a secret file into a program."""
    for w in simple_commands(cmd):
        exe, args = _os.path.basename(w[0]), w[1:]
        if exe not in _READERS:
            continue
        if exe == "cut" and all(re.fullmatch(r"-f1|1", x) for x in (args[args.index("-f") + 1:args.index("-f") + 2] if "-f" in args else [a for a in args if a.startswith("-f")])):
            continue  # cut -d= -f1 .env lists variable names only (the house rule allows it)
        if exe in ("grep", "egrep", "fgrep", "rg", "ag"):
            if any(re.fullmatch(r"-\w*[qclL]\w*|--(quiet|count|files-with(out)?-matches)", x) for x in args):
                continue  # only says whether/where it matches, never prints a value
            files, skip, have_pat = [], False, any(x in ("-e", "-f", "--regexp") for x in args)
            for x in args:
                if skip:
                    skip = False
                    continue
                if x in ("-e", "-f", "--regexp", "-A", "-B", "-C", "-m", "--include", "--exclude", "-g"):
                    skip = True
                    continue
                if x.startswith("-"):
                    continue
                if not have_pat:
                    have_pat = True
                    continue
                files.append(x)
            if any(secret_path(f) for f in files):
                return True
            continue
        if exe in ("scp", "rsync", "ssh", "sftp"):  # -i key / -F config only authenticate; they never print the file
            args = [a for i, a in enumerate(args) if not (a in ("-i", "-F", "-o", "-e") or (i and args[i - 1] in ("-i", "-F", "-o", "-e")))]
        if exe in ("python", "python3", "node", "ruby", "perl") and not any(secret_path(a) for a in args):
            continue
        if any(secret_path(a) for a in args if not a.startswith("-") or exe == "openssl"):
            return True
    if re.search(r"<\s*\S*\.env\b(?!\.(example|sample|template))", _HEREDOC.sub("", cmd)):
        return True  # `while read l; do ...; done < .env`
    for m in _CODE_HEREDOC.finditer(cmd):  # `python3 - <<EOF ... open('.env') ... EOF`: the body is code that runs
        if any(secret_path(s) for s in _QUOTED.findall(m.group(0))):
            return True
    return False


_CODE_HEREDOC = re.compile(r"\b(python3?|node|ruby|perl|bash|sh|zsh|osascript)\b[^\n<]*<<-?\s*(['\"]?)(\w+)\2[^\n]*\n.*?\n[ \t]*\3[ \t]*(?=\n|$|\))", re.S)
_QUOTED = re.compile(r"['\"`]([^'\"`\s]*(?:\.env[\w.-]*|id_(?:rsa|dsa|ecdsa|ed25519)[\w-]*|\.pem|\.key|credentials?\.json|\.netrc))['\"`]")


def _assignments(cmd: str) -> dict:
    env = {}
    for m in re.finditer(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;&|)]+)", cmd):
        v = m.group(2).strip("'\"")
        env[m.group(1)] = re.sub(r"\$\{?(\w+)\}?", lambda x: env.get(x.group(1), x.group(0)), v)
    return env


# R05 scans the RAW text, on purpose: a delete wrapped in a heredoc fed to a shell, `xargs -0`, `timeout 5`,
# `bash -c "..."`, or a word with `#` inside must still be seen. Erring toward a false positive (an `echo`
# that mentions rm -rf) is the safe side for a delete guard.
_RM_SEGMENT = re.compile(r"[;|&()\n`]+")


def rm_recursive_force_targets(cmd: str):
    """Operand lists of every `rm` that is both recursive and forced, whatever the flag spelling
    (-rf, -fr, -r -f, -R -f, --recursive --force). After `--` every token is an operand."""
    out = []
    for seg in _RM_SEGMENT.split(cmd):
        toks = [t.strip("'\"") for t in seg.split()]
        for i, t in enumerate(toks):
            if _os.path.basename(t) != "rm":
                continue
            short, longs, operands, opts = "", set(), [], True
            for x in toks[i + 1:]:
                if opts and x == "--":
                    opts = False
                elif opts and x.startswith("--"):
                    longs.add(x)
                elif opts and x.startswith("-") and len(x) > 1:
                    short += x[1:]
                else:
                    operands.append(x)
            if ("r" in short.lower() or "--recursive" in longs) and ("f" in short or "--force" in longs):
                out.append(operands)
            break  # one rm call per segment
    return out


# Targets that mean "everything": / , ~ , $HOME and wildcards over them. A path INSIDE home is scoped (asks).
_ROOT_TARGETS = {"/", "/*", "~", "~/*", "$home", "$home/*", "${home}", "${home}/*", "*"}


def is_root_target(arg: str) -> bool:
    s = re.sub(r"/{2,}", "/", arg.lower())
    s = re.sub(r"(?<=.)(/\.)+$", "", s)  # `/.` and `~/.` name the same directory
    if s == "/.":
        s = "/"
    if s != "/":
        s = s.rstrip("/")
    return s in _ROOT_TARGETS


def deletes_outside_temp(cmd: str) -> bool:
    """rm -rf whose targets are not all in temp/scratchpad/Trash (variables set in the same command are resolved).
    A call with no static operand (`xargs rm -rf`) takes its targets from input, so it can't be proven temp."""
    env = _assignments(cmd)
    tmp = _os.environ.get("TMPDIR", "")
    for operands in rm_recursive_force_targets(cmd):
        if not operands:
            return True
        for a in operands:
            p = re.sub(r"\$\{?(\w+)\}?", lambda x: env.get(x.group(1), _os.environ.get(x.group(1), x.group(0))), a)
            p = _os.path.expanduser(p)
            if "$" in p:
                return True  # unknown variable: can't prove it is temp
            p = _os.path.abspath(p).lower() + "/"
            if not (p.startswith(_TEMP) or (tmp and p.startswith(tmp.lower())) or "/.trash/" in p or "/scratchpad/" in p):
                return True
    return False
# --- end R05/R06 v2


def evaluate(tool_name: str, tool_input: dict) -> Tuple[str, str]:
    """Pure core: return (decision, reason). decision in {allow, ask, deny}. First match wins."""
    if tool_name == "Bash":
        cmd = str(tool_input.get("command") or "")
        low = cmd.lower()
        if re.search(r"(^|\s|;|&&|\|)sudo\s", cmd):
            return "deny", "R01: refuse sudo / privilege escalation"
        if "git push" in low and re.search(r"(--force(\b|=)|\s-f\b|\s\+\w)", cmd):
            return "deny", "R02: refuse force-push (rewrites shared history)"
        if "--no-verify" in low or "--no-gpg-sign" in low:
            return "deny", "R03: refuse --no-verify / hook bypass"
        if re.search(r"git\s+reset\s+--hard", low) or re.search(r"git\s+clean\s+-\w*f", low) \
           or re.search(r"git\s+(checkout|restore)\s+--?\s*\.", low):
            return "ask", "R04: destructive git op; confirm before running"
        targets = rm_recursive_force_targets(cmd)
        if any(is_root_target(t) for ts in targets for t in ts):
            return "deny", "R05: refuse rm -rf on / ~ or wildcard root"
        if targets and deletes_outside_temp(cmd):
            return "ask", "R05: recursive force delete outside temp; confirm the scope"
        if reads_secret(cmd):
            return "ask", "R06: reading a possible secret file; confirm"
        return "allow", ""
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(tool_input.get("file_path") or tool_input.get("path") or "").lower()
        if ".git/" in path or "/.ssh/" in "/" + path or secret_path(path):
            return "deny", f"R07: refuse write to protected/secret path ({path})"
        return "allow", ""
    return "allow", ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open: never block on a parse error
    try:
        decision, reason = evaluate(str(data.get("tool_name") or ""), data.get("tool_input") or {})
    except Exception:
        return 0  # fail-open: never block on a guard bug
    if decision == "allow":
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"devmode guardrail: {reason}",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
