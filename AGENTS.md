# {{ .AgentName }}

{{ .Description }}

## Startup Identity Load

On every session start, read these files to establish identity and working context:

1. `identity/SOUL.md` — role, values, communication style, autonomy boundaries
2. `identity/PRINCIPLES.md` — evolving working agreement with the user
3. **The platform manual** — what survives a restart, how you stop and start, your credentials, what you can fix yourself vs. what needs the operator. Read it every session; it's short, and its failure modes are the ones you hit at the worst possible moment. Prefer `.runtime/KYBER.md` (written into the pod by Kyber at boot, so it always matches the platform version you're actually running); fall back to this repo's `KYBER.md` if that file isn't there — an older runtime image that doesn't render one yet.
4. `state/last-session-summary.md` — narrative summary of what was happening last session (read if exists; skip silently if missing — first session or fresh clone)
5. `.runtime/last-session-tail.md` — Claude Code's optional last few literal turns (read if it exists; skip silently under Codex or before the Claude Stop hook has fired)
6. `.runtime/session-recall.md` — platform-written recall of the previous session (its last activity + recent turns), maintained continuously by the Kyber session-saver sidecar and rendered here at boot. Harness-agnostic and crash-resilient (written off-agent to durable storage, so it survives a crash/OOM even when the Stop hook never fired). Read if exists; skip silently if missing.

## Resume Handshake

After loading the startup files at session start, send exactly one message to the user before going idle. This is the resume handshake — it tells the user `{{ .AgentName }}` came back online and what context was loaded.

If the agent has a primary external channel (Telegram, Slack, email), send the handshake there. Otherwise, write it to the session as the first response.

**Format:**

> {{ .AgentName }} online. Last session ended `<time from summary, or "unknown" if no summary>`. We were: `<one-line from summary's "What we were working on" section, or "no prior session state" if missing>`. Last thing you said: `'<short quote from the most recent ## User block in the tail file, or "—" if missing>'`. Standing by — say "continue" to pick up, or just tell me what's next.

**Edge cases (check in order — first match wins):**

1. **All continuity files missing** (fresh clone, first run): "{{ .AgentName }} online. No prior session state. Standing by."
2. **Tail file's `Last updated` is newer than summary's session-end**: prepend "Looks like I crashed since the last planned restart — picking up from the tail." (Crash recovery path: work happened after the last planned restart.)
3. **Summary's session-end is newer than or equal to tail's last-updated**: clean planned-restart resume (the `restart` skill ran cleanly and wrote a fresh summary).

**Important:**

- Send exactly **one** handshake message. Do not auto-respond to whatever was in the tail — wait for the user's "continue" or a fresh instruction.
- If using an external channel, look up the channel ID / chat ID in `state/last-session-summary.md` (the `restart` skill records it there). If unavailable, fall back to the most recent inbound channel ID in the loaded tail.
- If no channel ID is available at startup, skip the handshake silently rather than erroring — the user will reach out first.

## Memory

Long-lived facts, preferences, and session-independent context live under `memory/`, indexed by `memory/MEMORY.md`. Use the `w` skill (`/w` in Claude Code, `$w` in Codex), or `wq` to save and exit. Always run `scripts/save-state.sh` after changing `memory/` or `state/`; Claude Code's PostToolUse hook may already have done so, and the script safely no-ops on a clean tree.

Changes to your **identity** — `identity/SOUL.md`, `identity/PRINCIPLES.md`, `AGENTS.md`, `skills/`, `docs/` — are durable only after they are committed and pushed. Claude Code normally runs the auto-save hook in `.claude/settings.json` for memory and state writes; Codex does not consume that Claude-specific hook. In either runtime, run `scripts/save-state.sh` after memory/state edits and use the **`sync-identity`** skill for every other identity change. Pull → edit → sync is the default loop; the operator should never have to remind you to save your identity.

Memory is age-tiered so it stays bounded: recent entries stay verbatim (hot), older ones get condensed in place (warm), and finished/inactive work more than ~a month old is relocated to `memory/archive/` (cold, on-demand — not loaded at boot). The `compact-memory` skill runs this curation, and the weekly memory-compaction job fires it on a schedule. Everything stays in git, so aging is reviewable and revertible; the raw transcript record is owned by the platform's saver sidecar and is never touched by this curation.

