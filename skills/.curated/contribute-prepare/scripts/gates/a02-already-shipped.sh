#!/usr/bin/env bash
# Catalog: A2 — Claim work that's already merged in another PR
# Mitigates: PostHog #55412 trap (2026-05-02) — issue was open but PR #57145
# had already merged the principled fix. Without this check we'd have
# submitted a duplicate and burned an AI policy strike.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

# Check each of GitHub's three auto-close keywords. NB: gh search uses --merged
# (NOT --state=merged), and "X OR Y OR Z" is treated as a literal phrase, so
# we must run separate calls. (Lessons logged in scout's MEMORY.md.)
SHIPPED_PR=""
for KW in closes fixes resolves ; do
  HIT=$(gh_safe search prs --repo="$GATE_REPO" "$KW #$ISSUE_NUM" --merged --limit 1 --json url --jq '.[0].url // empty' || /usr/bin/echo "")
  if [[ -n "$HIT" ]]; then
    SHIPPED_PR="$HIT"
    break
  fi
done

if [[ -n "$SHIPPED_PR" ]]; then
  gate_block "issue already shipped in $SHIPPED_PR" "the issue is open but its fix has already merged. Post a 'safe to close?' comment on the issue (good citizen move) and pick a different candidate."
fi

gate_pass "no merged PR claims to close this issue"
