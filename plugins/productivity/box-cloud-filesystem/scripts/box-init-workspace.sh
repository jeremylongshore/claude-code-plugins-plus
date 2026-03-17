#!/usr/bin/env bash
# Initialize a Box workspace: download folder contents and build a manifest.
# Usage: box-init-workspace.sh <BOX_FOLDER_ID> [WORKSPACE_PATH]
# Requires: box CLI (@box/cli), jq

set -euo pipefail

BOX_FOLDER_ID="${1:?Usage: box-init-workspace.sh <BOX_FOLDER_ID> [WORKSPACE_PATH]}"
WORKSPACE="${2:-/tmp/box-workspace}"

# Verify Box CLI is available and authenticated
if ! command -v box &>/dev/null; then
  echo "Error: box CLI not found. Install with: npm install --global @box/cli" >&2
  exit 1
fi

if ! box users:get --me &>/dev/null; then
  echo "Error: Box CLI not authenticated. Run: box login" >&2
  exit 1
fi

mkdir -p "$WORKSPACE"

# Download folder contents
echo "Downloading Box folder $BOX_FOLDER_ID to $WORKSPACE..."
box folders:download "$BOX_FOLDER_ID" --destination "$WORKSPACE"

# Build manifest (filename -> file_id mapping for sync hooks)
echo "Building file manifest..."
box folders:items "$BOX_FOLDER_ID" --json --fields name,id,content_modified_at \
  > "$WORKSPACE/.box-manifest.json"

# Save workspace config for hooks to discover
cat > "${HOME}/.box-cloud-filesystem.json" <<EOF
{
  "workspace": "$WORKSPACE",
  "box_folder_id": "$BOX_FOLDER_ID",
  "initialized_at": "$(date -Iseconds)"
}
EOF

ITEM_COUNT=$(jq '.entries | length' "$WORKSPACE/.box-manifest.json" 2>/dev/null || echo "0")

echo ""
echo "Box workspace initialized:"
echo "  Local path:  $WORKSPACE"
echo "  Box folder:  $BOX_FOLDER_ID"
echo "  Files:       $ITEM_COUNT"
echo ""
echo "Files written or edited inside $WORKSPACE will auto-sync to Box."
