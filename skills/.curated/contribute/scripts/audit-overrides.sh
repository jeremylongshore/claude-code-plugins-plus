#!/usr/bin/env bash
# audit-overrides.sh — report override frequency and reasons across gates.
#
# Closes beads contributing-clanker-15b.3 and contributing-clanker-i4y.1
# (both ask for the same reporter: every --override-gate logged with reason +
# override frequency by gate).
#
# Reads ~/.contribute-system/log.jsonl. Aggregates two event types:
#   - gate_override  → an engineer pressed --override-gate=<ID> "reason"
#   - gate_run       → every gate verdict (BLOCK / PASS / WARN / etc.)
#
# Output: per-gate row with [overrides, blocks, override_rate, top_reason].
# Sorted by override_rate desc — the most-overridden gates surface first.
# A high override_rate means the gate is either too strict (false-positive
# heavy) or genuinely catching real risk that engineers consciously accept.
# Either way, it's the signal worth surfacing.
#
# Usage:
#   audit-overrides.sh                           # all-time, all repos
#   audit-overrides.sh --since=30                # last 30 days only
#   audit-overrides.sh --scope=org:posthog       # only posthog/* repos
#   audit-overrides.sh --scope=repo:foo/bar      # exact repo
#   audit-overrides.sh --json                    # JSON output (no table)
#   audit-overrides.sh --gate=A05                # drill into one gate

set -uo pipefail

LOG="${HOME}/.contribute-system/log.jsonl"
SINCE_DAYS=""
SCOPE=""
GATE_FILTER=""
JSON_OUT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since=*)     SINCE_DAYS="${1#*=}" ;;
    --scope=*)     SCOPE="${1#*=}" ;;
    --gate=*)      GATE_FILTER="${1#*=}" ;;
    --json)        JSON_OUT=1 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      /usr/bin/printf 'unknown arg: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -f "$LOG" ]]; then
  /usr/bin/printf 'no log file at %s — run a transition first\n' "$LOG" >&2
  exit 0
fi

# Build a jq filter that applies --since + --scope + --gate filters before
# aggregation. The repo field is on .details.repo for gate_run, and on
# .details.candidate (a path) for gate_override — gate_override events don't
# carry a repo string directly, so for gate_override we extract from the path
# pattern <owner>__<repo>__issue<N>.md when present, falling back to "" when
# not parseable. That's why scope filtering for overrides is best-effort.

since_filter='true'
if [[ -n "$SINCE_DAYS" ]]; then
  cutoff=$(/usr/bin/date -u -d "$SINCE_DAYS days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
    || /usr/bin/date -u -v-"${SINCE_DAYS}"d +%Y-%m-%dT%H:%M:%SZ)
  since_filter=".ts >= \"$cutoff\""
fi

case "$SCOPE" in
  org:*)
    owner="${SCOPE#org:}"
    scope_run='(.details.repo // "") | startswith("'"$owner"'/")'
    scope_ovr='(.details.candidate // "") | test("/'"$owner"'__")'
    ;;
  repo:*)
    repo="${SCOPE#repo:}"
    scope_run='(.details.repo // "") == "'"$repo"'"'
    owner_repo_path=$(/usr/bin/printf '%s' "$repo" | /usr/bin/sed 's|/|__|')
    scope_ovr='(.details.candidate // "") | test("/'"$owner_repo_path"'__")'
    ;;
  "")
    scope_run='true'
    scope_ovr='true'
    ;;
  *)
    /usr/bin/printf 'invalid --scope (use org:OWNER or repo:OWNER/NAME)\n' >&2
    exit 2
    ;;
esac

gate_filter_run='true'
gate_filter_ovr='true'
if [[ -n "$GATE_FILTER" ]]; then
  # Gate IDs in gate_run are lowercase ("a05"); in gate_override they're as
  # passed by the engineer (often uppercase "A05"). Match case-insensitively.
  gate_filter_run='(.details.gate // "" | ascii_downcase) == "'"$(/usr/bin/printf '%s' "$GATE_FILTER" | /usr/bin/tr '[:upper:]' '[:lower:]')"'"'
  gate_filter_ovr='(.details.gate // "" | ascii_downcase) == "'"$(/usr/bin/printf '%s' "$GATE_FILTER" | /usr/bin/tr '[:upper:]' '[:lower:]')"'"'
