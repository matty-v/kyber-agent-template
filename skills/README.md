# Skills

A skill is a reusable workflow this agent can invoke — `/name` in Claude Code,
`$name` in Codex — and that either runtime can also trigger on its own when the
description matches what is being asked.

## The layout

```
skills/
  <name>/
    SKILL.md        # required
    references/     # optional: anything else the skill needs
```

`SKILL.md` starts with YAML frontmatter:

```markdown
---
name: <name>
description: What this does, and when to reach for it.
---

The instructions the agent follows.
```

The **directory name is what gets invoked**. If the frontmatter `name`
disagrees with it, the directory wins — keep them the same.

## Why this exact path

Kyber links every `skills/<name>/` package into **both** runtime homes
(`~/.claude/skills/` and `~/.codex/skills/`) at boot and on every identity
sync. That is what makes one identity repo work under either runtime, and it is
what lets the platform report the agent's skills back to the Kyber UI.

Skills vendored from a shared package live under `vendor/<package>/skills/` and
are not this agent's to edit. A vendored skill **replaces** one of the agent's
own with the same name, so pick distinct names.

## Saving a skill

Inside a Kyber pod:

```
kyber-skills install                       # save what is already in skills/
kyber-skills install --from /tmp/some-skill  # import from elsewhere on disk
kyber-skills list                          # what the agent has, and what is broken
```

`install` is idempotent. It links the skill into both runtimes so it works
immediately instead of at the next boot, then commits and pushes it here.

Writing a skill directly into `~/.claude/skills/` or `~/.codex/skills/` looks
like it works and is the one reliable way to lose it: nothing there is
committed, so it disappears when the pod is reprovisioned.

## What the operator sees

The agent's skills appear on its **Skills** tab in the Kyber UI, read-only.
That view is a scan of the pod's real filesystem rather than of this repo, so a
skill that is committed but not loadable shows up as broken instead of fine.
Adding, changing, and removing skills is done by asking the agent.
