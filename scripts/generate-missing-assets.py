#!/usr/bin/env python3
"""
Generate Missing Asset Files using Vertex AI Gemini

This script:
1. Scans all plugins for assets/README.md files
2. Extracts checklists of missing files
3. Uses Gemini to generate contextual content for each missing file
4. Creates the asset files with appropriate content
5. Tracks progress in SQLite database

Usage:
    python3 scripts/generate-missing-assets.py [--plugin PLUGIN_NAME] [--dry-run]
"""

import os
import sys
import re
import json
import sqlite3
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
except ImportError:
    print("❌ Error: google-cloud-aiplatform not installed")
    print("Install with: pip install google-cloud-aiplatform")
    sys.exit(1)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "diagnostic-pro-start-up")
REGION = "us-central1"
MODEL_NAME = "gemini-1.5-flash"  # Use stable model (002 variant not available in this project)
DB_PATH = "backups/asset_generation.db"
RATE_LIMIT_DELAY = 2  # Delay between API calls in seconds

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel(MODEL_NAME)

class AssetGenerator:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.db_conn = self.init_database()
        self.stats = {
            "plugins_processed": 0,
            "assets_created": 0,
            "assets_skipped": 0,
            "errors": 0
        }

    def init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database for tracking progress"""
        os.makedirs("backups", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_generation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_name TEXT NOT NULL,
                asset_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                content_length INTEGER,
                generated_at TIMESTAMP,
                error_message TEXT,
                UNIQUE(plugin_name, asset_path)
            )
        """)

        conn.commit()
        return conn

    def extract_missing_assets(self, assets_readme_path: str) -> List[Dict[str, str]]:
        """Extract checklist items from assets/README.md"""
        if not os.path.exists(assets_readme_path):
            return []

        with open(assets_readme_path, 'r') as f:
            content = f.read()

        # Pattern: - [ ] filename.ext: Description
        pattern = r'-\s*\[\s*\]\s+([^:]+?):\s*(.+?)(?:\n|$)'
        matches = re.findall(pattern, content)

        assets = []
        for filename, description in matches:
            filename = filename.strip()
            description = description.strip()
            assets.append({
                "filename": filename,
                "description": description
            })

        return assets

    def get_plugin_context(self, plugin_path: str) -> Dict[str, str]:
        """Read plugin README and plugin.json for context"""
        context = {
            "plugin_name": os.path.basename(plugin_path),
            "description": "",
            "category": "",
            "readme_content": ""
        }

        # Read plugin.json
        plugin_json_path = os.path.join(plugin_path, ".claude-plugin", "plugin.json")
        if os.path.exists(plugin_json_path):
            with open(plugin_json_path, 'r') as f:
                try:
                    plugin_data = json.load(f)
                    context["description"] = plugin_data.get("description", "")
                    context["category"] = plugin_data.get("category", "")
                except:
                    pass

        # Read README.md (first 2000 chars for context)
        readme_path = os.path.join(plugin_path, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as f:
                context["readme_content"] = f.read()[:2000]

        return context

    def generate_asset_content(self, asset_info: Dict[str, str], context: Dict[str, str]) -> str:
        """Use Gemini to generate contextual content for asset file"""
        filename = asset_info["filename"]
        description = asset_info["description"]

        # Determine file type and appropriate generation strategy
        file_ext = Path(filename).suffix.lower()

        # Build prompt based on file type
        if file_ext in ['.json']:
            prompt = self.build_json_prompt(filename, description, context)
        elif file_ext in ['.md', '.txt']:
            prompt = self.build_markdown_prompt(filename, description, context)
        elif file_ext in ['.yaml', '.yml']:
            prompt = self.build_yaml_prompt(filename, description, context)
        elif file_ext in ['.html']:
            prompt = self.build_html_prompt(filename, description, context)
        elif file_ext in ['.py']:
            prompt = self.build_python_prompt(filename, description, context)
        elif file_ext in ['.sh']:
            prompt = self.build_shell_prompt(filename, description, context)
        else:
            # Generic template
            prompt = self.build_generic_prompt(filename, description, context)

        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                generation_config = GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192
                )

                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )

                # Add delay after successful generation to avoid rate limits
                time.sleep(RATE_LIMIT_DELAY)

                return response.text.strip()

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error
                if "429" in error_str or "Quota exceeded" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff: 5s, 15s, 45s
                        wait_time = 5 * (3 ** attempt)
                        print(f"    ⏳ Rate limited, waiting {wait_time}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ❌ Rate limit exceeded after {max_retries} retries")
                        return None
                else:
                    print(f"  ❌ Gemini generation failed: {e}")
                    return None

        return None

    def build_json_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a JSON file for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Create a valid, well-formatted JSON file
