#!/usr/bin/env bash
# Catalog: A1 — Claim already-assigned issue
# Mitigates: Tracer-Cloud opensre #1129 trap (2026-05-02) — issue assigned to
# unKnownNG day before our scout run; he was actively asking maintainer
# clarifying questions in comments. We almost claim-jumped real human work.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Pull issue number from candidate frontmatter
ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

# Live check (this is one of the few gates that MUST be live — assignment
# state changes too fast to trust the dossier)
ASSIGNEES=$(gh_safe issue view "$ISSUE_NUM" --repo "$GATE_REPO" --json assignees --jq '[.assignees[].login] | join(",")' || /usr/bin/echo "")

if [[ -n "$ASSIGNEES" ]]; then
  gate_block "issue is assigned to [$ASSIGNEES]" "wait for them to drop it, or pick a different candidate. Override only if you've coordinated with the assignee in a comment."
fi

gate_pass "no assignees on issue"
