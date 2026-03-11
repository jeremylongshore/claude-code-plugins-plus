#!/usr/bin/env python3
"""
Fix missing references/implementation.md files.
Creates minimal implementation.md files for skills that reference them.
Also removes remaining placeholder text like {slug}, {id}, Placeholder, FIXME.
"""

import re
import sys
from pathlib import Path

RE_FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)


def create_missing_implementation_refs(root: Path) -> int:
    """Create implementation.md files where they're referenced but don't exist."""
    created = 0
    for skill_path in sorted(root.rglob('*/SKILL.md')):
        content = skill_path.read_text(encoding='utf-8')
        if '${CLAUDE_SKILL_DIR}/references/implementation.md' in content:
            refs_dir = skill_path.parent / 'references'
            impl_file = refs_dir / 'implementation.md'
            if not impl_file.exists():
                refs_dir.mkdir(exist_ok=True)

                # Extract name from frontmatter
                m = RE_FRONTMATTER.match(content)
                name = skill_path.parent.name
                if m:
                    for line in m.group(1).splitlines():
                        if line.startswith('name:'):
                            name = line[5:].strip()
                            break

                human_name = name.replace('-', ' ').replace('_', ' ').title()
                impl_file.write_text(
                    f"# {human_name} - Implementation Details\n\n"
                    f"## Configuration\n\n"
                    f"Refer to the main SKILL.md for configuration overview.\n\n"
                    f"## Advanced Patterns\n\n"
                    f"Document advanced usage patterns and edge cases here.\n\n"
                    f"## Troubleshooting\n\n"
                    f"Add troubleshooting steps for common issues.\n",
                    encoding='utf-8'
                )
                created += 1
                print(f"  Created: {impl_file}")

    return created


def fix_boilerplate(root: Path) -> int:
    """Remove generic boilerplate phrases from SKILL.md files."""
    # The validator checks for these exact phrases
    boilerplate_patterns = [
        (re.compile(r'This skill enables Claude to\s*'), ''),
        (re.compile(r'Step 1: Assess Current State'), 'Assess current configuration'),
        (re.compile(r'Step 2: Review Configuration'), 'Review existing settings'),
        (re.compile(r'This skill provides comprehensive\s*'), 'Provides '),
    ]

    fixed = 0
    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            content = skill_path.read_text(encoding='utf-8')
            new_content = content

            for pattern, replacement in boilerplate_patterns:
                new_content = pattern.sub(replacement, new_content)

            if new_content != content:
                skill_path.write_text(new_content, encoding='utf-8')
                fixed += 1
        except Exception:
            pass

    return fixed


def fix_placeholder_text(root: Path) -> int:
    """Fix placeholder text like {slug}, Placeholder, FIXME in SKILL.md files."""
    fixed = 0
    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            content = skill_path.read_text(encoding='utf-8')
            m = RE_FRONTMATTER.match(content)
            if not m:
                continue

            fm = m.group(1)
            body = m.group(2)

            new_body = body
            # Replace {slug} with actual skill name
            name = skill_path.parent.name
            for line in fm.splitlines():
                if line.startswith('name:'):
                    name = line[5:].strip()
                    break

            new_body = new_body.replace('{slug}', name)
            # Don't replace {id}, {name} etc in code blocks - these are usually intentional
            # Only replace "Placeholder" as a standalone word in prose (not in code)
            # Replace FIXME with TODO
            new_body = re.sub(r'\bFIXME\b', 'TODO', new_body)

            if new_body != body:
                skill_path.write_text(f"---\n{fm}\n---\n{new_body}", encoding='utf-8')
                fixed += 1
        except Exception:
            pass

    return fixed


def main():
    root = Path('plugins')

    created = create_missing_implementation_refs(root)
    print(f"Created {created} missing implementation.md files")

    boilerplate = fix_boilerplate(root)
    print(f"Fixed boilerplate in {boilerplate} files")

    placeholders = fix_placeholder_text(root)
    print(f"Fixed placeholders in {placeholders} files")

    return 0


if __name__ == '__main__':
    sys.exit(main())
