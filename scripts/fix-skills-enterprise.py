#!/usr/bin/env python3
"""
Fix skills to meet Intent Solutions Enterprise Standards.

Adds missing fields:
- author: Jeremy Longshore <jeremy@intentsolutions.io>
- license: MIT
- version: 1.0.0 (if missing)

Also fixes common errors:
- Bash(*) -> Bash (remove invalid wildcard)
- Hardcoded paths -> {baseDir}
- YAML quote issues
"""

import re
import sys
from pathlib import Path

# Enterprise defaults
DEFAULT_AUTHOR = "Jeremy Longshore <jeremy@intentsolutions.io>"
DEFAULT_LICENSE = "MIT"
DEFAULT_VERSION = "1.0.0"


def fix_skill_file(file_path: Path, dry_run: bool = True) -> dict:
    """Fix a single SKILL.md file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'error': f'Cannot read: {e}'}

    original = content
    fixes = []

    # Check if has frontmatter
    if not content.startswith('---'):
        return {'error': 'No frontmatter found'}

    # Split frontmatter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {'error': 'Invalid frontmatter structure'}

    frontmatter = parts[1]
    body = parts[2]

    # Fix 1: Add missing author
    if 'author:' not in frontmatter:
        frontmatter = frontmatter.rstrip() + f'\nauthor: {DEFAULT_AUTHOR}\n'
        fixes.append('Added author field')

    # Fix 2: Add missing license
    if 'license:' not in frontmatter:
        frontmatter = frontmatter.rstrip() + f'\nlicense: {DEFAULT_LICENSE}\n'
        fixes.append('Added license field')

    # Fix 3: Add missing version
    if 'version:' not in frontmatter:
        frontmatter = frontmatter.rstrip() + f'\nversion: {DEFAULT_VERSION}\n'
        fixes.append('Added version field')

    # Fix 4: Invalid Bash(*) wildcard - remove the wildcard entirely
    if 'Bash(*)' in frontmatter:
        frontmatter = frontmatter.replace('Bash(*)', 'Bash')
        fixes.append('Fixed Bash(*) -> Bash')

    # Fix 5: Malformed Bash(cmd:* missing close paren
    frontmatter = re.sub(r'Bash\(([^)]+):\*(?!\))', r'Bash(\1:*)', frontmatter)
    if 'Fixed Bash(' not in str(fixes) and re.search(r'Bash\([^)]+:\*\)', frontmatter):
        fixes.append('Fixed malformed Bash wildcard')

    # Fix 6: Hardcoded paths in body
    if '/home/' in body or '/Users/' in body:
        body = re.sub(r'/home/\w+/[^\s"\']+', '{baseDir}', body)
        body = re.sub(r'/Users/\w+/[^\s"\']+', '{baseDir}', body)
        fixes.append('Replaced hardcoded paths with {baseDir}')

    # Fix 7: /tmp/ paths
    if '/tmp/' in body:
        body = body.replace('/tmp/', '{baseDir}/tmp/')
        fixes.append('Replaced /tmp/ with {baseDir}/tmp/')

    # Reconstruct
    new_content = f'---{frontmatter}---{body}'

    if new_content != original:
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        return {'fixed': True, 'fixes': fixes}

    return {'fixed': False, 'fixes': []}


def main():
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print("   Run without --dry-run to apply fixes\n")
    else:
        print("🔧 APPLYING FIXES to skill files\n")

    plugins_dir = Path(__file__).parent.parent / 'plugins'
    skill_files = list(plugins_dir.rglob('skills/*/SKILL.md'))

    # Also check standalone skills
    standalone_dir = Path(__file__).parent.parent / 'skills'
    if standalone_dir.exists():
        skill_files.extend(standalone_dir.rglob('*/SKILL.md'))

    total = len(skill_files)
    fixed = 0
    errors = 0

    for skill_file in skill_files:
        result = fix_skill_file(skill_file, dry_run=dry_run)
        rel_path = skill_file.relative_to(plugins_dir) if plugins_dir in skill_file.parents else skill_file

        if 'error' in result:
            print(f"❌ {rel_path}: {result['error']}")
            errors += 1
        elif result['fixed']:
            fixed += 1
            if verbose or dry_run:
                print(f"✅ {rel_path}:")
                for fix in result['fixes']:
                    print(f"   - {fix}")
        elif verbose:
            print(f"⏭️  {rel_path}: Already compliant")

    print(f"\n{'=' * 60}")
    print(f"📊 SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total skills: {total}")
    print(f"{'Would fix' if dry_run else 'Fixed'}: {fixed}")
    print(f"Errors: {errors}")
    print(f"Already compliant: {total - fixed - errors}")

    if dry_run and fixed > 0:
        print(f"\n💡 Run without --dry-run to apply {fixed} fixes")

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
