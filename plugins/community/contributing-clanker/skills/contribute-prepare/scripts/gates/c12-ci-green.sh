#!/usr/bin/env bash
# Catalog: C12 — CI not green (any failed/pending checks block flip-to-ready)
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

PR_NUMBER=$(fm_field "$GATE_CANDIDATE_PATH" "pr_number")
if [[ -z "$PR_NUMBER" ]]; then
  gate_skip "no pr_number in candidate (no PR yet)"
fi

CHECKS_JSON=$(gh_safe pr checks "$PR_NUMBER" --repo "$GATE_REPO" --json bucket || /usr/bin/echo "[]")
if [[ -z "$CHECKS_JSON" ]]; then
  CHECKS_JSON="[]"
fi

FAIL_COUNT=$(/usr/bin/printf '%s' "$CHECKS_JSON" | jq '[.[] | select(.bucket == "fail")] | length' 2>/dev/null || /usr/bin/echo "0")
PENDING_COUNT=$(/usr/bin/printf '%s' "$CHECKS_JSON" | jq '[.[] | select(.bucket == "pending")] | length' 2>/dev/null || /usr/bin/echo "0")

if [[ "$FAIL_COUNT" != "0" ]]; then
  FAILED=$(/usr/bin/printf '%s' "$CHECKS_JSON" | jq -r '[.[] | select(.bucket == "fail") | .name] | join(", ")' 2>/dev/null || /usr/bin/echo "")
  gate_block "CI has $FAIL_COUNT failing check(s): $FAILED" "fix the failing checks before flipping to ready-for-review"
fi

if [[ "$PENDING_COUNT" != "0" ]]; then
  gate_warn "$PENDING_COUNT CI check(s) still pending" "wait for CI to finish before flipping to ready-for-review"
fi

gate_pass "all CI checks green"
