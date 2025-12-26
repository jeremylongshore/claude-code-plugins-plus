#!/usr/bin/env python3
"""
Validates YAML frontmatter in command/agent markdown files for Claude Code plugins.

Ported from nixtla source of truth:
  /home/jeremy/000-projects/nixtla/004-scripts/validate_command_agent_frontmatter.py

Validates frontmatter in:
- plugins/**/commands/*.md
- plugins/**/agents/*.md

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any


def extract_frontmatter(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Extract YAML frontmatter from markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, f"Cannot read file: {e}"

    # Match frontmatter between --- delimiters
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, "No frontmatter found"

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            return None, "Frontmatter is not a YAML mapping"
        return frontmatter, None
    except yaml.YAMLError as e:
        return None, f"Invalid YAML: {e}"


def validate_command_frontmatter(frontmatter: Dict[str, Any], file_path: Path) -> Tuple[List[str], List[str]]:
    """Validate frontmatter for command files. Returns (errors, warnings)."""
    errors = []
    warnings = []

    # Required field: name
    if 'name' not in frontmatter:
        errors.append("Missing required field: name")
    elif not isinstance(frontmatter['name'], str):
        errors.append("Field 'name' must be a string")
    else:
        name = frontmatter['name']
        # Kebab-case is best practice, not required (WARN)
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            warnings.append("Field 'name' should be kebab-case (lowercase + hyphens)")
        # Should match filename (WARN)
        expected_name = file_path.stem
        if name != expected_name:
            warnings.append(f"Field 'name' '{name}' should match filename '{expected_name}.md'")

    # Required field: description
    if 'description' not in frontmatter:
        errors.append("Missing required field: description")
    elif not isinstance(frontmatter['description'], str):
        errors.append("Field 'description' must be a string")
    else:
        desc = frontmatter['description']
        if len(desc) < 10:
            errors.append("Field 'description' must be at least 10 characters")
        if len(desc) > 80:
            warnings.append("Field 'description' should be 80 characters or less")

    # Optional field: shortcut
    if 'shortcut' in frontmatter:
        shortcut = frontmatter['shortcut']
        if not isinstance(shortcut, str):
            errors.append("Field 'shortcut' must be a string")
        elif len(shortcut) < 1 or len(shortcut) > 4:
            warnings.append("Field 'shortcut' should be 1-4 characters")
        elif not shortcut.islower():
            warnings.append("Field 'shortcut' should be lowercase")
        elif not shortcut.isalpha():
            warnings.append("Field 'shortcut' should contain only letters")

    # Optional field: category (expanded list from nixtla)
    valid_categories = ['git', 'deployment', 'security', 'testing', 'documentation',
                       'database', 'api', 'frontend', 'backend', 'devops', 'forecasting',
                       'analytics', 'migration', 'monitoring', 'other']
    if 'category' in frontmatter:
        if frontmatter['category'] not in valid_categories:
            warnings.append(f"Unknown category: {frontmatter['category']}")

    # Optional field: difficulty
    valid_difficulties = ['beginner', 'intermediate', 'advanced', 'expert']
    if 'difficulty' in frontmatter:
        if frontmatter['difficulty'] not in valid_difficulties:
            warnings.append(f"Unknown difficulty: {frontmatter['difficulty']}")

    return errors, warnings


def validate_agent_frontmatter(frontmatter: Dict[str, Any], file_path: Path) -> Tuple[List[str], List[str]]:
    """Validate frontmatter for agent files. Returns (errors, warnings)."""
    errors = []
    warnings = []

    # Required field: name
    if 'name' not in frontmatter:
        errors.append("Missing required field: name")
    elif not isinstance(frontmatter['name'], str):
        errors.append("Field 'name' must be a string")
    else:
        name = frontmatter['name']
        # Kebab-case is best practice (WARN)
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            warnings.append("Field 'name' should be kebab-case (lowercase + hyphens)")

    # Required field: description (20 chars minimum for agents)
    if 'description' not in frontmatter:
        errors.append("Missing required field: description")
    elif not isinstance(frontmatter['description'], str):
        errors.append("Field 'description' must be a string")
    else:
        desc = frontmatter['description']
        if len(desc) < 20:
            errors.append("Field 'description' must be at least 20 characters")
        if len(desc) > 200:
            warnings.append("Field 'description' should be 200 characters or less")

    # Capabilities are best practice, not required (WARN)
    if 'capabilities' not in frontmatter:
        warnings.append("Missing recommended field: capabilities")
    elif not isinstance(frontmatter['capabilities'], list):
        warnings.append("Field 'capabilities' should be an array")
    elif len(frontmatter['capabilities']) < 2:
        warnings.append("Field 'capabilities' should have at least 2 items")
    elif len(frontmatter['capabilities']) > 10:
        warnings.append("Field 'capabilities' should have 10 or fewer items")
    else:
        # Check each capability is a string
        for i, cap in enumerate(frontmatter['capabilities']):
            if not isinstance(cap, str):
                errors.append(f"Field 'capabilities[{i}]' must be a string")

    # Optional field: expertise_level
    valid_expertise = ['intermediate', 'advanced', 'expert']
    if 'expertise_level' in frontmatter:
        if frontmatter['expertise_level'] not in valid_expertise:
            warnings.append(f"Unknown expertise_level: {frontmatter['expertise_level']}")

    # Optional field: activation_priority
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if 'activation_priority' in frontmatter:
        if frontmatter['activation_priority'] not in valid_priorities:
            warnings.append(f"Unknown activation_priority: {frontmatter['activation_priority']}")

    return errors, warnings


def find_command_agent_files(root: Path) -> List[Tuple[Path, str]]:
    """Find all command and agent markdown files in plugins/."""
    results = []

    plugins_dir = root / "plugins"
    if not plugins_dir.exists():
        return results

    # Find command files
    for cmd_file in plugins_dir.rglob("commands/*.md"):
        if cmd_file.is_file():
            results.append((cmd_file, "command"))

    # Find agent files
    for agent_file in plugins_dir.rglob("agents/*.md"):
        if agent_file.is_file():
            results.append((agent_file, "agent"))

    return results


def validate_file(file_path: Path, file_type: str) -> Dict[str, Any]:
    """Validate a single command or agent markdown file."""
    # Extract frontmatter
    frontmatter, error = extract_frontmatter(file_path)
    if error:
        return {'fatal': error}

    # Validate based on file type
    if file_type == "command":
        errors, warnings = validate_command_frontmatter(frontmatter, file_path)
    elif file_type == "agent":
        errors, warnings = validate_agent_frontmatter(frontmatter, file_path)
    else:
        return {'fatal': f"Unknown file type: {file_type}"}

    return {'errors': errors, 'warnings': warnings}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    files = find_command_agent_files(repo_root)

    if not files:
        print("No command or agent files found - nothing to validate.")
        return 0

    print(f"🔍 COMMAND/AGENT FRONTMATTER VALIDATOR")
    print(f"   Nixtla Plugin Standard (ported)")
    print(f"{'=' * 70}\n")
    print(f"Found {len(files)} files to validate.\n")

    total_errors = 0
    total_warnings = 0
    files_with_errors = []
    files_with_warnings = []
    files_compliant = []

    for file_path, file_type in files:
        rel = file_path.relative_to(repo_root)
        result = validate_file(file_path, file_type)

        if 'fatal' in result:
            print(f"❌ {rel} ({file_type}): FATAL - {result['fatal']}")
            total_errors += 1
            files_with_errors.append(str(rel))
            continue

        errors = result.get('errors', [])
        warnings = result.get('warnings', [])

        if errors:
            print(f"❌ {rel} ({file_type}):")
            for error in errors:
                print(f"   ERROR: {error}")
            for warn in warnings:
                print(f"   WARN: {warn}")
            total_errors += len(errors)
            total_warnings += len(warnings)
            files_with_errors.append(str(rel))
        elif warnings:
            print(f"⚠️  {rel} ({file_type}):")
            for warn in warnings:
                print(f"   WARN: {warn}")
            total_warnings += len(warnings)
            files_with_warnings.append(str(rel))
        else:
            files_compliant.append(str(rel))

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total files validated: {len(files)}")
    print(f"✅ Fully compliant: {len(files_compliant)}")
    print(f"⚠️  Warnings only: {len(files_with_warnings)}")
    print(f"❌ With errors: {len(files_with_errors)}")
    print(f"{'=' * 70}")

    # Compliance rate (passing = no errors)
    passing_count = len(files_compliant) + len(files_with_warnings)
    compliant_pct = (passing_count / len(files) * 100) if files else 0
    print(f"\n📈 Compliance rate: {compliant_pct:.1f}%")

    if total_errors > 0:
        print(f"\n❌ Validation FAILED with {total_errors} errors")
        return 1
    elif total_warnings > 0:
        print(f"\n⚠️  Validation PASSED with {total_warnings} warnings")
        print(f"(Warnings are best practices - not blocking)")
        return 0
    else:
        print(f"\n✅ All command/agent files fully compliant!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
