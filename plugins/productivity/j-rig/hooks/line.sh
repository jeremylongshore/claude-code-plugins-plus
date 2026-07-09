#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# L2 — LINE  ($ mid-tier — Haiku scores rollouts, Sonnet runs the refiner)
# ─────────────────────────────────────────────────────────────────────────────
# Event: Stop (end of turn).
# Captures end-of-turn rollouts. If a skill was invoked during the turn AND
# j-rig has scored its rollouts, append a rollout record to the append-only
# event log at .j-rig/refiner/log.jsonl. Once N rollouts accumulate on a
# single skill, fire the refiner in the BACKGROUND (never blocks the turn) so
# the candidate surfaces in the next turn's context.
#
# Rollout accumulation makes this layer amortized-cheap: no per-edit model
# call; the Sonnet refiner only fires once a skill has enough scored evidence
# (default threshold N=5). Reads the Stop event JSON from stdin.
set -euo pipefail

INPUT=$(cat)

LOG_DIR=".j-rig/refiner"
LOG_FILE="${LOG_DIR}/log.jsonl"
# Accumulation threshold — fire the refiner once this many rollouts land on
# one skill. Overridable via env for demos/tests.
: "${JRIG_LINE_ROLLOUT_THRESHOLD:=5}"

# Was a skill invoked this turn? The Stop event carries session context; a
# real deployment inspects j-rig's scored-rollout store. Absent a store, exit
# quietly — the Line layer is opportunistic, never noisy.
SKILL_ID=$(echo "$INPUT" | jq -r '.skill_id // .last_skill // empty' 2>/dev/null || true)
if [ -z "$SKILL_ID" ]; then
  exit 0
fi

# Validate before use: a skill id is a simple slug. Reject anything with regex
# metacharacters or path separators BEFORE it reaches a grep pattern (count
# inflation) or a CLI path argument (`../../…` traversal outside skills/).
if ! printf '%s' "$SKILL_ID" | grep -qE '^[a-zA-Z0-9_-]+$'; then
  exit 0
fi

mkdir -p "$LOG_DIR"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"rollout-captured","skill_id":"%s","at":"%s"}\n' "$SKILL_ID" "$TS" >> "$LOG_FILE"

# Count rollouts for this skill. -F (fixed-string) match — SKILL_ID is a
# validated slug, and -F removes any doubt about regex interpretation.
COUNT=$(grep -Fc "\"skill_id\":\"${SKILL_ID}\"" "$LOG_FILE" 2>/dev/null || echo 0)

# Amortize correctly: fire only when THRESHOLD *new* rollouts have accumulated
# SINCE THE LAST background fire for this skill — not on every turn once the
# lifetime count first crosses the threshold (which would fire indefinitely and
# silently burn budget). Track the count at last fire, per skill.
FIRED_FILE="${LOG_DIR}/.last-fired-${SKILL_ID}"
LAST_FIRED=$(cat "$FIRED_FILE" 2>/dev/null || echo 0)
case "$LAST_FIRED" in '' | *[!0-9]*) LAST_FIRED=0 ;; esac
if [ "$((COUNT - LAST_FIRED))" -ge "$JRIG_LINE_ROLLOUT_THRESHOLD" ]; then
  {
    echo "[j-rig · Line L2] ${COUNT} rollouts on skill '${SKILL_ID}' ($((COUNT - LAST_FIRED)) since last pass)."
    echo "  Firing a background refiner pass. Review the candidate next turn with:"
    echo "    /j-rig refine status ${SKILL_ID}"
  } >&2
  # Record the fire BEFORE launching so a rapid second Stop in the same window
  # cannot double-fire; the next fire waits for another THRESHOLD rollouts.
  echo "$COUNT" > "$FIRED_FILE"
  # Thin wrapper over the published refiner CLI; background + detached so the
  # Stop hook returns immediately (mid-tier cost is paid off-turn).
  if command -v j-rig >/dev/null 2>&1; then
    ( j-rig refine propose "skills/${SKILL_ID}" --model sonnet >/dev/null 2>&1 & ) || true
  fi
fi

exit 0
