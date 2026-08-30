#!/usr/bin/env bash
# Catalog: C2 — PR title violates repo-required regex
# Mitigates: maintainer immediately requests rename, signals "didn't read CONTRIBUTING".
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier — cannot determine pr_title_regex"
fi

REGEX=$(fm_field "$GATE_DOSSIER_PATH" "pr_title_regex")
if [[ -z "$REGEX" ]]; then
  gate_skip "dossier has no pr_title_regex"
fi

# Try frontmatter first
TITLE=$(fm_field "$GATE_CANDIDATE_PATH" "pr_title")

# Fall back to ## PR title section (single line content)
if [[ -z "$TITLE" ]]; then
  TITLE=$(/usr/bin/awk '/^## PR title/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null \
    | /usr/bin/grep -m1 -v '^[[:space:]]*$' \
    | /usr/bin/sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    || /usr/bin/echo "")
fi

if [[ -z "$TITLE" ]]; then
  gate_skip "no PR title in candidate (frontmatter or ## PR title section)"
fi

if /usr/bin/printf '%s' "$TITLE" | /usr/bin/grep -qE "$REGEX"; then
  gate_pass "PR title matches required regex"
fi

gate_block "PR title '$TITLE' does not match required regex /$REGEX/" "rename PR title to match /$REGEX/ per CONTRIBUTING.md"
