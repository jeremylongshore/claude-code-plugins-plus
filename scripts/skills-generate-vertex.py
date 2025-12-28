#!/usr/bin/env python3
"""
Vertex AI Gemini Skills Generator
Batch-generate Agent Skills for all 229 plugins using Vertex AI

Uses ccpi-web-app-prod project with Vertex AI Gemini 2.0 Flash
"""

import json
import os
import sys
from pathlib import Path
import time
from datetime import datetime

# Vertex AI SDK
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting

# Initialize Vertex AI
PROJECT_ID = "ccpi-web-app-prod"
LOCATION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.0-flash-exp")
    print(f"✅ Vertex AI initialized: {PROJECT_ID} / {LOCATION}")
except Exception as e:
    print(f"❌ Vertex AI init failed: {e}")
    print("\nRun: gcloud auth application-default login")
    sys.exit(1)

# Safety settings (allow creative output)
SAFETY_SETTINGS = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
]

def read_plugin_context(plugin_path):
    """Read plugin files to understand what it does"""
    base = Path(plugin_path)
    context = []

    # Read plugin.json
    plugin_json = base / '.claude-plugin' / 'plugin.json'
    if plugin_json.exists():
        context.append(f"=== plugin.json ===\n{plugin_json.read_text()}\n")

    # Read README (first 3000 chars)
    readme = base / 'README.md'
    if readme.exists():
        content = readme.read_text()[:3000]
        context.append(f"=== README.md ===\n{content}\n")

    # Sample commands
    commands_dir = base / 'commands'
    if commands_dir.exists():
        cmd_files = list(commands_dir.glob('*.md'))[:2]
        for cmd in cmd_files:
            context.append(f"=== Command: {cmd.name} ===\n{cmd.read_text()[:600]}\n")

    # Sample agents
    agents_dir = base / 'agents'
    if agents_dir.exists():
        agent_files = list(agents_dir.glob('*.md'))[:2]
        for agent in agent_files:
            context.append(f"=== Agent: {agent.name} ===\n{agent.read_text()[:600]}\n")

    return "\n".join(context)

def generate_skill_with_vertex(plugin_name, plugin_desc, plugin_category, plugin_path):
    """Use Vertex AI Gemini to generate SKILL.md"""

    context = read_plugin_context(plugin_path)

    prompt = f"""You are an expert at creating Agent Skills for Claude Code plugins.

PLUGIN DETAILS:
- Name: {plugin_name}
- Category: {plugin_category}
- Description: {plugin_desc}

PLUGIN FILES:
{context}

TASK: Generate a complete SKILL.md file that follows this EXACT format:

	---
	name: [Descriptive Skill Name - make it action-oriented]
	description: |
	  [Write 2-3 sentences explaining:
	   - WHEN this skill automatically activates (what triggers it)
	   - WHAT value it provides to the user
	   - WHY it's useful for this plugin's purpose]
	allowed-tools: "Read, Grep, Glob, Edit, Write, Bash(git:*), Bash(python:*)"
	---

## How It Works

[Explain the skill's workflow in 3-5 clear, actionable steps]

1. **[Step 1 Title]:** [What happens first]
2. **[Step 2 Title]:** [What happens second]
3. **[Step 3 Title]:** [What happens third]

## When This Skill Activates

This skill automatically activates when:
- [Trigger condition 1]
- [Trigger condition 2]
- [Trigger condition 3]

## Examples

### Example 1: [Realistic Use Case]
```
User: "[Natural language request that would trigger this skill]"

Skill activates and:
1. [Action taken]
2. [Result produced]
```

### Example 2: [Another Common Scenario]
```
User: "[Another natural request]"

Skill activates and:
1. [Action taken]
2. [Result produced]
```

## Tips & Best Practices
- **[Tip category 1]:** [Specific actionable tip]
- **[Tip category 2]:** [Another useful tip]
- **[Tip category 3]:** [Performance or workflow tip]

## Integration Notes
[How this skill works with other plugins or tools in the ecosystem]

REQUIREMENTS:
- Write in active, engaging voice
- Be SPECIFIC to this plugin's actual purpose (not generic)
- Examples must be realistic and match the plugin's domain
- Description should clearly explain auto-activation triggers
- Keep total length under 250 lines
- Use proper markdown formatting
- Make it immediately useful to users

Generate the complete SKILL.md content now:"""

    try:
        response = model.generate_content(
            prompt,
            safety_settings=SAFETY_SETTINGS,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 2048,
            }
        )
        return response.text
    except Exception as e:
        print(f"    ❌ Vertex AI error: {e}")
        return None

