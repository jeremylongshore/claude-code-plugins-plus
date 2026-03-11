#!/usr/bin/env bash
# Quality gate hook for product-catalog documents.
# Fires after Write/Edit — reminds Claude to check the quality bar
# when writing to the product-catalog/ directory.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.file // empty' 2>/dev/null || true)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

if echo "$FILE_PATH" | grep -q "product-catalog/"; then
  cat <<'REMINDER'
[PM Quality Gate] This file is in product-catalog/ — the shareable artifact directory.
Before finalizing, verify this document meets the quality bar:
- [ ] Accurate: Claims backed by evidence (code, data, or docs)
- [ ] Clear: A reader unfamiliar with context can follow it
- [ ] Owned: Has a clear author and date
- [ ] Evidenced: Links to supporting data or analysis
- [ ] Audience-appropriate: Tone and detail level match the reader
REMINDER
fi