2. Include realistic example data appropriate for the plugin's purpose
3. Add comments using "_comment" fields where helpful
4. Ensure the structure matches the file's intended use
5. Make it production-ready and usable as a template

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the JSON content (no markdown code blocks, no explanations):"""

    def build_markdown_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a Markdown template file for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Create a professional, well-structured Markdown document
2. Include clear headings and sections
3. Add placeholders where users should insert their data
4. Include helpful examples and instructions
5. Make it production-ready

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the Markdown content (no code blocks, no preamble):"""

    def build_yaml_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a YAML configuration file for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Create valid YAML syntax
2. Include clear comments explaining each section
3. Use realistic default values
4. Add placeholders (REPLACE_ME, YOUR_VALUE_HERE) where needed
5. Make it production-ready

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the YAML content (no markdown code blocks, no explanations):"""

    def build_html_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate an HTML template file for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Create valid HTML5 with proper structure
2. Include inline CSS for styling
3. Add placeholders {{{{variable}}}} where dynamic content goes
4. Make it responsive and modern
5. Include helpful comments

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the HTML content (no markdown code blocks, no explanations):"""

    def build_python_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a Python script for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Include proper shebang and imports
2. Add comprehensive docstrings
3. Follow PEP 8 style guidelines
4. Include example usage in __main__
5. Add error handling

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the Python code (no markdown code blocks, no explanations):"""

    def build_shell_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a Bash shell script for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Include proper shebang (#!/bin/bash)
2. Add clear comments
3. Use proper error handling (set -e)
4. Include usage instructions
5. Make it executable-ready

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the shell script content (no markdown code blocks, no explanations):"""

    def build_generic_prompt(self, filename: str, description: str, context: Dict) -> str:
        return f"""Generate a template file for a Claude Code plugin asset.

Plugin: {context['plugin_name']}
Category: {context['category']}
Description: {context['description']}

File to Generate: {filename}
Purpose: {description}

Requirements:
1. Create appropriate content for the file type
2. Include helpful comments or instructions
3. Add placeholders where needed
4. Make it production-ready

Context from plugin README:
{context['readme_content'][:500]}...

Generate ONLY the file content (no markdown code blocks, no explanations):"""

    def clean_generated_content(self, content: str, file_ext: str) -> str:
        """Clean up Gemini's response - remove markdown code blocks if present"""
        if not content:
            return content

        # Remove markdown code blocks
        content = re.sub(r'^```[a-z]*\n', '', content)
        content = re.sub(r'\n```$', '', content)

        # Remove leading/trailing whitespace
        content = content.strip()

        return content

    def process_plugin(self, plugin_path: str) -> bool:
        """Process a single plugin to generate missing assets"""
        plugin_name = os.path.basename(plugin_path)
        print(f"\n{'='*60}")
        print(f"Processing: {plugin_name}")
        print(f"{'='*60}")

        # Find all assets/README.md files in skills
        assets_readme_files = []
        skills_dir = os.path.join(plugin_path, "skills")

        if not os.path.exists(skills_dir):
            print(f"  ⏭️  No skills directory")
            return False

        for root, dirs, files in os.walk(skills_dir):
            if "README.md" in files and "assets" in root:
                assets_readme_files.append(os.path.join(root, "README.md"))

        if not assets_readme_files:
            print(f"  ⏭️  No assets/README.md files found")
            return False

        # Get plugin context
        context = self.get_plugin_context(plugin_path)

        # Process each assets/README.md
        for assets_readme in assets_readme_files:
            assets_dir = os.path.dirname(assets_readme)
            print(f"\n  📁 Assets directory: {os.path.relpath(assets_dir, plugin_path)}")

            # Extract missing assets
            missing_assets = self.extract_missing_assets(assets_readme)

            if not missing_assets:
                print(f"    ✅ No missing assets")
                continue

            print(f"    Found {len(missing_assets)} missing assets")

            # Generate each missing asset
            for asset_info in missing_assets:
                filename = asset_info["filename"]

                # Skip directories (indicated by trailing /)
                if filename.endswith('/'):
                    print(f"      ⏭️  Skipping directory: {filename}")
                    continue

                asset_path = os.path.join(assets_dir, filename)

                # Check if file already exists
                if os.path.exists(asset_path):
                    print(f"      ✅ Already exists: {filename}")
                    self.stats["assets_skipped"] += 1
                    continue

                print(f"      🔄 Generating: {filename}")

                if self.dry_run:
                    print(f"         [DRY RUN] Would generate {filename}")
                    continue

                # Generate content with Gemini
                content = self.generate_asset_content(asset_info, context)

                if content:
                    # Clean up content
                    file_ext = Path(filename).suffix.lower()
                    content = self.clean_generated_content(content, file_ext)

                    # Create file
                    try:
                        os.makedirs(os.path.dirname(asset_path), exist_ok=True)
                        with open(asset_path, 'w') as f:
                            f.write(content)

                        print(f"         ✅ Created ({len(content)} bytes)")

                        # Track in database
                        self.track_asset(
                            plugin_name,
                            os.path.relpath(asset_path, plugin_path),
                            filename,
                            asset_info["description"],
                            "completed",
                            len(content)
                        )

                        self.stats["assets_created"] += 1

                    except Exception as e:
                        print(f"         ❌ Failed to write file: {e}")
                        self.track_asset(
                            plugin_name,
                            os.path.relpath(asset_path, plugin_path),
                            filename,
                            asset_info["description"],
                            "failed",
                            0,
                            str(e)
                        )
                        self.stats["errors"] += 1
                else:
                    print(f"         ❌ Generation failed")
                    self.stats["errors"] += 1

        self.stats["plugins_processed"] += 1
        return True

    def track_asset(self, plugin_name: str, asset_path: str, filename: str,
                   description: str, status: str, content_length: int,
                   error_message: str = None):
        """Record asset generation in database"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO asset_generation
            (plugin_name, asset_path, file_name, description, status, content_length, generated_at, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (plugin_name, asset_path, filename, description, status, content_length, datetime.now(), error_message))
        self.db_conn.commit()

    def process_all_plugins(self, target_plugin: str = None):
        """Process all plugins or a specific plugin"""
        plugins_dir = Path("plugins")

        if target_plugin:
            # Process specific plugin
            plugin_path = None
            for category_dir in plugins_dir.iterdir():
                if category_dir.is_dir():
                    potential_path = category_dir / target_plugin
                    if potential_path.exists():
                        plugin_path = str(potential_path)
                        break

            if not plugin_path:
                print(f"❌ Plugin '{target_plugin}' not found")
                return

            self.process_plugin(plugin_path)
        else:
            # Process all plugins
            for category_dir in plugins_dir.iterdir():
                if category_dir.is_dir() and not category_dir.name.startswith('.'):
                    for plugin_dir in category_dir.iterdir():
                        if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                            try:
                                self.process_plugin(str(plugin_dir))
                            except Exception as e:
                                print(f"❌ Error processing {plugin_dir.name}: {e}")
                                self.stats["errors"] += 1

    def print_summary(self):
        """Print generation summary"""
        print(f"\n{'='*60}")
        print("GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"Plugins processed: {self.stats['plugins_processed']}")
        print(f"Assets created: {self.stats['assets_created']}")
        print(f"Assets skipped (already exist): {self.stats['assets_skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\nDatabase: {DB_PATH}")
        print(f"{'='*60}\n")

    def close(self):
        """Close database connection"""
        self.db_conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate missing asset files using Gemini")
    parser.add_argument("--plugin", help="Process specific plugin only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating files")
    parser.add_argument("--limit", type=int, help="Limit number of plugins to process")

    args = parser.parse_args()

    print("🚀 Starting Asset Generation with Vertex AI Gemini")
    print(f"Model: {MODEL_NAME}")
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Dry Run: {args.dry_run}")
    print("")

    generator = AssetGenerator(dry_run=args.dry_run)

    try:
        generator.process_all_plugins(target_plugin=args.plugin)
        generator.print_summary()
    finally:
        generator.close()

if __name__ == "__main__":
    main()
