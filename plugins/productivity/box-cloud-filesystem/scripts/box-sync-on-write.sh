#!/usr/bin/env bash
# PostToolUse hook: auto-sync files to Box after Write/Edit
# Reads tool_input JSON from stdin, uploads changed files to Box cloud storage.
# Only fires for files inside the configured Box workspace directory.
# Requires: box CLI (@box/cli), jq

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.file // empty' 2>/dev/null)

# Exit silently if no file path extracted
[ -z "$FILE_PATH" ] && exit 0

# Exit if Box workspace not configured
BOX_CONFIG="${HOME}/.box-cloud-filesystem.json"
[ ! -f "$BOX_CONFIG" ] && exit 0

WORKSPACE=$(jq -r '.workspace' "$BOX_CONFIG" 2>/dev/null)
BOX_FOLDER_ID=$(jq -r '.box_folder_id' "$BOX_CONFIG" 2>/dev/null)

# Only sync files inside the configured workspace
[[ "$FILE_PATH" != "$WORKSPACE"* ]] && exit 0

# Verify the file actually exists on disk
[ ! -f "$FILE_PATH" ] && exit 0

MANIFEST="$WORKSPACE/.box-manifest.json"
BASENAME=$(basename "$FILE_PATH")
ACTION="unknown"
FILE_ID=""
NEW_ID=""

if [ -f "$MANIFEST" ]; then
  FILE_ID=$(jq -r --arg name "$BASENAME" \
    '.entries[]? | select(.name == $name) | .id' "$MANIFEST" 2>/dev/null)

  if [ -n "$FILE_ID" ] && [ "$FILE_ID" != "null" ]; then
    # Known file — upload as new version (preserves history)
    box files:versions:upload "$FILE_ID" "$FILE_PATH" 2>/dev/null
    ACTION="version_upload"
  else
    # New file — upload to the Box folder
    RESULT=$(box files:upload "$FILE_PATH" --parent-id "$BOX_FOLDER_ID" --json 2>/dev/null)
    NEW_ID=$(echo "$RESULT" | jq -r '.entries[0].id // empty' 2>/dev/null)

    # Append new file to the manifest so subsequent edits use version upload
    if [ -n "$NEW_ID" ] && [ "$NEW_ID" != "null" ]; then
      TIMESTAMP=$(date -Iseconds)
      jq --arg name "$BASENAME" --arg id "$NEW_ID" --arg ts "$TIMESTAMP" \
        '.entries += [{"name": $name, "id": $id, "content_modified_at": $ts}]' \
        "$MANIFEST" > "${MANIFEST}.tmp" && mv "${MANIFEST}.tmp" "$MANIFEST"
    fi
    ACTION="new_upload"
  fi
else
  # No manifest — upload as new file
  RESULT=$(box files:upload "$FILE_PATH" --parent-id "$BOX_FOLDER_ID" --json 2>/dev/null)
  NEW_ID=$(echo "$RESULT" | jq -r '.entries[0].id // empty' 2>/dev/null)
  ACTION="new_upload"
fi

# Log the sync action for the Stop hook summary
LOG_FILE="$WORKSPACE/.box-sync.log"
echo "$(date -Iseconds) $ACTION $BASENAME ${FILE_ID:-$NEW_ID}" >> "$LOG_FILE"
