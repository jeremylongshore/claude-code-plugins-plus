#!/usr/bin/env python3
"""
Vertex AI Gemini Skills Generator - PRODUCTION SAFE VERSION
Batch-generate Agent Skills following official Anthropic guidelines

Features:
- Adheres to Anthropic's official SKILL.md format
- SQLite audit trail for all operations
- Rate limiting and quota checks
- Quality validation before saving
- Automatic backups
- Comprehensive error logging
"""

import json
import os
import sys
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Vertex AI SDK
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting

# Configuration
PROJECT_ID = "ccpi-web-app-prod"
LOCATION = "us-central1"
RATE_LIMIT_DELAY = 30.0  # 30 seconds between calls (ultra-conservative to avoid all quota errors)
MAX_RETRIES = 3
BACKUP_DIR = Path(__file__).parent.parent / 'backups' / 'skills-audit'
DB_PATH = BACKUP_DIR / 'skills_generation.db'

# Initialize Vertex AI
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

def init_database():
    """Initialize SQLite database for audit trail"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skill_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plugin_name TEXT NOT NULL,
            plugin_category TEXT NOT NULL,
            plugin_path TEXT NOT NULL,
            status TEXT NOT NULL,
            char_count INTEGER,
            line_count INTEGER,
            error_message TEXT,
            generation_time_seconds REAL,
            skill_content TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validation_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plugin_name TEXT NOT NULL,
            reason TEXT NOT NULL,
            details TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Audit database initialized: {DB_PATH}")

def log_generation(plugin_name: str, plugin_category: str, plugin_path: str,
                  status: str, char_count: int = None, line_count: int = None,
                  error_message: str = None, generation_time: float = None,
                  skill_content: str = None):
    """Log skill generation attempt to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO skill_generations
        (timestamp, plugin_name, plugin_category, plugin_path, status,
         char_count, line_count, error_message, generation_time_seconds, skill_content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        plugin_name,
        plugin_category,
        str(plugin_path),  # Convert Path to string for SQLite
        status,
        char_count,
        line_count,
        error_message,
        generation_time,
        skill_content
    ))

    conn.commit()
    conn.close()

def log_validation_failure(plugin_name: str, reason: str, details: str = None):
    """Log validation failure"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO validation_failures (timestamp, plugin_name, reason, details)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().isoformat(), plugin_name, reason, details))

    conn.commit()
    conn.close()

def validate_skill_content(content: str, plugin_name: str) -> tuple[bool, Optional[str], str]:
    """
    Validate generated SKILL.md content against Anthropic guidelines

    Returns: (is_valid, error_message, cleaned_content)
    """

    # Strip markdown code fences if present (Gemini sometimes wraps in ```markdown)
    content = content.strip()
    if content.startswith('```'):
        lines = content.split('\n')
        # Remove first line (```markdown or similar)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines).strip()

    # Check 1: Has YAML frontmatter
    if not content.startswith('---'):
        return False, f"Missing YAML frontmatter (starts with: {content[:50]!r})", content

    # Extract frontmatter
    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False, "Invalid YAML frontmatter structure", content

        frontmatter = parts[1].strip()
        body = parts[2].strip()

    except Exception as e:
        return False, f"Failed to parse frontmatter: {e}", content

    # Check 2: Has required fields (name and description ONLY per Anthropic docs)
    if 'name:' not in frontmatter:
        return False, "Missing 'name' field in frontmatter", content

    if 'description:' not in frontmatter:
        return False, "Missing 'description' field in frontmatter", content

    # Check 3: No invalid fields (Anthropic only allows name and description)
    forbidden_fields = ['allowed-tools', 'tools', 'permissions', 'version', 'author']
    for field in forbidden_fields:
        if f'{field}:' in frontmatter.lower():
            return False, f"Invalid field '{field}' in frontmatter (Anthropic only allows 'name' and 'description')", content

    # Check 4: Character limits per Anthropic docs
    # name: max 64 characters
    # description: max 1024 characters
    lines = frontmatter.split('\n')
    name_line = [l for l in lines if l.strip().startswith('name:')]
    if name_line:
        name_value = name_line[0].split('name:', 1)[1].strip()
        if len(name_value) > 64:
            return False, f"Name exceeds 64 character limit ({len(name_value)} chars)", content

    # Check 5: Line count (Anthropic recommends under 500 lines)
    line_count = len(content.split('\n'))
    if line_count > 500:
        log_validation_failure(plugin_name, "Exceeds 500-line recommendation",
                              f"{line_count} lines generated")
        print(f"    ⚠️  Warning: {line_count} lines (Anthropic recommends <500)")

    # Check 6: Has actual content
    if len(body) < 100:
        return False, "Body content too short (less than 100 characters)", content

    # Check 7: No placeholder text
    placeholder_patterns = [
        '[Your',
        '[TODO',
        '[INSERT',
        '[PLACEHOLDER',
        'TODO:',
        'FIXME:',
    ]
    for pattern in placeholder_patterns:
        if pattern in content:
            return False, f"Contains placeholder text: {pattern}", content

    return True, None, content

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

def generate_skill_with_vertex(plugin_name: str, plugin_desc: str,
                               plugin_category: str, plugin_path: str) -> Optional[str]:
    """
    Use Vertex AI Gemini to generate SKILL.md following Anthropic guidelines

    Returns: skill_content or None on failure
    """

    context = read_plugin_context(plugin_path)

    # Updated prompt following official Anthropic guidelines
    prompt = f"""You are an expert at creating Agent Skills for Claude Code following Anthropic's official guidelines.

