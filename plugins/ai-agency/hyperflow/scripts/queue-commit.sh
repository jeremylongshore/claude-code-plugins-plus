#!/usr/bin/env bash
# queue-commit.sh — record a deferred commit on the chain's staging branch.
#
# Used by /hyperflow:dispatch when commit-when=end. Instead of committing
# directly to the user's working branch after each sub-task PASS, we commit
# to a private staging branch named hyperflow/staging-<chain-id>. At chain
# end, scripts/flush-commits.sh fast-forwards / cherry-picks the staging
# branch onto the user's branch, producing N real commits in chronological
# order (preserving per-task commit cadence + file-to-message mapping).
#
# Usage:
#   queue-commit.sh <project-root> <chain-id> "<conventional-commit-msg>" <file> [<file> ...]
#
# Exits 0 on success, non-zero on failure (caller surfaces to user).

set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "queue-commit: usage: queue-commit.sh <project-root> <chain-id> <msg> <file> [<file>...]" >&2
  exit 2
fi

PROJECT_ROOT="$1"; shift
CHAIN_ID="$1"; shift
MSG="$1"; shift

cd "$PROJECT_ROOT"

# Resolve user's working branch (only once per chain, cached in queue manifest).
QUEUE_DIR="$PROJECT_ROOT/.hyperflow/commits-queue"
MANIFEST="$QUEUE_DIR/manifest.json"
STAGING_BRANCH="hyperflow/staging-$CHAIN_ID"

mkdir -p "$QUEUE_DIR"

USER_BRANCH=""
if [ -f "$MANIFEST" ]; then
  USER_BRANCH="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['user_branch'])" 2>/dev/null || echo "")"
fi

if [ -z "$USER_BRANCH" ]; then
  USER_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  if [ "$USER_BRANCH" = "$STAGING_BRANCH" ]; then
    echo "queue-commit: already on staging branch but manifest absent — refusing to proceed" >&2
    exit 3
  fi
  STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 - <<PY
import json
data = {
  "chain_id": "$CHAIN_ID",
  "started_at": "$STARTED_AT",
  "user_branch": "$USER_BRANCH",
  "staging_branch": "$STAGING_BRANCH",
  "commits": [],
}
open("$MANIFEST", "w").write(json.dumps(data, indent=2))
PY
  # Create the staging branch from user's current HEAD if it doesn't exist.
  if ! git rev-parse --verify --quiet "$STAGING_BRANCH" >/dev/null; then
    git branch "$STAGING_BRANCH" "$USER_BRANCH"
  fi
fi

# Switch to staging branch (or no-op if already there).
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$STAGING_BRANCH" ]; then
  # Stash any uncommitted state on the user branch (in case lean mode left
  # tracked-but-unstaged work) so the checkout is clean. We only care about
  # the files this sub-task touched.
  git checkout "$STAGING_BRANCH" 2>>"$PROJECT_ROOT/.hyperflow/.commits-queue.log"
fi

# Stage only the files this sub-task touched. Per-task cadence preserved.
git add -- "$@"

# Commit. If nothing was staged (worker no-op), skip silently with success.
if git diff --cached --quiet; then
  echo "queue-commit: no changes to commit for this sub-task (no-op)" >&2
  exit 0
fi

git commit -m "$MSG" || {
  echo "queue-commit: git commit failed (hook rejection or other error) — staging branch left as-is for inspection" >&2
  echo "queue-commit: fix the rejected files and re-run dispatch from the affected sub-task (the manifest tracks what was queued)" >&2
  exit 4
}

# Record the commit in the manifest for traceability.
SHA="$(git rev-parse HEAD)"
python3 - <<PY
import json
data = json.load(open("$MANIFEST"))
data["commits"].append({
  "sha": "$SHA",
  "message": $(python3 -c "import sys,json;print(json.dumps(sys.argv[1]))" "$MSG"),
  "files": $(python3 -c "import sys,json;print(json.dumps(sys.argv[1:]))" "$@"),
  "queued_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
})
open("$MANIFEST", "w").write(json.dumps(data, indent=2))
PY

echo "queue-commit: queued $SHA on $STAGING_BRANCH ($(echo "$MSG" | head -c 60))"
