#!/usr/bin/env bash
# Draft status hook for sandbox documents.
# Fires after Write/Edit — reminds Claude that sandbox files are drafts
# and suggests adding status metadata.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.file // empty' 2>/dev/null || true)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

if echo "$FILE_PATH" | grep -q "sandbox/" && echo "$FILE_PATH" | grep -qE '\.md$'; then
  HAS_STATUS=$(head -20 "$FILE_PATH" 2>/dev/null | grep -ci "status:" || true)
  if [ "$HAS_STATUS" -eq 0 ]; then
    cat <<'REMINDER'
[PM Draft Status] This file is in sandbox/ but has no status marker.
Consider adding a status line near the top:
  **Status:** Draft | Ready for Review | Final
This helps track what's work-in-progress vs ready to graduate to product-catalog/.
REMINDER
  fi
fi