fi

# Phase 1: aggregate override counts + reasons per gate
overrides_json=$(jq -cs --slurpfile _ <(/usr/bin/printf '[]') '
  map(select(.event == "gate_override" and ('"$since_filter"') and ('"$scope_ovr"') and ('"$gate_filter_ovr"')))
  | group_by(.details.gate // "" | ascii_downcase)
  | map({
      gate: (.[0].details.gate // "" | ascii_downcase),
      overrides: length,
      reasons: (map(.details.reason // "") | unique)
    })
' "$LOG" 2>/dev/null || /usr/bin/printf '[]')

# Phase 2: aggregate BLOCK count per gate (denominator for override rate)
blocks_json=$(jq -cs '
  map(select(.event == "gate_run" and (.details.severity // "") == "BLOCK"
             and ('"$since_filter"') and ('"$scope_run"') and ('"$gate_filter_run"')))
  | group_by(.details.gate // "" | ascii_downcase)
  | map({
      gate: (.[0].details.gate // "" | ascii_downcase),
      blocks: length
    })
' "$LOG" 2>/dev/null || /usr/bin/printf '[]')

# Phase 3: merge and compute rate
merged=$(jq -cn --argjson o "$overrides_json" --argjson b "$blocks_json" '
  ($o + $b)
  | group_by(.gate)
  | map({
      gate: .[0].gate,
      overrides: ((map(.overrides // 0) | add) // 0),
      blocks: ((map(.blocks // 0) | add) // 0),
      reasons: ((map(.reasons // [])  | add | unique) // [])
    })
  | map(. + {
      override_rate: (if .blocks > 0 then (.overrides / .blocks * 100 | floor) else null end),
      top_reason: (.reasons | first // "")
    })
  | sort_by(if .override_rate == null then -1 else -.override_rate end)
')

if [[ "$JSON_OUT" -eq 1 ]]; then
  /usr/bin/printf '%s\n' "$merged" | jq .
  exit 0
fi

# Render text table
header_parts=()
[[ -n "$SINCE_DAYS" ]] && header_parts+=("last ${SINCE_DAYS}d")
[[ -n "$SCOPE" ]] && header_parts+=("scope=${SCOPE}")
[[ -n "$GATE_FILTER" ]] && header_parts+=("gate=${GATE_FILTER}")
[[ ${#header_parts[@]} -eq 0 ]] && header_parts+=("all-time")
header=$(/usr/bin/printf '%s, ' "${header_parts[@]}" | /usr/bin/sed 's/, $//')
/usr/bin/printf '\nOverride audit — %s\n' "$header"
/usr/bin/printf '%s\n' '─────────────────────────────────────────────────────────────────────────'
/usr/bin/printf '%-6s %10s %8s %10s  %s\n' "GATE" "OVERRIDES" "BLOCKS" "RATE" "TOP REASON"
/usr/bin/printf '%s\n' '─────────────────────────────────────────────────────────────────────────'

count=$(/usr/bin/printf '%s' "$merged" | jq 'length')
if [[ "$count" -eq 0 ]]; then
  /usr/bin/printf '  (no override events match the filter)\n\n'
  exit 0
fi

/usr/bin/printf '%s\n' "$merged" | jq -r '
  .[] | [
    .gate,
    .overrides,
    .blocks,
    (if .override_rate == null then "n/a" else "\(.override_rate)%" end),
    (if (.top_reason | length) > 50 then (.top_reason[0:47] + "...") else .top_reason end)
  ] | @tsv
' | /usr/bin/awk -F'\t' '{ printf "%-6s %10s %8s %10s  %s\n", $1, $2, $3, $4, $5 }'

/usr/bin/printf '%s\n\n' '─────────────────────────────────────────────────────────────────────────'

# Surface insight
high_rate=$(/usr/bin/printf '%s' "$merged" | jq -r '[.[] | select(.override_rate != null and .override_rate >= 50)] | length')
if [[ "$high_rate" -gt 0 ]]; then
  /usr/bin/printf '  ⚠ %d gate(s) overridden ≥50%% of the time — investigate false positives.\n\n' "$high_rate"
fi
