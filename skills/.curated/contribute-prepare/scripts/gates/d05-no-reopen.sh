#!/usr/bin/env bash
# Catalog: D5 — reopening a PR that a maintainer closed
# Mitigates: comes across as ignoring maintainer feedback; usually a fresh PR is better.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

PR_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "pr_number")
if [[ -z "$PR_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no pr_number or repo in candidate"
fi

INFO=$(gh_safe pr view "$PR_NUM" --repo "$GATE_REPO" --json state,closedAt --jq '{state: .state, closedAt: .closedAt}' || /usr/bin/echo "")
if [[ -z "$INFO" ]]; then
  gate_skip "could not fetch PR state"
fi

STATE=$(/usr/bin/printf '%s' "$INFO" | jq -r '.state // ""')
CLOSED_AT=$(/usr/bin/printf '%s' "$INFO" | jq -r '.closedAt // ""')

if [[ "$STATE" != "CLOSED" || -z "$CLOSED_AT" || "$CLOSED_AT" == "null" ]]; then
  gate_skip "PR is not in CLOSED state (state=$STATE) — nothing to reopen"
fi

gate_warn "PR #$PR_NUM was closed at $CLOSED_AT — reopening may be read as ignoring the maintainer" "the maintainer closed this PR; reopening without addressing their feedback can come across as disrespectful. Consider a fresh PR if you've made substantial changes"
