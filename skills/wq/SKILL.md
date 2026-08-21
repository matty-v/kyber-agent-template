---
name: wq
description: Use when the user invokes /wq in Claude Code, $wq in Codex, or asks to save memories and exit. Combines the w memory flow with exit. Vim-style write-and-quit.
---

# /wq — Save Memories and Exit

Save memories from this session, then end it.

## Process

1. **Execute the `w` skill** — follow its full memory-saving process (scan conversation, check for duplicates, save memories, report what was saved).

2. **Exit** — after memories are saved and confirmed, end the session.

Use this when the user wants to wrap up cleanly without doing the full `restart` flow (which also writes `state/last-session-summary.md` and sends a heads-up).
