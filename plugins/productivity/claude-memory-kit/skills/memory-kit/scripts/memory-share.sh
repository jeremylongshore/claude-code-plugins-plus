#!/usr/bin/env bash
# memory-share.sh — Stage, commit, and push MEMORY.md in one shot
set -euo pipefail

if [ ! -f MEMORY.md ]; then
  echo "ERROR: No MEMORY.md found in current directory"
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: Not inside a git repository"
  exit 1
fi

TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
BRANCH=$(git branch --show-current)

git add MEMORY.md
git commit -m "chore: update session memory [${TIMESTAMP}]"

if git push; then
  echo "Memory synced to ${BRANCH} at ${TIMESTAMP}"
else
  echo "ERROR: Push failed. Try: git pull --rebase && git push"
  exit 1
fi
