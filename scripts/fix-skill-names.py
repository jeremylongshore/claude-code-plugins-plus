#!/usr/bin/env python3
"""
Fix Agent Skills names to comply with Anthropic's official spec.

Converts Title Case names to hyphen-case format as required by:
https://github.com/anthropics/skills/blob/main/agent_skills_spec.md

Example:
  "Creating GitHub Issues from Web Research" → "creating-github-issues-from-web-research"
"""

import os
import re
from pathlib import Path


def title_to_hyphen_case(title):
    """Convert Title Case to hyphen-case.

    Args:
        title: Title Case string like "Creating GitHub Issues"

    Returns:
        Hyphen-case string like "creating-github-issues"
    """
    # Convert to lowercase
    name = title.lower()
    # Replace spaces with hyphens
    name = re.sub(r'\s+', '-', name)
    # Remove non-alphanumeric except hyphens
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name


def main():
    """Fix all SKILL.md files in plugins directory."""

    # Find all SKILL.md files
    skill_files = list(Path('plugins').rglob('SKILL.md'))

    if not skill_files:
        print("❌ No SKILL.md files found in plugins directory")
        return 1

    print(f"Found {len(skill_files)} SKILL.md files")
    print("=" * 80)

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for skill_file in skill_files:
        try:
            content = skill_file.read_text()

            # Extract current name from frontmatter
            match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)

            if not match:
                print(f"⚠️  No name field found: {skill_file}")
                error_count += 1
                continue

            old_name = match.group(1).strip()
            new_name = title_to_hyphen_case(old_name)

            # Skip if already in correct format
            if old_name == new_name:
                skipped_count += 1
                continue

            # Replace name in frontmatter (only first occurrence in YAML section)
            new_content = re.sub(
                r'^name:\s*.+$',
                f'name: {new_name}',
                content,
                count=1,
                flags=re.MULTILINE
            )

            # Write updated content
            skill_file.write_text(new_content)

            print(f"✅ {skill_file}")
            print(f"   OLD: {old_name}")
            print(f"   NEW: {new_name}")
            print()

            fixed_count += 1

        except Exception as e:
            print(f"❌ Error processing {skill_file}: {e}")
            error_count += 1

    print("=" * 80)
    print(f"✅ Fixed: {fixed_count}")
    print(f"⏭️  Skipped (already correct): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(skill_files)}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
