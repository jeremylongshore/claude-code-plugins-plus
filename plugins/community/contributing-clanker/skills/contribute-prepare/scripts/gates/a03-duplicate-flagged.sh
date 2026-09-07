#!/usr/bin/env bash
# Catalog: A3 — Issue flagged as duplicate in body or comments
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

TEXT=$(gh_safe issue view "$ISSUE_NUM" --repo "$GATE_REPO" --json body,comments --jq '.body + " " + (.comments | map(.body) | join(" "))' || /usr/bin/echo "")

if [[ -z "$TEXT" ]]; then
  gate_inform "could not fetch issue body/comments"
fi

if /usr/bin/printf '%s' "$TEXT" | /usr/bin/grep -qiE "(duplicate of|dupe of|see)[[:space:]]+#[0-9]+"; then
  gate_warn "issue body or comments mention being a duplicate" "verify with the maintainer before claiming; the underlying issue may be elsewhere"
fi

gate_pass "no duplicate references found"
