#!/usr/bin/env bash
# open_in_browser.sh — OS-aware HTML file opener for engineer-design-diagram output.
# Usage: open_in_browser.sh path/to/file.html
# Exits 0 on launch attempt, non-zero if no opener found.

set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 path/to/file.html" >&2
  exit 2
fi

FILE="$1"
if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE" >&2
  exit 2
fi

# Probe openers in priority order: xdg-open (Linux), open (macOS), wslview (WSL), start (Git Bash on Windows)
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FILE" >/dev/null 2>&1 &
  echo "Opened via xdg-open: $FILE"
elif command -v open >/dev/null 2>&1; then
  open "$FILE"
  echo "Opened via macOS open: $FILE"
elif command -v wslview >/dev/null 2>&1; then
  wslview "$FILE"
  echo "Opened via wslview: $FILE"
elif command -v start >/dev/null 2>&1; then
  start "$FILE"
  echo "Opened via start: $FILE"
else
  echo "No browser opener found. Open manually: $FILE" >&2
  exit 1
fi
