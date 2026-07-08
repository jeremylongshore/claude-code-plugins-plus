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

mkdir -p "$LOG_DIR"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '{"type":"rollout-captured","skill_id":"%s","at":"%s"}\n' "$SKILL_ID" "$TS" >> "$LOG_FILE"

# Count rollouts for this skill; once the threshold is met, fire the refiner
# in the background (Sonnet propose / Haiku score) and surface next turn.
COUNT=$(grep -c "\"skill_id\":\"${SKILL_ID}\"" "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$COUNT" -ge "$JRIG_LINE_ROLLOUT_THRESHOLD" ]; then
  {
    echo "[j-rig · Line L2] ${COUNT} rollouts accumulated on skill '${SKILL_ID}'."
    echo "  Firing a background refiner pass. Review the candidate next turn with:"
    echo "    /j-rig refine status ${SKILL_ID}"
  } >&2
  # Thin wrapper over the published refiner CLI; background + detached so the
  # Stop hook returns immediately (mid-tier cost is paid off-turn).
  if command -v j-rig >/dev/null 2>&1; then
    ( j-rig refine propose "skills/${SKILL_ID}" --model sonnet >/dev/null 2>&1 & ) || true
  fi
fi

exit 0
