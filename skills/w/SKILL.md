---
name: w
description: Use when the user invokes /w in Claude Code, $w in Codex, or asks to save memories from the current session. Reviews the full conversation for memorable information and persists it to the memory system.
---

# /w — Save Memories

Review the entire conversation and save any information worth remembering to the memory system at `memory/`.

## Process

1. **Scan the full conversation** for information matching these memory types:
   - **user**: Role, preferences, expertise, responsibilities
   - **feedback**: Corrections, confirmations, approach guidance
   - **project**: Ongoing work, goals, decisions, deadlines (convert relative dates to absolute)
   - **reference**: Pointers to external systems, URLs, dashboards

2. **Check existing memories** — read `memory/MEMORY.md` and any relevant memory files to avoid duplicates. Update existing memories if the conversation contains newer information.

3. **Skip things that should NOT be saved:**
   - Code patterns, architecture, file paths derivable from the codebase
   - Git history recoverable via `git log` / `git blame`
   - Ephemeral task details only useful in this conversation
   - Anything already in `AGENTS.md` or `identity/*.md`

4. **For each memory to save:**
   - Write the memory file with proper frontmatter (name, description, type)
   - For feedback/project types, include **Why:** and **How to apply:** lines
   - Add/update the pointer in `memory/MEMORY.md`

## Memory file format

```markdown
---
name: short-slug
description: One-line description used to decide relevance in future conversations
type: user | feedback | project | reference
---

<memory body>

For feedback/project types:
**Why:** <reason this matters>
**How to apply:** <when this kicks in>
```

## After saving

Run `scripts/save-state.sh`, verify the push succeeds, then briefly tell the user what was saved (filename + one-line description for each). Claude Code may already have triggered the same script through its PostToolUse hook; running it again is safe and becomes a no-op when the tree is clean. This explicit step keeps the workflow identical under Codex.
