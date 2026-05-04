#!/usr/bin/env bash
# gate-runner.sh — the orchestrator that runs gates for a lifecycle transition.
#
# Usage: gate-runner.sh <action> <candidate-path> [<dossier-path>]
#   action: e.g., "shortlist→claimed", "working→submitted", "open-pr", "post-comment"
#
# Discovers gates by glob from ~/.contribute-system/gates/<phase>*.sh,
# filters by which gates apply to this action (per the gate's filename phase
# letter and the action's lifecycle stage), runs each in turn with a 10-second
# timeout, aggregates verdicts.
#
# Output: one JSON per gate to stderr (for human-readable progress);
# final aggregated verdict to stdout.
#
# Exit code: 0 if all PASS/WARN/INFORM/SKIP; 1 if any BLOCK (unless every
# BLOCK was overridden via the candidate's overrides: frontmatter).

set -euo pipefail

ACTION="${1:-}"
CANDIDATE="${2:-}"
DOSSIER="${3:-}"

if [[ -z "$ACTION" || -z "$CANDIDATE" ]]; then
  echo "usage: $0 <action> <candidate-path> [<dossier-path>]" >&2
  exit 64
fi

# Discover gates from two dirs, in priority order:
#   1. Bundled canonical set at skill/scripts/gates/ (discovered via script location)
#   2. User-override gates at ~/.contribute-system/gates/ (personal additions / overrides)
# This split means the bundled set is always present (distributable) and users can
# add custom gates or fork existing ones without modifying the skill package.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLED_GATE_DIR="${SCRIPT_DIR}/gates"
USER_GATE_DIR="$HOME/.contribute-system/gates"
LOG="$HOME/.contribute-system/log.jsonl"
NOW=$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ)

# Map action → relevant gate phases. Gates are filtered by phase letter
# (first char of filename). An action runs all gates in its applicable phases.
case "$ACTION" in
  "open→shortlist")        PHASES="A" ;;
  "shortlist→claimed")     PHASES="A E" ;;
  "claimed→working")       PHASES="A B" ;;
  "working→submitted")     PHASES="B C E F G" ;;
  "open-pr")               PHASES="C E" ;;
  "flip-to-ready")         PHASES="C" ;;
  "post-comment")          PHASES="D" ;;
  "open-issue")            PHASES="D" ;;
  *)                       PHASES="A B C D E F G" ;; # unknown: run everything
esac

# Read disabled_gates from dossier (per-repo opt-out)
DISABLED=""
if [[ -n "$DOSSIER" && -f "$DOSSIER" ]]; then
  DISABLED=$(/usr/bin/awk '/^---$/{fm=!fm?1:2;next} fm==1 && /^disabled_gates:/{
    sub(/^disabled_gates:[[:space:]]*\[/,""); sub(/\][[:space:]]*$/,""); gsub(/[[:space:]]/,""); print; exit
  }' "$DOSSIER" 2>/dev/null || /usr/bin/echo "")
fi

# Read repo + branch from candidate frontmatter
REPO=$(/usr/bin/awk '/^---$/{fm=!fm?1:2;next} fm==1 && /^repo:/{sub(/^repo:[[:space:]]*/,""); print; exit}' "$CANDIDATE" 2>/dev/null || /usr/bin/echo "")
BRANCH=$(/usr/bin/awk '/^---$/{fm=!fm?1:2;next} fm==1 && /^branch:/{sub(/^branch:[[:space:]]*/,""); print; exit}' "$CANDIDATE" 2>/dev/null || /usr/bin/echo "")

# Build the input JSON once (passed to every gate)
INPUT_JSON=$(jq -nc \
  --arg candidate "$CANDIDATE" \
  --arg dossier "$DOSSIER" \
  --arg action "$ACTION" \
  --arg repo "$REPO" \
  --arg branch "$BRANCH" \
  '{candidate: $candidate, dossier: $dossier, action: $action, env: {repo: $repo, branch: $branch}}')

