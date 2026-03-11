#!/usr/bin/env python3
"""
Fix purpose statement warnings in SKILL.md files:
1. Shorten purpose statements that are 3+ sentences to 1-2
2. Trim purpose statements > 400 chars
3. Add purpose statements where missing
4. Add numbered steps to Instructions sections that lack them
"""

import re
import sys
from pathlib import Path

RE_FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
CODE_FENCE = re.compile(r'^```')


def fix_purpose_and_instructions(content: str) -> str:
    """Fix purpose statement and Instructions formatting."""
    m = RE_FRONTMATTER.match(content)
    if not m:
        return content

    fm = m.group(1)
    body = m.group(2)
    lines = body.splitlines()
    new_lines = []

    # Extract name from frontmatter
    name = ''
    for fml in fm.splitlines():
        if fml.startswith('name:'):
            name = fml[5:].strip()
            break

    # Find the first paragraph after the first heading (purpose statement)
    found_heading = False
    in_code = False
    purpose_start = -1
    purpose_end = -1
    in_purpose = False

    for i, line in enumerate(lines):
        if CODE_FENCE.match(line):
            in_code = not in_code
        if in_code:
            continue

        if not found_heading and re.match(r'^#\s+', line):
            found_heading = True
            continue

        if found_heading and not in_purpose and purpose_start == -1:
            if line.strip() and not line.startswith('#'):
                purpose_start = i
                in_purpose = True
            elif line.startswith('#'):
                break  # No purpose statement before next heading
            continue

        if in_purpose:
            if not line.strip() or line.startswith('#'):
                purpose_end = i
                in_purpose = False
                break

    if purpose_start >= 0 and purpose_end < 0:
        purpose_end = purpose_start + 1

    if purpose_start >= 0 and purpose_end > purpose_start:
        purpose_text = ' '.join(l.strip() for l in lines[purpose_start:purpose_end] if l.strip())

        # Count sentences
        sentences = re.split(r'(?<=[.!?])\s+', purpose_text.strip())
        sentences = [s for s in sentences if s.strip()]

        if len(sentences) > 2:
            # Keep only first 2 sentences
            shortened = ' '.join(sentences[:2])
            if not shortened.endswith('.'):
                shortened += '.'
            lines[purpose_start] = shortened
            # Remove extra lines
            for j in range(purpose_start + 1, purpose_end):
                lines[j] = ''

        elif len(purpose_text) > 400 and len(sentences) <= 2:
            # Just trim the text
            trimmed = purpose_text[:397] + '...'
            # Find a good break point
            last_period = purpose_text[:400].rfind('.')
            if last_period > 200:
                trimmed = purpose_text[:last_period + 1]
            lines[purpose_start] = trimmed
            for j in range(purpose_start + 1, purpose_end):
                lines[j] = ''

    # Fix Instructions section - add numbered steps if missing
    in_code = False
    instructions_start = -1
    instructions_end = -1

    for i, line in enumerate(lines):
        if CODE_FENCE.match(line):
            in_code = not in_code
        if in_code:
            continue

        if line.strip().lower() == '## instructions':
            instructions_start = i + 1
        elif instructions_start >= 0 and re.match(r'^##\s+', line):
            instructions_end = i
            break

    if instructions_start >= 0 and instructions_end < 0:
        instructions_end = len(lines)

    if instructions_start >= 0:
        instr_lines = lines[instructions_start:instructions_end]
        instr_text = '\n'.join(instr_lines)

        # Check for numbered list or step headings
        has_numbered = bool(re.search(r'(?m)^\s*1\.\s+\S+', instr_text))
        has_step_heading = bool(re.search(r'(?mi)^\s*#{2,6}\s*step\s*\d+', instr_text))
        has_step_label = bool(re.search(r'(?mi)^\s*step\s*\d+[:\-]', instr_text))

        if not (has_numbered or has_step_heading or has_step_label):
            # Convert bullet points to numbered list
            step_num = 0
            for j in range(instructions_start, instructions_end):
                stripped = lines[j].strip()
                if stripped.startswith('- ') or stripped.startswith('* '):
                    step_num += 1
                    # Replace bullet with number
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    lines[j] = ' ' * indent + f"{step_num}. {stripped[2:]}"

            # If no bullets were found either, wrap existing paragraphs as numbered steps
            if step_num == 0:
                para_lines = []
                for j in range(instructions_start, instructions_end):
                    if lines[j].strip() and not lines[j].startswith('#') and not CODE_FENCE.match(lines[j]):
                        para_lines.append(j)

                if para_lines and len(para_lines) <= 10:
                    for idx, j in enumerate(para_lines):
                        if not re.match(r'^\s*\d+\.', lines[j]):
                            lines[j] = f"{idx + 1}. {lines[j].strip()}"

    body = '\n'.join(lines)
    return f"---\n{fm}\n---\n{body}"


def main():
    root = Path('plugins')
    fixed = 0

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            content = skill_path.read_text(encoding='utf-8')
            new_content = fix_purpose_and_instructions(content)
            if new_content != content:
                skill_path.write_text(new_content, encoding='utf-8')
                fixed += 1
        except Exception as e:
            print(f"  Error: {skill_path}: {e}", file=sys.stderr)

    print(f"Fixed purpose/instructions in {fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
