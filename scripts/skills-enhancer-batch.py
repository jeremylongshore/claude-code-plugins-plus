#!/usr/bin/env python3
"""
Overnight Plugin Enhancement System
Analyzes ALL plugins against Anthropic standards and automatically enhances them
Uses Vertex AI Gemini (free tier) to run overnight batch enhancements

Process:
1. Analyze plugin structure
2. Compare against Anthropic standards
3. Identify missing pieces
4. Generate enhancements
5. Validate and backup
6. Update plugin files

Author: Intent Solutions IO
"""

import json
import os
import sys
import sqlite3
import time
import shutil
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Vertex AI SDK
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Part

# Configuration
PROJECT_ID = "ccpi-web-app-prod"
LOCATION = "us-central1"
RATE_LIMIT_DELAY = 45.0  # 45 seconds base delay (conservative but faster)
RATE_LIMIT_RANDOMNESS = 15.0  # Add 0-15 seconds random variation
MAX_RETRIES = 3
BACKUP_DIR = Path(__file__).parent.parent / 'backups' / 'plugin-enhancements'
DB_PATH = BACKUP_DIR / 'enhancements.db'
STANDARDS_DOC = Path(__file__).parent.parent / 'claudes-docs' / 'anthropic-skills-comparison-2025-10-19.md'

# Plugin categories to process (ALL CATEGORIES - 236 plugins)
CATEGORIES = [
    'productivity', 'security', 'testing', 'packages', 'examples', 'community', 'mcp',
    'ai-agency', 'ai-ml', 'api-development', 'crypto', 'database', 'devops',
    'fairdb-operations-kit', 'finance', 'performance', 'skill-enhancers'
]