def update_keywords(plugin_path, marketplace_path):
    """Add agent-skills keyword to plugin.json and marketplace"""

    # Update plugin.json
    plugin_json_path = Path(plugin_path) / '.claude-plugin' / 'plugin.json'
    if plugin_json_path.exists():
        with open(plugin_json_path, 'r') as f:
            data = json.load(f)

        if 'keywords' not in data:
            data['keywords'] = []

        if 'agent-skills' not in data['keywords']:
            data['keywords'].append('agent-skills')

        with open(plugin_json_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')

    # Update marketplace.extended.json
    with open(marketplace_path, 'r') as f:
        marketplace = json.load(f)

    for plugin in marketplace['plugins']:
        if plugin['source'] == plugin_path:
            if 'keywords' not in plugin:
                plugin['keywords'] = []
            if 'agent-skills' not in plugin['keywords']:
                plugin['keywords'].append('agent-skills')
            break

    with open(marketplace_path, 'w') as f:
        json.dump(marketplace, f, indent=2)
        f.write('\n')

def process_plugin(plugin, repo_root, marketplace_extended, batch_num, total):
    """Process a single plugin"""
    plugin_path = repo_root / plugin['source'].lstrip('./')

    print(f"\n[{batch_num}/{total}] 🎯 {plugin['name']}")
    print(f"    Category: {plugin['category']}")

    # Check if already has skills
    if 'agent-skills' in plugin.get('keywords', []):
        print(f"    ⏭️  Already has agent-skills keyword")
        return False

    # Check if skills folder already exists
    skills_dir = plugin_path / 'skills'
    if skills_dir.exists():
        print(f"    ⏭️  Skills folder already exists")
        return False

    # Generate skill content
    print(f"    🤖 Generating with Vertex AI Gemini...")
    start = time.time()

    skill_content = generate_skill_with_vertex(
        plugin['name'],
        plugin['description'],
        plugin['category'],
        plugin_path
    )

    elapsed = time.time() - start

    if not skill_content:
        print(f"    ❌ Generation failed")
        return False

    # Create skills directory
    skill_adapter_dir = plugin_path / 'skills' / 'skill-adapter'
    skill_adapter_dir.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    skill_file = skill_adapter_dir / 'SKILL.md'
    skill_file.write_text(skill_content)
    print(f"    ✅ Created SKILL.md ({len(skill_content)} chars in {elapsed:.1f}s)")

    # Update keywords
    update_keywords(plugin['source'].lstrip('./'), marketplace_extended)
    print(f"    ✅ Updated keywords")

    return True

def main():
    repo_root = Path(__file__).parent.parent
    marketplace_file = repo_root / '.claude-plugin' / 'marketplace.json'
    marketplace_extended = repo_root / '.claude-plugin' / 'marketplace.extended.json'

    # Load marketplace
    with open(marketplace_file, 'r') as f:
        marketplace = json.load(f)

    # Priority categories
    priority_categories = ['devops', 'security', 'testing', 'ai-ml', 'performance', 'database']

    # Find plugins needing skills
    all_plugins_needing_skills = [
        p for p in marketplace['plugins']
        if 'agent-skills' not in p.get('keywords', [])
    ]

    priority_plugins = [
        p for p in all_plugins_needing_skills
        if p.get('category') in priority_categories
    ]

    print(f"""
╔════════════════════════════════════════════════════════════╗
║     Vertex AI Gemini Skills Generator (Pimp Mode)         ║
╚════════════════════════════════════════════════════════════╝

Project: {PROJECT_ID}
Model: Gemini 2.0 Flash Experimental
Location: {LOCATION}

📊 Status:
   Total plugins: {len(marketplace['plugins'])}
   Need skills: {len(all_plugins_needing_skills)}
   Priority (devops/security/testing/ai-ml/performance/database): {len(priority_plugins)}
   Others: {len(all_plugins_needing_skills) - len(priority_plugins)}
""")

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--priority':
            # Process all priority plugins
            print(f"\n🚀 PIMP MODE: Processing all {len(priority_plugins)} priority plugins\n")
            success_count = 0

            for i, plugin in enumerate(priority_plugins, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(priority_plugins)):
                    success_count += 1
                time.sleep(0.5)  # Rate limiting

            print(f"\n✅ Processed {success_count}/{len(priority_plugins)} priority plugins!")

        elif arg == '--all':
            # Process ALL plugins
            print(f"\n🚀 ULTRA PIMP MODE: Processing ALL {len(all_plugins_needing_skills)} plugins\n")
            success_count = 0

            for i, plugin in enumerate(all_plugins_needing_skills, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(all_plugins_needing_skills)):
                    success_count += 1
                time.sleep(0.5)  # Rate limiting

            print(f"\n✅ Processed {success_count}/{len(all_plugins_needing_skills)} plugins!")

        elif arg.isdigit():
            # Process N plugins
            n = int(arg)
            targets = all_plugins_needing_skills[:n]
            print(f"\n🚀 Processing {n} plugins\n")
            success_count = 0

            for i, plugin in enumerate(targets, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(targets)):
                    success_count += 1
                time.sleep(0.5)

            print(f"\n✅ Processed {success_count}/{len(targets)} plugins!")

        else:
            # Process specific plugin
            plugin = next((p for p in all_plugins_needing_skills if p['name'] == arg), None)
            if plugin:
                process_plugin(plugin, repo_root, marketplace_extended, 1, 1)
            else:
                print(f"❌ Plugin '{arg}' not found or already has skills")
                return

    else:
        # Show options
        print("""
Usage:
  python3 scripts/vertex-skills-generator.py [option]

Options:
  --priority              Process all priority category plugins (devops, security, testing, ai-ml)
  --all                   Process ALL plugins (ULTRA PIMP MODE)
  <number>                Process next N plugins
  <plugin-name>           Process specific plugin
  (no args)               Show this help

Examples:
  python3 scripts/vertex-skills-generator.py --priority
  python3 scripts/vertex-skills-generator.py 20
  python3 scripts/vertex-skills-generator.py deployment-pipeline
""")
        return

    # Always remind to sync
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                    NEXT STEPS                              ║
╚════════════════════════════════════════════════════════════╝

1. Sync marketplace:
   node scripts/sync-marketplace.cjs

2. Review generated skills:
   find plugins -name "SKILL.md" -newer /tmp -exec head -30 {{}} \\;

3. Commit:
   git add .
   git commit -m "feat(skills): batch generate Agent Skills via Vertex AI"
   git push

4. Deploy marketplace:
   cd marketplace && npm run build && firebase deploy
""")

if __name__ == '__main__':
    main()
