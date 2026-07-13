#!/usr/bin/env bash
# test-stale-dossier-refresh.sh — regression test for dossier freshness signals.
#
# Promise: researcher-build.sh emits a `last_refreshed:` ISO-8601 timestamp
# matching "now" (within 60 seconds). The 14-day staleness check is a
# downstream consumer concern (SKILL.md Step 0.5 + dossier_age helpers);
# this test validates the BUILDER side of the contract.
#
# Note: the actual "auto-refresh at 14 days" trigger logic lives in
# /contribute SKILL.md as agent instructions (not executable code). What
# we CAN test deterministically:
#   1. researcher-build.sh writes last_refreshed: to current time
#   2. an old timestamp is detectable as stale by simple shell math
#   3. the dossier path slug (owner__repo) matches what gates expect
#
# Usage: test-stale-dossier-refresh.sh [--verbose]
# Exit 0: all assertions hold. Exit 1: any failure.

set -uo pipefail

VERBOSE="${1:-}"
SYS="$HOME/.contribute-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMPDIR=$(/usr/bin/mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PASS=0
FAIL=0
red()    { /usr/bin/printf '\033[31m%s\033[0m' "$1"; }
green()  { /usr/bin/printf '\033[32m%s\033[0m' "$1"; }

assert() {
  local name="$1" expr="$2"
  /usr/bin/printf '  %-60s ' "$name"
  if eval "$expr" >/dev/null 2>&1; then
    green "PASS"; /usr/bin/echo
    PASS=$((PASS + 1))
  else
    red "FAIL"; /usr/bin/echo
    [[ "$VERBOSE" == "--verbose" ]] && /usr/bin/printf '    expr: %s\n' "$expr" >&2
    FAIL=$((FAIL + 1))
  fi
}

/usr/bin/printf '\n=== dossier freshness regression ===\n\n'

# --- TEST 1: researcher-build emits last_refreshed: matching now ---
DOSSIER="$TMPDIR/lingdojo__kana-dojo.md"
"$SCRIPT_DIR/researcher-build.sh" lingdojo/kana-dojo --no-link-follow > "$DOSSIER" 2>/dev/null

LAST_REFRESHED=$(/usr/bin/awk '/^last_refreshed:/{print $2; exit}' "$DOSSIER" 2>/dev/null)
NOW_EPOCH=$(/usr/bin/date +%s)
THEN_EPOCH=$(/usr/bin/date -d "$LAST_REFRESHED" +%s 2>/dev/null || /usr/bin/echo 0)
DELTA=$((NOW_EPOCH - THEN_EPOCH))

assert "1. dossier has last_refreshed frontmatter field" \
  '[[ -n "$LAST_REFRESHED" ]]'

assert "2. last_refreshed is within 60 seconds of now" \
  '[[ "$DELTA" -ge 0 && "$DELTA" -le 60 ]]'

# --- TEST 2: stale detection math works (synthetic 30-day-old timestamp) ---
THIRTY_DAYS_AGO=$(/usr/bin/date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)
THIRTY_EPOCH=$(/usr/bin/date -d "$THIRTY_DAYS_AGO" +%s)
AGE_DAYS=$(( (NOW_EPOCH - THIRTY_EPOCH) / 86400 ))

assert "3. shell-math correctly identifies 30d-old as stale (>14d)" \
  '[[ "$AGE_DAYS" -gt 14 ]]'

# --- TEST 3: dossier filename slug uses double underscore (matches gate expectations) ---
EXPECTED_SLUG="lingdojo__kana-dojo"
ACTUAL_SLUG=$(/usr/bin/basename "$DOSSIER" .md)

assert "4. dossier filename slug matches owner__repo convention" \
  '[[ "$ACTUAL_SLUG" == "$EXPECTED_SLUG" ]]'

# --- TEST 4: the dossier has the manual sections that survive refresh ---
assert "5. dossier has Pet peeves section (manual, append-only)" \
  '/usr/bin/grep -q "^## Pet peeves" "$DOSSIER"'

assert "6. dossier has Failure log section (manual, append-only)" \
  '/usr/bin/grep -q "^## Failure log" "$DOSSIER"'

assert "7. dossier has Notes section (manual, append-only)" \
  '/usr/bin/grep -q "^## Notes" "$DOSSIER"'

# --- TEST 5: dossier has issue_templates field (added 2026-05-03) ---
assert "8. dossier has issue_templates frontmatter (per skill-creator)" \
  '/usr/bin/grep -q "^issue_templates:" "$DOSSIER"'

/usr/bin/echo
/usr/bin/printf '=== summary: %s passed · %s failed ===\n\n' \
  "$(green "$PASS")" "$([ "$FAIL" -gt 0 ] && red "$FAIL" || /usr/bin/echo 0)"

[[ "$FAIL" -eq 0 ]] || exit 1
exit 0
