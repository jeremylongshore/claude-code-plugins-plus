#!/usr/bin/env bash
# Catalog: E2 — AI policy strike tracking, ORG-LEVEL (not just repo-level)
# Mitigates: Round-1 AI-policy GAP-6 — PostHog AI_POLICY says "Two or more
# closures: We'll block the account." Stake is account-level, not per-repo.
# A 1st closure on PostHog/posthog + 1st on PostHog/posthog-js = blocked,
# and a per-repo gate would never see it. This gate evaluates strikes at
# the org-owner level.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_REPO" ]]; then
  gate_skip "no repo in candidate"
fi

# Read strike scope from dossier (default: org)
STRIKE_SCOPE="org"
if [[ -n "$GATE_DOSSIER_PATH" && -f "$GATE_DOSSIER_PATH" ]]; then
  V=$(fm_field "$GATE_DOSSIER_PATH" "strike_scope")
  [[ -n "$V" ]] && STRIKE_SCOPE="$V"
fi

OWNER="${GATE_REPO%%/*}"
LOG="$HOME/.contribute-system/log.jsonl"

if [[ ! -f "$LOG" ]]; then
  gate_pass "no log.jsonl yet (no prior strikes possible)"
fi

# Count prior closures with reason matching AI policy at the appropriate scope.
# Reason patterns: any 'dropped' event with reason containing 'ai_policy', 'ai-policy', 'slop', 'ai policy'
case "$STRIKE_SCOPE" in
  repo)    SCOPE_FILTER=".details.repo == \"$GATE_REPO\"" ;;
  org)     SCOPE_FILTER=".details.repo | startswith(\"$OWNER/\")" ;;
  account) SCOPE_FILTER="true" ;;
  *)       gate_block "unknown strike_scope in dossier: $STRIKE_SCOPE" "set strike_scope to repo|org|account in the dossier" ;;
esac

STRIKE_COUNT=$(jq -c "
  select(.event == \"candidate_dropped\")
  | select($SCOPE_FILTER)
  | select(.details.reason | tostring | test(\"ai[ _-]?policy|ai[ _-]?slop\"; \"i\"))
" "$LOG" 2>/dev/null | /usr/bin/wc -l | /usr/bin/awk '{print $1}')

# Note: pre-Phase-3, there's no way to query PostHog's ACTUAL record of our
# strikes; we only know what WE logged. If we never logged a closure (e.g.,
# PostHog closed without us calling it out), we'd undercount. Best-effort.

if [[ "${STRIKE_COUNT:-0}" -ge 1 ]]; then
  if [[ "$STRIKE_COUNT" -eq 1 ]]; then
    gate_block "1 prior AI-policy closure at $STRIKE_SCOPE-scope ($OWNER). Next closure = account block at PostHog-tier repos." "manual override required: --override-gate=E2 \"<reason you're confident this PR won't get closed>\". This is the gate that prevents account-block."
  else
    gate_block "$STRIKE_COUNT prior AI-policy closures at $STRIKE_SCOPE-scope ($OWNER). HARD STOP — pause contributions to this org until you've discussed with maintainers." "manual override is intentionally inconvenient here. If you must proceed, --override-gate=E2 \"<written rationale>\" AND post a comment on the issue acknowledging the prior closures."
  fi
fi

gate_pass "no prior AI-policy closures at $STRIKE_SCOPE-scope ($OWNER)"
