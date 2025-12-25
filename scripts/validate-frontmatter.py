#!/usr/bin/env python3
"""
Validates YAML frontmatter in markdown files for Claude Code plugins.
Checks for required fields and proper formatting.
"""

import sys
import re
import yaml
from pathlib import Path


def extract_frontmatter(file_path):
    """Extract YAML frontmatter from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match frontmatter between --- delimiters
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, "No frontmatter found"

    try:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter, None
    except yaml.YAMLError as e:
        return None, f"Invalid YAML: {e}"


def validate_command_frontmatter(frontmatter, file_path):
    """Validate frontmatter for command files."""
    errors = []

    # Required field: description
    if 'description' not in frontmatter:
        errors.append("Missing required field: description")
    elif not isinstance(frontmatter['description'], str):
        errors.append("Field 'description' must be a string")
    elif len(frontmatter['description']) < 10:
        errors.append("Field 'description' must be at least 10 characters")
    elif len(frontmatter['description']) > 80:
        errors.append("Field 'description' must be 80 characters or less")

    # Optional field: shortcut
    if 'shortcut' in frontmatter:
        shortcut = frontmatter['shortcut']
        if not isinstance(shortcut, str):
            errors.append("Field 'shortcut' must be a string")
        elif len(shortcut) < 1 or len(shortcut) > 4:
            errors.append("Field 'shortcut' must be 1-4 characters")
        elif not shortcut.islower():
            errors.append("Field 'shortcut' must be lowercase")
        elif not shortcut.isalpha():
            errors.append("Field 'shortcut' must contain only letters")

    # Optional field: category
    valid_categories = ['git', 'deployment', 'security', 'testing', 'documentation',
                       'database', 'api', 'frontend', 'backend', 'devops', 'other']
    if 'category' in frontmatter:
        if frontmatter['category'] not in valid_categories:
            errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

    # Optional field: difficulty
    valid_difficulties = ['beginner', 'intermediate', 'advanced', 'expert']
    if 'difficulty' in frontmatter:
        if frontmatter['difficulty'] not in valid_difficulties:
            errors.append(f"Invalid difficulty. Must be one of: {', '.join(valid_difficulties)}")

    return errors


def validate_agent_frontmatter(frontmatter, file_path):
    """Validate frontmatter for agent files."""
    errors = []

    # Required field: description
    if 'description' not in frontmatter:
        errors.append("Missing required field: description")
    elif not isinstance(frontmatter['description'], str):
        errors.append("Field 'description' must be a string")
    elif len(frontmatter['description']) < 20:
        errors.append("Field 'description' must be at least 20 characters")
    elif len(frontmatter['description']) > 80:
        errors.append("Field 'description' must be 80 characters or less")

    # Required field: capabilities
    if 'capabilities' not in frontmatter:
        errors.append("Missing required field: capabilities")
    elif not isinstance(frontmatter['capabilities'], list):
        errors.append("Field 'capabilities' must be an array")
    elif len(frontmatter['capabilities']) < 2:
        errors.append("Field 'capabilities' must have at least 2 items")
    elif len(frontmatter['capabilities']) > 10:
        errors.append("Field 'capabilities' must have 10 or fewer items")

    # Optional field: expertise_level
    valid_expertise = ['intermediate', 'advanced', 'expert']
    if 'expertise_level' in frontmatter:
        if frontmatter['expertise_level'] not in valid_expertise:
            errors.append(f"Invalid expertise_level. Must be one of: {', '.join(valid_expertise)}")

    # Optional field: activation_priority
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if 'activation_priority' in frontmatter:
        if frontmatter['activation_priority'] not in valid_priorities:
            errors.append(f"Invalid activation_priority. Must be one of: {', '.join(valid_priorities)}")

    return errors


def main():
    args = sys.argv[1:]

    strict = False
    if '--strict' in args:
        strict = True
        args = [a for a in args if a != '--strict']

    if len(args) == 0:
        candidates = []
        for pattern in ('plugins/**/commands/*.md', 'plugins/**/agents/*.md'):
            candidates.extend(Path('.').glob(pattern))

        if not candidates:
            print("⚠️  No command/agent markdown files found under plugins/.")
            sys.exit(0)

        total = 0
        warnings = 0
        errors_count = 0
        sample_errors = []

        for file_path in sorted(set(candidates)):
            total += 1

            frontmatter, error = extract_frontmatter(file_path)
            if error:
                if strict:
                    print(f"Error in {file_path}: {error}")
                    errors_count += 1
                else:
                    print(f"⚠️  {file_path}: {error}")
                    warnings += 1
                continue

            if '/commands/' in str(file_path):
                errors = validate_command_frontmatter(frontmatter, file_path)
                file_type = "command"
            elif '/agents/' in str(file_path):
                errors = validate_agent_frontmatter(frontmatter, file_path)
                file_type = "agent"
            else:
                continue

            if errors:
                errors_count += 1
                if len(sample_errors) < 25:
                    sample_errors.append((file_path, file_type, errors))

        print("\nFrontmatter validation summary:")
        print(f"  Files checked: {total}")
        print(f"  Warnings:      {warnings}")
        print(f"  Errors:        {errors_count}")

        if sample_errors:
            print("\nSample validation errors (first 25):")
            for file_path, file_type, errors in sample_errors:
                print(f"- {file_path} ({file_type}):")
                for err in errors:
                    print(f"  - {err}")

        if strict and errors_count > 0:
            sys.exit(1)

        # Non-strict mode is a CI smoke check: report but do not fail the build.
        sys.exit(0)

    if len(args) != 1:
        print("Usage: validate-frontmatter.py [--strict] <markdown-file>")
        print("       validate-frontmatter.py [--strict]   # validates all plugins/**/commands/*.md and plugins/**/agents/*.md")
        sys.exit(1)

    file_path = Path(args[0])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    frontmatter, error = extract_frontmatter(file_path)
    if error:
        print(f"Error in {file_path}: {error}")
        sys.exit(1)

    if '/commands/' in str(file_path):
        errors = validate_command_frontmatter(frontmatter, file_path)
        file_type = "command"
    elif '/agents/' in str(file_path):
        errors = validate_agent_frontmatter(frontmatter, file_path)
        file_type = "agent"
    else:
        print(f"Warning: Cannot determine file type for {file_path}")
        sys.exit(0)

    if errors:
        print(f"Validation errors in {file_path} ({file_type}):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"✅ Valid {file_type} frontmatter: {file_path}")
        sys.exit(0)


if __name__ == '__main__':
    main()
