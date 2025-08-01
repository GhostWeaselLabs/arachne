#!/usr/bin/env bash
set -euo pipefail
test -f "Arachne/README.md" || { echo "Run from the repo root containing Arachne/"; exit 1; }
git add -A
if ! git diff --cached --quiet; then
  git commit -m "docs: governance, roadmap, support; README map; smart .gitignore; ownership update (Lead: doubletap-dave); changelog (2025-08-01)"
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "No 'origin' remote found. Creating GitHub repo via gh CLI..."
  gh repo create GhostWeasel/Arachne --public --source=. --push
else
  CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo '')"
  if [ -z "$CURRENT_BRANCH" ]; then CURRENT_BRANCH="main"; fi
  if [ "$CURRENT_BRANCH" != "main" ]; then
    git branch -M main
  fi
  git push -u origin main
fi
