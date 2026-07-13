#!/usr/bin/env bash
# test-override-audit.sh — regression test for the override audit trail.
#
# Promise: every `transition.sh --override-gate <ID> "reason"` call
#   1. appends a `gate_override` event to ~/.contribute-system/log.jsonl
#   2. writes the override into the candidate's frontmatter overrides: array
#   3. allows the transition to proceed (BLOCK gate becomes effective-PASS)
#
# This validates the audit trail that lets engineers see WHY a gate was bypassed.
#
# Usage: test-override-audit.sh [--verbose]
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

# Build a synthetic candidate (closed issue, will trigger A05 BLOCK)
SYNTH="$TMPDIR/synth-override.md"
/usr/bin/cat > "$SYNTH" <<'EOF'
---
discovered_at: 2026-05-03T00:00:00Z
repo: lingdojo/kana-dojo
issue_number: 15441
issue_url: https://github.com/lingdojo/kana-dojo/issues/15441
star_tier: mainstream
star_count: 2231
repo_lang: TypeScript
competing_prs: 0
primary_label: bug
scout_score: 0.5
status: open
last_refreshed: 2026-05-03T00:00:00Z
---

# synthetic — override audit test
EOF

LOG_BEFORE_LINES=$(/usr/bin/wc -l < "$SYS/log.jsonl" 2>/dev/null || /usr/bin/echo "0")

/usr/bin/printf '\n=== override audit regression ===\n\n'

# --- TEST 1: dry-run override pre-records WITHOUT mutating candidate ---
"$SCRIPT_DIR/transition.sh" "shortlist→claimed" "$SYNTH" \
  --dry-run \
  --override-gate A05 "regression test: dry-run should not write" \
  >/dev/null 2>&1

assert "1. dry-run override does NOT write 'overrides:' to candidate" \
  '! /usr/bin/grep -q "^overrides:" "$SYNTH"'

# --- TEST 2: real override (no --dry-run) writes to candidate frontmatter ---
"$SCRIPT_DIR/transition.sh" "shortlist→claimed" "$SYNTH" \
  --override-gate A05 "test 2: real override audit" \
  >/dev/null 2>&1 || true   # gate block exit-code may be 0 or 1; we don't care

assert "2. real override DOES write 'overrides:' to candidate" \
  '/usr/bin/grep -q "^overrides:" "$SYNTH"'

assert "3. override entry contains gate ID A05" \
  '/usr/bin/grep -q "gate: A05" "$SYNTH"'

assert "4. override entry contains the reason text" \
  '/usr/bin/grep -q "test 2: real override audit" "$SYNTH"'

# --- TEST 3: log.jsonl gets gate_override event ---
LOG_AFTER_LINES=$(/usr/bin/wc -l < "$SYS/log.jsonl" 2>/dev/null || /usr/bin/echo "0")

assert "5. log.jsonl grew (new event lines appended)" \
  '[[ "$LOG_AFTER_LINES" -gt "$LOG_BEFORE_LINES" ]]'

assert "6. log.jsonl contains a gate_override event for A05" \
  '/usr/bin/tail -20 "$SYS/log.jsonl" | /usr/bin/grep -q "\"event\":\"gate_override\".*\"gate\":\"A05\""'

/usr/bin/echo
/usr/bin/printf '=== summary: %s passed · %s failed ===\n\n' \
  "$(green "$PASS")" "$([ "$FAIL" -gt 0 ] && red "$FAIL" || /usr/bin/echo 0)"

[[ "$FAIL" -eq 0 ]] || exit 1
exit 0
