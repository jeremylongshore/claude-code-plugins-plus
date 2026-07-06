#!/usr/bin/env bash
# chromeless-launcher.sh — opt-in dispatcher for run-automation-suite Step 5.
#
# Launches the Kobiton device-only view in Chrome --app mode and (where
# supported) resizes the resulting window to a phone-shaped frame. The
# skill prose calls this script ONLY when the user has opted in via
# --chromeless and the resolved browser preference is Chrome.
#
# Exit codes:
#   0  — Chrome launched (resize may or may not have succeeded; failure is
#        logged but does not propagate)
#   2  — Chrome / Chromium not detected on this host; the caller should
#        fall through to the default-browser open path
#   64 — usage error (missing or unknown args)
#
# The script never aborts the automation session — resize failures are
# logged to stderr and treated as best-effort.

set -euo pipefail

URL=""
WIDTH=540
HEIGHT=920
ORIENTATION="portrait"
X=100
Y=100

usage() {
  cat >&2 <<EOF
usage: chromeless-launcher.sh --url <URL> [--width N] [--height N]
                              [--orientation portrait|landscape] [--x N] [--y N]
EOF
}

# Argument-parsing helper: assert a value is a positive integer. Avoids the
# confusing `set -e` failure on later arithmetic when a caller passes a
# non-numeric or zero/negative dimension.
is_positive_int() {
  case "$1" in
    ''|*[!0-9]*) return 1;;
  esac
  [ "$1" -gt 0 ]
}

require_positive_int() {
  is_positive_int "$2" || {
    echo "chromeless-launcher: $1 must be a positive integer (got: $2)" >&2
    exit 64
  }
}

while [ $# -gt 0 ]; do
  case "$1" in
    --url)         URL="$2"; shift 2;;
    --width)       WIDTH="$2"; require_positive_int --width "$WIDTH"; shift 2;;
    --height)      HEIGHT="$2"; require_positive_int --height "$HEIGHT"; shift 2;;
    --orientation) ORIENTATION="$2"; shift 2;;
    --x)           X="$2"; require_positive_int --x "$X"; shift 2;;
    --y)           Y="$2"; require_positive_int --y "$Y"; shift 2;;
    -h|--help)     usage; exit 0;;
    *)             echo "chromeless-launcher: unknown arg: $1" >&2; usage; exit 64;;
  esac
done

if [ -z "$URL" ]; then
  echo "chromeless-launcher: --url is required" >&2
  usage
  exit 64
fi

# Reject URLs that could break the double-quoted bash boundary or carry a
# non-http(s) scheme. Only the four characters that can escape `"..."` in
# bash are flagged — `"`, backtick, `$`, and `\`. URL syntax chars (`&`,
# `?`, `=`, `;`, `|`, `<`, `>`, single-quote) are valid inside a quoted
# URL value and were over-blocked by an earlier revision.
case "$URL" in
  *\"*|*\`*|*\$*|*\\*)
    echo "chromeless-launcher: refusing URL with quoting-breaking metacharacters (\", backtick, \$, \\)" >&2
    exit 64
    ;;
  http://*|https://*) ;;
  *)
    echo "chromeless-launcher: --url must start with http:// or https://" >&2
    exit 64
    ;;
esac

# Landscape swaps width/height when the caller didn't pass explicit dimensions
# already shaped for landscape. The defaults (480x1000 phone / caller-supplied
# 768x1024 tablet / 580x1080 fold — per SKILL.md Step 5 device-class heuristic)
# all assume portrait; for a landscape device the caller should pass already-
# swapped dimensions directly, but if they only pass --orientation landscape,
# swap here as a convenience.
if [ "$ORIENTATION" = "landscape" ] && [ "$WIDTH" -lt "$HEIGHT" ]; then
  TMP="$WIDTH"; WIDTH="$HEIGHT"; HEIGHT="$TMP"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

case "${OSTYPE:-}" in
  darwin*)
    exec bash "$SCRIPT_DIR/chromeless-launcher-mac.sh" \
      --url "$URL" --width "$WIDTH" --height "$HEIGHT" --x "$X" --y "$Y"
    ;;
  linux*|freebsd*)
    exec bash "$SCRIPT_DIR/chromeless-launcher-linux.sh" \
      --url "$URL" --width "$WIDTH" --height "$HEIGHT"
    ;;
  msys*|cygwin*|win32*)
    # Windows-from-WSL or git-bash; the skill prose routes Windows through
    # pwsh directly, but provide a fallback that surfaces a clear message.
    echo "chromeless-launcher: Windows must be invoked via chromeless-launcher-windows.ps1 (pwsh)" >&2
    exit 64
    ;;
  *)
    echo "chromeless-launcher: unsupported OSTYPE='${OSTYPE:-unknown}' — falling back to default browser" >&2
    exit 2
    ;;
esac
