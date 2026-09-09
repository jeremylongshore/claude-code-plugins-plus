#!/usr/bin/env python3
"""Remind about /reflect after git commits. PostToolUse hook for Bash.

Cross-platform compatible (Windows, macOS, Linux).
This script is called by Claude Code's PostToolUse hook after Bash commands.
It detects git commits and reminds the user to run /reflect.
"""
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import load_queue


def main() -> int:
    """Main entry point."""
    # Read hook input from stdin
    input_data = sys.stdin.read()
    if not input_data:
        return 0

    try:
        data = json.loads(input_data)
        command = data.get("tool_input", {}).get("command", "")
    except json.JSONDecodeError:
        return 0

    if not command:
        return 0

    # Check if it was a git commit command (not amend)
    if "git commit" not in command or "--amend" in command:
        return 0

    # Build reminder message
    msg = "Git commit detected!"

    items = load_queue()
    if items:
        msg += f" You have {len(items)} queued learning(s)."

    msg += " Feature complete? Run /reflect to process learnings."

    # Output proper JSON for hook response
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg
        }
    }
    print(json.dumps(response))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block on errors - just log and exit 0
        print(f"Warning: post_commit_reminder.py error: {e}", file=sys.stderr)
        sys.exit(0)