# Discover gate scripts for the relevant phases.
# Bundled gates first, then user-override dir.
# A user gate with the same basename shadows the bundled one (by position in GATES array).
# gate-runner runs all discovered gates; SKIP is cheap.
declare -A SEEN_GATES=()
GATES=()
for DIR in "$BUNDLED_GATE_DIR" "$USER_GATE_DIR" ; do
  [[ -d "$DIR" ]] || continue
  for PHASE in $PHASES ; do
    for GATE in "$DIR"/${PHASE,,}*.sh ; do
      [[ -f "$GATE" && -x "$GATE" ]] || continue
      BN=$(/usr/bin/basename "$GATE")
      # User-override dir wins — if a gate with same name was already queued from
      # bundled dir, replace it. Simple: add all, let user-dir overwrite.
      [[ -z "${SEEN_GATES[$BN]:-}" ]] && GATES+=("$GATE") || true
      SEEN_GATES[$BN]="$GATE"
    done
  done
done

if [[ "${#GATES[@]}" -eq 0 ]]; then
  /usr/bin/echo '{"verdict":"PASS","gates_run":0,"reason":"no gates applicable for this action"}'
  exit 0
fi

# Run each gate. Aggregate.
PASS_COUNT=0
WARN_COUNT=0
BLOCK_COUNT=0
INFORM_COUNT=0
SKIP_COUNT=0
BLOCKERS=()
WARNINGS=()

/usr/bin/printf '\n=== gate-runner: %s — %d gates ===\n' "$ACTION" "${#GATES[@]}" >&2

for GATE in "${GATES[@]}" ; do
  GATE_NAME=$(/usr/bin/basename "$GATE" .sh)
  GATE_ID=$(/usr/bin/printf '%s' "$GATE_NAME" | /usr/bin/cut -d- -f1 | /usr/bin/tr 'a-z' 'A-Z')

  # Per-repo opt-out check
  if /usr/bin/echo ",$DISABLED," | /usr/bin/grep -qi ",$GATE_ID,"; then
    /usr/bin/printf '  [%s] SKIP — disabled per dossier\n' "$GATE_ID" >&2
    SKIP_COUNT=$(( SKIP_COUNT + 1 ))
    continue
  fi

  # Run the gate with timeout. Capture stdout. Exit non-zero = treat as BLOCK.
  if VERDICT_JSON=$(/usr/bin/timeout 10 bash -c "/usr/bin/printf '%s' '$INPUT_JSON' | '$GATE'" 2>/dev/null); then
    : # ok, parse verdict
  else
    VERDICT_JSON=$(jq -nc --arg gid "$GATE_ID" '{severity:"BLOCK", gate:$gid, reason:"gate timed out or crashed (>10s or non-zero exit) — fail-closed", fix_hint:"check the gate script for bugs; preamble.sh should have caught it"}')
  fi

  # Defensive parse: if the gate returned malformed JSON, treat as BLOCK
  if ! /usr/bin/printf '%s' "$VERDICT_JSON" | jq -e . >/dev/null 2>&1; then
    VERDICT_JSON=$(jq -nc --arg gid "$GATE_ID" --arg raw "$VERDICT_JSON" '{severity:"BLOCK", gate:$gid, reason:"gate returned malformed JSON — fail-closed", fix_hint:("raw stdout: " + ($raw | tostring))}')
  fi

  SEV=$(/usr/bin/printf '%s' "$VERDICT_JSON" | jq -r '.severity')
  REASON=$(/usr/bin/printf '%s' "$VERDICT_JSON" | jq -r '.reason')
  FIX=$(/usr/bin/printf '%s' "$VERDICT_JSON" | jq -r '.fix_hint // ""')

  case "$SEV" in
    PASS)   PASS_COUNT=$((PASS_COUNT+1));   /usr/bin/printf '  [%s] \033[32mPASS\033[0m  — %s\n' "$GATE_ID" "$REASON" >&2 ;;
    WARN)   WARN_COUNT=$((WARN_COUNT+1));   WARNINGS+=("$GATE_ID: $REASON ($FIX)") ; /usr/bin/printf '  [%s] \033[33mWARN\033[0m  — %s\n' "$GATE_ID" "$REASON" >&2 ;;
    BLOCK)  BLOCK_COUNT=$((BLOCK_COUNT+1)); BLOCKERS+=("$GATE_ID: $REASON ($FIX)") ; /usr/bin/printf '  [%s] \033[31mBLOCK\033[0m — %s\n         fix: %s\n' "$GATE_ID" "$REASON" "$FIX" >&2 ;;
    INFORM) INFORM_COUNT=$((INFORM_COUNT+1)); /usr/bin/printf '  [%s] INFO  — %s\n' "$GATE_ID" "$REASON" >&2 ;;
    SKIP)   SKIP_COUNT=$((SKIP_COUNT+1));   /usr/bin/printf '  [%s] SKIP  — %s\n' "$GATE_ID" "$REASON" >&2 ;;
    *)      BLOCK_COUNT=$((BLOCK_COUNT+1)); BLOCKERS+=("$GATE_ID: unknown severity '$SEV'") ; /usr/bin/printf '  [%s] BLOCK — unknown severity: %s\n' "$GATE_ID" "$SEV" >&2 ;;
  esac

  # Append run to log
  /usr/bin/printf '%s\n' "$(jq -nc \
    --arg ts "$NOW" \
    --arg gate "$GATE_ID" \
    --arg action "$ACTION" \
    --arg repo "$REPO" \
    --arg sev "$SEV" \
    --arg reason "$REASON" \
    '{ts: $ts, event: "gate_run", details: {gate: $gate, action: $action, repo: $repo, severity: $sev, reason: $reason}}')" >> "$LOG" 2>/dev/null || true
