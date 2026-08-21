#!/usr/bin/env python3
"""Stop hook: write the verbatim tail of the current session to .runtime/last-session-tail.md.

Reads the Claude Code transcript JSONL (path passed via the hook payload's
`transcript_path` field), extracts the last few real user↔assistant
exchanges, and writes them as markdown to the agent's identity repo.

The tail file is what enables "I crashed, what was happening?" recovery.
The Resume Handshake in AGENTS.md reads it on the next session start.

Never blocks the agent: any exception is caught at the top of the script,
logged to .runtime/tail-writer.log, and the script always exits 0.
"""
import json
import os
import sys
from datetime import datetime, timezone

REPO_DIR = os.path.expanduser("~/dev/{{ .AgentName }}-agent")
RUNTIME_DIR = os.path.join(REPO_DIR, ".runtime")
TAIL_PATH = os.path.join(RUNTIME_DIR, "last-session-tail.md")
LOG_PATH = os.path.join(RUNTIME_DIR, "tail-writer.log")


def parse_transcript(entries, max_exchanges=5, max_msg_chars=2000):
    """Build a markdown tail from a list of parsed JSONL entries.

    Pure function — no I/O. The "Last updated" timestamp is taken as a
    parameter so the function is deterministic for testing; production
    callers pass datetime.now(timezone.utc).

    Rules:
    - Keep `user` entries only when content is a string (real prompts).
    - Skip `user` entries with list content (tool results).
    - For `assistant` entries, concatenate all `text` blocks; skip
      `thinking` and `tool_use` blocks.
    - Drop assistant entries that yield no text (thinking-only).
    - Keep only the last `max_exchanges` user/assistant pairs.
    - Truncate any single message body over `max_msg_chars` chars.
    """
    messages = []
    for entry in entries:
        etype = entry.get("type")
        ts = entry.get("timestamp", "")
        if etype == "user":
            content = entry.get("message", {}).get("content")
            if isinstance(content, str):
                messages.append(("user", ts, content))
        elif etype == "assistant":
            blocks = entry.get("message", {}).get("content", [])
            text_parts = [
                b.get("text", "") for b in blocks if b.get("type") == "text"
            ]
            text = "\n".join(p for p in text_parts if p)
            if text:
                messages.append(("assistant", ts, text))

    keep = max_exchanges * 2
    tail = messages[-keep:] if len(messages) > keep else messages

    out = ["# Last Session Tail", ""]
    out.append(f"Last updated: {datetime.now(timezone.utc).isoformat()}")
    out.append("")
    if not tail:
        out.append("(no messages)")
        return "\n".join(out) + "\n"

    for role, ts, text in tail:
        if len(text) > max_msg_chars:
            text = text[:max_msg_chars] + "\n…[truncated]"
        ts_short = ts[11:19] if len(ts) >= 19 else ts
        out.append(f"## {role.capitalize()} ({ts_short})")
        out.append(text)
        out.append("")
    return "\n".join(out) + "\n"


def read_transcript(path):
    """Read a JSONL file and return a list of parsed dicts. Skips bad lines."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def atomic_write(path, content):
    """Write content to path atomically via tmp + rename. Avoids leaving a
    half-written tail file if the script is killed mid-write."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.rename(tmp, path)


def log_error(message):
    """Append a timestamped line to the error log. Logging itself must
    never raise — Stop hook contract is "always exit 0"."""
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")
    except Exception:
        pass


def main():
    payload = json.loads(sys.stdin.read() or "{}")
    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.exists(transcript_path):
        log_error(f"missing or invalid transcript_path: {transcript_path!r}")
        return
    entries = read_transcript(transcript_path)
    output = parse_transcript(entries)
    atomic_write(TAIL_PATH, output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"ERROR: {type(e).__name__}: {e}")
    sys.exit(0)
