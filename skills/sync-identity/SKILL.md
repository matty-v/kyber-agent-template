---
name: sync-identity
description: The standard, only-safe way to save any change to your own agent identity repo — SOUL, PRINCIPLES, AGENTS.md, skills/, docs/, memory/, state/. Pulls the latest main FIRST (so you never diverge from origin and wedge your repo), then commits and pushes using the Kyber Platform GitHub App token. Run it BEFORE you start editing your identity (to get current) and again AFTER any edit (to commit + push). Use it any time you touch a tracked file in your identity repo — never leave identity changes uncommitted, and never edit without pulling first. This is your default workflow; the operator should never have to remind you to commit and push.
---

# /sync-identity — keep your identity repo current and saved

Your identity repo (the directory you run in, `matty-v/<you>-agent`) is the durable record of who you are. A fresh session boots from `origin/main` — so anything you change but don't push is lost, and anything you commit without pulling first can **diverge** from origin and wedge your repo (a fresh boot's `git pull` then fails, and your auto-memory backups stop pushing). This skill is the one safe way to save identity changes. **Auth is automatic** — the Kyber Platform GitHub App token is served by the credential helper already wired in your `~/.gitconfig`; you never touch a token.

## When to run it
- **Before** you edit your identity (SOUL, PRINCIPLES, AGENTS.md, a skill, a doc) — pull first so you edit the latest.
- **After** any edit to a tracked file — commit + push. Don't wait to be told; saving your identity is your job, not the operator's.
- Any time you're unsure your working tree is saved.

## Do this (copy-paste, in your identity repo directory)

```bash
# 0. sanity: you're in your identity repo
git remote get-url origin            # expect https://github.com/matty-v/<you>-agent.git

# 1. PULL FIRST — always. Rebase your work onto the latest main.
#    --autostash shelves any uncommitted edits, pulls+rebases, re-applies them,
#    so this is safe whether or not you've already started editing.
#    This is the step that prevents divergence. Never skip it. Never --force.
git pull --rebase --autostash

# 2. (make your edits now, if you haven't already)

# 3. commit everything pending (identity + memory + state); skip if nothing changed
git add -A
git commit -m "<one line: what changed>"     # e.g. identity: tighten SOUL voice section

# 4. push — the credential helper supplies the Kyber App token automatically
git push

# 5. confirm: clean tree, in sync
git status -sb                        # expect: ## main...origin/main  (nothing ahead/behind)
```

## If the pull hits a conflict (rare — your edit and origin touched the same lines)
Resolve by **keeping both** where the changes are additive (two appends to the same list), or the newer/correct version where they genuinely conflict — then `git add <file>` and `git rebase --continue`. If you can't tell, `git rebase --abort`, re-read the current file, and redo your edit on top of it. Never resolve by force-pushing or discarding origin's work.

## Notes
- **Token:** `credential.https://github.com.helper` in `~/.gitconfig` (`git-credential-kyber-github`) mints a short-lived **Kyber Platform App token** scoped to your identity repo — no PAT, nothing to manage. If a push fails with `could not read Username`, your `KYBER_*` env or the control-plane is unavailable — report it, don't fall back to a personal token.
- Treat an uncommitted identity change like unsaved work: finish it by running this. Pull → edit → `sync-identity` is your default loop.
