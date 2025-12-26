#!/usr/bin/env python3
"""
Fix geepers-agents files with <example> tags inside YAML frontmatter.

Handles two cases:
1. <example> blocks on separate lines in frontmatter
2. <example> blocks embedded inline in description field
"""

import re
from pathlib import Path


def fix_frontmatter(filepath: Path) -> bool:
    """Fix a single file by moving examples from frontmatter to body."""
    content = filepath.read_text(encoding='utf-8')

    # Check if file has frontmatter
    if not content.startswith('---'):
        return False

    # Find all lines
    lines = content.split('\n')

    # Check if <example> is in the content
    has_inline_examples = False
    has_multiline_examples = False

    for i, line in enumerate(lines):
        if '<example>' in line:
            # Check if it's on same line as description
            if 'description:' in line:
                has_inline_examples = True
            else:
                has_multiline_examples = True
            break

    if not has_inline_examples and not has_multiline_examples:
        return False

    if has_inline_examples:
        return fix_inline_examples(filepath, lines)
    else:
        return fix_multiline_examples(filepath, lines)


def fix_inline_examples(filepath: Path, lines: list) -> bool:
    """Fix examples embedded inline in description field."""
    new_lines = []
    examples_to_add = []

    for line in lines:
        if 'description:' in line and '<example>' in line:
            # Extract the description part before examples
            match = re.match(r'^(description:\s*)(.+?)(<example>.*)', line)
            if match:
                prefix = match.group(1)
                desc_text = match.group(2).strip()
                examples_part = match.group(3)

                # Remove \\n at the end of description
                desc_text = re.sub(r'\\n+$', '', desc_text)

                # Quote the description properly
                new_lines.append(f'{prefix}"{desc_text}"')

                # Extract all examples
                example_pattern = r'<example>(.*?)</example>'
                raw_examples = re.findall(example_pattern, examples_part, re.DOTALL)

                for raw_ex in raw_examples:
                    # Convert \n to real newlines
                    example_content = raw_ex.replace('\\n', '\n')
                    examples_to_add.append(example_content.strip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if not examples_to_add:
        return False

    # Find where body starts (after ---)
    body_start = -1
    in_frontmatter = False
    for i, line in enumerate(new_lines):
        if i == 0 and line.strip() == '---':
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == '---':
            body_start = i + 1
            break

    if body_start == -1:
        return False

    # Insert examples section after frontmatter
    examples_section = ['', '## Examples', '']
    for j, ex in enumerate(examples_to_add, 1):
        examples_section.append(f'### Example {j}')
        examples_section.append('')
        examples_section.append('<example>')
        examples_section.append(ex)
        examples_section.append('</example>')
        examples_section.append('')

    # Reconstruct
    final_lines = new_lines[:body_start] + examples_section + new_lines[body_start:]

    filepath.write_text('\n'.join(final_lines), encoding='utf-8')
    return True


def fix_multiline_examples(filepath: Path, lines: list) -> bool:
    """Fix <example> blocks on separate lines in frontmatter."""
    # Find start and end of frontmatter
    frontmatter_end = -1
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == '---':
            frontmatter_end = i
            break

    if frontmatter_end == -1:
        return False

    # Extract frontmatter section (lines 1 to frontmatter_end-1)
    fm_lines = lines[1:frontmatter_end]
    body_lines = lines[frontmatter_end+1:]

    # Separate clean YAML fields from <example> blocks
    yaml_lines = []
    example_blocks = []
    in_example = False
    current_example = []

    for line in fm_lines:
        if '<example>' in line:
            in_example = True
            current_example = [line]
        elif '</example>' in line:
            current_example.append(line)
            example_blocks.append('\n'.join(current_example))
            current_example = []
            in_example = False
        elif in_example:
            current_example.append(line)
        else:
            yaml_lines.append(line)

    if not example_blocks:
        return False

    # Clean up empty lines at end of yaml_lines
    while yaml_lines and not yaml_lines[-1].strip():
        yaml_lines.pop()

    # Reconstruct the file
    new_content_parts = [
        '---',
        '\n'.join(yaml_lines),
        '---',
        '',
        '## Examples',
        '',
    ]

    for i, example in enumerate(example_blocks, 1):
        new_content_parts.append(f'### Example {i}')
        new_content_parts.append('')
        new_content_parts.append(example)
        new_content_parts.append('')

    new_content_parts.extend(body_lines)

    filepath.write_text('\n'.join(new_content_parts), encoding='utf-8')
    return True


def main():
    # Find all geepers agent files
    geepers_dir = Path('plugins/community/geepers-agents/agents')

    if not geepers_dir.exists():
        print(f"Directory not found: {geepers_dir}")
        return

    fixed_count = 0
    for filepath in geepers_dir.glob('*.md'):
        if fix_frontmatter(filepath):
            print(f"Fixed: {filepath.name}")
            fixed_count += 1

    print(f"\nTotal fixed: {fixed_count} files")


if __name__ == '__main__':
    main()
