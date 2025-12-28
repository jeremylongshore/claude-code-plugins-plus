#!/usr/bin/env python3
"""
Fix missing purpose statement in SKILL.md files.

Adds a purpose statement after the title or ## Overview section.
"""

import re
import sys
from pathlib import Path


def add_purpose_statement(content: str, skill_name: str) -> tuple:
    """Add a markdown H1 title + purpose statement if missing."""
    changes = []

    def extract_frontmatter_and_body(text: str) -> tuple[str, str]:
        if not text.startswith('---'):
            return "", text
        parts = text.split('---', 2)
        if len(parts) < 3:
            return "", text
        frontmatter = parts[1]
        body = parts[2]
        if body.startswith('\n'):
            body = body[1:]
        return frontmatter, body

    def build_title_from_name(name: str) -> str:
        return name.replace('_', '-').replace('-', ' ').strip().title()

    def iter_body_lines(body_text: str):
        return body_text.splitlines()

    def find_markdown_h1_index(body_text: str) -> int:
        in_code = False
        for idx, raw in enumerate(iter_body_lines(body_text)):
            if re.match(r'^\s*(```|~~~)', raw):
                in_code = not in_code
                continue
            if in_code:
                continue
            if re.match(r'^#\s+\S', raw) and not raw.startswith('## '):
                return idx
        return -1

    def find_purpose_paragraph_after_h1(body_text: str, h1_idx: int, max_scan: int = 60) -> str:
        lines = iter_body_lines(body_text)
        in_code = False
        paragraph = []
        scan_end = min(len(lines), h1_idx + 1 + max_scan)

        for raw in lines[h1_idx + 1:scan_end]:
            if re.match(r'^\s*(```|~~~)', raw):
                in_code = not in_code
                continue
            if in_code:
                continue

            line = raw.strip()
            if not line:
                if paragraph:
                    break
                continue
            if line.startswith('#'):
                break
            if line.startswith(('-', '*', '+')) or re.match(r'^\d+\.\s', line):
                if paragraph:
                    break
                continue
            paragraph.append(line)

        return ' '.join(paragraph).strip()

    frontmatter, body = extract_frontmatter_and_body(content)
    if not body:
        return content, changes

    h1_idx = find_markdown_h1_index(body)

    # Generate a conservative, single-sentence purpose (matches validator constraints)
    purpose = f"This skill provides automated assistance for {skill_name.replace('-', ' ').strip()} tasks."

    if h1_idx == -1:
        title = build_title_from_name(skill_name)
        new_body = f"# {title}\n\n{purpose}\n\n{body.lstrip()}"
        if frontmatter:
            new_content = f"---{frontmatter}---\n{new_body}"
        else:
            new_content = new_body
        changes.append("Inserted missing H1 title + purpose near top")
        return new_content, changes

    # H1 exists; ensure purpose paragraph exists right after it
    existing_purpose = find_purpose_paragraph_after_h1(body, h1_idx)
    if existing_purpose:
        return content, changes

    body_lines = iter_body_lines(body)
    insert_at = h1_idx + 1
    while insert_at < len(body_lines) and not body_lines[insert_at].strip():
        insert_at += 1
    body_lines.insert(insert_at, purpose)
    body_lines.insert(insert_at + 1, "")
    new_body = "\n".join(body_lines)

    if frontmatter:
        new_content = f"---{frontmatter}---\n{new_body}"
    else:
        new_content = new_body

    changes.append("Inserted missing purpose paragraph after existing H1 title")
    return new_content, changes


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