class PluginEnhancer:
    def __init__(self):
        """Initialize Vertex AI and database"""
        self.init_vertex_ai()
        self.init_database()
        self.load_standards()

    def init_vertex_ai(self):
        """Initialize Vertex AI Gemini"""
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.model = GenerativeModel("gemini-2.0-flash-exp")
            print(f"✅ Vertex AI initialized: {PROJECT_ID} / {LOCATION}")
        except Exception as e:
            print(f"❌ Vertex AI init failed: {e}")
            print("\nRun: gcloud auth application-default login")
            sys.exit(1)

    def init_database(self):
        """Initialize SQLite audit database"""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhancements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                plugin_name TEXT NOT NULL,
                plugin_path TEXT NOT NULL,
                enhancement_type TEXT NOT NULL,
                status TEXT NOT NULL,
                analysis_results TEXT,
                changes_made TEXT,
                error_message TEXT,
                processing_time_seconds REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                plugin_name TEXT NOT NULL,
                score_before INTEGER,
                score_after INTEGER,
                improvements TEXT
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✅ Audit database initialized: {DB_PATH}")

    def load_standards(self):
        """Load Anthropic standards document"""
        if not STANDARDS_DOC.exists():
            print(f"❌ Standards document not found: {STANDARDS_DOC}")
            sys.exit(1)

        with open(STANDARDS_DOC, 'r') as f:
            self.standards = f.read()

        print(f"✅ Loaded standards document ({len(self.standards)} chars)")

    def find_all_plugins(self) -> List[Dict[str, Any]]:
        """Find all plugins in the repository"""
        plugins = []
        plugins_dir = Path(__file__).parent.parent / 'plugins'

        for category in CATEGORIES:
            category_dir = plugins_dir / category
            if not category_dir.exists():
                continue

            for plugin_dir in category_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                plugin_json = plugin_dir / '.claude-plugin' / 'plugin.json'
                if not plugin_json.exists():
                    continue

                with open(plugin_json, 'r') as f:
                    metadata = json.load(f)

                plugins.append({
                    'name': metadata.get('name', plugin_dir.name),
                    'path': str(plugin_dir),
                    'category': category,
                    'metadata': metadata
                })

        print(f"✅ Found {len(plugins)} plugins")
        return plugins

    def analyze_plugin(self, plugin: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a plugin against Anthropic standards"""
        plugin_path = Path(plugin['path'])

        # Read plugin structure
        structure = {
            'has_readme': (plugin_path / 'README.md').exists(),
            'has_plugin_json': (plugin_path / '.claude-plugin' / 'plugin.json').exists(),
            'has_commands': (plugin_path / 'commands').exists(),
            'has_agents': (plugin_path / 'agents').exists(),
            'has_skills': (plugin_path / 'skills' / 'skill-adapter').exists(),
            'has_scripts': (plugin_path / 'scripts').exists(),
            'has_hooks': (plugin_path / 'hooks').exists(),
            'has_mcp': (plugin_path / 'mcp').exists(),
        }

        # Check for Agent Skill
        skill_md = plugin_path / 'skills' / 'skill-adapter' / 'SKILL.md'
        skill_analysis = None

        if skill_md.exists():
            with open(skill_md, 'r') as f:
                skill_content = f.read()

            skill_analysis = {
                'exists': True,
                'size': len(skill_content),
                'has_frontmatter': skill_content.startswith('---'),
                'has_bundled_resources': any([
                    'scripts/' in skill_content.lower(),
                    'references/' in skill_content.lower(),
                    'assets/' in skill_content.lower()
                ]),
                'content': skill_content[:500]  # First 500 chars for context
            }
        else:
            skill_analysis = {'exists': False}

        # Read README for context
        readme_content = ""
        if structure['has_readme']:
            with open(plugin_path / 'README.md', 'r') as f:
                readme_content = f.read()[:2000]  # First 2000 chars

        return {
            'structure': structure,
            'skill_analysis': skill_analysis,
            'readme_excerpt': readme_content,
            'metadata': plugin['metadata']
        }

    def smart_delay(self, message: str = "Rate limiting"):
        """Intelligent delay with randomness to avoid timeouts"""
        delay = RATE_LIMIT_DELAY + random.uniform(0, RATE_LIMIT_RANDOMNESS)
        print(f"  ⏸️  {message}: {delay:.1f}s...")
        time.sleep(delay)

    def generate_enhancement_plan(self, plugin: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Use Gemini to generate enhancement plan"""

        prompt = f"""You are an expert at enhancing Claude Code plugins following Anthropic's Agent Skills best practices.

# ANTHROPIC STANDARDS (Your Bible)
{self.standards[:15000]}  # Include relevant portion of standards

# PLUGIN TO ENHANCE
Name: {plugin['name']}
Category: {plugin['category']}
Path: {plugin['path']}

# CURRENT ANALYSIS
Structure: {json.dumps(analysis['structure'], indent=2)}
Skill Analysis: {json.dumps(analysis['skill_analysis'], indent=2)}

README Excerpt:
{analysis['readme_excerpt']}

# YOUR TASK

Analyze this plugin and create a comprehensive enhancement plan following these steps:

## Step 1: Gap Analysis
Identify what's missing compared to Anthropic standards:
- Does SKILL.md exist? If yes, is it comprehensive (8000+ bytes)?
- Does it follow hyphen-case naming convention?
- Does it use imperative/infinitive writing style?
- Are there bundled resources (scripts/, references/, assets/)?
- Is there progressive disclosure (3-level loading)?
- Are there 10-15 code examples?
- Is there a detailed workflow with phases?

## Step 2: Priority Classification
Rate each missing piece as HIGH/MEDIUM/LOW priority

## Step 3: Enhancement Recommendations
For each gap, provide:
- What to create/enhance
- Why it's important
- Specific implementation guidance
- Example content structure

## Step 4: Bundled Resources Plan
Identify what scripts, references, and assets should be created:
- scripts/ - What automation utilities would help?
- references/ - What documentation should be added?
- assets/ - What templates/examples are needed?

## Step 5: Quality Score
Give the plugin a quality score (0-100) based on:
- Content depth (0-30 points)
- Bundled resources (0-25 points)
- Code examples (0-20 points)
- Writing style adherence (0-15 points)
- Progressive disclosure (0-10 points)

## OUTPUT FORMAT

Return ONLY valid JSON with this structure:
{{
  "quality_score_before": 0-100,
  "quality_score_after_estimate": 0-100,
  "high_priority_gaps": ["gap1", "gap2", ...],
  "medium_priority_gaps": ["gap1", ...],
  "low_priority_gaps": ["gap1", ...],
  "bundled_resources_needed": {{
    "scripts": ["script1.sh description", "script2.py description"],
    "references": ["ref1.md description"],
    "assets": ["asset1 description"]
  }},
  "skill_md_enhancements": {{
    "create_new": true/false,
    "suggested_size_bytes": 8000,
    "sections_to_add": ["section1", "section2"],
    "writing_style_issues": ["issue1", "issue2"]
  }},
  "implementation_priority": "HIGH/MEDIUM/LOW",
  "estimated_impact": "Brief description of impact",
  "next_steps": ["step1", "step2", ...]
}}

Be thorough and specific. This analysis will drive automated enhancements."""

        try:
            print(f"  🤖 Asking Gemini for enhancement plan...")
            start_time = time.time()

            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,  # Lower temperature for structured output
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 4096,
                }
            )

            elapsed = time.time() - start_time
            print(f"  ✅ Gemini responded in {elapsed:.1f}s")

            # Rate limit delay after API call
            self.smart_delay("Post-analysis delay")

            # Extract JSON from response
            response_text = response.text.strip()

            # Try to find JSON in response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            plan = json.loads(response_text)
            return plan

        except Exception as e:
            print(f"  ❌ Enhancement plan generation failed: {e}")
            return None

    def create_skill_md(self, plugin: Dict[str, Any], analysis: Dict[str, Any], plan: Dict[str, Any]) -> Optional[str]:
        """Use Gemini to create comprehensive SKILL.md"""

        if not plan:
            return None

        # Skip if not high priority or skill exists and is good
        if plan.get('implementation_priority') != 'HIGH':
            print(f"  ⏭️  Skipping SKILL.md creation (priority: {plan.get('implementation_priority')})")
            return None

        if analysis['skill_analysis'].get('exists') and analysis['skill_analysis'].get('size', 0) > 5000:
            print(f"  ⏭️  SKILL.md already comprehensive ({analysis['skill_analysis']['size']} bytes)")
            return None

        prompt = f"""You are an expert at creating Agent Skills for Claude Code plugins following Anthropic's official guidelines.

# ANTHROPIC STANDARDS
{self.standards[20000:50000]}  # Include SKILL.md examples section

# PLUGIN INFORMATION
Name: {plugin['name']}
Category: {plugin['category']}

README:
{analysis['readme_excerpt']}

Metadata:
{json.dumps(plugin['metadata'], indent=2)}

# ENHANCEMENT PLAN
{json.dumps(plan, indent=2)}

# YOUR TASK

Create a comprehensive SKILL.md file following Anthropic's standards:

	## Requirements:
	1. **Frontmatter** (YAML):
	   - name: {plugin['name'].lower().replace(' ', '-')}  # hyphen-case
	   - description: Multi-line with trigger phrases
	   - license: MIT
	   - allowed-tools: "Read, Grep, Glob, Edit, Write, Bash(git:*)"  # CSV string
	   - metadata: author, version, category

2. **Content Structure**:
   - Overview (2-3 sentences)
   - Core Philosophy/Capabilities
   - Workflow (4-6 phases with detailed steps)
   - Using Bundled Resources (reference scripts/, references/, assets/)
   - Examples (3-4 complete scenarios with workflows)
   - Troubleshooting
   - Integration notes

3. **Writing Style**:
   - Use imperative/infinitive form ("To accomplish X, do Y")
   - NO second person ("you should")
   - Objective, instructional language
   - Clear action directives

4. **Content Depth**:
   - Target 8,000+ bytes
   - 10-15 code examples
   - Detailed procedural instructions
   - Progressive disclosure references

5. **Code Examples**:
   - Bash scripts for automation
   - Configuration templates
   - Usage examples
   - Error handling patterns

Return ONLY the complete SKILL.md content (no explanations, just the file content).
Start with --- for frontmatter and end with proper markdown."""

        try:
            print(f"  🤖 Generating comprehensive SKILL.md...")
            start_time = time.time()

            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.4,
                    'top_p': 0.9,
                    'top_k': 40,
                    'max_output_tokens': 8192,  # Allow large output
                }
            )

            elapsed = time.time() - start_time
            skill_content = response.text.strip()

            print(f"  ✅ Generated SKILL.md ({len(skill_content)} bytes) in {elapsed:.1f}s")

            # Rate limit delay after API call
            self.smart_delay("Post-generation delay")

            # Validate it starts with frontmatter
            if not skill_content.startswith('---'):
                print(f"  ⚠️  Warning: SKILL.md doesn't start with frontmatter")
                return None

            return skill_content

        except Exception as e:
            print(f"  ❌ SKILL.md generation failed: {e}")
            return None

    def backup_plugin(self, plugin: Dict[str, Any]):
        """Create timestamped backup of plugin before modifications"""
        plugin_path = Path(plugin['path'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = BACKUP_DIR / 'plugin-backups' / f"{plugin['name']}_{timestamp}"

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plugin_path, backup_path)

        print(f"  💾 Backup created: {backup_path}")
        return backup_path

    def apply_enhancements(self, plugin: Dict[str, Any], plan: Dict[str, Any], skill_content: Optional[str]) -> bool:
        """Apply enhancements to plugin"""
        plugin_path = Path(plugin['path'])
        changes = []

        try:
            # Create backup first
            self.backup_plugin(plugin)

            # Create SKILL.md if generated
            if skill_content:
                skill_dir = plugin_path / 'skills' / 'skill-adapter'
                skill_dir.mkdir(parents=True, exist_ok=True)

                skill_path = skill_dir / 'SKILL.md'
                with open(skill_path, 'w') as f:
                    f.write(skill_content)

                changes.append(f"Created/updated {skill_path}")
                print(f"  ✅ Wrote SKILL.md ({len(skill_content)} bytes)")

            # Create bundled resource directories
            for resource_type in ['scripts', 'references', 'assets']:
                if plan.get('bundled_resources_needed', {}).get(resource_type):
                    resource_dir = plugin_path / 'skills' / 'skill-adapter' / resource_type
                    resource_dir.mkdir(parents=True, exist_ok=True)

                    # Create README in each directory
                    readme_path = resource_dir / 'README.md'
                    if not readme_path.exists():
                        with open(readme_path, 'w') as f:
                            f.write(f"# {resource_type.title()}\n\n")
                            f.write(f"Bundled resources for {plugin['name']} skill\n\n")
                            for item in plan['bundled_resources_needed'][resource_type]:
                                f.write(f"- [ ] {item}\n")

                        changes.append(f"Created {resource_dir}/")
                        print(f"  ✅ Created {resource_type}/ directory with TODO README")

            # Log enhancements to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO enhancements
                (timestamp, plugin_name, plugin_path, enhancement_type, status, changes_made)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                plugin['name'],
                plugin['path'],
                'comprehensive',
                'success',
                json.dumps(changes)
            ))

            conn.commit()
            conn.close()

            print(f"  🎉 Enhancements applied successfully!")
            return True

        except Exception as e:
            print(f"  ❌ Failed to apply enhancements: {e}")
            return False

    def process_plugin(self, plugin: Dict[str, Any]) -> bool:
        """Process a single plugin through the enhancement pipeline"""
        print(f"\n{'='*60}")
        print(f"🔧 Processing: {plugin['name']} ({plugin['category']})")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # Step 1: Analyze current state
            print(f"\n📊 Step 1: Analyzing plugin structure...")
            analysis = self.analyze_plugin(plugin)

            # Step 2: Generate enhancement plan
            print(f"\n🎯 Step 2: Generating enhancement plan...")
            plan = self.generate_enhancement_plan(plugin, analysis)

            if not plan:
                print(f"  ⚠️  Could not generate enhancement plan")
                return False

            print(f"  Quality score: {plan.get('quality_score_before', 0)}/100")
            print(f"  Priority: {plan.get('implementation_priority', 'UNKNOWN')}")
            print(f"  High priority gaps: {len(plan.get('high_priority_gaps', []))}")

            # Step 3: Create SKILL.md if needed
            skill_content = None
            if plan.get('skill_md_enhancements', {}).get('create_new'):
                print(f"\n📝 Step 3: Creating comprehensive SKILL.md...")
                skill_content = self.create_skill_md(plugin, analysis, plan)
                # Delay is handled inside create_skill_md now
            else:
                print(f"\n⏭️  Step 3: SKILL.md creation not needed")

            # Step 4: Apply enhancements
            print(f"\n✨ Step 4: Applying enhancements...")
            success = self.apply_enhancements(plugin, plan, skill_content)

            elapsed = time.time() - start_time
            print(f"\n⏱️  Total time: {elapsed:.1f}s")

            return success

        except Exception as e:
            print(f"\n❌ Plugin processing failed: {e}")
            return False

    def run_overnight_batch(self, limit: Optional[int] = None):
        """Run overnight batch enhancement of all plugins"""
        print(f"\n{'='*60}")
        print(f"🌙 OVERNIGHT PLUGIN ENHANCEMENT BATCH")
        print(f"{'='*60}")
        print(f"Project: {PROJECT_ID}")
        print(f"Model: gemini-2.0-flash-exp")
        print(f"Rate limit: {RATE_LIMIT_DELAY}s between calls")
        print(f"Backup dir: {BACKUP_DIR}")
        print(f"{'='*60}\n")

        # Find all plugins
        plugins = self.find_all_plugins()

        if limit:
            plugins = plugins[:limit]
            print(f"⚠️  Limited to first {limit} plugins for testing\n")

        # Process each plugin
        total = len(plugins)
        success_count = 0
        failure_count = 0

        start_time = time.time()

        for idx, plugin in enumerate(plugins, 1):
            print(f"\n\n{'#'*60}")
            print(f"Plugin {idx}/{total}")
            print(f"{'#'*60}")

            success = self.process_plugin(plugin)

            if success:
                success_count += 1
            else:
                failure_count += 1

            # Smart rate limiting between plugins
            if idx < total:
                self.smart_delay(f"Inter-plugin delay ({idx}/{total})")

                # Extra long delay every 10 plugins
                if idx % 10 == 0:
                    extra_delay = random.uniform(30, 60)
                    print(f"  ⏸️  Extra rest break: {extra_delay:.1f}s...")
                    time.sleep(extra_delay)

        # Final summary
        elapsed = time.time() - start_time
        elapsed_hours = elapsed / 3600

        print(f"\n\n{'='*60}")
        print(f"🎉 BATCH COMPLETE")
        print(f"{'='*60}")
        print(f"Total plugins: {total}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"Success rate: {success_count/total*100:.1f}%")
        print(f"Total time: {elapsed_hours:.2f} hours")
        print(f"Database: {DB_PATH}")
        print(f"Backups: {BACKUP_DIR}")
        print(f"{'='*60}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Overnight Plugin Enhancement System')
    parser.add_argument('--limit', type=int, help='Limit number of plugins (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, no changes')
    parser.add_argument('--plugin', type=str, help='Process specific plugin by name')

    args = parser.parse_args()

    enhancer = PluginEnhancer()

    if args.plugin:
        # Process single plugin
        plugins = enhancer.find_all_plugins()
        target = next((p for p in plugins if p['name'] == args.plugin), None)

        if not target:
            print(f"❌ Plugin not found: {args.plugin}")
            sys.exit(1)

        enhancer.process_plugin(target)
    else:
        # Run batch
        enhancer.run_overnight_batch(limit=args.limit)


if __name__ == '__main__':
    main()
