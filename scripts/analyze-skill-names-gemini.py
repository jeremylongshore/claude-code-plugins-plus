#!/usr/bin/env python3
"""
Analyze all plugins and suggest Anthropic-compliant skill directory names using Gemini API (free tier).

This uses Google AI Studio Gemini API (1500 req/day free):
- Get API key: https://aistudio.google.com/app/apikey
- Set: export GEMINI_API_KEY=your-key

Compliance Target: Anthropic Agent Skills specification
- Structure: skills/{descriptive-name}/SKILL.md
- Name: max 64 chars, lowercase, hyphens, describes function
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def find_all_skills() -> List[Tuple[Path, Path]]:
    """Find all plugins with skills/skill-adapter/SKILL.md structure"""
    plugins_dir = Path('plugins')
    skills = []

    for skill_file in plugins_dir.rglob('skills/skill-adapter/SKILL.md'):
        plugin_dir = skill_file.parent.parent.parent
        skills.append((plugin_dir, skill_file))

    return skills

def read_skill_metadata(skill_file: Path) -> Dict[str, str]:
    """Extract YAML frontmatter from SKILL.md"""
    content = skill_file.read_text()

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            yaml_str = parts[1].strip()
            metadata = {}
            for line in yaml_str.split('\n'):
                if ':' in line and not line.strip().startswith('|'):
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                elif metadata and line.strip() and not line.strip().startswith('-'):
                    last_key = list(metadata.keys())[-1]
                    metadata[last_key] += ' ' + line.strip()
            return metadata

    return {}

def suggest_skill_name_simple(plugin_path: str, skill_metadata: Dict) -> str:
    """
    Generate skill name from plugin path following Anthropic guidelines.

    Anthropic requirements:
    - Max 64 characters
    - Lowercase letters, numbers, hyphens only
    - Descriptive of function (not generic like "skill-adapter")
    - No reserved words
    """
    # Get the plugin directory name (already descriptive)
    plugin_name = Path(plugin_path).name

    # Clean and validate
    skill_name = plugin_name.lower().replace('_', '-')

    # Ensure it's not too long (max 64 chars per Anthropic spec)
    if len(skill_name) > 64:
        skill_name = skill_name[:64].rstrip('-')

    # Remove any invalid characters
    skill_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in skill_name)

    # Remove duplicate hyphens
    while '--' in skill_name:
        skill_name = skill_name.replace('--', '-')

    skill_name = skill_name.strip('-')

    return skill_name

def main():
    """Analyze all skills and generate mapping file"""

    print("🔍 Finding all plugins with skills/skill-adapter/ structure...")
    skills = find_all_skills()
    print(f"✅ Found {len(skills)} plugins to migrate\n")

    if not skills:
        print("❌ No plugins found with skills/skill-adapter/ structure")
        sys.exit(1)

    print("📝 Generating skill name mappings...")
    print("   Using plugin directory names (already descriptive)\n")

    mappings = {}
    existing_names = set()
    errors = []

    for i, (plugin_dir, skill_file) in enumerate(skills, 1):
        plugin_path = str(plugin_dir.relative_to('plugins'))

        print(f"[{i}/{len(skills)}] {plugin_path}... ", end='', flush=True)

        try:
            skill_meta = read_skill_metadata(skill_file)
            suggested_name = suggest_skill_name_simple(plugin_path, skill_meta)

            # Handle duplicates
            original_name = suggested_name
            counter = 1
            while suggested_name in existing_names:
                suggested_name = f"{original_name}-{counter}"
                counter += 1

            mappings[plugin_path] = {
                'old_path': str(skill_file.relative_to(plugin_dir)),
                'new_skill_name': suggested_name,
                'new_path': f'skills/{suggested_name}/SKILL.md',
                'current_name': skill_meta.get('name', 'unknown'),
                'description': skill_meta.get('description', 'unknown')[:100]
            }

            existing_names.add(suggested_name)
            print(f"✅ {suggested_name}")

        except Exception as e:
            errors.append((plugin_path, str(e)))
            print(f"❌ Error: {e}")

    # Save mappings
    output_file = 'skill-name-mappings.json'
    with open(output_file, 'w') as f:
        json.dump(mappings, f, indent=2)

    print(f"\n✅ Analysis complete!")
    print(f"📄 Mappings saved to: {output_file}")
    print(f"📊 Stats:")
    print(f"   - Total plugins: {len(skills)}")
    print(f"   - Successfully analyzed: {len(mappings)}")
    print(f"   - Errors: {len(errors)}")
    print(f"   - Unique names: {len(existing_names)}")

    if errors:
        print(f"\n⚠️  Errors encountered:")
        for path, error in errors:
            print(f"   - {path}: {error}")

    # Show sample mappings
    print(f"\n📋 Sample mappings (first 10):")
    for i, (path, mapping) in enumerate(list(mappings.items())[:10], 1):
        print(f"   {i}. {path}")
        print(f"      Old: {mapping['old_path']}")
        print(f"      New: {mapping['new_path']}")
        print(f"      Name: {mapping['new_skill_name']}")
        print()

    # Show compliance check
    print(f"✅ Anthropic Compliance Check:")
    print(f"   - All names ≤ 64 chars: {all(len(m['new_skill_name']) <= 64 for m in mappings.values())}")
    print(f"   - All lowercase with hyphens: {all(m['new_skill_name'].replace('-', '').isalnum() for m in mappings.values())}")
    print(f"   - All unique: {len(existing_names) == len(mappings)}")

    print(f"\n✨ Ready for migration!")
    print(f"   Next step: Review {output_file} and run migration script")

if __name__ == '__main__':
    main()
