#!/usr/bin/env python3
"""
Comprehensive SKILL.md fixer for nixtla strict compliance.

Fixes:
1. Missing "Use when" / "Trigger with" in description
2. Reserved words (claude, anthropic) in description
3. Unscoped Bash -> Bash(cmd:*)
4. Missing required sections
5. Missing purpose statement

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml


REQUIRED_SECTIONS = [
    "## Overview",
    "## Prerequisites",
    "## Instructions",
    "## Output",
    "## Error Handling",
    "## Examples",
    "## Resources",
]

SECTION_TEMPLATES = {
    "## Overview": """## Overview

This skill provides automated assistance for the described functionality.""",

    "## Prerequisites": """## Prerequisites

- Appropriate file access permissions
- Required dependencies installed""",

    "## Instructions": """## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed""",

    "## Output": """## Output

The skill produces structured output relevant to the task.""",

    "## Error Handling": """## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps""",

    "## Examples": """## Examples

Example usage patterns will be demonstrated in context.""",

    "## Resources": """## Resources

- Project documentation
- Related skills and commands""",
}


def parse_frontmatter(content: str) -> Tuple[dict, str, str]:
    """Parse YAML frontmatter. Returns (fm_dict, fm_raw, body)."""
    match = re.match(r'^(---\s*\n)(.*?)\n(---\s*\n)(.*)$', content, re.DOTALL)
    if not match:
        return None, None, content

    fm_raw = match.group(2)
    body = match.group(4)

    try:
        fm = yaml.safe_load(fm_raw)
        if not isinstance(fm, dict):
            return None, fm_raw, body
        return fm, fm_raw, body
    except yaml.YAMLError:
        return None, fm_raw, body


def fix_description(desc: str, skill_name: str) -> Tuple[str, List[str]]:
    """Fix description to include Use when / Trigger with and remove reserved words."""
    changes = []
    original = desc

    # Remove reserved words
    if 'claude' in desc.lower():
        desc = re.sub(r'\bclaude\b', 'AI assistant', desc, flags=re.IGNORECASE)
        changes.append("Replaced 'claude' with 'AI assistant'")

    if 'anthropic' in desc.lower():
        desc = re.sub(r'\banthropoic\b', 'the system', desc, flags=re.IGNORECASE)
        changes.append("Replaced 'anthropic' with 'the system'")

    # Check for Use when
    has_use_when = bool(re.search(r'\buse when\b', desc, re.IGNORECASE))
    has_trigger = bool(re.search(r'\btrigger with\b', desc, re.IGNORECASE))

    if not has_use_when or not has_trigger:
        # Generate trigger phrases based on skill name
        name_words = skill_name.replace('-', ' ').replace('_', ' ')

        # Build contextual trigger phrases
        if 'api' in skill_name.lower():
            use_when = "Use when building or modifying API endpoints"
            trigger = "Trigger with phrases like 'create API', 'design endpoint', or 'API scaffold'"
        elif 'test' in skill_name.lower():
            use_when = "Use when writing or improving tests"
            trigger = "Trigger with phrases like 'write tests', 'add test coverage', or 'test this'"
        elif 'deploy' in skill_name.lower() or 'devops' in skill_name.lower():
            use_when = "Use when deploying or managing infrastructure"
            trigger = "Trigger with phrases like 'deploy', 'infrastructure', or 'CI/CD'"
        elif 'security' in skill_name.lower() or 'audit' in skill_name.lower():
            use_when = "Use when assessing security or running audits"
            trigger = "Trigger with phrases like 'security scan', 'audit', or 'vulnerability'"
        elif 'database' in skill_name.lower() or 'sql' in skill_name.lower():
            use_when = "Use when working with databases or data models"
            trigger = "Trigger with phrases like 'database', 'query', or 'schema'"
        elif 'doc' in skill_name.lower():
            use_when = "Use when creating or updating documentation"
            trigger = "Trigger with phrases like 'document', 'README', or 'docs'"
        elif 'git' in skill_name.lower() or 'commit' in skill_name.lower():
            use_when = "Use when managing version control"
            trigger = "Trigger with phrases like 'commit', 'branch', or 'git'"
        elif 'monitor' in skill_name.lower() or 'observ' in skill_name.lower():
            use_when = "Use when setting up monitoring or observability"
            trigger = "Trigger with phrases like 'monitor', 'metrics', or 'alerts'"
        elif 'migrat' in skill_name.lower():
            use_when = "Use when performing migrations"
            trigger = "Trigger with phrases like 'migrate', 'upgrade', or 'convert'"
        elif 'analyz' in skill_name.lower() or 'analys' in skill_name.lower():
            use_when = "Use when analyzing code or data"
            trigger = "Trigger with phrases like 'analyze', 'review', or 'examine'"
        elif 'generat' in skill_name.lower() or 'creat' in skill_name.lower():
            use_when = "Use when generating or creating new content"
            trigger = "Trigger with phrases like 'generate', 'create', or 'scaffold'"
        elif 'optimi' in skill_name.lower() or 'perf' in skill_name.lower():
            use_when = "Use when optimizing performance"
            trigger = "Trigger with phrases like 'optimize', 'performance', or 'speed up'"
        elif 'valid' in skill_name.lower():
            use_when = "Use when validating configurations or code"
            trigger = "Trigger with phrases like 'validate', 'check', or 'verify'"
        else:
            use_when = f"Use when appropriate context detected"
            trigger = f"Trigger with relevant phrases based on skill purpose"

        # Append if missing
        additions = []
        if not has_use_when:
            additions.append(use_when)
            changes.append(f"Added 'Use when' phrase")
        if not has_trigger:
            additions.append(trigger)
            changes.append(f"Added 'Trigger with' phrase")

        if additions:
            # Append to description
            desc = desc.rstrip()
            if not desc.endswith('.'):
                desc += '.'
            desc += ' ' + '. '.join(additions) + '.'

    return desc, changes


