# Kyber agent identity template

This repository is the public scaffold Kyber uses to create a durable identity
repository for a managed agent. Kyber replaces template expressions such as
`{{ .AgentName }}` and `{{ .Description }}` while scaffolding the private
identity repository owned by that agent.

The template contains identity documents, an initially empty memory index,
session-continuity hooks, and reusable skills. It intentionally contains no
real agent identity, user profile, memory, session state, credentials, or
communication identifiers.

## Security model

This is a runtime template, not a safe configuration for running Claude Code
directly on an untrusted workstation. `.claude/settings.json` suppresses
Claude Code's dangerous-mode permission prompt because Kyber runs the agent in
an isolated Kubernetes pod with platform-owned security controls. Review or
remove that setting before using this repository outside Kyber.

Never add rendered identity repositories, memory files, session tails,
credentials, API keys, bot tokens, channel IDs, or user-specific configuration
to this template. Generated agent identity repositories should normally remain
private.

## Layout

- `identity/SOUL.md` — who `{{ .AgentName }}` is: role, communication style, values, autonomy boundaries
- `identity/PRINCIPLES.md` — evolving working agreement with the user (corrections + agreements over time)
- `AGENTS.md` — canonical runtime-neutral identity instructions; Codex reads it directly
- `CLAUDE.md` — Claude Code compatibility entrypoint pointing to `AGENTS.md`
- `KYBER.md` — the platform manual: what an agent needs to know about *running on Kyber* (durability tiers, lifecycle phases, credentials, how work reaches it, what it can fix itself vs. what needs the operator). Loaded at startup through the canonical instructions. This documents the platform, not the agent — the `kyber` repo's docs are the source of truth if it goes stale
- `memory/` — topic-indexed long-term memory; `MEMORY.md` is the index loaded every session
- `state/` — planned-shutdown summaries (written by the `restart` skill)
- `.runtime/` — platform recall plus optional Claude Code tail; ephemeral recovery context
- `scripts/` — runtime-neutral state saver plus Claude Code hook implementation
  - `save-state.sh` — auto-commit + push when memory/ or state/ files change
  - `write_session_tail.py` — writes `.runtime/last-session-tail.md` after every assistant turn
- `skills/` — shared workflows, invoked as `/name` in Claude Code or `$name` in Codex
  - `restart` — planned shutdown: save summary, commit, push, send heads-up
  - `w` — save memories from this session
  - `wq` — save memories from this session, then exit
- `.claude/settings.json` — Claude Code-only project hooks; ignored by Codex

## How it works

On pod boot, Kyber clones this repo to `~/dev/{{ .AgentName }}-agent` and starts the selected runtime there. Codex reads `AGENTS.md` directly. Claude Code reads the small `CLAUDE.md` compatibility entrypoint, which directs it to the same canonical `AGENTS.md`. Both runtimes therefore load the same identity, memory, recovery, and Resume Handshake contract.

The Claude Code PostToolUse hook in `.claude/settings.json` calls `scripts/save-state.sh` on every Write/Edit/MultiEdit. Codex does not consume that Claude-specific settings file, so the shared instructions and memory skills tell either runtime to run `scripts/save-state.sh` explicitly after memory/state edits. The script commits and pushes those paths so they survive reprovisioning.

Claude Code's Stop hook calls `scripts/write_session_tail.py` after every assistant turn. Codex does not use that hook; both runtimes instead receive `.runtime/session-recall.md` from Kyber's harness-independent session-saver sidecar. The Resume Handshake treats the Claude-only tail as optional and the platform recall as the cross-runtime recovery source.

## Customizing

- **Identity**: edit `identity/SOUL.md` and `identity/PRINCIPLES.md` to evolve who `{{ .AgentName }}` is.
- **Memory**: use `/w` in Claude Code or `$w` in Codex, or hand-edit files under `memory/`. Run `scripts/save-state.sh` afterward; it safely no-ops if Claude's hook already committed the change.
- **Claude Code plugins**: add project plugin settings under `.claude/` when needed. Telegram is platform-owned through the Kyber MCP sidecar; never enable the retired Telegram plugin here.
- **Claude Code hooks**: add Stop / PostToolUse / UserPromptSubmit hooks in `.claude/settings.json`. Codex ignores this file, so shared behavior belongs in `AGENTS.md`, scripts, or skills instead.
- **Skills**: drop new skills under `skills/<name>/SKILL.md` with frontmatter (name, description). They become available as `/<name>` in Claude Code and `$<name>` in Codex, with implicit triggering from a matching description in either runtime.

## See also

- Kyber docs on [agent identity repos](https://github.com/matty-v/kyber/blob/main/docs/agents-identity-repos.md)
- [Kyber](https://github.com/matty-v/kyber), the platform that renders and
  consumes this template.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