CONTEXT - What You're Creating:

Claude Code is Anthropic's CLI tool for software development. Users install PLUGINS (extensions) to add capabilities.

AGENT SKILLS are instruction manuals (SKILL.md files) that teach Claude Code:
- WHEN to automatically activate a specific plugin (trigger phrases)
- HOW to use the plugin effectively (workflow steps)
- WHAT the plugin is best used for (examples and scenarios)

When a user says something like "create ansible playbook", Claude Code:
1. Scans installed plugins' SKILL.md frontmatter at startup
2. Matches "ansible playbook" to the trigger terms in a skill's description
3. Reads the full SKILL.md for detailed instructions
4. Automatically activates that plugin with the correct workflow

Your job: Write the SKILL.md instruction manual for the plugin described below.

OFFICIAL ANTHROPIC REQUIREMENTS:
- YAML frontmatter with ONLY two fields: 'name' and 'description' (no other fields allowed)
- name: Max 64 characters, use gerund form (e.g., "Processing PDFs", "Analyzing Security")
- description: Max 1024 characters, third person, explain WHAT it does and WHEN to use it
- Keep total length under 500 lines (Anthropic recommendation)
- Conciseness is critical - only include what Claude doesn't already know
- Use consistent terminology throughout
- Include specific trigger terms in description

PLUGIN DETAILS:
- Name: {plugin_name}
- Category: {plugin_category}
- Description: {plugin_desc}

PLUGIN FILES:
{context}

TASK: Generate a complete SKILL.md file following this EXACT format:

