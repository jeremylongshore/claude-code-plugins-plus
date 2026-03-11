#!/usr/bin/env bash
# Pre-commit reminder hook.
# Fires before Bash tool use — when the command is a git commit,
# reminds Claude to capture lessons learned in CLAUDE.md.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
  exit 0
fi

if echo "$COMMAND" | grep -q "git commit"; then
  cat <<'REMINDER'
[PM Commit Reminder] Before committing, consider:
- Did you learn something that should be added to CLAUDE.md? ("Update CLAUDE.md so you don't make that mistake again")
- Are sandbox/ drafts marked with status (draft/ready/final)?
- Should any sandbox work graduate to product-catalog/?
REMINDER
fi
