#!/usr/bin/env bash
# Catalog: C9 — PR body lacks `Closes #N` / `Fixes #N` referencing the candidate
# Mitigates: PR doesn't auto-close the issue on merge → maintainer has to do it
# manually → reads as low-effort.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# This gate runs at open-pr / flip-to-ready transitions and needs the PR body.
# At this stage the PR body lives in the candidate's `pr_body_draft:` field
# (written by writer subagent in Slice 3). For now, look in the candidate's
# `## PR body` section if present.
ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" ]]; then
  gate_skip "no issue_number in candidate (cannot verify link)"
fi

# Extract PR body draft from candidate's body sections
PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$PR_BODY" ]]; then
  # No PR body drafted yet — gate is informational at pre-draft stages
  gate_inform "no PR body drafted yet (candidate has no '## PR body' section)"
fi

# Look for any of: Closes #N, Fixes #N, Resolves #N (case-insensitive)
if /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qiE "(closes|fixes|resolves)[[:space:]]+#?$ISSUE_NUM\b"; then
  gate_pass "PR body links issue #$ISSUE_NUM via auto-close keyword"
fi

gate_block "PR body does not reference issue #$ISSUE_NUM with an auto-close keyword" "add 'Closes #$ISSUE_NUM' (or Fixes/Resolves) to the PR body so the issue auto-closes on merge."
