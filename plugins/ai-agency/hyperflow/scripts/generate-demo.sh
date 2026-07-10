#!/usr/bin/env bash
# generate-demo.sh — one-shot pipeline: synthesize cast → render GIF
#
#   scripts/generate-demo-cast.py  →  docs/assets/demo.cast
#                                  →  agg → docs/assets/demo.gif
#
# Use this for the marketing GIF (deterministic, no live typing).
# For a live recording instead, use scripts/record-demo.sh.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$REPO_ROOT/docs/assets"
CAST_FILE="$ASSETS_DIR/demo.cast"
GIF_FILE="$ASSETS_DIR/demo.gif"
GENERATOR="$REPO_ROOT/scripts/generate-demo-cast.py"

SPEED="${HYPERFLOW_DEMO_SPEED:-1.6}"
THEME="${HYPERFLOW_DEMO_THEME:-dracula}"
FONT_SIZE="${HYPERFLOW_DEMO_FONT_SIZE:-11}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    printf '\033[31m✗\033[0m missing: %s  (%s)\n' "$1" "$2" >&2
    exit 1
  }
}

require python3 "preinstalled on macOS/Linux"
require agg     "cargo install --locked agg  |  brew install agg"

mkdir -p "$ASSETS_DIR"

printf '\033[35m▸\033[0m generating cast\n'
python3 "$GENERATOR" --output "$CAST_FILE"

printf '\033[35m▸\033[0m rendering gif (speed %s · theme %s · font %spx)\n' "$SPEED" "$THEME" "$FONT_SIZE"
agg \
  --speed     "$SPEED" \
  --theme     "$THEME" \
  --font-size "$FONT_SIZE" \
  "$CAST_FILE" \
  "$GIF_FILE" \
  >/dev/null 2>&1

SIZE_KB=$(( $(wc -c < "$GIF_FILE") / 1024 ))
DIMS=$(file "$GIF_FILE" | awk -F', ' '{for(i=1;i<=NF;i++) if($i ~ /[0-9]+ x [0-9]+/) print $i}')

printf '\033[32m✓\033[0m %s  ·  %s  ·  %d KB\n' "${GIF_FILE#$REPO_ROOT/}" "$DIMS" "$SIZE_KB"

if [ "$SIZE_KB" -gt 3072 ]; then
  printf '\033[33m⚠\033[0m gif > 3 MB — try HYPERFLOW_DEMO_SPEED=1.5 or HYPERFLOW_DEMO_FONT_SIZE=9\n'
fi

# The site hero serves demo.mp4 (5-10x smaller, better LCP) with the gif as fallback.
MP4_FILE="$ASSETS_DIR/demo.mp4"
POSTER_FILE="$ASSETS_DIR/demo-poster.png"
if command -v ffmpeg >/dev/null 2>&1; then
  printf '\033[35m▸\033[0m rendering mp4 + poster\n'
  ffmpeg -y -loglevel error -i "$GIF_FILE" \
    -movflags faststart -pix_fmt yuv420p \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    "$MP4_FILE"
  ffmpeg -y -loglevel error -i "$GIF_FILE" -vframes 1 \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    "$POSTER_FILE"
  MP4_KB=$(( $(wc -c < "$MP4_FILE") / 1024 ))
  printf '\033[32m✓\033[0m %s  ·  %d KB\n' "${MP4_FILE#$REPO_ROOT/}" "$MP4_KB"
else
  printf '\033[33m⚠\033[0m ffmpeg not found — skipping demo.mp4/demo-poster.png (hero falls back to gif)\n'
fi
