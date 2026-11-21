#!/usr/bin/env python3
"""devmode guardrails — a deterministic PreToolUse hook (gates-as-code).

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

# A `.env` file (`.env`, `.env.local`, `.envrc`, `config/.env`) but NOT words like
# "environment" (no leading dot+token boundary).
_ENV_RE = re.compile(r"\.env(rc)?(\b|$|[./\s'\"])")
SECRET_SUBSTR = ("id_rsa", "id_ed25519", ".pem", "credential", "secret", ".ssh/")


def _is_secretish(text: str) -> bool:
    t = text.lower()
    return bool(_ENV_RE.search(t)) or any(s in t for s in SECRET_SUBSTR)


# --- R05/R06 v2 (Projects/testes/aprovador/guardas/regras_v2.py): ask only when a command really reads a secret
# or deletes outside temp. v1 asked on any cat/head/tail + the word secret/.env anywhere (heredocs, greps).
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
    if re.fullmatch(r"\.env(rc|\.[\w.-]+)?", base):
        return not re.search(r"\.(example|sample|template|dist|exemplo|modelo)$", base)
    if base.endswith((".pem", ".key", ".p12", ".pfx", ".keystore", ".jks")) or re.fullmatch(r"[\w.-]+\.env", base):
        return True
    if re.fullmatch(r"id_(rsa|dsa|ecdsa|ed25519)(_[\w-]+)?", base) or (
            "/.ssh/" in "/" + a and not base.endswith((".pub", "known_hosts", "config", "authorized_keys")) and base not in ("", ".ssh")):
        return True
    return bool(re.fullmatch(r"(credentials?|secrets?)(\.(json|ya?ml|toml|env|txt|ini|conf))?", base)) or \
        base in ("auth.json", ".netrc", ".pgpass", ".npmrc", ".pypirc", "token", "tokens.json")


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
        if exe in ("scp", "rsync", "ssh", "sftp"):  # -i chave / -F config só autenticam, não leem o conteúdo para a tela
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


def deletes_outside_temp(cmd: str) -> bool:
    """rm -rf whose targets are not all in temp/scratchpad/Trash (variables set in the same command are resolved)."""
    env = _assignments(cmd)
    tmp = _os.environ.get("TMPDIR", "")
    for w in simple_commands(cmd):
        if _os.path.basename(w[0]) != "rm":
            continue
        flags = "".join(x[1:] for x in w[1:] if x.startswith("-") and not x.startswith("--"))
        if "r" not in flags.lower() and "--recursive" not in w:
            continue
        for a in (x for x in w[1:] if not x.startswith("-")):
            p = re.sub(r"\$\{?(\w+)\}?", lambda x: env.get(x.group(1), _os.environ.get(x.group(1), x.group(0))), a)
            p = _os.path.expanduser(p)
            if "$" in p:
                return True  # unknown variable: can't prove it is temp
            p = _os.path.abspath(p).lower() + "/"
            if not (p.startswith(_TEMP) or (tmp and p.startswith(tmp.lower())) or "/.trash/" in p or "/scratchpad/" in p):
                return True
    return False
# --- fim R05/R06 v2


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
            return "ask", "R04: destructive git op — confirm before running"
        if re.search(r"\brm\s+-\w*r\w*f\w*|\brm\s+-\w*f\w*r\w*", low):
            if re.search(r"\s(/|~|\$home|\*)(\s|/|$)", low):
                return "deny", "R05: refuse rm -rf on / ~ or wildcard root"
            if deletes_outside_temp(cmd):
                return "ask", "R05: recursive force delete outside temp — confirm the scope"
        if reads_secret(cmd):
            return "ask", "R06: reading a possible secret file — confirm"
        return "allow", ""
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(tool_input.get("file_path") or tool_input.get("path") or "").lower()
        if ".git/" in path or _is_secretish(path):
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
        "permissionDecisionReason": f"devmode guardrail — {reason}",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
