#!/usr/bin/env bash
# generate-whats-new.sh — produce docs/assets/whats-new.{cast,gif}
#
#   scripts/generate-whats-new-cast.py  →  docs/assets/whats-new.cast
#                                       →  agg → docs/assets/whats-new.gif
#
# All flags are forwarded to generate-whats-new-cast.py:
#   --from <tag>        start ref (default: most recent git tag)
#   --to <ref>          end ref (default: HEAD)
#   --version <X.Y.Z>   version label
#   --output <path>     override output cast path

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$REPO_ROOT/docs/assets"
CAST_FILE="$ASSETS_DIR/whats-new.cast"
GIF_FILE="$ASSETS_DIR/whats-new.gif"
GENERATOR="$REPO_ROOT/scripts/generate-whats-new-cast.py"

SPEED="${HYPERFLOW_WHATSNEW_SPEED:-1.0}"
THEME="${HYPERFLOW_WHATSNEW_THEME:-monokai}"
FONT_SIZE="${HYPERFLOW_WHATSNEW_FONT_SIZE:-14}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    printf '\033[31m✗\033[0m missing: %s  (%s)\n' "$1" "$2" >&2
    exit 1
  }
}

require python3 "preinstalled on macOS/Linux"

mkdir -p "$ASSETS_DIR"

printf '\033[35m▸\033[0m generating whats-new cast\n'
python3 "$GENERATOR" --output "$CAST_FILE" "$@"

if command -v agg >/dev/null 2>&1; then
  printf '\033[35m▸\033[0m rendering whats-new.gif (speed %s · theme %s · font %spx)\n' "$SPEED" "$THEME" "$FONT_SIZE"
  agg --speed "$SPEED" --theme "$THEME" --font-size "$FONT_SIZE" "$CAST_FILE" "$GIF_FILE" >/dev/null 2>&1
  SIZE_KB=$(( $(wc -c < "$GIF_FILE") / 1024 ))
  printf '\033[32m✓\033[0m %s  ·  %d KB\n' "${GIF_FILE#$REPO_ROOT/}" "$SIZE_KB"
else
  printf '\033[33m⚠\033[0m agg not installed — skipping gif (cast still generated)\n'
  printf '\033[33m  install:\033[0m cargo install --locked agg  |  brew install agg\n'
fi
