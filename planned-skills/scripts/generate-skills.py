#!/usr/bin/env python3
"""Generate SKILL.md files for a category."""

import os
import sys
import json

def generate_skill_md(skill_name: str, category: dict) -> str:
    """Generate SKILL.md content for a skill."""

    # Convert skill name to display name
    display_name = skill_name.replace('-', ' ').title()

    # Determine allowed tools based on category
    category_tools = {
        "devops": "Read, Write, Edit, Bash, Grep",
        "security": "Read, Write, Grep, Bash(npm:*)",
        "frontend": "Read, Write, Edit, Bash(npm:*), Bash(npx:*)",
        "backend": "Read, Write, Edit, Bash, Grep",
        "ml": "Read, Write, Edit, Bash(python:*), Bash(pip:*)",
        "test": "Read, Write, Edit, Bash, Grep",
        "data": "Read, Write, Edit, Bash, Grep",
        "aws": "Read, Write, Edit, Bash(aws:*)",
        "gcp": "Read, Write, Edit, Bash(gcloud:*)",
        "api": "Read, Write, Edit, Bash(curl:*), Grep",
        "docs": "Read, Write, Edit",
        "business": "Read, Write, Edit, Bash",
    }

    # Get tools based on category tags
    tools = "Read, Write, Edit, Bash, Grep"
    for tag in category.get('tags', []):
        if tag in category_tools:
            tools = category_tools[tag]
            break

    # Generate trigger phrases
    triggers = f"{skill_name.replace('-', ' ')}, {display_name.lower()}"

    content = f'''---
name: {skill_name}
description: |
  {display_name} - Auto-activating skill for {category['name']}.
  Triggers on: {triggers}
  Part of the {category['name']} skill category.
allowed-tools: {tools}
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# {display_name}

## Purpose

This skill provides automated assistance for {display_name.lower()} tasks within the {category['name']} domain.

## When to Use

This skill activates automatically when you:
- Mention "{skill_name.replace('-', ' ')}" in your request
- Ask about {display_name.lower()} patterns or best practices
- Need help with {category['description'].lower()}

## Capabilities

- Provides step-by-step guidance for {display_name.lower()}
- Follows industry best practices and patterns
- Generates production-ready code and configurations
- Validates outputs against common standards

## Example Triggers

- "Help me with {skill_name.replace('-', ' ')}"
- "Set up {display_name.lower()}"
- "How do I implement {skill_name.replace('-', ' ')}?"

## Related Skills

Part of the **{category['name']}** skill category.
Tags: {', '.join(category.get('tags', []))}
'''
    return content


def generate_category(category_id: str, output_dir: str):
    """Generate all skills for a category."""

    # Load category config
    config_path = f"planned-skills/categories/{category_id}/category-config.json"
    with open(config_path) as f:
        category = json.load(f)

    # Create output directory
    cat_output = os.path.join(output_dir, category_id)
    os.makedirs(cat_output, exist_ok=True)

    generated = 0
    for skill_name in category.get('skills', []):
        skill_dir = os.path.join(cat_output, skill_name)
        os.makedirs(skill_dir, exist_ok=True)

        skill_path = os.path.join(skill_dir, 'SKILL.md')
        content = generate_skill_md(skill_name, category)

        with open(skill_path, 'w') as f:
            f.write(content)

        generated += 1
        print(f"  Created: {skill_name}/SKILL.md")

    return generated


def main():
    # High-priority categories for Phase 2
    categories = [
        "01-devops-basics",
        "02-devops-advanced",
        "03-security-fundamentals",
        "06-backend-dev",
        "13-aws-skills",
        "14-gcp-skills",
    ]

    output_dir = "planned-skills/generated"
    os.makedirs(output_dir, exist_ok=True)

    total = 0
    for cat_id in categories:
        print(f"\nGenerating {cat_id}...")
        count = generate_category(cat_id, output_dir)
        total += count
        print(f"  Generated {count} skills")

    print(f"\n=== Total: {total} skills generated ===")


if __name__ == "__main__":
    main()
