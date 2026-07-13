#!/usr/bin/env bash
# Catalog: G6 — Override rate limit (anti-habituation)
# Mitigates: Round-1 security GAP-2 — under "just ship it" pressure, an agent
# learns to invoke overrides reflexively. Without a rate limit, the override
# mechanism becomes a slop escape valve. ≥3 overrides at one repo in 30d =
# the system is telling you something; pause and reflect.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_REPO" ]]; then
  gate_skip "no repo in candidate"
fi

LOG="$HOME/.contribute-system/log.jsonl"
[[ ! -f "$LOG" ]] && gate_pass "no log.jsonl yet"

# Count override events in last 30 days at this repo
THIRTY_AGO=$(/usr/bin/date -u -d '30 days ago' +%s)

OVERRIDE_COUNT=$(jq -r --arg cutoff "$THIRTY_AGO" --arg repo "$GATE_REPO" '
  select(.event == "gate_override")
  | select(.details.repo == $repo)
  | select((.ts | fromdateiso8601) >= ($cutoff | tonumber))
' "$LOG" 2>/dev/null | jq -s 'length' 2>/dev/null || /usr/bin/echo 0)

if [[ "${OVERRIDE_COUNT:-0}" -ge 3 ]]; then
  gate_block "$OVERRIDE_COUNT gate overrides at $GATE_REPO in last 30 days (rate limit: 3)" "the system is telling you something. Either your scope at this repo is wrong, your dossier is out of date, or you're forcing through patterns that will eventually trigger an AI-policy closure. To override THIS rate limit: edit ~/.contribute-system/g06-rate-limit-reset && touch it. Don't just shrug it off."
fi

gate_pass "$OVERRIDE_COUNT/3 overrides at $GATE_REPO in last 30 days"
