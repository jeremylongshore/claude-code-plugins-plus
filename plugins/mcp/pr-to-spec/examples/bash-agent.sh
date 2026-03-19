#!/bin/bash
# bash-agent.sh — Minimal bash script that fetches a PR spec and makes a decision
#
# Usage:
#   export GITHUB_TOKEN=ghp_xxx
#   export ANTHROPIC_API_KEY=sk-ant-xxx
#   ./examples/bash-agent.sh owner/repo 42

set -euo pipefail

REPO="${1:?Usage: bash-agent.sh <owner/repo> <pr-number>}"
PR_NUM="${2:?Usage: bash-agent.sh <owner/repo> <pr-number>}"

# Step 1: Generate the spec
echo "Generating spec for ${REPO}#${PR_NUM}..."
SPEC=$(pr-to-prompt --repo "$REPO" --pr "$PR_NUM" --json)
EXIT_CODE=$?

# Step 2: Check exit code for high-risk
if [ $EXIT_CODE -eq 2 ]; then
	echo "WARNING: High-risk PR detected"
	echo "$SPEC" | jq '.risk_flags[] | select(.severity == "high")'
fi

# Step 3: Extract key fields
CHANGE_TYPE=$(echo "$SPEC" | jq -r '.intent.change_type')
FILES_CHANGED=$(echo "$SPEC" | jq -r '.stats.files_changed')
RISK_COUNT=$(echo "$SPEC" | jq '.risk_flags | length')
HIGH_RISK_COUNT=$(echo "$SPEC" | jq '[.risk_flags[] | select(.severity == "high")] | length')
DECISION_PROMPT=$(echo "$SPEC" | jq -r '.decision_prompt')

echo ""
echo "=== PR Summary ==="
echo "Type: ${CHANGE_TYPE}"
echo "Files: ${FILES_CHANGED}"
echo "Risks: ${RISK_COUNT} (${HIGH_RISK_COUNT} high)"
echo ""

# Step 4: Auto-decide based on heuristics
if [ "$HIGH_RISK_COUNT" -gt 0 ]; then
	echo "DECISION: REQUEST_CHANGES — High-risk flags require human review"
	echo ""
	echo "High-risk items:"
	echo "$SPEC" | jq -r '.risk_flags[] | select(.severity == "high") | "  - [\(.category)] \(.description)"'
	exit 2
fi

if [ "$FILES_CHANGED" -gt 30 ]; then
	echo "DECISION: NEEDS_INFO — PR is too large (${FILES_CHANGED} files). Consider splitting."
	exit 2
fi

# Step 5: For medium-risk or clean PRs, use an LLM for nuanced review
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
	echo "Sending to Claude for review..."
	REVIEW=$(echo "$SPEC" | claude --print "You are a code reviewer. $(echo "$DECISION_PROMPT")" 2>/dev/null || true)

	if [ -n "$REVIEW" ]; then
		echo ""
		echo "=== AI Review ==="
		echo "$REVIEW"
	else
		echo "DECISION: APPROVE — No high risks, LLM review unavailable"
	fi
else
	echo "DECISION: APPROVE — No high risks detected (set ANTHROPIC_API_KEY for AI review)"
fi
