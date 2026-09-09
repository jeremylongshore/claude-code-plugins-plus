#!/usr/bin/env python3
"""Extract user corrections from tool rejections in session files.

Cross-platform compatible (Windows, macOS, Linux).
Usage: python extract_tool_rejections.py <session-file>
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import extract_tool_rejections


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: extract_tool_rejections.py <session-file>")
        return 1

    session_file = Path(sys.argv[1])

    if not session_file.exists():
        print(f"Error: Session file not found: {session_file}", file=sys.stderr)
        return 1

    rejections = extract_tool_rejections(session_file)

    for rejection in rejections:
        print(rejection)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
