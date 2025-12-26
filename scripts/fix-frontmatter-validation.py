#!/usr/bin/env python3
"""
Fix frontmatter validation errors across all plugins.

Fixes:
1. shortcut: Must be 1-4 lowercase letters only
2. description: Must be 80 characters or less
"""

import os
import re
import sys
from pathlib import Path

# Shortcut abbreviation mappings for common patterns
SHORTCUT_MAPPINGS = {
    'batch': 'btch',
    'implement': 'impl',
    'generate': 'gen',
    'create': 'crt',
    'validate': 'val',
    'check': 'chk',
    'manage': 'mgr',
    'build': 'bld',
    'migrate': 'mig',
    'monitor': 'mon',
    'scan': 'scn',
    'detect': 'det',
    'analyze': 'anlz',
    'setup': 'set',
    'test': 'tst',
    'report': 'rpt',
}


def extract_shortcut_from_filename(filename: str) -> str:
    """Generate a 1-4 letter shortcut from a filename."""
    # Remove extension and split by common separators
    name = Path(filename).stem
    parts = re.split(r'[-_]', name)

    # Try common abbreviation mappings first
    for part in parts:
        if part.lower() in SHORTCUT_MAPPINGS:
            return SHORTCUT_MAPPINGS[part.lower()]

    # Take first letter of each word (up to 4)
    if len(parts) >= 2:
        abbrev = ''.join(p[0] for p in parts[:4] if p).lower()
        if len(abbrev) >= 1 and abbrev.isalpha():
            return abbrev[:4]

    # Just take first 4 letters of the name
    letters = ''.join(c for c in name if c.isalpha()).lower()
    return letters[:4] if letters else 'cmd'


def fix_shortcut(value: str, filename: str) -> str:
    """Fix shortcut to be 1-4 lowercase letters only."""
    if not value:
        return extract_shortcut_from_filename(filename)

    # Remove non-letters and lowercase
    letters = ''.join(c for c in value if c.isalpha()).lower()

    if len(letters) > 4:
        # Check if we have a mapping
        if value.lower() in SHORTCUT_MAPPINGS:
            return SHORTCUT_MAPPINGS[value.lower()]
        # Otherwise truncate
        return letters[:4]

    if len(letters) == 0:
        return extract_shortcut_from_filename(filename)

    return letters


def fix_description(value: str) -> str:
    """Fix description to be 80 characters or less."""
    if not value or len(value) <= 80:
        return value

    # Truncate at word boundary if possible
    truncated = value[:77]
    last_space = truncated.rfind(' ')
    if last_space > 50:
        truncated = truncated[:last_space]

    return truncated.rstrip() + '...'


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return None, content

    # Find the closing ---
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return None, content

    end_pos = end_match.end() + 3
    frontmatter = content[4:end_match.start() + 3]
    body = content[end_pos:]

    return frontmatter, body


def rebuild_content(frontmatter: str, body: str) -> str:
    """Rebuild markdown content with updated frontmatter."""
    # Ensure frontmatter doesn't end with newline (we add one)
    frontmatter = frontmatter.rstrip('\n')
    # Ensure body starts properly
    if not body.startswith('\n'):
        body = '\n' + body
    return f'---\n{frontmatter}\n---{body}'


def fix_frontmatter_field(frontmatter: str, field: str, fixer, filename: str = None) -> str:
    """Fix a specific field in the frontmatter."""
    # Match the field line
    pattern = rf'^({field}:\s*)(.+)$'
    match = re.search(pattern, frontmatter, re.MULTILINE)

    if not match:
        return frontmatter

    old_value = match.group(2).strip()
    if filename:
        new_value = fixer(old_value, filename)
    else:
        new_value = fixer(old_value)

    if old_value != new_value:
        return frontmatter[:match.start()] + f'{field}: {new_value}' + frontmatter[match.end():]

    return frontmatter


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """Process a single file and fix validation errors."""
    result = {'file': str(filepath), 'changes': [], 'errors': []}

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result['errors'].append(f'Read error: {e}')
        return result

    frontmatter, body = parse_frontmatter(content)
    if frontmatter is None:
        return result

    original_frontmatter = frontmatter

    # Fix shortcut field
    if 'shortcut:' in frontmatter:
        new_frontmatter = fix_frontmatter_field(
            frontmatter, 'shortcut', fix_shortcut, filepath.name
        )
        if new_frontmatter != frontmatter:
            # Extract old and new values for logging
            old_match = re.search(r'^shortcut:\s*(.+)$', frontmatter, re.MULTILINE)
            new_match = re.search(r'^shortcut:\s*(.+)$', new_frontmatter, re.MULTILINE)
            if old_match and new_match:
                result['changes'].append(
                    f"shortcut: '{old_match.group(1).strip()}' -> '{new_match.group(1).strip()}'"
                )
            frontmatter = new_frontmatter

    # Fix description field
    if 'description:' in frontmatter:
        new_frontmatter = fix_frontmatter_field(
            frontmatter, 'description', fix_description
        )
        if new_frontmatter != frontmatter:
            old_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
            new_match = re.search(r'^description:\s*(.+)$', new_frontmatter, re.MULTILINE)
            if old_match and new_match:
                old_len = len(old_match.group(1).strip())
                new_len = len(new_match.group(1).strip())
                result['changes'].append(f'description: {old_len} chars -> {new_len} chars')
            frontmatter = new_frontmatter

    if frontmatter != original_frontmatter:
        new_content = rebuild_content(frontmatter, body)
        if not dry_run:
            filepath.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix frontmatter validation errors')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--path', default='plugins', help='Path to scan')
    args = parser.parse_args()

    plugins_dir = Path(args.path)
    if not plugins_dir.exists():
        print(f'Error: {plugins_dir} does not exist')
        sys.exit(1)

    # Find all markdown files in commands/, agents/ directories
    patterns = [
        '**/commands/*.md',
        '**/agents/*.md',
    ]

    files_fixed = 0
    total_changes = 0

    for pattern in patterns:
        for filepath in plugins_dir.glob(pattern):
            result = process_file(filepath, args.dry_run)

            if result['changes']:
                files_fixed += 1
                total_changes += len(result['changes'])
                print(f"\n{result['file']}:")
                for change in result['changes']:
                    print(f"  - {change}")

            if result['errors']:
                for error in result['errors']:
                    print(f"  ERROR: {error}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {files_fixed} files, {total_changes} changes")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")


if __name__ == '__main__':
    main()