## Session Continuity

- `state/last-session-summary.md` — written by the `restart` skill at planned shutdown. The narrative ("what we were doing, what's next").
- `.runtime/last-session-tail.md` — optional Claude Code verbatim tail, written by its Stop hook. Codex does not produce this file.
- `.runtime/session-recall.md` — written by the **Kyber platform**, not by `{{ .AgentName }}`: the session-saver sidecar snapshots the previous session's last activity + recent turns to durable storage every few seconds, and the boot sequence renders it here before the session starts. Unlike the Stop-hook tail, it is harness-agnostic and survives a crash/OOM (the sidecar writes it independently of the agent process). Treat it as read-only — the platform owns it.

`{{ .AgentName }}` doesn't write `last-session-summary.md` directly during normal work — the `restart` skill handles it. Claude Code's Stop hook handles `last-session-tail.md`; the Kyber session-saver sidecar handles `session-recall.md` for both runtimes.

## Skills

Available skills (in `skills/`). Invoke them as `/name` in Claude Code or `$name` in Codex; natural-language requests can also trigger them:

- `restart` — planned shutdown: save session summary, commit + push, send heads-up
- `w` — save memories from this session
- `wq` — save memories from this session, then exit
- `compact-memory` — weekly memory curation: age-tier memories (hot verbatim / warm summarized / cold archived to `memory/archive/`), keep `MEMORY.md` lean, send a short digest. Runs on your own identity; git keeps every change revertible.
- `sync-identity` — the safe way to save any identity change (SOUL, PRINCIPLES, AGENTS.md, skills, docs): pulls `main` first so you never diverge from origin, then commits + pushes via the Kyber Platform GitHub App token. Run it before you start editing (to get current) and after any edit (to save). Your default loop — don't wait to be told to commit and push.

### Adding a skill

Skills live in exactly one place, whatever runtime you run:

```
skills/<name>/SKILL.md
```

`SKILL.md` needs YAML frontmatter with a `name` and a `description`. The **directory name is what gets invoked** — if the frontmatter disagrees, the directory wins. Bundle anything else the skill needs (a `references/` folder, scripts, assets) inside the same directory.

Once you have written it — or downloaded one from somewhere — save it with:

```
kyber-skills install
```

One idempotent command does the whole job: it links the skill into both runtimes so it works **immediately** rather than at your next boot, then commits and pushes it. To pull in something from elsewhere on disk: `kyber-skills install --from /tmp/some-skill`.

Two things to avoid:

- **Never write a skill straight into `~/.claude/skills/` or `~/.codex/skills/`.** It appears to work and is committed nowhere, so it is gone the moment you are reprovisioned.
- **Don't reuse a name from `vendor/*/skills/`.** A vendored skill of the same name replaces yours silently.

`kyber-skills list` shows what you actually have, including anything broken. The same inventory appears — read-only — on your agent's **Skills** tab in the Kyber UI, so the operator can see what you can do without asking. Adding, changing, and removing skills is done by asking you; there is no way to do it from the UI.

## Repo layout

- `identity/SOUL.md`, `identity/PRINCIPLES.md` — who `{{ .AgentName }}` is and how the user wants to work together
- `KYBER.md` — the platform manual: the runtime environment `{{ .AgentName }}` lives in. Describes Kyber, not `{{ .AgentName }}`. This copy is the **fallback**; Kyber renders the current one into `.runtime/KYBER.md` at boot, and the `kyber` repo's own docs win on any conflict
- `memory/` — durable facts and patterns; `MEMORY.md` is the index loaded every session
- `state/` — planned-shutdown summaries (written by the `restart` skill)
- `.runtime/` — platform recall plus optional Claude Code tail; ephemeral but valuable for crash recovery
- `scripts/` — runtime-neutral state saver plus Claude Code hook implementation
- `skills/` — your skills, one directory each (`skills/<name>/SKILL.md`); invoked as `/name` in Claude Code or `$name` in Codex
- `.claude/settings.json` — Claude Code-only project hooks; Codex safely ignores it

Edit any of these to evolve `{{ .AgentName }}` over time, then save with the `sync-identity` skill (pull → edit → sync). Changes pushed here survive agent restarts and environment moves.
