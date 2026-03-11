#!/usr/bin/env python3
"""
Refactor skills to Progressive Disclosure Architecture (PDA) pattern.
Moves detailed content to references/ directory, keeping SKILL.md concise.
"""

import re
import sys
from pathlib import Path


def extract_sections(content: str) -> dict:
    """Extract sections from markdown content."""
    sections = {}
    current_section = 'header'
    current_content = []

    lines = content.split('\n')
    in_frontmatter = False
    frontmatter_lines = []
    body_start = 0

    # Extract frontmatter
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            in_frontmatter = True
            frontmatter_lines.append(line)
            continue
        if in_frontmatter:
            frontmatter_lines.append(line)
            if line.strip() == '---':
                body_start = i + 1
                break

    sections['frontmatter'] = '\n'.join(frontmatter_lines)

    # Extract body sections
    for line in lines[body_start:]:
        if line.startswith('## '):
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip().lower().replace(' ', '_')
            current_content = [line]
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def create_concise_skill(sections: dict, skill_name: str) -> str:
    """Create a concise SKILL.md with references."""
    lines = [sections.get('frontmatter', '')]

    # Title
    title = skill_name.replace('-', ' ').title()
    lines.append(f'\n# {title}\n')

    # Overview - keep brief
    if 'overview' in sections:
        overview = sections['overview']
        # Take first paragraph only
        paragraphs = overview.split('\n\n')
        first_para = paragraphs[1] if len(paragraphs) > 1 else paragraphs[0]
        if not first_para.startswith('## '):
            lines.append('## Overview\n')
            lines.append(first_para[:500] + '\n')

    # Prerequisites - keep as-is if short
    if 'prerequisites' in sections:
        prereq = sections['prerequisites']
        prereq_lines = prereq.split('\n')
        if len(prereq_lines) <= 15:
            lines.append(prereq + '\n')
        else:
            lines.append('## Prerequisites\n')
            lines.append('See `${CLAUDE_SKILL_DIR}/references/prerequisites.md` for detailed requirements.\n')

    # Instructions - keep concise
    if 'instructions' in sections:
        instr = sections['instructions']
        instr_lines = instr.split('\n')
        if len(instr_lines) <= 20:
            lines.append(instr + '\n')
        else:
            # Extract just the numbered steps, not code blocks
            condensed = ['## Instructions\n']
            for line in instr_lines:
                if re.match(r'^\d+\.', line.strip()):
                    condensed.append(line)
            if len(condensed) > 1:
                lines.append('\n'.join(condensed[:12]) + '\n')
            lines.append('\nSee `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.\n')

    # Output - brief
    if 'output' in sections:
        output = sections['output']
        output_lines = output.split('\n')
        if len(output_lines) <= 15:
            lines.append(output + '\n')
        else:
            lines.append('## Output\n')
            # Extract just bullet points
            bullets = [l for l in output_lines if l.strip().startswith('-')][:6]
            lines.append('\n'.join(bullets) + '\n')

    # Error Handling - always reference
    if 'error_handling' in sections:
        lines.append('## Error Handling\n')
        lines.append('See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.\n')

    # Examples - always reference
    if 'examples' in sections:
        lines.append('## Examples\n')
        lines.append('See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.\n')

    # Resources - keep brief
    if 'resources' in sections:
        res = sections['resources']
        res_lines = res.split('\n')
        if len(res_lines) <= 10:
            lines.append(res + '\n')
        else:
            lines.append('## Resources\n')
            # Keep just first few links
            links = [l for l in res_lines if '](http' in l or l.strip().startswith('-')][:5]
            lines.append('\n'.join(links) + '\n')

    return '\n'.join(lines)