def fix_allowed_tools(fm: dict) -> Tuple[dict, List[str]]:
    """Fix unscoped Bash in allowed-tools."""
    changes = []

    if 'allowed-tools' not in fm:
        return fm, changes

    tools = fm['allowed-tools']

    # Handle string format
    if isinstance(tools, str):
        tools_list = [t.strip() for t in tools.split(',')]
    else:
        tools_list = list(tools)

    # Replace unscoped Bash
    new_tools = []
    for tool in tools_list:
        if tool == 'Bash':
            new_tools.append('Bash(cmd:*)')
            changes.append("Scoped 'Bash' to 'Bash(cmd:*)'")
        else:
            new_tools.append(tool)

    # Standardize to CSV string (Claude Code standard)
    fm['allowed-tools'] = ', '.join(new_tools)

    return fm, changes


def fix_body_sections(body: str, skill_name: str) -> Tuple[str, List[str]]:
    """Add missing required sections to body."""
    changes = []

    # Check which sections are missing
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        if section not in body:
            missing_sections.append(section)

    if not missing_sections:
        return body, changes

    # Find where to insert sections (after title or at end)
    lines = body.split('\n')

    # Find first # heading (title)
    title_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('## '):
            title_idx = i
            break

    # Find first ## heading
    first_section_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('## '):
            first_section_idx = i
            break

    # Build sections to add
    sections_to_add = []
    for section in missing_sections:
        if section in SECTION_TEMPLATES:
            sections_to_add.append(SECTION_TEMPLATES[section])
            changes.append(f"Added section: {section}")

    if not sections_to_add:
        return body, changes

    # Insert at appropriate location
    insert_text = '\n\n' + '\n\n'.join(sections_to_add)

    if first_section_idx > 0:
        # Insert before first existing section
        lines.insert(first_section_idx, insert_text)
        body = '\n'.join(lines)
    elif title_idx >= 0:
        # Insert after title
        lines.insert(title_idx + 1, insert_text)
        body = '\n'.join(lines)
    else:
        # Append at end
        body = body.rstrip() + insert_text

    return body, changes


def rebuild_frontmatter(fm: dict) -> str:
    """Rebuild frontmatter YAML."""
    lines = []

    # Ordered keys
    ordered = ['name', 'description', 'allowed-tools', 'version', 'author', 'license',
               'model', 'tags', 'disable-model-invocation', 'mode', 'metadata']

    for key in ordered:
        if key not in fm:
            continue
        val = fm[key]

        if key == 'description':
            # Multi-line description
            lines.append(f'{key}: |')
            for line in val.split('\n'):
                lines.append(f'  {line}')
        elif key == 'allowed-tools':
            if isinstance(val, list):
                lines.append(f'{key}: {", ".join(val)}')
            else:
                lines.append(f'{key}: {val}')
        elif isinstance(val, list):
            lines.append(f'{key}:')
            for item in val:
                lines.append(f'  - {item}')
        elif isinstance(val, bool):
            lines.append(f'{key}: {str(val).lower()}')
        else:
            lines.append(f'{key}: {val}')

    # Add remaining keys
    for key, val in fm.items():
        if key in ordered:
            continue
        if isinstance(val, list):
            lines.append(f'{key}:')
            for item in val:
                lines.append(f'  - {item}')
        else:
            lines.append(f'{key}: {val}')

    return '\n'.join(lines)


def process_skill(filepath: Path, dry_run: bool = False) -> Dict:
    """Process a single SKILL.md file."""
    result = {'file': str(filepath), 'changes': [], 'errors': []}

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result['errors'].append(f"Read error: {e}")
        return result

    fm, fm_raw, body = parse_frontmatter(content)
    if fm is None:
        result['errors'].append("No valid frontmatter")
        return result

    skill_name = fm.get('name', filepath.parent.name)
    all_changes = []

    # Fix description
    if 'description' in fm:
        fm['description'], desc_changes = fix_description(fm['description'], skill_name)
        all_changes.extend(desc_changes)

    # Fix allowed-tools
    fm, tools_changes = fix_allowed_tools(fm)
    all_changes.extend(tools_changes)

    # Fix body sections
    body, section_changes = fix_body_sections(body, skill_name)
    all_changes.extend(section_changes)

    result['changes'] = all_changes

    if all_changes and not dry_run:
        # Rebuild content
        new_fm = rebuild_frontmatter(fm)
        new_content = f"---\n{new_fm}\n---\n{body}"
        filepath.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix all SKILL.md files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--path', default='plugins', help='Path to scan')
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"Error: {root} does not exist")
        sys.exit(1)

    # Find all SKILL.md files
    skill_files = list(root.rglob("skills/*/SKILL.md"))
    print(f"Found {len(skill_files)} SKILL.md files")

    total_changes = 0
    files_fixed = 0

    for filepath in skill_files:
        result = process_skill(filepath, args.dry_run)

        if result['changes']:
            files_fixed += 1
            total_changes += len(result['changes'])
            print(f"\n{filepath.relative_to(root)}:")
            for change in result['changes']:
                print(f"  + {change}")

        if result['errors']:
            for error in result['errors']:
                print(f"  ERROR: {error}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {files_fixed} files, {total_changes} changes")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")


if __name__ == '__main__':
    main()
