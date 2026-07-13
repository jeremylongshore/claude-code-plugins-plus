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

# Pre-record any overrides into the candidate file (atomic temp+rename).
#
# Earlier implementation used `awk -v RS='---'` to insert `overrides: []`
# before the closing frontmatter delimiter, then `sed -i "/^overrides:/a"`
# to append each entry. That path corrupted YAML: the awk RS=--- handling
# mangled the opening delimiter to "------" (6 dashes) and the sed
# append landed entries OUTSIDE the array as sibling list items rather
# than children of `overrides`.
#
# Replace with a Python yaml round-trip — parse frontmatter, append to
# the overrides list as proper YAML mapping entries, re-serialize. The
# body (everything after the second `---`) passes through unchanged.
if [[ "${#OVERRIDES_NEW[@]}" -gt 0 ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "(dry-run) would record ${#OVERRIDES_NEW[@]} overrides; skipping write" >&2
  else
    TMP="${CANDIDATE}.tmp.$$"
    # Build a flat list of "gate=reason" pairs for the Python helper.
    # Use NUL as field separator to handle reasons containing any char.
    PAIRS_FILE="${CANDIDATE}.pairs.$$"
    : > "$PAIRS_FILE"
    i=0
    while [[ $i -lt ${#OVERRIDES_NEW[@]} ]]; do
      /usr/bin/printf '%s\0%s\0' "${OVERRIDES_NEW[$i]}" "${OVERRIDES_NEW[$((i+1))]}" >> "$PAIRS_FILE"
      i=$((i+2))
    done

    /usr/bin/python3 - "$CANDIDATE" "$NOW" "$PAIRS_FILE" "$TMP" <<'PYEOF'
import sys, yaml

cand_path, now_iso, pairs_path, out_path = sys.argv[1:5]

with open(cand_path) as f:
    text = f.read()

# Split frontmatter from body (markdown convention: --- on its own line)
lines = text.split('\n')
if not lines or lines[0].strip() != '---':
    sys.stderr.write("transition: candidate has no opening frontmatter delimiter\n")
    sys.exit(2)
try:
    end = lines.index('---', 1)
except ValueError:
    sys.stderr.write("transition: candidate has no closing frontmatter delimiter\n")
    sys.exit(2)

fm_text = '\n'.join(lines[1:end])
body_text = '\n'.join(lines[end+1:])

fm = yaml.safe_load(fm_text) or {}
if not isinstance(fm, dict):
    sys.stderr.write("transition: frontmatter is not a mapping\n")
    sys.exit(2)

if 'overrides' not in fm or fm['overrides'] is None:
    fm['overrides'] = []
if not isinstance(fm['overrides'], list):
    sys.stderr.write("transition: existing overrides field is not a list\n")
    sys.exit(2)

# Read NUL-separated pairs from pairs_path: gate, reason, gate, reason, ...
with open(pairs_path, 'rb') as f:
    raw = f.read()
parts = raw.split(b'\x00')
# Trailing NUL produces an empty final element — drop it.
if parts and parts[-1] == b'':
    parts.pop()
if len(parts) % 2 != 0:
    sys.stderr.write("transition: malformed override pairs (odd count)\n")
    sys.exit(2)

for i in range(0, len(parts), 2):
    gate = parts[i].decode('utf-8')
    reason = parts[i+1].decode('utf-8')
    fm['overrides'].append({'gate': gate, 'reason': reason, 'at': now_iso})

# Re-serialize. default_flow_style=False keeps blocks readable.
new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True).rstrip('\n')
new_text = '---\n' + new_fm + '\n---\n' + body_text

with open(out_path, 'w') as f:
    f.write(new_text)
PYEOF

    PY_EXIT=$?
    /usr/bin/rm -f "$PAIRS_FILE"
    if [[ "$PY_EXIT" -ne 0 ]]; then
      /usr/bin/rm -f "$TMP"
      echo "transition: yaml round-trip failed (exit $PY_EXIT) — candidate not modified" >&2
      exit 65
    fi

    /usr/bin/mv "$TMP" "$CANDIDATE"  # atomic rename

    # Log each override
    i=0
    while [[ $i -lt ${#OVERRIDES_NEW[@]} ]]; do
      OG="${OVERRIDES_NEW[$i]}"
      OR="${OVERRIDES_NEW[$((i+1))]}"
      i=$((i+2))
      jq -nc --arg ts "$NOW" --arg gate "$OG" --arg reason "$OR" --arg cand "$CANDIDATE" \
        '{ts: $ts, event: "gate_override", details: {gate: $gate, reason: $reason, candidate: $cand}}' >> "$LOG"
    done
  fi
fi

# Advisory: warn on missing required body sections per target status.
# Per skills/contribute/references/candidate-file-format.md § "Required
# sections by lifecycle stage". WARN (not BLOCK) — backfilled candidates
# legitimately came in mid-lifecycle without early-stage sections.
TARGET_STATUS="${ACTION##*→}"
REQUIRED_SECTIONS=""
case "$TARGET_STATUS" in
  shortlist) REQUIRED_SECTIONS="## Scope|## Files to touch" ;;
  claimed)   REQUIRED_SECTIONS="## Scope|## Files to touch|## Claim comment draft" ;;
  working)   REQUIRED_SECTIONS="## Scope|## Files to touch|## Claim comment draft" ;;
  submitted) REQUIRED_SECTIONS="## PR title|## PR body|## Test results" ;;
  merged)    REQUIRED_SECTIONS="## PR title|## PR body|## Test results" ;;
  *)         REQUIRED_SECTIONS="" ;;  # open, dropped: no body requirements
esac

MISSING_SECTIONS=()
if [[ -n "$REQUIRED_SECTIONS" ]]; then
  IFS='|' read -ra SECTIONS <<< "$REQUIRED_SECTIONS"
  for sec in "${SECTIONS[@]}"; do
    # Match the section header anchored at line start (avoid false positives
    # inside code blocks or quoted text).
    if ! /usr/bin/grep -qE "^${sec}\b" "$CANDIDATE"; then
      MISSING_SECTIONS+=("$sec")
    fi
  done
fi

if [[ "${#MISSING_SECTIONS[@]}" -gt 0 ]]; then
  /usr/bin/printf '[transition] WARN: candidate is missing %d required section(s) for status=%s:\n' \
    "${#MISSING_SECTIONS[@]}" "$TARGET_STATUS" >&2
  for sec in "${MISSING_SECTIONS[@]}"; do
    /usr/bin/printf '[transition]   - %s\n' "$sec" >&2
  done
  /usr/bin/printf '[transition]   (advisory only — see references/candidate-file-format.md;\n' >&2
  /usr/bin/printf '[transition]    backfilled candidates legitimately skip early-stage sections)\n' >&2
  # Log it so audits can see the pattern frequency
  MISSING_JSON=$(/usr/bin/printf '%s\n' "${MISSING_SECTIONS[@]}" | jq -Rsc 'split("\n") | map(select(. != ""))')
  jq -nc --arg ts "$NOW" --arg cand "$CANDIDATE" --arg target "$TARGET_STATUS" \
        --argjson missing "$MISSING_JSON" \
    '{ts: $ts, event: "transition_section_warn",
      details: {candidate: $cand, target_status: $target, missing_sections: $missing}}' \
    >> "$LOG" 2>/dev/null || true
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
