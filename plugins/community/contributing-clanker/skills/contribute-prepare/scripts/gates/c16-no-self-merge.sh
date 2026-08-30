#!/usr/bin/env bash
# Catalog: C16 — author attempts to merge their own PR
# Mitigates: bypassing maintainer review on a contribution is a hard etiquette violation.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

PR_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "pr_number")
if [[ -z "$PR_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no pr_number or repo in candidate"
fi

PR_AUTHOR=$(gh_safe pr view "$PR_NUM" --repo "$GATE_REPO" --json author --jq '.author.login' || /usr/bin/echo "")
ME=$(gh_safe api user --jq '.login' || /usr/bin/echo "")

if [[ -z "$PR_AUTHOR" || -z "$ME" ]]; then
  gate_skip "could not resolve PR author or current user"
fi

if [[ "$PR_AUTHOR" == "$ME" ]]; then
  gate_block "you ($ME) authored PR #$PR_NUM — self-merge would bypass maintainer review" "you authored this PR — wait for a maintainer to merge"
fi

gate_pass "PR author ($PR_AUTHOR) differs from current user ($ME)"
