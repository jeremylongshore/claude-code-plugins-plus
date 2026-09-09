#!/usr/bin/env python3
"""Show pending learnings reminder at session start. SessionStart hook.

Cross-platform compatible (Windows, macOS, Linux).
This script is called by Claude Code's SessionStart hook to remind
user of pending learnings that need review.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import load_queue, get_cleanup_period_days


def main() -> int:
    """Main entry point."""
    # Check if reminder is disabled via environment variable
    if os.environ.get("CLAUDE_REFLECT_REMINDER", "true").lower() == "false":
        return 0

    # Warn if cleanupPeriodDays is not configured (self-resolving: stops once user sets it)
    cleanup_days = get_cleanup_period_days()
    if cleanup_days is None or cleanup_days <= 30:
        print(f"\n⚠️  Claude Code deletes sessions after {cleanup_days or 30} days.")
        print(f"   claude-reflect needs session history for /reflect and /reflect-skills.")
        print(f"   Extend retention: add {{\"cleanupPeriodDays\": 99999}} to ~/.claude/settings.json")

    items = load_queue()

    if not items:
        return 0

    count = len(items)
    print(f"\n{'='*50}")
    print(f"📚 {count} pending learning(s) to review")
    print(f"{'='*50}")

    # Show up to 5 items
    for i, item in enumerate(items[:5], 1):
        msg = item.get("message", "")
        # Truncate long messages
        if len(msg) > 60:
            msg = msg[:57] + "..."
        confidence = item.get("confidence", 0.5)
        print(f"  {i}. [{confidence:.0%}] {msg}")

    if count > 5:
        print(f"  ... and {count - 5} more")

    print(f"\n💡 Run /reflect to review and apply")
    print(f"{'='*50}\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Never block on errors - just log and exit 0
        print(f"Warning: session_start_reminder.py error: {e}", file=sys.stderr)
        sys.exit(0)