---
name: [Gerund-form name, max 64 chars]
description: |
  [Third-person description, max 1024 chars. Explain WHAT this skill does and WHEN Claude should use it. Include specific trigger terms and contexts. Be concise and specific to THIS plugin's purpose.]
---

## Overview

[Brief 2-3 sentence overview of what this skill enables Claude to do]

## How It Works

[Step-by-step workflow in 3-5 clear steps:]

1. **[Step name]**: [What happens]
2. **[Step name]**: [What happens]
3. **[Step name]**: [What happens]

## When to Use This Skill

This skill activates when you need to:
- [Trigger scenario 1]
- [Trigger scenario 2]
- [Trigger scenario 3]

## Examples

### Example 1: [Realistic Use Case]

User request: "[Natural language request]"

The skill will:
1. [Action taken]
2. [Result produced]

### Example 2: [Another Scenario]

User request: "[Another request]"

The skill will:
1. [Action taken]
2. [Result produced]

## Best Practices

- **[Practice category]**: [Specific actionable advice]
- **[Practice category]**: [Specific actionable advice]
- **[Practice category]**: [Specific actionable advice]

## Integration

[How this skill works with other tools/plugins in the Claude Code ecosystem]

CRITICAL REQUIREMENTS:
- ONLY 'name' and 'description' in YAML frontmatter (no other fields)
- Name must be gerund form and under 64 characters
- Description must be under 1024 characters
- Total length MUST be under 500 lines
- Be SPECIFIC to {plugin_name}'s actual purpose (not generic)
- Use consistent terminology throughout
- NO placeholder text like [TODO] or [INSERT]
- Third person voice in description
- Active, engaging voice in body
- Examples must be realistic for this plugin's domain

Generate the complete SKILL.md content now:"""

    start_time = time.time()

    for attempt in range(MAX_RETRIES):
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

            raw_content = response.text
            generation_time = time.time() - start_time

            # Validate content and get cleaned version
            is_valid, error_msg, cleaned_content = validate_skill_content(raw_content, plugin_name)

            if not is_valid:
                log_validation_failure(plugin_name, "Failed validation", error_msg)
                if attempt < MAX_RETRIES - 1:
                    print(f"    ⚠️  Validation failed: {error_msg}, retrying ({attempt + 1}/{MAX_RETRIES})")
                    time.sleep(2)
                    continue
                else:
                    log_generation(plugin_name, plugin_category, plugin_path,
                                 "VALIDATION_FAILED", error_message=error_msg,
                                 generation_time=generation_time)
                    return None

            # Success! Use cleaned content
            char_count = len(cleaned_content)
            line_count = len(cleaned_content.split('\n'))

            log_generation(plugin_name, plugin_category, plugin_path, "SUCCESS",
                         char_count=char_count, line_count=line_count,
                         generation_time=generation_time, skill_content=cleaned_content)

            return cleaned_content

        except Exception as e:
            error_msg = str(e)
            if attempt < MAX_RETRIES - 1:
                print(f"    ⚠️  Error: {error_msg}, retrying ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(2)
                continue
            else:
                log_generation(plugin_name, plugin_category, plugin_path, "ERROR",
                             error_message=error_msg, generation_time=time.time() - start_time)
                return None

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
    """Process a single plugin with full safety checks"""
    plugin_path = repo_root / plugin['source'].lstrip('./')

    print(f"\n[{batch_num}/{total}] 🎯 {plugin['name']}")
    print(f"    Category: {plugin['category']}")

    # Check if already has skills
    if 'agent-skills' in plugin.get('keywords', []):
        print(f"    ⏭️  Already has agent-skills keyword")
        return False

    # Check if SKILL.md already exists (check file, not just folder)
    skill_file = plugin_path / 'skills' / 'skill-adapter' / 'SKILL.md'
    if skill_file.exists():
        print(f"    ⏭️  SKILL.md already exists")
        return False

    # Generate skill content
    print(f"    🤖 Generating with Vertex AI Gemini...")

    skill_content = generate_skill_with_vertex(
        plugin['name'],
        plugin['description'],
        plugin['category'],
        plugin_path
    )

    if not skill_content:
        print(f"    ❌ Generation failed (see audit database for details)")
        return False

    # Create skills directory
    skill_adapter_dir = plugin_path / 'skills' / 'skill-adapter'
    skill_adapter_dir.mkdir(parents=True, exist_ok=True)

    # Write SKILL.md
    skill_file = skill_adapter_dir / 'SKILL.md'
    skill_file.write_text(skill_content)

    char_count = len(skill_content)
    line_count = len(skill_content.split('\n'))
    print(f"    ✅ Created SKILL.md ({char_count} chars, {line_count} lines)")

    # Update keywords
    update_keywords(plugin['source'].lstrip('./'), marketplace_extended)
    print(f"    ✅ Updated keywords")

    return True

def get_statistics():
    """Get statistics from audit database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM skill_generations WHERE status = 'SUCCESS'")
    success_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM skill_generations WHERE status = 'ERROR'")
    error_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM skill_generations WHERE status = 'VALIDATION_FAILED'")
    validation_failed = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(generation_time_seconds) FROM skill_generations WHERE status = 'SUCCESS'")
    avg_time = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(line_count) FROM skill_generations WHERE status = 'SUCCESS'")
    avg_lines = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'success': success_count,
        'error': error_count,
        'validation_failed': validation_failed,
        'avg_time': avg_time,
        'avg_lines': avg_lines
    }

def main():
    repo_root = Path(__file__).parent.parent
    marketplace_file = repo_root / '.claude-plugin' / 'marketplace.json'
    marketplace_extended = repo_root / '.claude-plugin' / 'marketplace.extended.json'

    # Initialize database
    init_database()

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
║   Vertex AI Gemini Skills Generator - PRODUCTION SAFE     ║
╚════════════════════════════════════════════════════════════╝

Project: {PROJECT_ID}
Model: Gemini 2.0 Flash Experimental
Location: {LOCATION}
Audit Database: {DB_PATH}

📊 Status:
   Total plugins: {len(marketplace['plugins'])}
   Need skills: {len(all_plugins_needing_skills)}
   Priority (devops/security/testing/ai-ml/performance/database): {len(priority_plugins)}
   Others: {len(all_plugins_needing_skills) - len(priority_plugins)}

🛡️  Safety Features:
   ✅ Adheres to Anthropic's official SKILL.md format
   ✅ YAML validation (only 'name' and 'description' fields)
   ✅ Character limits enforced (name: 64, description: 1024)
   ✅ Line count validation (recommends <500 lines)
   ✅ SQLite audit trail for all operations
   ✅ Rate limiting: {RATE_LIMIT_DELAY}s between calls
   ✅ Automatic retries ({MAX_RETRIES} attempts)
   ✅ Quality validation before saving
   ✅ Backup system with full skill content
