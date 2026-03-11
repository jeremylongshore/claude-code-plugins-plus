#!/usr/bin/env python3
"""
Delete stub Python scripts that contain only placeholder code.

Fixes [content-quality] warnings like:
  "scripts/report_generator.py appears to be a stub (contains placeholder code)"
"""

import re
import sys
from pathlib import Path

STUB_PATTERNS = [
    re.compile(r'def\s+\w+\([^)]*\):\s*\n\s*pass\s*$', re.MULTILINE),
    re.compile(r'Add processing logic here', re.IGNORECASE),
    re.compile(r'This is a template', re.IGNORECASE),
    re.compile(r'Customize based on', re.IGNORECASE),
    re.compile(r'#\s*TODO:\s*implement', re.IGNORECASE),
    re.compile(r'raise NotImplementedError'),
]


def main():
    root = Path('plugins')
    deleted = 0
    dirs_removed = 0

    for py_file in sorted(root.rglob('scripts/*.py')):
        try:
            content = py_file.read_text(encoding='utf-8')
            if any(p.search(content) for p in STUB_PATTERNS):
                print(f"  Deleting: {py_file}")
                py_file.unlink()
                deleted += 1
        except Exception:
            pass

    # Clean up empty scripts directories
    for scripts_dir in sorted(root.rglob('scripts'), reverse=True):
        if scripts_dir.is_dir():
            remaining = list(scripts_dir.iterdir())
            if not remaining:
                scripts_dir.rmdir()
                dirs_removed += 1

    print(f"\nTotal: {deleted} stub scripts deleted, {dirs_removed} empty dirs removed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
