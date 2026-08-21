#!/usr/bin/env bash
set -euo pipefail

# Save agent state: commit and push memory + state directories.
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# Pull first so an out-of-band write to origin (an operator edit, a cross-agent
# maintenance push) can't make the push below reject and wedge the repo.
# --autostash shelves any uncommitted work, rebases onto origin, reapplies it.
# On failure (conflict/network) abort cleanly and continue — never block.
git pull --rebase --autostash || git rebase --abort 2>/dev/null || true

git add -A memory/ state/
if ! git diff --cached --quiet; then
  git commit -m "Save state: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git push
  echo "State saved and pushed."
else
  echo "No changes to save."
fi
