#!/usr/bin/env bash
# Catalog: A6 — Repo requires claim-etiquette comment before working
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

REQUIRED=$(fm_field "$GATE_DOSSIER_PATH" "etiquette_comment_required")
if [[ "$REQUIRED" != "true" ]]; then
  gate_skip "etiquette_comment_required is not true"
fi

ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

LOGIN=$(gh_safe api user --jq .login || /usr/bin/echo "")
if [[ -z "$LOGIN" ]]; then
  gate_inform "could not resolve gh user login"
fi

COMMENTS=$(gh_safe issue view "$ISSUE_NUM" --repo "$GATE_REPO" --json comments --jq "[.comments[] | select(.author.login == \"$LOGIN\") | .body] | join(\"\n---\n\")" || /usr/bin/echo "")

if [[ -z "$COMMENTS" ]]; then
  gate_block "no claim comment from $LOGIN found on issue #$ISSUE_NUM" "this repo wants you to comment on the issue before working on it; post a claim comment and re-run the transition"
fi

if /usr/bin/printf '%s' "$COMMENTS" | /usr/bin/grep -qiE "(i'?d like to take this|i'?ll take this|happy to take this|working on this|claiming this|would like to work on|let me know if i can take|i'?d be happy to work)"; then
  gate_pass "found claim-shaped comment from $LOGIN"
fi

gate_block "no claim-shaped comment from $LOGIN on issue #$ISSUE_NUM" "this repo wants you to comment on the issue before working on it; post a claim comment and re-run the transition"
