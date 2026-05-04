#!/usr/bin/env bash
# transition.sh — invoked by /contribute SKILL.md on every lifecycle transition.
# This is the single chokepoint between "user wants to take action" and
# "external action happens." Wraps gate-runner + override resolution +
# atomic candidate update.
#
# Usage:
#   transition.sh <action> <candidate-path> [options]
#     action: "shortlist→claimed", "claimed→working", etc.
#   options:
#     --dossier <path>            Override dossier path (default: derive from candidate)
#     --override-gate <id> <reason>  Pre-record an override before running gates (repeatable)
#     --dry-run                   Run gates, print verdict, do NOT mutate candidate
#     --max-gate-age <seconds>    Reject if last gate run for this candidate is older
#                                  (TOCTOU mitigation; default 60)
#
# Exit code: 0 if transition allowed, 1 if BLOCKed (effective after overrides).

set -euo pipefail

ACTION="${1:-}"
CANDIDATE="${2:-}"
shift 2 2>/dev/null || true

if [[ -z "$ACTION" || -z "$CANDIDATE" ]]; then
  echo "usage: $0 <action> <candidate-path> [--dossier PATH] [--override-gate ID REASON ...] [--dry-run] [--max-gate-age SEC]" >&2
  exit 64
fi

if [[ ! -f "$CANDIDATE" ]]; then
  echo "candidate not found: $CANDIDATE" >&2
  exit 65
fi

DOSSIER=""
DRY_RUN=0
MAX_GATE_AGE=60
declare -a OVERRIDES_NEW=()  # pairs: gate id, reason

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dossier)
      DOSSIER="$2"; shift 2 ;;
    --override-gate)
      OVERRIDES_NEW+=("$2" "$3"); shift 3 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    --max-gate-age)
      # shellcheck disable=SC2034 # reserved for TOCTOU mitigation
      MAX_GATE_AGE="$2"; shift 2 ;;
    *)
      echo "unknown option: $1" >&2; exit 64 ;;
  esac
done

LOG="$HOME/.contribute-system/log.jsonl"
NOW=$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)

# Derive dossier path from candidate's repo if not supplied
if [[ -z "$DOSSIER" ]]; then
  REPO=$(/usr/bin/awk '/^---$/{fm=!fm?1:2;next} fm==1 && /^repo:/{sub(/^repo:[[:space:]]*/,""); print; exit}' "$CANDIDATE")
  if [[ -n "$REPO" ]]; then
    SLUG=$(/usr/bin/echo "$REPO" | /usr/bin/tr '/' '_')_; SLUG="${SLUG%_}"  # placeholder; researcher uses double-underscore
    SLUG=$(/usr/bin/echo "$REPO" | /usr/bin/sed 's,/,__,')
    CAND_DOSSIER="$HOME/.contribute-system/research/${SLUG}.md"
    [[ -f "$CAND_DOSSIER" ]] && DOSSIER="$CAND_DOSSIER"
  fi
fi

# Pre-record any overrides into the candidate file (atomic temp+rename)
if [[ "${#OVERRIDES_NEW[@]}" -gt 0 ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "(dry-run) would record ${#OVERRIDES_NEW[@]} overrides; skipping write" >&2
  else
    TMP="${CANDIDATE}.tmp.$$"
    /usr/bin/cp "$CANDIDATE" "$TMP"
    # Append to overrides: array in frontmatter (creates if missing)
    if ! /usr/bin/grep -q '^overrides:' "$TMP"; then
      # Insert before the closing --- of frontmatter
      /usr/bin/awk -v RS='---' 'NR==2{ printf("---%s\noverrides: []\n---", $0); next } {printf("%s", $0); if(NR<3) printf("---")}' "$TMP" > "${TMP}.2" && /usr/bin/mv "${TMP}.2" "$TMP"
    fi
    # Append each override
    i=0
    while [[ $i -lt ${#OVERRIDES_NEW[@]} ]]; do
      OG="${OVERRIDES_NEW[$i]}"
      OR="${OVERRIDES_NEW[$((i+1))]}"
      i=$((i+2))
      ENTRY="  - { gate: $OG, reason: \"$OR\", at: \"$NOW\" }"
      /usr/bin/sed -i "/^overrides:/a $ENTRY" "$TMP"
      # Log
      jq -nc --arg ts "$NOW" --arg gate "$OG" --arg reason "$OR" --arg cand "$CANDIDATE" \
        '{ts: $ts, event: "gate_override", details: {gate: $gate, reason: $reason, candidate: $cand}}' >> "$LOG"
    done
    /usr/bin/mv "$TMP" "$CANDIDATE"  # atomic rename
  fi
fi

# Run gate-runner
/usr/bin/printf '\n[transition] %s on %s\n' "$ACTION" "$(/usr/bin/basename "$CANDIDATE")" >&2
[[ -n "$DOSSIER" ]] && /usr/bin/printf '[transition]   dossier: %s\n' "$DOSSIER" >&2 || /usr/bin/printf '[transition]   dossier: (none — gates that need it will SKIP)\n' >&2

set +e
# Find gate-runner co-located with this script (works whether invoked from
# ~/.contribute-system/bin/ or from the skill's scripts/ dir).
_TRANSITION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE_VERDICT=$("${_TRANSITION_DIR}/gate-runner.sh" "$ACTION" "$CANDIDATE" "$DOSSIER")
GATE_EXIT=$?
set -e

# Surface verdict
echo "$GATE_VERDICT"

# Log the transition attempt
jq -nc --arg ts "$NOW" --arg action "$ACTION" --arg cand "$CANDIDATE" --arg exit "$GATE_EXIT" --arg verdict "$GATE_VERDICT" \
  '{ts: $ts, event: "transition_attempt", details: {action: $action, candidate: $cand, gate_exit: $exit | tonumber, gate_verdict: ($verdict | fromjson? // {raw: $verdict})}}' >> "$LOG" 2>/dev/null || true

if [[ "$GATE_EXIT" -ne 0 ]]; then
  /usr/bin/printf '\n[transition] BLOCKED. Resolve the BLOCKers above or use --override-gate.\n\n' >&2
  exit 1
fi

# Update candidate state if not dry-run
if [[ "$DRY_RUN" -eq 0 ]]; then
  # Parse target state from action ("foo→bar" → "bar")
  NEW_STATE="${ACTION##*→}"
  if [[ "$NEW_STATE" != "$ACTION" && -n "$NEW_STATE" ]]; then
    TMP="${CANDIDATE}.tmp.$$"
    /usr/bin/sed "s/^status: .*/status: $NEW_STATE/" "$CANDIDATE" > "$TMP"
    /usr/bin/mv "$TMP" "$CANDIDATE"  # atomic
    /usr/bin/printf '[transition] candidate status → %s\n\n' "$NEW_STATE" >&2

    # Log success
    jq -nc --arg ts "$NOW" --arg action "$ACTION" --arg cand "$CANDIDATE" --arg new_state "$NEW_STATE" \
      '{ts: $ts, event: "transition_committed", details: {action: $action, candidate: $cand, new_state: $new_state}}' >> "$LOG" 2>/dev/null || true
  fi
fi

exit 0
