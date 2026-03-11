#!/usr/bin/env python3
"""
Fix dead references in references/README.md and assets/README.md files.

Removes checkbox entries that reference files that don't exist.
This fixes [content-quality] warnings like:
  "references/README.md lists 'X.md' but file doesn't exist"
"""

import re
import sys
from pathlib import Path


def fix_readme_references(readme_path: Path) -> int:
    """Remove checkbox lines referencing nonexistent files. Returns count of removed lines."""
    if not readme_path.exists():
        return 0

    parent_dir = readme_path.parent
    content = readme_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    new_lines = []
    removed = 0

    checkbox_pattern = re.compile(r'-\s*\[[ xX]\]\s*([^\s:]+\.(?:md|yaml|json|py|sh|template))')

    for line in lines:
        m = checkbox_pattern.search(line)
        if m:
            filename = m.group(1)
            file_path = parent_dir / filename
            if not file_path.exists():
                removed += 1
                continue
        new_lines.append(line)

    if removed > 0:
        # Check if the remaining content is just a header with no entries
        remaining_content = '\n'.join(new_lines).strip()
        non_empty_lines = [l for l in new_lines if l.strip() and not l.strip().startswith('#')]

        if not non_empty_lines:
            # README is now empty (just headers) — delete it
            readme_path.unlink()
            # If parent directory is now empty, remove it too
            try:
                parent_dir.rmdir()
            except OSError:
                pass  # directory not empty
        else:
            readme_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')

    return removed


def main():
    root = Path('plugins')
    total_fixed = 0
    files_fixed = 0

    # Find all references/README.md and assets/README.md files
    for readme_type in ['references', 'assets']:
        for readme_path in sorted(root.rglob(f'{readme_type}/README.md')):
            removed = fix_readme_references(readme_path)
            if removed > 0:
                total_fixed += removed
                files_fixed += 1
                print(f"  Fixed {removed} dead refs in {readme_path}")

    print(f"\nTotal: {total_fixed} dead references removed from {files_fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
