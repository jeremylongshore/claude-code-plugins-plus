#!/usr/bin/env bash
# lint-candidate.sh — report missing required body sections in candidate files.
#
# Sibling to audit-overrides.sh and catalog-coverage.sh: a read-only reporter
# that walks ~/.contribute-system/candidates/, reads each candidate's status,
# and surfaces missing required sections per the matrix in
# skills/contribute/references/candidate-file-format.md.
#
# Required-sections matrix (matches the spec + transition.sh):
#   shortlist  → ## Scope, ## Files to touch
#   claimed    → ## Scope, ## Files to touch, ## Claim comment draft
#   working    → same as claimed
#   submitted  → ## PR title, ## PR body, ## Test results
#   merged     → same as submitted
#   open       → no body requirements
#   dropped    → no body requirements
#
# Usage:
#   lint-candidate.sh                  # all candidates, table output
#   lint-candidate.sh --status=submitted   # filter to one status
#   lint-candidate.sh --missing-only       # only candidates with missing sections
#   lint-candidate.sh --json               # JSON output (one object per candidate)
#   lint-candidate.sh --candidates-dir=X   # override the candidate dir
#
# Exit codes:
#   0  — no missing sections across the filtered set (clean)
#   1  — at least one candidate has missing required sections
#   64 — bad arguments

set -uo pipefail

CAND_DIR="${HOME}/.contribute-system/candidates"
STATUS_FILTER=""
MISSING_ONLY=0
JSON_OUT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status=*)         STATUS_FILTER="${1#*=}" ;;
    --missing-only)     MISSING_ONLY=1 ;;
    --json)             JSON_OUT=1 ;;
    --candidates-dir=*) CAND_DIR="${1#*=}" ;;
    -h|--help)          /usr/bin/sed -n '2,28p' "$0" | /usr/bin/sed 's/^# \{0,1\}//'; exit 0 ;;
    *)                  /usr/bin/echo "unknown arg: $1" >&2; exit 64 ;;
  esac
  shift
done

if [[ ! -d "$CAND_DIR" ]]; then
  /usr/bin/echo "candidate dir not found: $CAND_DIR" >&2
  exit 64
fi

# Required-sections per status. Pipe-delimited for compatibility with the
# same scheme transition.sh uses.
required_for() {
  case "$1" in
    shortlist) /usr/bin/echo '## Scope|## Files to touch' ;;
    claimed)   /usr/bin/echo '## Scope|## Files to touch|## Claim comment draft' ;;
    working)   /usr/bin/echo '## Scope|## Files to touch|## Claim comment draft' ;;
    submitted) /usr/bin/echo '## PR title|## PR body|## Test results' ;;
    merged)    /usr/bin/echo '## PR title|## PR body|## Test results' ;;
    *)         /usr/bin/echo '' ;;  # open, dropped, unknown
  esac
}

# Per-candidate evaluation. Echoes a JSON object per candidate so the table
# pass and the JSON pass can both consume it.
evaluate_one() {
  local file="$1"
  local basename
  basename=$(/usr/bin/basename "$file")
  local status
  status=$(/usr/bin/awk '/^---$/{fm=!fm?1:2;next} fm==1 && /^status:/{sub(/^status:[[:space:]]*/,""); print; exit}' "$file" 2>/dev/null)
  status="${status:-unknown}"

  local req
  req=$(required_for "$status")

  local missing=()
  if [[ -n "$req" ]]; then
    IFS='|' read -ra SECTIONS <<< "$req"
    for sec in "${SECTIONS[@]}"; do
      if ! /usr/bin/grep -qE "^${sec}\b" "$file" 2>/dev/null; then
        missing+=("$sec")
      fi
    done
  fi

  local missing_json
  if [[ "${#missing[@]}" -eq 0 ]]; then
    missing_json='[]'
  else
    missing_json=$(/usr/bin/printf '%s\n' "${missing[@]}" | jq -Rsc 'split("\n") | map(select(. != ""))')
  fi

  jq -nc --arg cand "$basename" --arg status "$status" --argjson missing "$missing_json" \
    '{candidate: $cand, status: $status, missing: $missing, missing_count: ($missing | length)}'
}

# Walk all candidates, evaluate each, capture rows.
ROWS=()
EXIT_CODE=0
shopt -s nullglob
for f in "$CAND_DIR"/*.md; do
  row=$(evaluate_one "$f")
  STATUS=$(/usr/bin/echo "$row" | jq -r .status)
  MISSING_COUNT=$(/usr/bin/echo "$row" | jq -r .missing_count)

  # Apply --status filter
  if [[ -n "$STATUS_FILTER" && "$STATUS" != "$STATUS_FILTER" ]]; then
    continue
  fi
  # Apply --missing-only filter
  if [[ "$MISSING_ONLY" -eq 1 && "$MISSING_COUNT" -eq 0 ]]; then
    continue
  fi

  ROWS+=("$row")
  if [[ "$MISSING_COUNT" -gt 0 ]]; then
    EXIT_CODE=1
  fi
done
shopt -u nullglob

# Emit
if [[ "$JSON_OUT" -eq 1 ]]; then
  /usr/bin/printf '%s\n' "${ROWS[@]}" | jq -s '.'
else
  /usr/bin/printf '%-55s  %-10s  %s\n' 'candidate' 'status' 'missing'
  /usr/bin/printf '%-55s  %-10s  %s\n' '---------' '------' '-------'
  if [[ "${#ROWS[@]}" -eq 0 ]]; then
    /usr/bin/printf '(no candidates matched filter)\n'
  else
    for row in "${ROWS[@]}"; do
      cand=$(/usr/bin/echo "$row" | jq -r .candidate)
      status=$(/usr/bin/echo "$row" | jq -r .status)
      missing_str=$(/usr/bin/echo "$row" | jq -r '.missing | if length == 0 then "(none)" else join(", ") end')
      /usr/bin/printf '%-55s  %-10s  %s\n' "$cand" "$status" "$missing_str"
    done

    # Summary footer
    TOTAL=${#ROWS[@]}
    DIRTY=$(/usr/bin/printf '%s\n' "${ROWS[@]}" | jq -s '[.[] | select(.missing_count > 0)] | length')
    /usr/bin/printf '\n%d candidate(s) shown · %d with missing sections\n' "$TOTAL" "$DIRTY"
  fi
fi

exit "$EXIT_CODE"
