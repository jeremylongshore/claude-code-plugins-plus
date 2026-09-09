#!/usr/bin/env python3
"""Extract user messages from Claude Code session files.

Cross-platform compatible (Windows, macOS, Linux).
Usage: python extract_session_learnings.py <session-file> [--corrections-only]
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import extract_user_messages


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: extract_session_learnings.py <session-file> [--corrections-only]")
        return 1

    session_file = Path(sys.argv[1])
    corrections_only = len(sys.argv) > 2 and sys.argv[2] == "--corrections-only"

    if not session_file.exists():
        print(f"Error: Session file not found: {session_file}", file=sys.stderr)
        return 1

    messages = extract_user_messages(session_file, corrections_only=corrections_only)

    for msg in messages:
        print(msg)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
