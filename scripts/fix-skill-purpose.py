#!/usr/bin/env python3
"""
Fix missing purpose statement in SKILL.md files.

Adds a purpose statement after the title or ## Overview section.
"""

import re
import sys
from pathlib import Path


def add_purpose_statement(content: str, skill_name: str) -> tuple:
    """Add purpose statement if missing."""
    changes = []

    # Check if there's already a purpose statement (paragraph after title or ## Overview)
    # Look for patterns that indicate existing purpose
    has_purpose = False

    # Check for ## Purpose section
    if '## Purpose' in content or '## purpose' in content:
        has_purpose = True

    # Check for paragraph after # title (not a list, not a heading)
    lines = content.split('\n')
    title_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('## '):
            title_idx = i
            break

    if title_idx >= 0:
        # Check next non-empty lines
        for i in range(title_idx + 1, min(title_idx + 10, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
            if line.startswith('#'):
                # Hit a heading, no purpose statement yet
                break
            if line.startswith('-') or line.startswith('*') or line.startswith('1.'):
                # It's a list, not a purpose
                break
            # Found a paragraph - assume it's purpose
            if len(line) > 30:
                has_purpose = True
                break

    if has_purpose:
        return content, changes

    # Generate purpose statement
    name_readable = skill_name.replace('-', ' ').replace('_', ' ').title()

    purpose = f"This skill provides automated assistance for {name_readable.lower()} tasks."

    # Insert after ## Overview if exists, else after title
    if '## Overview' in content:
        # Insert after ## Overview heading
        pattern = r'(## Overview\s*\n)'
        replacement = r'\1\n' + purpose + '\n'
        new_content = re.sub(pattern, replacement, content, count=1)
        if new_content != content:
            changes.append("Added purpose statement after ## Overview")
            return new_content, changes
    elif title_idx >= 0:
        # Insert after title
        lines.insert(title_idx + 1, '\n' + purpose + '\n')
        new_content = '\n'.join(lines)
        changes.append("Added purpose statement after title")
        return new_content, changes

    return content, changes


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single SKILL.md file."""
    result = {'file': str(filepath), 'changes': [], 'errors': []}

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result['errors'].append(f"Read error: {e}")
        return result

    skill_name = filepath.parent.name

    new_content, changes = add_purpose_statement(content, skill_name)
    result['changes'] = changes

    if changes and not dry_run:
        filepath.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix missing purpose statements')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--path', default='plugins')
    args = parser.parse_args()

    root = Path(args.path)
    skill_files = list(root.rglob("skills/*/SKILL.md"))

    print(f"Found {len(skill_files)} SKILL.md files")

    files_fixed = 0
    for filepath in skill_files:
        result = process_file(filepath, args.dry_run)
        if result['changes']:
            files_fixed += 1
            print(f"{filepath.relative_to(root)}: {result['changes']}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Fixed: {files_fixed} files")


if __name__ == '__main__':
    main()
