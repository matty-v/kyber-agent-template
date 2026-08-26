#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

git init --bare "${TMP}/remote.git" >/dev/null
git init -b main "${TMP}/repo" >/dev/null
cd "${TMP}/repo"
git config user.name test-agent
git config user.email test@example.invalid
git remote add origin "${TMP}/remote.git"
mkdir -p memory state scripts identity
cp "${ROOT}/scripts/save-state.sh" scripts/save-state.sh
printf 'base\n' > memory/MEMORY.md
printf 'base\n' > state/last-session-summary.md
printf 'base\n' > identity/SOUL.md
git add .
git commit -m initial >/dev/null
git push -u origin main >/dev/null

printf 'identity edit\n' >> identity/SOUL.md
git add identity/SOUL.md
printf 'state edit\n' >> state/last-session-summary.md

bash scripts/save-state.sh >/dev/null

changed="$(git diff-tree --no-commit-id --name-only -r HEAD)"
[[ "${changed}" == 'state/last-session-summary.md' ]] || {
  echo "[FAIL] auto-save commit captured paths outside state/: ${changed}"
  exit 1
}
git diff --cached --quiet -- identity/SOUL.md && {
  echo '[FAIL] pre-staged identity edit was consumed by auto-save commit'
  exit 1
}
echo '[PASS] save-state commits only memory/ and state/ paths'
