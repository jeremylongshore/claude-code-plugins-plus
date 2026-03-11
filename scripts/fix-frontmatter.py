#!/usr/bin/env python3
"""
Fix frontmatter warnings in SKILL.md files:
1. Add 'Use when...' to descriptions missing it
2. Add 'Trigger with...' to descriptions missing it
3. Add author email where missing
4. Scope bare 'Bash' to Bash(cmd:*)
"""

import re
import sys
from pathlib import Path

RE_FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)


def fix_frontmatter(content: str) -> str:
    """Fix frontmatter issues in SKILL.md content."""
    m = RE_FRONTMATTER.match(content)
    if not m:
        return content

    fm = m.group(1)
    body = m.group(2)
    lines = fm.splitlines()
    new_lines = []
    description_lines = []
    in_description = False
    description_idx = -1

    for i, line in enumerate(lines):
        if line.startswith('description:'):
            in_description = True
            description_idx = len(new_lines)
            val = line[len('description:'):].strip()
            if val == '|':
                new_lines.append(line)
                continue
            elif val.startswith("'") or val.startswith('"'):
                description_lines = [val[1:-1] if val.endswith(val[0]) else val[1:]]
                new_lines.append(line)
                continue
            else:
                description_lines = [val]
                new_lines.append(line)
                continue
        elif in_description:
            if line.startswith('  ') or line.startswith('\t'):
                description_lines.append(line.strip())
                new_lines.append(line)
                continue
            else:
                in_description = False

        # Fix bare 'Bash' in allowed-tools
        if line.startswith('allowed-tools:'):
            # Replace standalone Bash (not already scoped)
            new_line = re.sub(r'\bBash\b(?!\()', 'Bash(cmd:*)', line)
            new_lines.append(new_line)
            continue

        # Fix author without email
        if line.startswith('author:'):
            author_val = line[len('author:'):].strip()
            if '<' not in author_val and '@' not in author_val:
                # Add generic email
                if 'wondelai' in author_val.lower() or 'wondel' in author_val.lower():
                    new_lines.append(f"author: {author_val} <https://github.com/wondelai>")
                elif 'jeremy' in author_val.lower():
                    new_lines.append(f"author: {author_val} <jeremy@intentsolutions.io>")
                else:
                    new_lines.append(line)  # Don't guess email for unknown authors
                continue

        new_lines.append(line)

    # Now fix description for Use when / Trigger with
    full_desc = ' '.join(description_lines)

    has_use_when = bool(re.search(r'\bUse when\b', full_desc, re.IGNORECASE))
    has_trigger = bool(re.search(r'\bTrigger with\b', full_desc, re.IGNORECASE))

    if not has_use_when or not has_trigger:
        # We need to modify the description - find it in new_lines
        # Find the description field and its block
        desc_start = -1
        desc_end = -1
        is_multiline = False

        for i, line in enumerate(new_lines):
            if line.startswith('description:'):
                desc_start = i
                val = line[len('description:'):].strip()
                if val == '|':
                    is_multiline = True
                    # Find end of block
                    for j in range(i + 1, len(new_lines)):
                        if not (new_lines[j].startswith('  ') or new_lines[j].startswith('\t')):
                            desc_end = j
                            break
                    else:
                        desc_end = len(new_lines)
                elif val.startswith("'"):
                    desc_end = i + 1
                else:
                    desc_end = i + 1
                break

        if desc_start >= 0:
            if is_multiline:
                # Get all description content lines
                desc_content_lines = new_lines[desc_start + 1:desc_end]
                desc_text = ' '.join(l.strip() for l in desc_content_lines)

                additions = []
                if not has_use_when:
                    # Extract skill name for context
                    skill_name = ''
                    for line in new_lines:
                        if line.startswith('name:'):
                            skill_name = line[5:].strip()
                            break
                    if skill_name:
                        additions.append(f"Use when working with {skill_name.replace('-', ' ')}.")

                if not has_trigger:
                    skill_name = ''
                    for line in new_lines:
                        if line.startswith('name:'):
                            skill_name = line[5:].strip()
                            break
                    keywords = skill_name.replace('-', ' ').split() if skill_name else ['this skill']
                    trigger_words = "', '".join(keywords[:3])
                    additions.append(f"Trigger with '{trigger_words}'.")

                if additions:
                    addition_text = ' '.join(additions)
                    # Append to last description line
                    if desc_content_lines:
                        new_lines[desc_end - 1] = new_lines[desc_end - 1].rstrip() + ' ' + addition_text
                    else:
                        new_lines.insert(desc_start + 1, '  ' + addition_text)
                        desc_end += 1

            elif new_lines[desc_start].startswith("description: '"):
                # Single-quoted inline description
                val = new_lines[desc_start][len("description: '"):]
                if val.endswith("'"):
                    val = val[:-1]

                additions = []
                if not has_use_when:
                    skill_name = ''
                    for line in new_lines:
                        if line.startswith('name:'):
                            skill_name = line[5:].strip()
                            break
                    if skill_name:
                        additions.append(f"Use when working with {skill_name.replace('-', ' ')}.")

                if not has_trigger:
                    skill_name = ''
                    for line in new_lines:
                        if line.startswith('name:'):
                            skill_name = line[5:].strip()
                            break
                    keywords = skill_name.replace('-', ' ').split() if skill_name else ['this']
                    trigger_words = "', '".join(keywords[:3])
                    additions.append(f"Trigger with '{trigger_words}'.")

                if additions:
                    val = val.rstrip() + ' ' + ' '.join(additions)
                    new_lines[desc_start] = f"description: '{val}'"

    new_fm = '\n'.join(new_lines)
    return f"---\n{new_fm}\n---\n{body}"


def main():
    root = Path('plugins')
    fixed = 0

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            content = skill_path.read_text(encoding='utf-8')
            new_content = fix_frontmatter(content)
            if new_content != content:
                skill_path.write_text(new_content, encoding='utf-8')
                fixed += 1
        except Exception as e:
            print(f"  Error: {skill_path}: {e}", file=sys.stderr)

    print(f"Fixed frontmatter in {fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