done

# Check overrides on the candidate (any BLOCK gate the user explicitly waived).
OVERRIDDEN=()
if [[ -f "$CANDIDATE" ]] && /usr/bin/grep -q '^overrides:' "$CANDIDATE" 2>/dev/null; then
  while IFS= read -r OG; do
    OVERRIDDEN+=("$OG")
  done < <(/usr/bin/awk '/^overrides:/{flag=1;next} /^[a-z_]+:/{flag=0} flag && /gate:/{sub(/.*gate:[[:space:]]*/,"");sub(/[[:space:]]*,.*$/,"");print}' "$CANDIDATE" 2>/dev/null)
fi

# Filter BLOCKERS against OVERRIDDEN
EFFECTIVE_BLOCKS=()
for B in "${BLOCKERS[@]}"; do
  BID="${B%%:*}"
  IS_OVERRIDDEN=0
  for O in "${OVERRIDDEN[@]}"; do
    [[ "$O" == "$BID" ]] && { IS_OVERRIDDEN=1; break; }
  done
  if [[ "$IS_OVERRIDDEN" -eq 0 ]]; then
    EFFECTIVE_BLOCKS+=("$B")
  fi
done

# Final verdict
TOTAL=${#GATES[@]}
EFFECTIVE_BLOCK_COUNT=${#EFFECTIVE_BLOCKS[@]}
/usr/bin/printf '\n=== summary: %d gates · %d PASS · %d WARN · %d BLOCK (%d after overrides) · %d INFORM · %d SKIP ===\n\n' \
  "$TOTAL" "$PASS_COUNT" "$WARN_COUNT" "$BLOCK_COUNT" "$EFFECTIVE_BLOCK_COUNT" "$INFORM_COUNT" "$SKIP_COUNT" >&2

if [[ "$EFFECTIVE_BLOCK_COUNT" -gt 0 ]]; then
  /usr/bin/echo "$(jq -nc --argjson b "$(printf '%s\n' "${EFFECTIVE_BLOCKS[@]}" | jq -R . | jq -s .)" --argjson w "$(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)" --argjson n "$EFFECTIVE_BLOCK_COUNT" '{verdict: "BLOCK", effective_blocks: $n, blockers: $b, warnings: $w}')"
  exit 1
else
  /usr/bin/echo "$(jq -nc --argjson w "$(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)" --argjson p "$PASS_COUNT" '{verdict: "PASS", gates_passed: $p, warnings: $w}')"
  exit 0
fi
