#!/bin/bash
# Boycott Filter — Setup Script
#
# Starts the local sync server and provides Chrome extension instructions.

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$PLUGIN_DIR/scripts/server.js"
LIST_FILE="$PLUGIN_DIR/boycott-list.json"

# Create empty boycott list if it doesn't exist
if [ ! -f "$LIST_FILE" ]; then
  echo '{"companies":[],"updated_at":null}' > "$LIST_FILE"
  echo "Created empty boycott list at $LIST_FILE"
fi

# Check if server is already running
if curl -s http://127.0.0.1:7847/health > /dev/null 2>&1; then
  echo "Boycott Filter server is already running on port 7847."
else
  echo "Starting Boycott Filter server..."
  node "$SERVER" &
  sleep 1
  if curl -s http://127.0.0.1:7847/health > /dev/null 2>&1; then
    echo "Server started successfully on http://127.0.0.1:7847"
  else
    echo "ERROR: Server failed to start. Check if port 7847 is available."
    exit 1
  fi
fi

echo ""
echo "=== Chrome Extension Setup ==="
echo ""
echo "Load the extension manually (one-time):"
echo "  1. Open chrome://extensions"
echo "  2. Enable 'Developer mode' (top right)"
echo "  3. Click 'Load unpacked'"
echo "  4. Select: $PLUGIN_DIR/extension/"
echo ""
echo "Done! Tell your Claude agent which brands to boycott."
