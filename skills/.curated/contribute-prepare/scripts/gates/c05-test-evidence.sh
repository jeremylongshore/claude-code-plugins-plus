#!/usr/bin/env bash
# Catalog: C5 — PR body lacks fenced test-runner output (evidence of local verification)
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Extract candidate's `## PR body` section
PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")
if [[ -z "$PR_BODY" ]]; then
  gate_skip "no '## PR body' section in candidate yet"
fi

# Walk fenced blocks (```...```) and check each for test-runner signals.
# Use awk to flip flag on ``` lines and collect block contents, separated by NUL-equivalent marker.
BLOCKS=$(/usr/bin/printf '%s' "$PR_BODY" | /usr/bin/awk '
  /^```/ { in_block = !in_block; if (!in_block) print "<<<BLOCK_END>>>"; next }
  in_block { print }
')

if [[ -z "$BLOCKS" ]]; then
  gate_block "PR body has no fenced code blocks" "paste your local test output as a fenced code block inside the PR body"
fi

# Test runner regexes — any one match in any block is sufficient
PATTERNS='pytest|cargo test|make test|pnpm test|npm test|yarn test|sbt test|go test|Test Suites:|[0-9]+ passed|[0-9]+ passing|[0-9]+ failed|^ok [0-9]+|PASS|FAIL'

if /usr/bin/printf '%s' "$BLOCKS" | /usr/bin/grep -qE "$PATTERNS"; then
  gate_pass "PR body contains fenced block with test-runner output"
fi

gate_block "no fenced code block in PR body looks like test runner output" "paste your local test output as a fenced code block inside the PR body"
