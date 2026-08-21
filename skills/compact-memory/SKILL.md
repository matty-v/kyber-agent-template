---
name: compact-memory
description: Use when asked to compact, curate, or prune long-term memory, or when fired by the weekly memory-compaction job. Age-tiers your own memory (hot verbatim / warm summarized / cold archived), keeps MEMORY.md lean, and sends a short digest. Operates only on hot memory (memory/, MEMORY.md, state/) — never the raw transcript layer.
---

# /compact-memory — Weekly memory curation

Curate your own long-term memory so it stays accurate and bounded. **You** write the summaries — you have the context and the voice — and everything is git-tracked, so every change is reviewable and revertible. You never touch the raw transcript layer: the saver sidecar owns it, you have no write access, and this routine only reads/writes `memory/` (including `memory/archive/`), `MEMORY.md`, and `state/`.

## Guardrails (read first)

- **Never destroy information — only condense or relocate.** The full text of anything you summarize or archive stays recoverable in git history. Never `git push --force`, never rewrite history.
- **Preserve load-bearing detail; drop prose.** Keep exact identifiers verbatim — PR/issue/commit numbers, file paths, command lines, config keys, env vars, secret names, error strings, and error→fix pairs. Summarize the *narrative* around them, not the facts themselves.
- **Re-summarize from source, never from a summary.** When condensing a file that is already partly summarized, work from its full current content (and `git log` if you need earlier detail) — summarizing a summary compounds drift.
- **Type-aware aging.** `user`, `feedback`, and `reference` memories are usually evergreen (who the user is, working agreements, external pointers). Evaluate them for continued *accuracy*, do not age them out by the clock. `project` memories for finished or inactive work are the primary aging target.
- **When unsure, keep it.** Err toward retention. A borderline memory stays where it is and gets flagged in the digest, never archived on a guess.

## Reading a memory's `type` (two frontmatter schemas exist)

Frontmatter comes in two shapes across an agent's history:

```yaml
# older files                      # newer files
---                                ---
name: ...                          name: ...
type: project                      description: ...
---                                metadata:
                                     type: project
                                   ---
```

