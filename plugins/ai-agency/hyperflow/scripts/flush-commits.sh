#!/usr/bin/env bash
# flush-commits.sh — replay the chain's staging-branch commits onto the user's branch.
#
# Used at /hyperflow:dispatch Step 4 wrap-up when commit-when=end was selected.
# Also runs as /hyperflow:flush for crash recovery.
#
# Behavior:
#   1. Read .hyperflow/commits-queue/manifest.json to find staging branch + user branch.
#   2. Switch to user's branch.
#   3. Fast-forward merge staging branch onto user's branch (every commit comes
#      across in chronological order; original messages + SHAs unchanged).
#   4. Delete staging branch.
#   5. Clear the queue directory.
#
# If fast-forward isn't possible (user diverged mid-chain), surface the error
# and leave staging branch in place — user resolves manually.
#
# Pre-commit hooks: queue-commit.sh runs hooks per sub-task on the staging
# branch (no --no-verify, ever). At flush time the commits already exist with
# messages + content frozen, so git merge --ff-only does not re-run hooks. If a
# user wants hooks to gate the final flushed state on the user's branch, they
# run them manually after flush; lint + typecheck + tests are already covered
# by dispatch Step 2b quality gates per sub-task.
#
# Usage:
#   flush-commits.sh <project-root> [--dry-run]
#
# Exits 0 on success, non-zero on failure.

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "flush-commits: usage: flush-commits.sh <project-root> [--dry-run]" >&2
  exit 2
fi

PROJECT_ROOT="$1"
DRY_RUN=""
if [ "${2:-}" = "--dry-run" ]; then
  DRY_RUN="1"
fi

QUEUE_DIR="$PROJECT_ROOT/.hyperflow/commits-queue"
MANIFEST="$QUEUE_DIR/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  echo "flush-commits: no queue to flush ($MANIFEST not found)"
  exit 0
fi

cd "$PROJECT_ROOT"

USER_BRANCH="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['user_branch'])")"
STAGING_BRANCH="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['staging_branch'])")"
COMMIT_COUNT="$(python3 -c "import json; print(len(json.load(open('$MANIFEST'))['commits']))")"

if [ "$COMMIT_COUNT" = "0" ]; then
  echo "flush-commits: queue is empty (no commits were queued during chain)"
  if [ -z "$DRY_RUN" ]; then
    if git rev-parse --verify --quiet "$STAGING_BRANCH" >/dev/null; then
      git branch -D "$STAGING_BRANCH"
    fi
    rm -rf "$QUEUE_DIR"
  fi
  exit 0
fi

# Check staging branch exists.
if ! git rev-parse --verify --quiet "$STAGING_BRANCH" >/dev/null; then
  echo "flush-commits: staging branch $STAGING_BRANCH does not exist — manifest is stale, clearing queue" >&2
  if [ -z "$DRY_RUN" ]; then
    rm -rf "$QUEUE_DIR"
  fi
  exit 0
fi

if [ -n "$DRY_RUN" ]; then
  echo "flush-commits (DRY RUN): would fast-forward $COMMIT_COUNT commits from $STAGING_BRANCH onto $USER_BRANCH"
  git log --oneline "$USER_BRANCH..$STAGING_BRANCH"
  exit 0
fi

# Switch back to user's branch.
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$USER_BRANCH" ]; then
  git checkout "$USER_BRANCH"
fi

# Fast-forward merge. This brings every staging commit across in order with
# original SHAs preserved.
if ! git merge --ff-only "$STAGING_BRANCH" 2>>"$PROJECT_ROOT/.hyperflow/.commits-queue.log"; then
  echo "flush-commits: fast-forward failed — user branch diverged from staging." >&2
  echo "flush-commits: staging branch $STAGING_BRANCH preserved for manual resolution." >&2
  echo "flush-commits: try: git rebase $STAGING_BRANCH OR git cherry-pick $STAGING_BRANCH..HEAD" >&2
  exit 5
fi

# Delete staging branch and clear queue dir.
git branch -D "$STAGING_BRANCH" 2>>"$PROJECT_ROOT/.hyperflow/.commits-queue.log"
rm -rf "$QUEUE_DIR"

echo "flush-commits: flushed $COMMIT_COUNT commits onto $USER_BRANCH"
git log --oneline -n "$COMMIT_COUNT" "$USER_BRANCH"
