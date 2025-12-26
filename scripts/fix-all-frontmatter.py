#!/usr/bin/env python3
"""
Comprehensive frontmatter fixer for commands and agents.

Fixes:
1. Missing `name` field - adds from filename
2. Invalid category - maps to valid category
3. Missing `capabilities` for agents - generates from description

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


# Valid categories per nixtla standard
VALID_CATEGORIES = {
    'git', 'deployment', 'security', 'testing', 'documentation',
    'database', 'api', 'frontend', 'backend', 'devops', 'forecasting',
    'analytics', 'migration', 'monitoring', 'other'
}

# Category mappings for invalid categories
CATEGORY_MAPPING = {
    'ai': 'other',
    'ai-ml': 'other',
    'ml': 'analytics',
    'machine-learning': 'analytics',
    'llm': 'api',
    'prompt': 'other',
    'rag': 'database',
    'crypto': 'security',
    'cryptography': 'security',
    'compliance': 'security',
    'infrastructure': 'devops',
    'cloud': 'deployment',
}


def extract_frontmatter(content: str) -> tuple:
    """Extract frontmatter and body from markdown."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return None, content

    try:
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict):
            return None, content
        return fm, match.group(2)
    except yaml.YAMLError:
        return None, content


def rebuild_content(fm: Dict[str, Any], body: str) -> str:
    """Rebuild markdown with updated frontmatter."""
    # Custom YAML dump to preserve order and formatting
    lines = ['---']

    # Order: name, description, shortcut, category, difficulty, capabilities, etc.
    ordered_keys = ['name', 'description', 'shortcut', 'category', 'difficulty',
                    'capabilities', 'expertise_level', 'activation_priority']

    for key in ordered_keys:
        if key in fm:
            val = fm[key]
            if key == 'description' and isinstance(val, str) and len(val) > 60:
                # Multi-line description
                lines.append(f'{key}: >')
                # Wrap at ~70 chars
                words = val.split()
                current_line = '  '
                for word in words:
                    if len(current_line) + len(word) + 1 > 75:
                        lines.append(current_line.rstrip())
                        current_line = '  ' + word + ' '
                    else:
                        current_line += word + ' '
                if current_line.strip():
                    lines.append(current_line.rstrip())
            elif key == 'capabilities' and isinstance(val, list):
                lines.append(f'{key}:')
                for item in val:
                    lines.append(f'  - {item}')
            elif isinstance(val, str):
                lines.append(f'{key}: {val}')
            else:
                lines.append(f'{key}: {val}')

    # Add any remaining keys not in ordered list
    for key, val in fm.items():
        if key not in ordered_keys:
            if isinstance(val, list):
                lines.append(f'{key}:')
                for item in val:
                    lines.append(f'  - {item}')
            else:
                lines.append(f'{key}: {val}')

    lines.append('---')

    # Ensure body starts with newline
    if not body.startswith('\n'):
        body = '\n' + body

    return '\n'.join(lines) + body


def generate_capabilities_from_description(desc: str, name: str) -> List[str]:
    """Generate capabilities list from agent description."""
    capabilities = []

    # Extract key action words from description
    action_patterns = [
        (r'analyz\w+', 'Code and configuration analysis'),
        (r'generat\w+', 'Content generation'),
        (r'creat\w+', 'Resource creation'),
        (r'valid\w+', 'Validation and verification'),
        (r'optimi\w+', 'Performance optimization'),
        (r'debug\w+', 'Debugging and troubleshooting'),
        (r'test\w+', 'Testing and quality assurance'),
        (r'deploy\w+', 'Deployment automation'),
        (r'monitor\w+', 'Monitoring and alerting'),
        (r'secur\w+', 'Security assessment'),
        (r'migrat\w+', 'Migration assistance'),
        (r'document\w+', 'Documentation generation'),
        (r'review\w+', 'Code review'),
        (r'audit\w+', 'Audit and compliance'),
        (r'scan\w+', 'Scanning and detection'),
    ]

    desc_lower = desc.lower()
    for pattern, capability in action_patterns:
        if re.search(pattern, desc_lower):
            capabilities.append(capability)

    # Ensure at least 2 capabilities
    if len(capabilities) < 2:
        # Add generic capabilities based on name
        name_lower = name.lower()
        if 'security' in name_lower or 'audit' in name_lower:
            capabilities.extend(['Security analysis', 'Vulnerability detection'])
        elif 'test' in name_lower:
            capabilities.extend(['Test generation', 'Test execution'])
        elif 'database' in name_lower or 'sql' in name_lower:
            capabilities.extend(['Database analysis', 'Query optimization'])
        elif 'api' in name_lower:
            capabilities.extend(['API design', 'Endpoint validation'])
        elif 'deploy' in name_lower or 'devops' in name_lower:
            capabilities.extend(['Deployment automation', 'Infrastructure management'])
        else:
            capabilities.extend(['Task automation', 'Intelligent assistance'])

    # Dedupe and limit to 5
    seen = set()
    unique = []
    for cap in capabilities:
        if cap.lower() not in seen:
            seen.add(cap.lower())
            unique.append(cap)

    return unique[:5]


