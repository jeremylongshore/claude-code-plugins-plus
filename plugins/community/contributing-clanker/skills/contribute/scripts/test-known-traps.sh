#!/usr/bin/env bash
# test-known-traps.sh — regression tests for the failure modes that motivated
# the gate system. Each test constructs a synthetic candidate file matching a
# known real-world trap and asserts the expected gate fires with the expected
# severity.
#
# Usage: test-known-traps.sh [--verbose]
# Exit 0: all tests pass.  Exit 1: any test fails.
#
# Tests:
#   1. PostHog #55412 — already-shipped issue (gate A02 must BLOCK)
#   2. opensre #1129  — assigned issue (gate A01 must BLOCK)
#   3. closed issue   — closed-not-planned (gate A05 must BLOCK)
#   4. clean candidate — no traps (transition must PASS or only SKIP)

set -uo pipefail

VERBOSE="${1:-}"
SYS="$HOME/.contribute-system"
TMPDIR=$(/usr/bin/mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PASS=0
FAIL=0
RESULTS=()

red()    { /usr/bin/printf '\033[31m%s\033[0m' "$1"; }
green()  { /usr/bin/printf '\033[32m%s\033[0m' "$1"; }
yellow() { /usr/bin/printf '\033[33m%s\033[0m' "$1"; }

# Helper: run transition.sh in dry-run mode against a candidate.
# Returns the verdict JSON on stdout.
run_transition() {
  local action="$1" candidate="$2"
  "$SYS/bin/transition.sh" "$action" "$candidate" --dry-run 2>/dev/null \
    | /usr/bin/grep -E '^\{.*"verdict"' \
    | /usr/bin/tail -1
}

# Helper: assert a specific gate ID appears with a specific severity in the
# verbose stderr output of transition.sh.
gate_fired_with_severity() {
  local action="$1" candidate="$2" gate_id="$3" expected_sev="$4"
  local stderr_output
  stderr_output=$("$SYS/bin/transition.sh" "$action" "$candidate" --dry-run 2>&1 >/dev/null)
  if [[ "$VERBOSE" == "--verbose" ]]; then
    /usr/bin/printf '\n--- transition output for %s on %s ---\n%s\n---\n' \
      "$action" "$(/usr/bin/basename "$candidate")" "$stderr_output" >&2
  fi
  /usr/bin/echo "$stderr_output" | /usr/bin/grep -qE "\[$gate_id\].*$expected_sev"
}

assert_gate() {
  local name="$1" action="$2" candidate="$3" gate_id="$4" expected_sev="$5"
  /usr/bin/printf '  %-50s ' "$name"
  if gate_fired_with_severity "$action" "$candidate" "$gate_id" "$expected_sev"; then
    green "PASS"; /usr/bin/echo
    PASS=$((PASS + 1))
    RESULTS+=("PASS: $name")
  else
    red "FAIL"; /usr/bin/echo
    /usr/bin/printf '    expected gate %s severity %s — not found\n' "$gate_id" "$expected_sev" >&2
    FAIL=$((FAIL + 1))
    RESULTS+=("FAIL: $name (expected $gate_id $expected_sev)")
  fi
}

# Build a synthetic candidate file. The frontmatter is what gates read.
# Body is unused for these tests.
make_candidate() {
  local repo="$1" issue="$2" status="${3:-open}" path
  path="$TMPDIR/synth_$(/usr/bin/echo "$repo" | /usr/bin/tr '/' '_')_$issue.md"
  /usr/bin/cat > "$path" <<EOF
---
discovered_at: 2026-05-03T00:00:00Z
repo: $repo
issue_number: $issue
issue_url: https://github.com/$repo/issues/$issue
star_tier: mainstream
star_count: 1000
repo_lang: TypeScript
competing_prs: 0
primary_label: bug
scout_score: 0.5
status: $status
last_refreshed: 2026-05-03T00:00:00Z
---

# $repo #$issue — synthetic regression test candidate
EOF
  /usr/bin/echo "$path"
}

/usr/bin/printf '\n=== contributing-clanker regression tests — known traps ===\n\n'

# ---- TEST 1: PostHog #55412 trap (already-shipped) ----
# The plan documents this as the originating trap for gate A02.
# Issue #55412 was closed by merged PR #57145. We need A02 to BLOCK.
/usr/bin/printf 'Test 1: PostHog #55412 already-shipped trap\n'
T1=$(make_candidate "PostHog/posthog" 55412)
assert_gate "  A02 already-shipped MUST BLOCK" \
  "shortlist→claimed" "$T1" "A02" "BLOCK"

# ---- TEST 2: Tracer-Cloud opensre #1129 trap (assigned) ----
# This issue was assigned to unKnownNG when scout found it. A01 must BLOCK.
/usr/bin/printf 'Test 2: Tracer-Cloud opensre #1129 assigned trap\n'
T2=$(make_candidate "Tracer-Cloud/opensre" 1129)
assert_gate "  A01 already-assigned MUST BLOCK" \
  "shortlist→claimed" "$T2" "A01" "BLOCK"

# ---- TEST 3: lingdojo/kana-dojo #15441 (closed not_planned) ----
# Verified empirically 2026-05-03 — A05 BLOCKs on closed issues.
/usr/bin/printf 'Test 3: lingdojo/kana-dojo #15441 closed-issue trap\n'
T3=$(make_candidate "lingdojo/kana-dojo" 15441)
assert_gate "  A05 issue-still-open MUST BLOCK" \
  "shortlist→claimed" "$T3" "A05" "BLOCK"

# ---- TEST 4: clean candidate (no traps) ----
# Pick a repo+issue that's currently OPEN and unassigned. We use a synthetic
# very-high issue number that won't match any real shipped PR.
# Note: this test runs against a real repo via gh; if the issue doesn't exist,
# the gates will produce ambiguous results. We pick something neutral.
/usr/bin/printf 'Test 4: clean candidate (open, unassigned, unshipped)\n'
T4=$(make_candidate "lingdojo/kana-dojo" 99999999)
# A01 should PASS or A03/A04/A05 — we just want NO unexpected BLOCKs from A1
# (which is the most common false-positive risk).
assert_gate "  A01 should NOT block (issue 99999999 nonexistent)" \
  "shortlist→claimed" "$T4" "A01" "(PASS|SKIP)"

/usr/bin/echo
/usr/bin/printf '=== summary: %s passed · %s failed ===\n\n' \
  "$(green "$PASS")" "$([ "$FAIL" -gt 0 ] && red "$FAIL" || /usr/bin/echo 0)"

if [[ "$FAIL" -gt 0 ]]; then
  /usr/bin/printf 'Failures:\n'
  for R in "${RESULTS[@]}"; do
    [[ "$R" == FAIL:* ]] && /usr/bin/printf '  %s\n' "$R"
  done
  exit 1
fi

exit 0
