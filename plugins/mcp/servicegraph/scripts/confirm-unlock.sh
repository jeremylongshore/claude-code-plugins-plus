#!/usr/bin/env bash
# confirm-unlock.sh — PreToolUse gate for mcp__servicegraph__unlock_rows.
#
# unlock_rows spends paid ServiceGraph credits irreversibly (~10 credits ≈
# $0.10 per row). The MCP server is remote HTTP, so this host-side hook is the
# only local enforcement point: it returns permissionDecision "ask" so the
# host always surfaces the spend for explicit user confirmation, regardless of
# auto-accept settings that honor hook decisions. Read-only tools are
# unaffected (the matcher targets unlock_rows alone).
set -euo pipefail

cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "unlock_rows spends paid ServiceGraph credits irreversibly (~10 credits ≈ $0.10 per row). Confirm the batch size and cost — check get_credit_balance first for large batches."
  }
}
JSON
