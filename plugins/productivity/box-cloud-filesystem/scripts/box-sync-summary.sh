#!/usr/bin/env bash
# Stop hook: report Box sync activity when Claude finishes responding.
# Reads the sync log written by box-sync-on-write.sh and prints a summary.

set -euo pipefail

BOX_CONFIG="${HOME}/.box-cloud-filesystem.json"
[ ! -f "$BOX_CONFIG" ] && exit 0

WORKSPACE=$(jq -r '.workspace' "$BOX_CONFIG" 2>/dev/null)
LOG_FILE="$WORKSPACE/.box-sync.log"

[ ! -f "$LOG_FILE" ] && exit 0

SYNC_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
[ "$SYNC_COUNT" -eq 0 ] && exit 0

echo ""
echo "Box Sync Summary: $SYNC_COUNT file(s) synced to Box"
while read -r ts action file id; do
  case "$action" in
    version_upload) echo "  - updated: $file (ID: $id)" ;;
    new_upload)     echo "  - uploaded: $file (ID: $id)" ;;
    *)              echo "  - $action: $file (ID: $id)" ;;
  esac
done < "$LOG_FILE"

# Clear log for next session
> "$LOG_FILE"
