#!/usr/bin/env bash
# test-plug-in.sh — regression test for the gate-runner plug-in / discovery contract.
#
# Promise: gate-runner discovers gate scripts by glob from
#   1. its own scripts/gates/ dir (bundled canonical set)
#   2. ~/.contribute-system/gates/ (user-override dir)
# Drop a new executable .sh in either dir and the runner picks it up
# automatically — no orchestrator changes needed.
#
# This is the load-bearing property that makes gates pluggable.
#
# Usage: test-plug-in.sh [--verbose]
# Exit 0: all assertions hold. Exit 1: any failure.

set -uo pipefail

VERBOSE="${1:-}"
SYS="$HOME/.contribute-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_GATES="$SYS/gates"

# Plant a no-op gate in the user-override dir. Use a phase letter that runs
# at shortlist→claimed (phase A). gate-runner globs phase-letter-prefix.sh.
PLUGIN_GATE_NAME="azz99-plugin-test-$$.sh"
PLUGIN_GATE="$USER_GATES/$PLUGIN_GATE_NAME"
TMPDIR=$(/usr/bin/mktemp -d)
trap 'rm -f "$PLUGIN_GATE"; rm -rf "$TMPDIR"' EXIT

# Construct the no-op gate. Just emits PASS.
/usr/bin/cat > "$PLUGIN_GATE" <<'EOF'
#!/usr/bin/env bash
# Catalog: AZZ99 — plug-in regression test no-op gate
source "$(dirname "$0")/lib/preamble.sh"
gate_read_input
gate_pass "no-op test gate discovered via plug-in mechanism"
EOF
/usr/bin/chmod +x "$PLUGIN_GATE"

# Build a synthetic candidate (won't trigger any real gate findings)
SYNTH="$TMPDIR/synth-plugin.md"
/usr/bin/cat > "$SYNTH" <<'EOF'
---
discovered_at: 2026-05-03T00:00:00Z
repo: example-org/example-repo
issue_number: 1
issue_url: https://github.com/example-org/example-repo/issues/1
star_tier: mainstream
star_count: 1000
repo_lang: TypeScript
competing_prs: 0
primary_label: bug
scout_score: 0.5
status: open
last_refreshed: 2026-05-03T00:00:00Z
---

# synthetic — plug-in test
EOF

PASS=0
FAIL=0
red()   { /usr/bin/printf '\033[31m%s\033[0m' "$1"; }
green() { /usr/bin/printf '\033[32m%s\033[0m' "$1"; }

/usr/bin/printf '\n=== gate-runner plug-in discovery regression ===\n\n'

# Run transition with stderr captured (gate output goes to stderr)
TRANSITION_OUT=$("$SCRIPT_DIR/transition.sh" "shortlist→claimed" "$SYNTH" --dry-run 2>&1 || true)

if [[ "$VERBOSE" == "--verbose" ]] ; then
  /usr/bin/printf 'transition output:\n%s\n\n' "$TRANSITION_OUT" >&2
fi

# Test 1: the plug-in gate appears in the output
/usr/bin/printf '  %-60s ' "1. user-override gate AZZ99 was discovered"
if /usr/bin/echo "$TRANSITION_OUT" | /usr/bin/grep -q "AZZ99"; then
  green "PASS"; /usr/bin/echo; PASS=$((PASS+1))
else
  red "FAIL"; /usr/bin/echo; FAIL=$((FAIL+1))
fi

# Test 2: the plug-in gate emitted PASS (proves the gate ran, not just listed)
/usr/bin/printf '  %-60s ' "2. plug-in gate executed and emitted PASS"
if /usr/bin/echo "$TRANSITION_OUT" | /usr/bin/grep -qE "AZZ99.*PASS"; then
  green "PASS"; /usr/bin/echo; PASS=$((PASS+1))
else
  red "FAIL"; /usr/bin/echo; FAIL=$((FAIL+1))
fi

# Test 3: bundled canonical gates still ran (a01 should appear)
/usr/bin/printf '  %-60s ' "3. bundled canonical gate A01 still ran (dual-dir)"
if /usr/bin/echo "$TRANSITION_OUT" | /usr/bin/grep -q "A01"; then
  green "PASS"; /usr/bin/echo; PASS=$((PASS+1))
else
  red "FAIL"; /usr/bin/echo; FAIL=$((FAIL+1))
fi

# Test 4: removing the plug-in gate makes it disappear
/usr/bin/rm -f "$PLUGIN_GATE"
TRANSITION_OUT2=$("$SCRIPT_DIR/transition.sh" "shortlist→claimed" "$SYNTH" --dry-run 2>&1 || true)
/usr/bin/printf '  %-60s ' "4. removing the plug-in gate stops it from running"
if ! /usr/bin/echo "$TRANSITION_OUT2" | /usr/bin/grep -q "AZZ99"; then
  green "PASS"; /usr/bin/echo; PASS=$((PASS+1))
else
  red "FAIL"; /usr/bin/echo; FAIL=$((FAIL+1))
fi

/usr/bin/echo
/usr/bin/printf '=== summary: %s passed · %s failed ===\n\n' \
  "$(green "$PASS")" "$([ "$FAIL" -gt 0 ] && red "$FAIL" || /usr/bin/echo 0)"

[[ "$FAIL" -eq 0 ]] || exit 1
exit 0
