#!/usr/bin/env python3
"""
Fix purpose statement warnings v2:
1. Shorten purpose statements that are 3+ sentences to 1-2
2. Trim purpose statements > 400 chars

Handles purpose in: ## Purpose section, first para after # Title, first para after ## Overview
"""

import re
import sys
from pathlib import Path

RE_FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)$', re.DOTALL)
CODE_FENCE = re.compile(r'^```')
HEADING = re.compile(r'^#{1,6}\s+')


def sentence_count(text: str) -> int:
    cleaned = re.sub(r'\s+', ' ', text.strip())
    if not cleaned:
        return 0
    parts = re.split(r'(?<=[.!?])\s+', cleaned)
    return len([p for p in parts if p.strip()])


def find_first_paragraph(lines: list, start: int) -> tuple:
    """Find first paragraph after start index. Returns (start_idx, end_idx, text)."""
    paragraph_lines = []
    para_start = -1
    in_code = False

    for i in range(start, len(lines)):
        line = lines[i]
        if CODE_FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if HEADING.match(line):
            break
        if not line.strip():
            if paragraph_lines:
                return (para_start, i, ' '.join(paragraph_lines))
            continue
        if line.lstrip().startswith(('-', '*', '+')):
            if paragraph_lines:
                return (para_start, i, ' '.join(paragraph_lines))
            continue
        if para_start < 0:
            para_start = i
        paragraph_lines.append(line.strip())

    if paragraph_lines:
        return (para_start, start + len(lines), ' '.join(paragraph_lines))
    return (-1, -1, '')


def shorten_purpose(text: str) -> str:
    """Shorten purpose to 1-2 sentences, max 400 chars."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s.strip()]

    if len(sentences) <= 2 and len(text) <= 400:
        return text  # Already fine

    # Take first 2 sentences
    shortened = ' '.join(sentences[:2])
    if not shortened.endswith(('.', '!', '?')):
        shortened += '.'

    # If still > 400, take just first sentence
    if len(shortened) > 400:
        shortened = sentences[0]
        if not shortened.endswith(('.', '!', '?')):
            shortened += '.'

    # If STILL > 400, truncate at last period before 400
    if len(shortened) > 400:
        last_period = shortened[:400].rfind('.')
        if last_period > 100:
            shortened = shortened[:last_period + 1]

    return shortened


def fix_skill(skill_path: Path) -> bool:
    """Fix purpose statement. Returns True if changed."""
    content = skill_path.read_text(encoding='utf-8')
    m = RE_FRONTMATTER.match(content)
    if not m:
        return False

    fm = m.group(1)
    body = m.group(2)
    lines = body.splitlines()

    # Find purpose statement location (same logic as validator)
    purpose_start = -1
    purpose_end = -1
    purpose_text = ''

    # 1. Check ## Purpose section
    for i, line in enumerate(lines):
        if line.strip().lower() == '## purpose':
            ps, pe, pt = find_first_paragraph(lines, i + 1)
            if pt:
                purpose_start, purpose_end, purpose_text = ps, pe, pt
            break

    # 2. Check first paragraph after # Title
    if not purpose_text:
        for i, line in enumerate(lines):
            if line.startswith('# ') and not line.startswith('## '):
                ps, pe, pt = find_first_paragraph(lines, i + 1)
                if pt:
                    purpose_start, purpose_end, purpose_text = ps, pe, pt
                else:
                    # 3. Check ## Overview
                    for j, line2 in enumerate(lines):
                        if line2.strip().lower() == '## overview':
                            ps2, pe2, pt2 = find_first_paragraph(lines, j + 1)
                            if pt2:
                                purpose_start, purpose_end, purpose_text = ps2, pe2, pt2
                            break
                break

    if not purpose_text:
        return False

    sc = sentence_count(purpose_text)
    if sc <= 2 and len(purpose_text) <= 400:
        return False  # No fix needed

    # Shorten the purpose
    shortened = shorten_purpose(purpose_text)
    if shortened == purpose_text:
        return False

    # Replace in the lines
    lines[purpose_start] = shortened
    for j in range(purpose_start + 1, purpose_end):
        if lines[j].strip() and not HEADING.match(lines[j]) and not lines[j].strip().startswith(('-', '*', '+')):
            lines[j] = ''
        else:
            break

    # Clean up empty lines
    new_lines = []
    prev_empty = False
    for line in lines:
        if not line.strip():
            if not prev_empty:
                new_lines.append(line)
            prev_empty = True
        else:
            new_lines.append(line)
            prev_empty = False

    body = '\n'.join(new_lines)
    skill_path.write_text(f"---\n{fm}\n---\n{body}", encoding='utf-8')
    return True


def main():
    root = Path('plugins')
    fixed = 0

    for skill_path in sorted(root.rglob('*/SKILL.md')):
        try:
            if fix_skill(skill_path):
                fixed += 1
        except Exception as e:
            print(f"  Error: {skill_path}: {e}", file=sys.stderr)

    print(f"Fixed purpose statements in {fixed} files")
    return 0


if __name__ == '__main__':
    sys.exit(main())
