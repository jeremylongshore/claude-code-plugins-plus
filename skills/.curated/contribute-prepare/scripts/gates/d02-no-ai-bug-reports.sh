#!/usr/bin/env bash
# Catalog: D2 — Block AI-shaped issue body when opening a new issue
# Many repos auto-close machine-generated bug reports on sight. We refuse
# to ship one in our name.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Extract the "## Issue body draft" section from the candidate
DRAFT=$(/usr/bin/awk '/^## Issue body draft/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "${DRAFT// /}" ]]; then
  gate_skip "no issue draft yet"
fi

# AI-shaped patterns. Case-insensitive. Each entry is one distinct pattern.
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

if (( COUNT >= 2 )); then
  gate_block "issue draft contains $COUNT AI-shaped phrases: $JOINED" "rewrite the issue in your own voice; many repos auto-close AI-shaped bug reports"
fi

if (( COUNT == 1 )); then
  gate_warn "issue draft contains AI-shaped phrase: $JOINED" "consider rewriting in your own voice"
fi

gate_pass "no AI-shaped phrases detected"
