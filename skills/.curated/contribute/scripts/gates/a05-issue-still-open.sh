#!/usr/bin/env bash
# Catalog: A5 — Issue is still OPEN right now (not closed since dossier built)
# Mitigates: lingdojo/kana-dojo #15441 trap (2026-05-03) — issue was OPEN at
# 04:54Z when scout shortlisted it; CLOSED at 05:00Z (NOT_PLANNED) by
# maintainer killing a bot-generated cron issue. Our dossier and the existing
# A1/A2 gates wouldn't have caught it because they check assignees and
# already-shipped, not state. This is the simplest gate to write and the
# highest-value catch — bot-generated issues at active repos can close
# minutes after discovery.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

STATE_JSON=$(gh_safe issue view "$ISSUE_NUM" --repo "$GATE_REPO" --json state,stateReason,closedAt --jq '{state, stateReason: (.stateReason // ""), closedAt: (.closedAt // "")}' || /usr/bin/echo "")

if [[ -z "$STATE_JSON" ]] ; then
  gate_skip "couldn't fetch issue state"
fi

STATE=$(/usr/bin/printf '%s' "$STATE_JSON" | jq -r '.state')
REASON=$(/usr/bin/printf '%s' "$STATE_JSON" | jq -r '.stateReason')
CLOSED_AT=$(/usr/bin/printf '%s' "$STATE_JSON" | jq -r '.closedAt' | /usr/bin/cut -c1-19)

if [[ "$STATE" == "CLOSED" ]] ; then
  gate_block "issue is CLOSED (reason: ${REASON:-unspecified}, closed at ${CLOSED_AT:-unknown})" "issue closed since shortlist. If reason is COMPLETED, fix already shipped — pick a different target. If NOT_PLANNED, maintainer rejected the work — drop the candidate."
fi

gate_pass "issue state = OPEN"
