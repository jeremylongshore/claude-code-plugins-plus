#!/usr/bin/env bash
# chromeless-launcher-linux.sh — Linux shim invoked by chromeless-launcher.sh.
#
# Launches Chrome / Chromium in --app mode and exits. Linux has no portable
# cross-WM hook for sizing a foreign window (X11 vs Wayland, GNOME vs KDE
# vs Sway), so this shim is launch-only by design. The user can resize
# manually once the window appears.
#
# Args: --url <URL> [--width N] [--height N]   (width/height accepted but
#                                               only logged for parity)

set -euo pipefail

URL=""
WIDTH=540
HEIGHT=920

is_positive_int() {
  case "$1" in ''|*[!0-9]*) return 1;; esac
  [ "$1" -gt 0 ]
}
require_positive_int() {
  is_positive_int "$2" || {
    echo "chromeless-launcher-linux: $1 must be a positive integer (got: $2)" >&2
    exit 64
  }
}

while [ $# -gt 0 ]; do
  case "$1" in
    --url)    URL="$2"; shift 2;;
    --width)  WIDTH="$2"; require_positive_int --width "$WIDTH"; shift 2;;
    --height) HEIGHT="$2"; require_positive_int --height "$HEIGHT"; shift 2;;
    --x|--y)  shift 2;;  # accepted for parity with mac shim, unused on Linux
    *)        echo "chromeless-launcher-linux: unknown arg: $1" >&2; exit 64;;
  esac
done

[ -z "$URL" ] && { echo "chromeless-launcher-linux: --url required" >&2; exit 64; }

# Reject URLs that could break the bash `"..."` boundary; everything
# else (including the `&` that Kobiton portal URLs need between
# query-string params) is intentionally allowed.
case "$URL" in
  *\"*|*\`*|*\$*|*\\*)
    echo "chromeless-launcher-linux: refusing URL with quoting-breaking metacharacters (\", backtick, \$, \\)" >&2
    exit 64
    ;;
  http://*|https://*) ;;
  *)
    echo "chromeless-launcher-linux: --url must start with http:// or https://" >&2
    exit 64
    ;;
esac

CHROME_BIN=""
for candidate in google-chrome google-chrome-stable chromium-browser chromium; do
  if command -v "$candidate" >/dev/null 2>&1; then
    CHROME_BIN="$candidate"
    break
  fi
done

if [ -z "$CHROME_BIN" ]; then
  echo "chromeless launcher requires Google Chrome or Chromium — falling back to default browser" >&2
  exit 2
fi

"$CHROME_BIN" --app="$URL" --window-size="$WIDTH,$HEIGHT" >/dev/null 2>&1 &
disown

echo "chromeless-launcher-linux: opened in --app mode (${WIDTH}x${HEIGHT} hint); auto-resize is macOS/Windows only on Linux — resize manually if the window manager ignored the size hint" >&2
exit 0