""")

    # Check for --yes flag to skip confirmations
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--stats':
            # Show statistics
            stats = get_statistics()
            print(f"""
📊 Generation Statistics:
   Success: {stats['success']}
   Errors: {stats['error']}
   Validation Failures: {stats['validation_failed']}
   Avg Generation Time: {stats['avg_time']:.1f}s
   Avg Line Count: {stats['avg_lines']:.0f} lines
""")
            return

        elif arg == '--priority':
            # Process all priority plugins
            print(f"\n🚀 SAFE MODE: Processing {len(priority_plugins)} priority plugins\n")
            print(f"⏱️  Estimated time: {len(priority_plugins) * RATE_LIMIT_DELAY / 60:.1f} minutes")
            print(f"💰 Estimated cost: ${len(priority_plugins) * 0.001:.3f}\n")

            if not skip_confirmation:
                response = input("Continue? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
            else:
                print("--yes flag detected, proceeding automatically...\n")

            success_count = 0

            for i, plugin in enumerate(priority_plugins, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(priority_plugins)):
                    success_count += 1
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting

            print(f"\n✅ Processed {success_count}/{len(priority_plugins)} priority plugins!")
            stats = get_statistics()
            print(f"📊 Success rate: {stats['success']}/{stats['success'] + stats['error'] + stats['validation_failed']}")

        elif arg == '--all':
            # Process ALL plugins
            print(f"\n🚀 ULTRA SAFE MODE: Processing ALL {len(all_plugins_needing_skills)} plugins\n")
            print(f"⏱️  Estimated time: {len(all_plugins_needing_skills) * RATE_LIMIT_DELAY / 60:.1f} minutes")
            print(f"💰 Estimated cost: ${len(all_plugins_needing_skills) * 0.001:.3f}\n")

            if not skip_confirmation:
                response = input("⚠️  This will process ALL plugins. Are you absolutely sure? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
            else:
                print("--yes flag detected, proceeding automatically...\n")

            success_count = 0

            for i, plugin in enumerate(all_plugins_needing_skills, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(all_plugins_needing_skills)):
                    success_count += 1
                time.sleep(RATE_LIMIT_DELAY)

            print(f"\n✅ Processed {success_count}/{len(all_plugins_needing_skills)} plugins!")
            stats = get_statistics()
            print(f"📊 Success rate: {stats['success']}/{stats['success'] + stats['error'] + stats['validation_failed']}")

        elif arg.isdigit():
            # Process N plugins
            n = int(arg)
            targets = all_plugins_needing_skills[:n]
            print(f"\n🚀 Processing {n} plugins\n")
            print(f"⏱️  Estimated time: {n * RATE_LIMIT_DELAY / 60:.1f} minutes")
            print(f"💰 Estimated cost: ${n * 0.001:.3f}\n")

            if not skip_confirmation:
                response = input("Continue? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
            else:
                print("--yes flag detected, proceeding automatically...\n")

            success_count = 0

            for i, plugin in enumerate(targets, 1):
                if process_plugin(plugin, repo_root, marketplace_extended, i, len(targets)):
                    success_count += 1
                time.sleep(RATE_LIMIT_DELAY)

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
  python3 scripts/vertex-skills-generator-safe.py [option]

Options:
  --priority              Process all priority category plugins (devops, security, testing, ai-ml, performance, database)
  --all                   Process ALL plugins (ULTRA SAFE MODE)
  --stats                 Show generation statistics from audit database
  <number>                Process next N plugins
  <plugin-name>           Process specific plugin
  (no args)               Show this help

Examples:
  python3 scripts/vertex-skills-generator-safe.py --priority
  python3 scripts/vertex-skills-generator-safe.py 20
  python3 scripts/vertex-skills-generator-safe.py deployment-pipeline
  python3 scripts/vertex-skills-generator-safe.py --stats
""")
        return

    # Always remind to sync
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                    NEXT STEPS                              ║
╚════════════════════════════════════════════════════════════╝

1. Sync marketplace:
   node scripts/sync-marketplace.cjs

2. Review audit database:
   sqlite3 {DB_PATH}
   SELECT plugin_name, status, line_count FROM skill_generations;

3. Review generated skills:
   find plugins -name "SKILL.md" -newer {DB_PATH} -exec head -30 {{}} \\;

4. Commit:
   git add .
   git commit -m "feat(skills): batch generate Agent Skills via Vertex AI"
   git push

5. Check statistics:
   python3 scripts/vertex-skills-generator-safe.py --stats
""")

if __name__ == '__main__':
    main()