Read `type` as: the value of a top-level `type:` **or** a `metadata.type:` — whichever is present. **Ignore `node_type:`** (it's always `memory` and is not the classification). A naive `grep '^type:'` misses the nested form and a loose `type:` match catches `node_type:` — do neither.

## Age tiers (defaults — tunable)

| Tier | Age since last meaningful update | Action |
|---|---|---|
| **Hot** | < 1 week | leave verbatim |
| **Warm** | 1 week – 1 month | condense in place (unless it's near-all identifiers — see step 3) |
| **Cold** | > 1 month **and** the work is done/inactive (see below) | relocate to `memory/archive/`, drop from the live index |

"Age" means the file's last *real* update, not filesystem mtime — a bulk clone or migration resets mtime. Read it from git:

```bash
git log -1 --format=%cs -- memory/<file>.md    # last-commit date (YYYY-MM-DD)
```

If the file's body/frontmatter carries a more recent date, prefer that.

### What counts as "done/inactive" (the crux of the cold rule)

Being old is **necessary but not sufficient** for cold. Archive an old `project` file **only if** its own text reads as finished — "shipped", "complete", "merged", "closed", "resolved", a dated one-off session/incident writeup — **and** it is not a living overview.

**Standing keep class — never archive by clock, even when old** (flag in the digest instead):
- roadmaps, system/platform overviews, repo overviews, role/charter descriptions (living reference state);
- anything whose text says "STILL OPEN", "pending", "TODO", "blocked on", "awaiting", or otherwise describes unfinished work;
- files referenced by `AGENTS.md` or `identity/*.md`.

This distinction is what keeps clock-based aging from silently deleting live context. When in doubt, it's a keep.

## How to run this (context isolation)

This routine reads and rewrites the entire `memory/` tree — heavy work that would bloat your live session's context, which matters because the weekly memory-compaction job fires this skill **inside your live session**. So **delegate the work to a subagent**:

- Spawn one general-purpose subagent. Tell it to follow this skill (`skills/compact-memory/SKILL.md`) against `memory/` — execute steps 1–5 and 7 (inventory → classify → condense → archive → index → commit) — and to return **only the digest payload**: the counts (condensed / archived / kept), `MEMORY.md` size before → after, and the list of standing-keep flags. It must **not** send any message itself.
- You (the main session) then do step 6: send that digest to your primary channel.

This keeps only a short summary in your live context — the whole point when the job fires while you may be mid-conversation. The subagent shares the repo and filesystem. Claude Code may auto-commit writes through its PostToolUse hook, while Codex will not; the explicit commit in step 7 is required in either runtime and safely handles both writes and `git rm` deletions.

(When you invoke this interactively — `/compact-memory` in Claude Code or `$compact-memory` in Codex — and don't care about context cost, you may run the steps directly instead of delegating.)

## Process

1. **Inventory.** List `memory/*.md` and read `MEMORY.md`. For each file record its `type` (per the two-schema rule above), last-update date (git command above), and current byte size. Note the current byte size of `MEMORY.md`.

2. **Classify.** Bucket each file hot / warm / cold. Apply type-aware aging (evergreen `user`/`feedback`/`reference` stay unless inaccurate) **and** the done/inactive test for cold `project` files. Produce the archive set (cold + done) and the warm-condense set; everything else is kept.

3. **Warm — condense in place.** Rewrite each warm file to a compact form: keep the frontmatter, keep every exact identifier / decision / error→fix pair, compress the surrounding story. **Low-prose exception:** if a warm file is already near-all identifiers, commands, or thresholds (a dense playbook/checklist with little narrative to cut), condensing is net-negative — leave it verbatim and note it in the digest. Condense only where there's prose to remove. Update the file's one-line pointer in `MEMORY.md` if its hook changed.

4. **Cold — archive.** For each file in the archive set:
   - Ensure `memory/archive/` exists (`mkdir -p memory/archive`).
   - Capture the source commit for re-expansion: `git log --format=%h -- memory/<file>.md | head -1`.
   - Choose the archive file by **owning system/repo**: `memory/archive/<system>.md` (e.g. `kyber-history.md`, `falcon-history.md`); a cross-cutting file goes under its *primary* system. Fall back to `memory/archive/<YYYY-MM>.md` only when there's no clear system. Keep any single archive file from ballooning — if one grows past ~30–40 KB, split it by period.
   - Append a heavily-condensed entry: one entry per source file, keeping all exact identifiers and citing the source commit hash so the full original is recoverable.
   - `git rm memory/<file>.md` (the full text survives in history).
   - Remove its pointer from the live `MEMORY.md` body and add/keep a short `## Archived` pointer line for its system (e.g. "`archive/kyber-history.md` — shipped Kyber work through <period>"). Don't leave archived topics silently invisible.

5. **Index hygiene.** Rewrite `MEMORY.md` so the live section is lean and scannable — one tight line per hot/warm memory — plus the `## Archived` section pointing at `memory/archive/`. Realistic targets: archiving alone lands `MEMORY.md` around ~18 KB; to get further under the 25 KB start-load budget, also **tighten the surviving one-liners** (they, not the removed pointers, are most of the bytes). Aim for the low-18s KB from archiving, lower if you tighten.

6. **Digest.** Send one short, phone-scannable message to your primary channel (Telegram / Slack / session text): counts (condensed / archived / left alone), `MEMORY.md` size before → after, and anything you were unsure about and kept (the standing-keep flags, any dense warm file left verbatim). This is the review tripwire — git holds the full revertible diff underneath, so keep the message to a glance.

7. **Commit + verify.** Claude Code may auto-commit archive-file Writes through its PostToolUse hook; Codex does not. A `git rm` also triggers no hook. Therefore, after all Writes and removals, **always** run the explicit commit yourself:

   ```bash
   cd ~/dev/<agent>-agent
   git add -A memory/ && git commit -m "memory: weekly compaction" && git push
   git status --porcelain            # must be empty
   ```

   Confirm the working tree and remote are clean before you finish.

## Off-schedule size-guard

If you were invoked because `MEMORY.md` is near the 25 KB budget rather than on the weekly clock, run the same process but prioritize the largest and oldest done `project` files first — the goal is to get back under budget in one pass. The weekly clock and the size ceiling are belt-and-suspenders; either can trigger a run.

## What this routine must never do

- Touch, delete, or rewrite the raw transcript layer (you have no access — it lives in object storage, written by the saver sidecar).
- Rewrite git history or force-push. Every change here is an ordinary, revertible commit.
- Delete a memory's information outright, or archive a file that reads as still-open/living. Cold memories are *relocated* to `memory/archive/` with a commit citation, never erased.
