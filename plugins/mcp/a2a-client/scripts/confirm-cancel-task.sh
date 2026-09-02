#!/usr/bin/env bash
# Host-side layer of cancel_task's three-layer confirmation policy. permissionDecision
# "ask" blocks tool execution pending host approval; exit code 2 is not used. The
# server also defaults cancellation off behind A2A_ALLOW_TASK_CANCELLATION=1,
# then requires "cancel <taskId>" and refuses mismatches at the wire.
set -euo pipefail

cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "cancel_task requests termination of remote work. Confirm the target task ID and intended cancellation. The tool also requires confirmation=\"cancel <taskId>\"."
  }
}
JSON