def fix_command_frontmatter(fm: Dict[str, Any], filepath: Path) -> tuple:
    """Fix command frontmatter issues. Returns (fixed_fm, changes)."""
    changes = []

    # Fix missing name
    if 'name' not in fm:
        fm['name'] = filepath.stem
        changes.append(f"Added name: {fm['name']}")

    # Fix invalid category
    if 'category' in fm and fm['category'] not in VALID_CATEGORIES:
        old_cat = fm['category']
        new_cat = CATEGORY_MAPPING.get(old_cat.lower(), 'other')
        fm['category'] = new_cat
        changes.append(f"Changed category: {old_cat} -> {new_cat}")

    return fm, changes


def fix_agent_frontmatter(fm: Dict[str, Any], filepath: Path) -> tuple:
    """Fix agent frontmatter issues. Returns (fixed_fm, changes)."""
    changes = []

    # Fix missing name
    if 'name' not in fm:
        fm['name'] = filepath.stem
        changes.append(f"Added name: {fm['name']}")

    # Fix missing capabilities
    if 'capabilities' not in fm:
        desc = fm.get('description', '')
        name = fm.get('name', filepath.stem)
        fm['capabilities'] = generate_capabilities_from_description(desc, name)
        changes.append(f"Added capabilities: {fm['capabilities']}")

    return fm, changes


def process_file(filepath: Path, file_type: str, dry_run: bool = False) -> Dict:
    """Process a single file."""
    result = {'file': str(filepath), 'changes': [], 'errors': []}

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result['errors'].append(f"Read error: {e}")
        return result

    fm, body = extract_frontmatter(content)
    if fm is None:
        result['errors'].append("No valid frontmatter found")
        return result

    # Fix based on type
    if file_type == 'command':
        fm, changes = fix_command_frontmatter(fm, filepath)
    elif file_type == 'agent':
        fm, changes = fix_agent_frontmatter(fm, filepath)
    else:
        result['errors'].append(f"Unknown type: {file_type}")
        return result

    result['changes'] = changes

    if changes and not dry_run:
        new_content = rebuild_content(fm, body)
        filepath.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix all frontmatter issues')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--path', default='plugins', help='Path to scan')
    args = parser.parse_args()

    plugins_dir = Path(args.path)
    if not plugins_dir.exists():
        print(f"Error: {plugins_dir} does not exist")
        sys.exit(1)

    # Find all command and agent files
    commands = list(plugins_dir.rglob("commands/*.md"))
    agents = list(plugins_dir.rglob("agents/*.md"))

    print(f"Found {len(commands)} command files and {len(agents)} agent files")

    total_changes = 0
    files_fixed = 0

    # Process commands
    for filepath in commands:
        result = process_file(filepath, 'command', args.dry_run)
        if result['changes']:
            files_fixed += 1
            total_changes += len(result['changes'])
            print(f"\n{filepath.relative_to(plugins_dir)}:")
            for change in result['changes']:
                print(f"  + {change}")
        if result['errors']:
            for error in result['errors']:
                print(f"  ERROR: {error}")

    # Process agents
    for filepath in agents:
        result = process_file(filepath, 'agent', args.dry_run)
        if result['changes']:
            files_fixed += 1
            total_changes += len(result['changes'])
            print(f"\n{filepath.relative_to(plugins_dir)}:")
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
