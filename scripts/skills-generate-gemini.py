#!/usr/bin/env python3
"""
Generate Agent Skills for plugins using Google Gemini
Uses your existing GCP setup - no Claude Code limits!
"""

import json
import os
import sys
from pathlib import Path
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Fast and cheap!

def read_plugin_context(plugin_path):
    """Read plugin files to understand what it does"""
    base = Path(plugin_path)
    context = []

    # Read plugin.json
    plugin_json = base / '.claude-plugin' / 'plugin.json'
    if plugin_json.exists():
        context.append(f"=== plugin.json ===\n{plugin_json.read_text()}\n")

    # Read README
    readme = base / 'README.md'
    if readme.exists():
        # Only first 2000 chars to save tokens
        content = readme.read_text()[:2000]
        context.append(f"=== README.md (excerpt) ===\n{content}\n")

    # Check for commands/agents
    commands_dir = base / 'commands'
    agents_dir = base / 'agents'

    if commands_dir.exists():
        cmd_files = list(commands_dir.glob('*.md'))[:3]  # Max 3 examples
        for cmd in cmd_files:
            context.append(f"=== {cmd.name} ===\n{cmd.read_text()[:500]}\n")

    if agents_dir.exists():
        agent_files = list(agents_dir.glob('*.md'))[:3]
        for agent in agent_files:
            context.append(f"=== {agent.name} ===\n{agent.read_text()[:500]}\n")

    return "\n".join(context)

def generate_skill(plugin_name, plugin_desc, plugin_category, plugin_path):
    """Use Gemini to generate SKILL.md content"""

    context = read_plugin_context(plugin_path)

    prompt = f"""You are an expert at creating Agent Skills for Claude Code plugins.

Plugin Details:
- Name: {plugin_name}
- Category: {plugin_category}
- Description: {plugin_desc}

Plugin Files Context:
{context}

Generate a SKILL.md file that follows this EXACT format:

	---
	name: [Descriptive Skill Name]
	description: |
	  [2-3 sentences explaining WHEN this skill activates automatically and WHAT it does.
	  Focus on the trigger conditions and the value it provides.]
	allowed-tools: "Read, Grep, Glob, Edit, Write, Bash(git:*), Bash(python:*)"
	---

## How It Works

[Explain the skill's workflow in 3-5 clear steps. Be specific about what the skill does.]

1. [First step]
2. [Second step]
3. [Third step]

## Examples

### Example 1: [Common Use Case Title]
```
[Show realistic example of when this skill would activate]
```

### Example 2: [Another Use Case Title]
```
[Another example]
```

## Tips
- [Practical tip 1]
- [Practical tip 2]
- [Practical tip 3]

IMPORTANT:
- Write in active voice
- Be specific to THIS plugin's purpose
- Examples should be realistic, not generic
- Description should explain WHEN it auto-activates
- Keep it under 200 lines total
- Use proper markdown formatting

Generate the SKILL.md content now:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini error: {e}")
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

        print(f"  ✅ Updated {plugin_json_path}")

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

    print(f"  ✅ Updated marketplace.extended.json")

def main():
    repo_root = Path(__file__).parent.parent
    marketplace_file = repo_root / '.claude-plugin' / 'marketplace.json'
    marketplace_extended = repo_root / '.claude-plugin' / 'marketplace.extended.json'

    # Check for API key
    if not os.environ.get('GOOGLE_API_KEY') and not os.environ.get('GEMINI_API_KEY'):
        print("❌ Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        print("   export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    # Load marketplace
    with open(marketplace_file, 'r') as f:
        marketplace = json.load(f)

    # Find plugins needing skills (high priority categories)
    priority_categories = ['devops', 'security', 'testing', 'ai-ml']

    plugins_needing_skills = [
        p for p in marketplace['plugins']
        if 'agent-skills' not in p.get('keywords', [])
        and p.get('category') in priority_categories
    ]

    print(f"📊 Found {len(plugins_needing_skills)} plugins needing skills in priority categories")
    print(f"   (devops, security, testing, ai-ml)")
    print()

    # Process argument
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            # Batch mode
            count = 0
            for plugin in plugins_needing_skills[:20]:  # Max 20 at a time
                print(f"\n🎯 Processing {plugin['name']}...")
                process_plugin(plugin, repo_root, marketplace_extended)
                count += 1

            print(f"\n✅ Processed {count} plugins!")
            print(f"   Run 'node scripts/sync-marketplace.cjs' to sync CLI catalog")

        elif sys.argv[1].isdigit():
            # Process N plugins
            n = int(sys.argv[1])
            for plugin in plugins_needing_skills[:n]:
                print(f"\n🎯 Processing {plugin['name']}...")
                process_plugin(plugin, repo_root, marketplace_extended)

            print(f"\n✅ Processed {n} plugins!")
            print(f"   Run 'node scripts/sync-marketplace.cjs' to sync CLI catalog")

        else:
            # Process specific plugin by name
            plugin = next((p for p in plugins_needing_skills if p['name'] == sys.argv[1]), None)
            if plugin:
                process_plugin(plugin, repo_root, marketplace_extended)
                print(f"\n✅ Done! Run 'node scripts/sync-marketplace.cjs' to sync")
            else:
                print(f"❌ Plugin '{sys.argv[1]}' not found or already has skills")

    else:
        # Interactive mode - process one
        if not plugins_needing_skills:
            print("✅ All priority plugins have skills!")
            return

        plugin = plugins_needing_skills[0]
        print(f"🎯 Next plugin: {plugin['name']}")
        print(f"   Category: {plugin['category']}")
        print(f"   Description: {plugin['description']}")
        print()

        response = input("Process this plugin? [y/N]: ")
        if response.lower() == 'y':
            process_plugin(plugin, repo_root, marketplace_extended)
            print(f"\n✅ Done! Run 'node scripts/sync-marketplace.cjs' to sync")

def process_plugin(plugin, repo_root, marketplace_extended):
    """Process a single plugin"""
    plugin_path = repo_root / plugin['source'].lstrip('./')

    # Generate skill content
    print(f"  🤖 Generating skill with Gemini...")
    skill_content = generate_skill(
        plugin['name'],
        plugin['description'],
        plugin['category'],
        plugin_path
    )

    if not skill_content:
        print(f"  ❌ Failed to generate skill")
        return

    # Create skills directory
    skills_dir = plugin_path / 'skills' / 'skill-adapter'
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    skill_file = skills_dir / 'SKILL.md'
    skill_file.write_text(skill_content)
    print(f"  ✅ Created {skill_file}")

    # Update keywords
    update_keywords(plugin['source'].lstrip('./'), marketplace_extended)

    print(f"  ✅ {plugin['name']} complete!")

if __name__ == '__main__':
    main()
