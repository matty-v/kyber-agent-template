---
name: restart
description: Use when the user invokes /restart in Claude Code, $restart in Codex, asks you to restart yourself, or signals a planned shutdown. Saves a session summary and any new memories, commits + pushes the identity repo, sends a heads-up message, then exits cleanly so the next session can resume seamlessly.
---

# /restart — Save state and shut down for planned restart

When invoked, do the following in order. If any step fails, **do not exit** — surface the error and wait for the user's instruction.

## Step 1: Review the current session in your context

You already have the full session in working memory. Identify:

- What was the user trying to accomplish in this session?
- What major actions or decisions happened?
- What's still in flight or unresolved?
- Which files, repos, or branches were touched and matter for picking up next time?

## Step 2: Save persistent memories

Run the `w` skill flow (review the conversation for memorable items, write them to `memory/` as new entries or updates to existing entries, refresh `MEMORY.md`). Skip if nothing new is worth saving.

## Step 3: Write `state/last-session-summary.md`

Write a markdown file at `~/dev/{{ .AgentName }}-agent/state/last-session-summary.md` with this structure:

```markdown
# Last Session Summary

**Session ended:** <ISO 8601 UTC timestamp>
**Channel ID:** <chat_id / channel ID from any inbound message in this session, or "unknown">

## What we were working on

<1–3 sentences>

## Key outcomes this session

- <bullet>
- <bullet>

## Open threads / next steps

- <bullet>
- <bullet>

## Active context

- Repos: <list>
- Branches: <list>
- Files in flight: <list>

## Notes for next session

<anything future-you should know — gotchas, half-finished thoughts, things the user cares about>
```

The `Channel ID` field is critical when the agent has an external channel (Telegram, Slack) — the resume handshake on next startup needs it to know where to send the heads-up message. Pull it from any inbound channel block in the current conversation. Skip the field if the agent is session-only.

## Step 4: Verify git state and push explicitly

Run:

```bash
cd ~/dev/{{ .AgentName }}-agent
git status
```

The auto-backup hook should have already committed `state/last-session-summary.md` as a side-effect of the Write tool. If `git status` shows anything uncommitted, commit it manually:

```bash
cd ~/dev/{{ .AgentName }}-agent
git add state/last-session-summary.md memory/
git commit -m "state: planned restart — session summary saved"
```

Then push and verify:

```bash
cd ~/dev/{{ .AgentName }}-agent
git push
```

If `git push` fails (network, auth, conflict), **do not exit**. Tell the user:

> "/restart blocked: git push failed with `<error>`. Holding here until you tell me how to proceed."

Wait for instruction.

## Step 5: Touch the save-complete sentinel (if Kyber is driving the restart)

If `/persist/var/run/` exists (Kyber pod), touch the sentinel so the controller knows the save is done and can proceed with the actual stop:

```bash
mkdir -p /persist/var/run 2>/dev/null
touch /persist/var/run/last-save.done 2>/dev/null
```

(No-op outside Kyber.)

## Step 6: Heads-up

Send one final message to the user via the agent's primary channel (Telegram, Slack, session text):

> "Session ended at `<time>`. Summary saved and pushed (`<short commit hash>`). Standing by for restart."

## Step 7: Exit cleanly

Once steps 1–6 are confirmed, exit the session. The next time `{{ .AgentName }}` starts, the Resume Handshake (in `AGENTS.md`) will read the summary and available continuity files and send the "{{ .AgentName }} online" message.
