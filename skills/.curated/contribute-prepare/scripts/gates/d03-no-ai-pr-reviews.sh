#!/usr/bin/env bash
# Catalog: D3 — Block AI-generated review comments on someone else's PR
# AI-shaped review comments are unwelcome at most repos. Stricter than D2:
# any single hit blocks.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

DRAFT=$(/usr/bin/awk '/^## Review draft/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "${DRAFT// /}" ]]; then
  gate_skip "no review draft yet"
fi

PATTERNS=(
  "I noticed"
  "It appears"
  "I observed"
  "the AI suggests"
  "Claude suggests"
  "ChatGPT suggests"
  "based on my analysis"
  "after analyzing"
  "I've identified"
  "the issue stems from"
)

HITS=()
for pat in "${PATTERNS[@]}"; do
  if /usr/bin/printf '%s' "$DRAFT" | /usr/bin/grep -qiE "$pat"; then
    HITS+=("$pat")
  fi
done

COUNT=${#HITS[@]}
JOINED=$(/usr/bin/printf '%s, ' "${HITS[@]}" 2>/dev/null | /usr/bin/sed 's/, $//')

if (( COUNT >= 1 )); then
  gate_block "review draft contains $COUNT AI-shaped phrase(s): $JOINED" "AI-generated review comments are unwelcome at most repos; either rewrite in your own voice or skip the review"
fi

gate_pass "no AI-shaped phrases detected"