def create_reference_files(sections: dict, refs_dir: Path) -> dict:
    """Create reference files from extracted sections."""
    refs_dir.mkdir(exist_ok=True)
    created = {}

    # Implementation guide (from instructions)
    if 'instructions' in sections:
        instr = sections['instructions']
        if len(instr.split('\n')) > 20:
            impl_content = f"# Implementation Guide\n\n{instr.replace('## Instructions', '').strip()}"
            (refs_dir / 'implementation.md').write_text(impl_content)
            created['implementation.md'] = True

    # Error handling
    if 'error_handling' in sections:
        err = sections['error_handling']
        err_content = f"# Error Handling Reference\n\n{err.replace('## Error Handling', '').strip()}"
        (refs_dir / 'errors.md').write_text(err_content)
        created['errors.md'] = True

    # Examples
    if 'examples' in sections:
        ex = sections['examples']
        ex_content = f"# Examples\n\n{ex.replace('## Examples', '').strip()}"
        (refs_dir / 'examples.md').write_text(ex_content)
        created['examples.md'] = True

    # Prerequisites (if long)
    if 'prerequisites' in sections:
        prereq = sections['prerequisites']
        if len(prereq.split('\n')) > 15:
            prereq_content = f"# Prerequisites\n\n{prereq.replace('## Prerequisites', '').strip()}"
            (refs_dir / 'prerequisites.md').write_text(prereq_content)
            created['prerequisites.md'] = True

    # Any other large sections
    for section_name, content in sections.items():
        if section_name in ['frontmatter', 'header', 'overview', 'output', 'resources']:
            continue
        if section_name in ['instructions', 'error_handling', 'examples', 'prerequisites']:
            continue
        if len(content.split('\n')) > 30:
            filename = f"{section_name.replace('_', '-')}.md"
            title = section_name.replace('_', ' ').title()
            ref_content = f"# {title}\n\n{content}"
            (refs_dir / filename).write_text(ref_content)
            created[filename] = True

    return created


def refactor_skill(skill_dir: Path, dry_run: bool = False) -> dict:
    """Refactor a single skill to PDA pattern."""
    skill_file = skill_dir / 'SKILL.md'
    if not skill_file.exists():
        return {'status': 'skip', 'reason': 'no SKILL.md'}

    content = skill_file.read_text()
    lines = len(content.split('\n'))

    # Skip if already concise
    refs_dir = skill_dir / 'references'
    if lines <= 150 and refs_dir.exists():
        return {'status': 'skip', 'reason': 'already optimized'}

    if lines <= 100:
        return {'status': 'skip', 'reason': 'already concise'}

    # Extract sections
    sections = extract_sections(content)
    skill_name = skill_dir.name

    # Create new concise SKILL.md
    new_skill = create_concise_skill(sections, skill_name)
    new_lines = len(new_skill.split('\n'))

    if dry_run:
        return {
            'status': 'would_refactor',
            'original_lines': lines,
            'new_lines': new_lines,
            'sections': list(sections.keys())
        }

    # Create reference files
    created_refs = create_reference_files(sections, refs_dir)

    # Write new SKILL.md
    skill_file.write_text(new_skill)

    return {
        'status': 'refactored',
        'original_lines': lines,
        'new_lines': new_lines,
        'references_created': list(created_refs.keys())
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Refactor skills to PDA pattern')
    parser.add_argument('path', nargs='?', default='plugins', help='Path to plugins directory or specific skill')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--min-lines', type=int, default=150, help='Minimum lines to trigger refactor')
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file() and path.name == 'SKILL.md':
        skills = [path.parent]
    elif (path / 'SKILL.md').exists():
        skills = [path]
    else:
        # Find all SKILL.md files
        skills = list(path.rglob('*/SKILL.md'))
        if not skills:
            skills = list(path.rglob('SKILL.md'))
        skills = [s.parent for s in skills]

    print(f"Found {len(skills)} skills to analyze")
    print("=" * 80)

    stats = {'refactored': 0, 'skipped': 0, 'errors': 0}

    for skill_dir in sorted(skills):
        try:
            result = refactor_skill(skill_dir, dry_run=args.dry_run)

            if result['status'] == 'skip':
                stats['skipped'] += 1
            elif result['status'] in ['refactored', 'would_refactor']:
                stats['refactored'] += 1
                action = 'Would refactor' if args.dry_run else 'Refactored'
                print(f"{action}: {skill_dir}")
                print(f"  Lines: {result['original_lines']} → {result['new_lines']}")
                if 'references_created' in result:
                    print(f"  Created: {', '.join(result['references_created'])}")
        except Exception as e:
            stats['errors'] += 1
            print(f"ERROR: {skill_dir}: {e}")

    print("=" * 80)
    print(f"Refactored: {stats['refactored']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")


if __name__ == '__main__':
    main()
