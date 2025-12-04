#!/usr/bin/env python3
"""
Validates all SKILL.md files comply with 2025 schema:
- name (required)
- description (required)
- allowed-tools (recommended warning if missing)
- version (recommended warning if missing)
"""

import sys
import re
from pathlib import Path

def extract_frontmatter(content):
    """Extract YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    frontmatter_str = match.group(1)
    frontmatter = {}
    current_key = None
    current_value = []

    for line in frontmatter_str.split('\n'):
        if ':' in line and not line.startswith(' '):
            if current_key:
                value = '\n'.join(current_value).strip()
                if value.startswith('|'):
                    value = value[1:].strip()
                frontmatter[current_key] = value

            key, val = line.split(':', 1)
            current_key = key.strip()
            current_value = [val.strip()] if val.strip() else []
        elif current_key and line.startswith(' '):
            current_value.append(line.strip())
        elif line.strip():
            if current_value:
                current_value[0] += ' ' + line.strip()

    if current_key:
        value = '\n'.join(current_value).strip()
        if value.startswith('|'):
            value = value[1:].strip()
        frontmatter[current_key] = value

    return frontmatter

def validate_skill(file_path):
    """Validate a single SKILL.md file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'error': f'Cannot read file: {e}'}

    frontmatter = extract_frontmatter(content)

    if not frontmatter:
        return {'error': 'No frontmatter found'}

    errors = []
    warnings = []

    # Required fields
    if 'name' not in frontmatter:
        errors.append('Missing required field: name')
    elif len(frontmatter['name']) > 64:
        errors.append('name exceeds 64 characters')

    if 'description' not in frontmatter:
        errors.append('Missing required field: description')
    elif len(frontmatter['description']) > 1024:
        errors.append('description exceeds 1024 characters')

    # Recommended fields (2025 schema)
    if 'allowed-tools' not in frontmatter:
        warnings.append('Missing recommended field: allowed-tools (2025 schema)')

    if 'version' not in frontmatter:
        warnings.append('Missing recommended field: version (2025 schema)')

    return {'errors': errors, 'warnings': warnings}

def main():
    plugins_dir = Path(__file__).parent.parent / 'plugins'
    skill_files = list(plugins_dir.rglob('skills/*/SKILL.md'))

    total_errors = 0
    total_warnings = 0
    total_files = len(skill_files)

    files_with_errors = []
    files_with_warnings = []

    for skill_file in skill_files:
        result = validate_skill(skill_file)

        if 'error' in result:
            print(f"❌ {skill_file.relative_to(plugins_dir)}: {result['error']}")
            total_errors += 1
            files_with_errors.append(str(skill_file.relative_to(plugins_dir)))
            continue

        if result['errors']:
            print(f"❌ {skill_file.relative_to(plugins_dir)}:")
            for error in result['errors']:
                print(f"   - {error}")
            total_errors += len(result['errors'])
            files_with_errors.append(str(skill_file.relative_to(plugins_dir)))

        if result['warnings']:
            for warning in result['warnings']:
                total_warnings += 1
            files_with_warnings.append(str(skill_file.relative_to(plugins_dir)))

    print(f"\n{'=' * 70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total files validated: {total_files}")
    print(f"✅ Files compliant: {total_files - len(files_with_errors) - len(files_with_warnings)}")
    print(f"⚠️  Files with warnings: {len(files_with_warnings)}")
    print(f"❌ Files with errors: {len(files_with_errors)}")
    print(f"{'=' * 70}")

    if total_errors > 0:
        print(f"\n❌ Validation failed with {total_errors} errors")
        return 1
    elif total_warnings > 0:
        print(f"\n⚠️  Validation passed with {total_warnings} warnings")
        print("   Consider updating skills to 2025 schema (add allowed-tools and version)")
        return 0
    else:
        print(f"\n✅ All skills comply with 2025 schema!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
