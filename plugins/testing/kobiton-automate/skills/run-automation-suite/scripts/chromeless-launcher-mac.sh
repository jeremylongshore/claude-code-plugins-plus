#!/usr/bin/env bash
# chromeless-launcher-mac.sh — macOS shim invoked by chromeless-launcher.sh.
#
# Launches Google Chrome in --app mode pointing at the device-only URL,
# then polls (up to 10s) for the resulting window and resizes it via
# osascript. The host process (Terminal, iTerm, Claude Code, …) needs
# Apple Events automation permission for Google Chrome (granted by macOS
# the first time via a "X wants to control Google Chrome" prompt; lives
# under System Settings → Privacy & Security → Automation, NOT
# Accessibility). If denied (-1743), the window simply stays at Chrome's
# default size and the script logs a one-line hint. The automation
# session is never affected.
#
# Args: --url <URL> --width <N> --height <N> [--x <N>] [--y <N>]

set -euo pipefail

URL=""
WIDTH=540
HEIGHT=920
X=100
Y=100

is_positive_int() {
  case "$1" in ''|*[!0-9]*) return 1;; esac
  [ "$1" -gt 0 ]
}
require_positive_int() {
  is_positive_int "$2" || {
    echo "chromeless-launcher-mac: $1 must be a positive integer (got: $2)" >&2
    exit 64
  }
}

while [ $# -gt 0 ]; do
  case "$1" in
    --url)    URL="$2"; shift 2;;
    --width)  WIDTH="$2"; require_positive_int --width "$WIDTH"; shift 2;;
    --height) HEIGHT="$2"; require_positive_int --height "$HEIGHT"; shift 2;;
    --x)      X="$2"; require_positive_int --x "$X"; shift 2;;
    --y)      Y="$2"; require_positive_int --y "$Y"; shift 2;;
    *)        echo "chromeless-launcher-mac: unknown arg: $1" >&2; exit 64;;
  esac
done

[ -z "$URL" ] && { echo "chromeless-launcher-mac: --url required" >&2; exit 64; }

# Defensive URL validation. Only the four characters that can break out
# of a bash `"..."` context are flagged: `"`, backtick, `$`, `\`. URL
# syntax characters (`&`, `?`, `=`, `;`, `|`, `<`, `>`, single-quote)
# are intentionally allowed — they are valid inside a quoted URL value
# and Kobiton portal URLs depend on `&` and `?`.
case "$URL" in
  *\"*|*\`*|*\$*|*\\*)
    echo "chromeless-launcher-mac: refusing URL with quoting-breaking metacharacters (\", backtick, \$, \\)" >&2
    exit 64
    ;;
  http://*|https://*) ;;
  *)
    echo "chromeless-launcher-mac: --url must start with http:// or https://" >&2
    exit 64
    ;;
esac

CHROME_BIN=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"; do
  if [ -x "$candidate" ]; then
    CHROME_BIN="$candidate"
    break
  fi
done
if [ -z "$CHROME_BIN" ]; then
  echo "chromeless launcher requires Google Chrome or Chromium — falling back to default browser" >&2
  exit 2
fi

# Launch detached so the skill caller does not block on Chrome's lifetime.
"$CHROME_BIN" --app="$URL" >/dev/null 2>&1 &
disown

# Compute bottom-right corner from top-left + dimensions for osascript bounds.
X2=$((X + WIDTH))
Y2=$((Y + HEIGHT))

# Poll up to 30 seconds (30 attempts × 1s) for a Chrome window whose
# active tab URL contains "view=device-only", then resize it. Matching by
# URL substring (rather than "window 1") avoids hitting a pre-existing
# Chrome window the user already had open. The 30s budget covers Chrome
# cold starts, profile-picker prompts, and slow page loads.
#
# The inner per-window check is wrapped in `try` so a stray window that
# has no active tab (e.g. a popped-out DevTools window) raises an error
# only for that window, not the whole `repeat` block — otherwise a single
# unrelated background window would abort every poll iteration.
for _ in $(seq 1 30); do
  if osascript >/dev/null 2>&1 <<EOF
    tell application "Google Chrome"
      repeat with w in windows
        try
          if URL of active tab of w contains "view=device-only" then
            set bounds of w to {${X}, ${Y}, ${X2}, ${Y2}}
            return "ok"
          end if
        end try
      end repeat
      error "device-only window not found yet"
    end tell
EOF
  then
    exit 0
  fi
  sleep 1
done

# 30s elapsed without a successful resize. The window may exist but
# osascript was denied Automation rights for Chrome (error -1743), or
# the window never opened (slow page load, Chrome cold start). Either
# way, the session is unaffected — log and return success so the caller
# proceeds.
HOST_PROC="${TERM_PROGRAM:-${SHELL:-the host terminal}}"
echo "chromeless-launcher-mac: window did not resize within 30s (host=${HOST_PROC})" >&2
echo "if a system prompt appeared, grant '${HOST_PROC}' permission to control Google Chrome in System Settings → Privacy & Security → Automation" >&2
exit 0
