#!/usr/bin/env bash
# record-demo.sh — capture a Hyperflow terminal session and convert it to docs/assets/demo.gif
#
# Pipeline: asciinema rec → demo.cast → agg → demo.gif
# Run from repo root: ./scripts/record-demo.sh
#
# Follow the scripted scenario in docs/demo-script.md while recording so the GIF
# touches all 9 layers (analysis, autonomy, routing, orchestrate, brainstorm,
# gates, memory, templates, git, security).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$REPO_ROOT/docs/assets"
CAST_FILE="$ASSETS_DIR/demo.cast"
GIF_FILE="$ASSETS_DIR/demo.gif"
COLS="${HYPERFLOW_DEMO_COLS:-120}"
ROWS="${HYPERFLOW_DEMO_ROWS:-32}"
SPEED="${HYPERFLOW_DEMO_SPEED:-1.6}"
THEME="${HYPERFLOW_DEMO_THEME:-monokai}"
FONT_SIZE="${HYPERFLOW_DEMO_FONT_SIZE:-14}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    printf '\033[31m✗\033[0m missing dependency: %s\n' "$1" >&2
    printf '   install hint: %s\n' "$2" >&2
    exit 1
  }
}

require asciinema "brew install asciinema  (macOS)  |  pipx install asciinema  (linux)"
require agg       "cargo install --locked agg  |  brew install agg"

mkdir -p "$ASSETS_DIR"

cat <<EOF

  Hyperflow demo recorder
  -----------------------
  cast → $CAST_FILE
  gif  → $GIF_FILE
  size → ${COLS}×${ROWS}  speed ×${SPEED}  theme ${THEME}

  Scenario: docs/demo-script.md  (open it in another window to follow along)

  When the recording starts:
    • follow the script top-to-bottom
    • exit the shell (Ctrl-D or 'exit') when done
    • the GIF will be regenerated automatically

EOF

read -rp "Press Enter to start recording (Ctrl-C to abort) ..." _

# 1. Record
rm -f "$CAST_FILE"
asciinema rec \
  --cols "$COLS" \
  --rows "$ROWS" \
  --idle-time-limit 2 \
  --title "Hyperflow — autonomous multi-agent orchestration" \
  --command "${SHELL:-/bin/bash} -l" \
  "$CAST_FILE"

# 2. Render
agg \
  --cols "$COLS" \
  --rows "$ROWS" \
  --speed "$SPEED" \
  --theme "$THEME" \
  --font-size "$FONT_SIZE" \
  "$CAST_FILE" \
  "$GIF_FILE"

SIZE_BYTES=$(wc -c < "$GIF_FILE")
SIZE_KB=$(( SIZE_BYTES / 1024 ))

printf '\n\033[32m✓\033[0m wrote %s (%d KB)\n' "$GIF_FILE" "$SIZE_KB"

if [ "$SIZE_KB" -gt 800 ]; then
  cat <<EOF

  ⚠  GIF is over 800 KB — consider:
     • shorter recording (re-run and trim the scenario)
     • higher --speed (e.g. HYPERFLOW_DEMO_SPEED=2.2)
     • smaller terminal (HYPERFLOW_DEMO_COLS=100 HYPERFLOW_DEMO_ROWS=28)

EOF
fi

cat <<EOF

  Next:
    1. preview  →  open $GIF_FILE
    2. embed    →  add this to README.md (under "How It Works"):

         <p align="center">
           <img src="docs/assets/demo.gif" alt="Hyperflow demo" width="100%" />
         </p>

    3. commit   →  git add docs/assets/demo.gif docs/assets/demo.cast

EOF
