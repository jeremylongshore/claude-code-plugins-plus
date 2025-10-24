#!/usr/bin/env python3
"""
Analyze all plugins and suggest compliant skill directory names using Vertex AI Gemini.

This script:
1. Scans all plugins with skills/skill-adapter/ structure
2. Reads each SKILL.md to understand purpose
3. Uses Gemini to suggest concise, descriptive directory names
4. Generates mapping file for migration

Compliance Target: Anthropic Agent Skills specification
- Structure: skills/{descriptive-name}/SKILL.md (not skills/skill-adapter/SKILL.md)
- Name should be clear, concise, and describe function (not generic)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import vertexai
from vertexai.generative_models import GenerativeModel

# Configure Vertex AI with Application Default Credentials
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'hustleapp-production')
vertexai.init(project=project_id, location='us-central1')
model = GenerativeModel('gemini-1.5-flash')  # Gemini Flash model

def find_all_skills() -> List[Tuple[Path, Path]]:
    """Find all plugins with skills/skill-adapter/SKILL.md structure"""
    plugins_dir = Path('plugins')
    skills = []

    for skill_file in plugins_dir.rglob('skills/skill-adapter/SKILL.md'):
        plugin_dir = skill_file.parent.parent.parent  # Go up from SKILL.md -> skill-adapter -> skills -> plugin
        skills.append((plugin_dir, skill_file))

    return skills

def read_skill_metadata(skill_file: Path) -> Dict[str, str]:
    """Extract YAML frontmatter from SKILL.md"""
    content = skill_file.read_text()

    # Simple YAML parsing (assumes clean format)
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
                    # Multi-line description continuation
                    last_key = list(metadata.keys())[-1]
                    metadata[last_key] += ' ' + line.strip()
            return metadata

    return {}

def read_plugin_metadata(plugin_dir: Path) -> Dict[str, str]:
    """Read plugin.json for additional context"""
    plugin_json = plugin_dir / '.claude-plugin' / 'plugin.json'
    if plugin_json.exists():
        try:
            return json.loads(plugin_json.read_text())
        except:
            pass
    return {}

def suggest_skill_name(plugin_path: str, skill_metadata: Dict, plugin_metadata: Dict, existing_names: set) -> str:
    """Use Gemini to suggest optimal skill directory name"""

    prompt = f"""You are an expert at naming things clearly and concisely for developer tools.

TASK: Suggest ONE ideal directory name for this Claude Code Agent Skill.

PLUGIN INFO:
- Plugin Path: {plugin_path}
- Current Skill Name: {skill_metadata.get('name', 'unknown')}
- Skill Description: {skill_metadata.get('description', 'unknown')}
- Plugin Category: {plugin_metadata.get('category', 'unknown')}

REQUIREMENTS:
1. **Concise**: 2-3 words maximum (prefer 2)
2. **Descriptive**: Clearly conveys what the skill DOES (action-oriented)
3. **Professional**: Use kebab-case (lowercase with hyphens)
4. **Unique**: Must not be one of these existing names: {sorted(list(existing_names))}
5. **Not redundant**: Don't include "skill", "agent", or "claude" in name
6. **Semantic**: Focus on the FUNCTION not the tool name

EXAMPLES:
- Plugin "security-test-scanner" → "vulnerability-scanner" (describes action)
- Plugin "github-pr-helper" → "pull-request-assistant" (clear function)
- Plugin "database-optimizer" → "query-optimizer" (specific action)

BAD examples:
- "security-test-scanner-skill" ❌ (redundant, includes "skill")
- "helper" ❌ (too vague)
- "github-integration" ❌ (describes category not function)

OUTPUT FORMAT:
Respond with ONLY the suggested directory name, nothing else.
Example: "vulnerability-scanner"
"""

    try:
        response = model.generate_content(prompt)
        suggested = response.candidates[0].content.parts[0].text.strip().lower().replace(' ', '-')

        # Clean up response (remove quotes, extra text)
        suggested = suggested.split('\n')[0]  # First line only
        suggested = suggested.replace('"', '').replace("'", "")

        # Validate format (kebab-case, alphanumeric + hyphens only)
        if not all(c.isalnum() or c == '-' for c in suggested):
            # Fallback: use plugin dir name
            return Path(plugin_path).name

        # Ensure uniqueness
        if suggested in existing_names:
            # Append category if collision
            category = plugin_metadata.get('category', 'tool')
            suggested = f"{suggested}-{category}"

        return suggested

    except Exception as e:
        print(f"⚠️  Gemini error for {plugin_path}: {e}", file=sys.stderr)
        # Fallback: use plugin directory name
        return Path(plugin_path).name

def main():
    """Analyze all skills and generate mapping file"""

    print("🔍 Finding all plugins with skills/skill-adapter/ structure...")
    skills = find_all_skills()
    print(f"✅ Found {len(skills)} plugins to migrate\n")

    if not skills:
        print("❌ No plugins found with skills/skill-adapter/ structure")
        sys.exit(1)

    print("🤖 Analyzing with Vertex AI Gemini (free tier)...")
    print("   This may take 2-3 minutes for 164 plugins\n")

    mappings = {}
    existing_names = set()
    errors = []

    for i, (plugin_dir, skill_file) in enumerate(skills, 1):
        plugin_path = str(plugin_dir.relative_to('plugins'))

        print(f"[{i}/{len(skills)}] {plugin_path}... ", end='', flush=True)

        try:
            skill_meta = read_skill_metadata(skill_file)
            plugin_meta = read_plugin_metadata(plugin_dir)

            suggested_name = suggest_skill_name(plugin_path, skill_meta, plugin_meta, existing_names)

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
    print(f"\n📋 Sample mappings (first 5):")
    for i, (path, mapping) in enumerate(list(mappings.items())[:5], 1):
        print(f"   {i}. {path}")
        print(f"      Old: {mapping['old_path']}")
        print(f"      New: {mapping['new_path']}")
        print(f"      Name: {mapping['new_skill_name']}")
        print()

    print(f"✨ Ready for manual review!")
    print(f"   Next step: Review {output_file} and validate names")

if __name__ == '__main__':
    main()
