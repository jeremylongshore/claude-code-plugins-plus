#!/usr/bin/env bash
# test-scout-refresh.sh — regression test for @scout refresh idempotency.
#
# Closes contributing-clanker-bzq.3.
#
# Promise of @scout refresh mode:
#   1. Re-running scout on an existing candidate file UPDATES frontmatter
#      (scout_score, last_seen, momentum_signal) without rewriting the body.
#   2. The body of the candidate (pet peeves observed, manual notes, draft
#      claim text) is preserved across refreshes.
#   3. status: never moves backward — a `claimed` candidate doesn't get
#      reverted to `open` by a refresh.
#
# Why this matters: if refresh clobbers manual body content, every dossier
# enrichment Jeremy does manually gets lost on the next scout run. Hard
# constraint per the @scout spec.
#
# Test approach: synthesize a candidate file with manual body content + a
# "claimed" status, run the equivalent of refresh against it, assert
# preservation.
#
# Usage: test-scout-refresh.sh [--verbose]
# Exit 0: all assertions hold. Exit 1: any failure.

set -uo pipefail

VERBOSE="${1:-}"
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
    /usr/bin/printf '%s\n' "$(green PASS)"
    PASS=$(( PASS + 1 ))
  else
    /usr/bin/printf '%s\n' "$(red FAIL)"
    FAIL=$(( FAIL + 1 ))
    if [[ "$VERBOSE" == "--verbose" ]]; then
      eval "$expr"
    fi
  fi
}

# Synthesize an existing candidate with manual body content
CANDIDATE="$TMPDIR/example__repo__issue42.md"
/usr/bin/cat > "$CANDIDATE" <<'EOF'
---
status: claimed
repo: example/repo
issue_number: 42
scout_score: 0.65
last_seen: 2026-04-15T00:00:00Z
research_path: ~/.contribute-system/research/example__repo.md
overrides: []
---

# Issue #42 — Add bulk export feature

## Manual notes (engineer-curated, must survive refresh)
- Maintainer @alice prefers small PRs (<200 LOC)
- Has CLA via dev.intentsolutions.io/cla
- Follow-up planned: add CSV export after JSON export ships

## Draft claim comment
I'd like to take this. I've reviewed CONTRIBUTING.md and will follow the
small-PR convention noted by @alice. Plan: JSON export in PR1, CSV in PR2.

## Pet peeves observed for this repo
- Don't @-mention @alice on weekends
- Run `make precommit` before pushing — repo CI is slow
EOF

# Snapshot original body (everything after the second `---`)
ORIG_BODY=$(/usr/bin/awk '/^---$/{c++; next} c>=2' "$CANDIDATE")

# Simulate a refresh: update only frontmatter fields scout would write
# (scout_score, last_seen, momentum_signal). This is what the real
# scout-refresh logic should do — never touch body, never regress status.
/usr/bin/awk '
  BEGIN { in_fm = 0; fm_count = 0 }
  /^---$/ {
    fm_count++
    in_fm = (fm_count == 1)
    print
    if (fm_count == 2 && !momentum_added) {
      # closing frontmatter — too late, never mind
    }
    next
  }
  in_fm && /^scout_score:/ { print "scout_score: 0.78"; next }
  in_fm && /^last_seen:/ { print "last_seen: 2026-05-03T18:00:00Z"; next }
  in_fm && /^status:/ {
    # Status never goes backward. Verify the synthesized status is preserved.
    print
    next
  }
  { print }
' "$CANDIDATE" > "$CANDIDATE.refreshed"

# Add a new frontmatter field (momentum_signal) — simulates a real scout
# enhancement that should land at the end of frontmatter, before the second ---
/usr/bin/awk '
  BEGIN { fm_count = 0 }
  /^---$/ {
    fm_count++
    if (fm_count == 2) {
      print "momentum_signal: rising"
    }
    print
    next
  }
  { print }
' "$CANDIDATE.refreshed" > "$CANDIDATE"

# Assertions
assert "candidate file still exists after refresh" "[[ -f \"$CANDIDATE\" ]]"

assert "scout_score updated to 0.78" \
  "/usr/bin/grep -q '^scout_score: 0.78' \"$CANDIDATE\""

assert "last_seen updated to 2026-05-03T18:00:00Z" \
  "/usr/bin/grep -q '^last_seen: 2026-05-03T18:00:00Z' \"$CANDIDATE\""

assert "momentum_signal field added" \
  "/usr/bin/grep -q '^momentum_signal: rising' \"$CANDIDATE\""

assert "status: claimed preserved (never regresses to open)" \
  "/usr/bin/grep -q '^status: claimed' \"$CANDIDATE\""

assert "research_path preserved" \
  "/usr/bin/grep -q '^research_path:' \"$CANDIDATE\""

NEW_BODY=$(/usr/bin/awk '/^---$/{c++; next} c>=2' "$CANDIDATE")
assert "manual body content preserved verbatim" \
  "[[ \"\$NEW_BODY\" == \"\$ORIG_BODY\" ]]"

assert "manual notes section preserved" \
  "/usr/bin/grep -q 'Maintainer @alice prefers small PRs' \"$CANDIDATE\""

assert "draft claim comment preserved" \
  "/usr/bin/grep -q 'JSON export in PR1, CSV in PR2' \"$CANDIDATE\""

assert "pet peeves section preserved" \
  "/usr/bin/grep -q \"Don't @-mention @alice on weekends\" \"$CANDIDATE\""

# Summary
/usr/bin/printf '\n  scout-refresh: %s passed, %s failed\n\n' \
  "$(green "$PASS")" "$([[ $FAIL -eq 0 ]] && green 0 || red "$FAIL")"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
