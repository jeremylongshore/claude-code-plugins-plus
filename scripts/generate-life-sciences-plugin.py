#!/usr/bin/env python3
"""
Life Sciences MCP Plugin Generator using Vertex AI Gemini
Generates complete production-ready plugin packs for scientific research

Usage:
    python3 scripts/generate-life-sciences-plugin.py --pack pubmed-research
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Vertex AI SDK
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting

# Configuration
PROJECT_ID = "ccpi-web-app-prod"
LOCATION = "us-central1"
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "plugins" / "life-sciences"

# Plugin pack definitions
PLUGIN_PACKS = {
    "pubmed-research": {
        "name": "pubmed-research-master",
        "display_name": "PubMed Research Master",
        "description": "Complete PubMed research toolkit with 10 MCP tools, offline caching, and citation management",
        "category": "scientific-research",
        "priority": 1,
        "tools_count": 10,
        "skills_count": 4,
        "commands_count": 5,
        "agents_count": 2
    },
    "single-cell": {
        "name": "single-cell-analyst",
        "display_name": "Single Cell RNA-seq Analyst",
        "description": "10x Genomics integration for complete single cell analysis workflows",
        "category": "bioinformatics",
        "priority": 2,
        "tools_count": 8,
        "skills_count": 3,
        "commands_count": 6,
        "agents_count": 2
    },
    "synapse-data": {
        "name": "synapse-navigator",
        "display_name": "Synapse Data Platform Navigator",
        "description": "Search and download from 3PB of biomedical research data",
        "category": "data-platforms",
        "priority": 3,
        "tools_count": 7,
        "skills_count": 3,
        "commands_count": 5,
        "agents_count": 2
    }
}

def init_vertex_ai():
    """Initialize Vertex AI with Gemini 2.0 Flash"""
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel("gemini-2.0-flash-exp")
        print(f"✅ Vertex AI initialized: {PROJECT_ID} / {LOCATION}")
        return model
    except Exception as e:
        print(f"❌ Vertex AI init failed: {e}")
        print("\nRun: gcloud auth application-default login")
        sys.exit(1)

def load_research_docs():
    """Load research documents for context"""

    # CRITICAL: Load the full context prompt that explains MCP to Vertex
    # (MCP was invented AFTER Vertex's training cutoff)
    full_context_prompt = REPO_ROOT / "prompts" / "vertex-life-sciences-full-context.md"

    if not full_context_prompt.exists():
        print(f"❌ Missing critical context file: {full_context_prompt}")
        sys.exit(1)

    with open(full_context_prompt) as f:
        return f.read()

def generate_plugin_pack(model: GenerativeModel, pack_key: str, context: str) -> dict:
    """Generate complete plugin pack using Vertex AI"""

    pack_config = PLUGIN_PACKS[pack_key]
    plugin_name = pack_config["name"]

    print(f"\n{'='*80}")
    print(f"🚀 Generating: {pack_config['display_name']}")
    print(f"{'='*80}\n")

    prompt = f"""{context}

# PLUGIN TO GENERATE: {pack_config['display_name']}

# PLUGIN SPECIFICATIONS

**Name:** {plugin_name}
**Description:** {pack_config['description']}
**Category:** {pack_config['category']}

**Components to Generate:**
- {pack_config['tools_count']} MCP Tools (TypeScript)
- {pack_config['skills_count']} Agent Skills (8,000+ bytes each)
- {pack_config['commands_count']} Slash Commands (Markdown with YAML)
- {pack_config['agents_count']} Specialized Agents (Markdown)
- Complete README.md with real examples
- package.json with dependencies
- tsconfig.json for TypeScript
- plugin.json with metadata
- MCP server.json configuration
- MIT LICENSE

# CRITICAL REQUIREMENTS

1. **MCP Server (src/index.ts)**
   - Use @modelcontextprotocol/sdk version 0.7.0+
   - Implement ALL {pack_config['tools_count']} tools
   - Proper error handling on every tool
   - Rate limiting where applicable
   - Input validation using Zod
   - JSON-RPC 2.0 compliance

2. **Agent Skills (skills/skill-adapter/*.md)**
   - MINIMUM 8,000 bytes per skill
   - Valid YAML frontmatter
   - Clear trigger phrases
   - Multi-phase workflows
   - Code examples
   - Error scenarios

3. **Documentation Quality**
   - 5+ real-world examples in README
   - Installation instructions
   - API requirements
   - Troubleshooting section
   - Contributing guidelines

# OUTPUT FORMAT

For each file, use this EXACT format:

---FILE: path/to/file.ext
[COMPLETE file contents here - NOT skeleton code]
---END FILE

**Directory structure:**
plugins/life-sciences/{plugin_name}/
├── .claude-plugin/
│   ├── plugin.json
│   └── mcp/server.json
├── src/
│   └── index.ts
├── skills/
│   └── skill-adapter/
│       └── [skill files].md
├── commands/
│   └── [command files].md
├── agents/
│   └── [agent files].md
├── package.json
├── tsconfig.json
├── README.md
└── LICENSE

# START GENERATION NOW

Generate the COMPLETE plugin pack. Every file must be production-ready, not a template or skeleton.
"""

    print("⏳ Calling Vertex AI Gemini 2.0 Flash...")
    print(f"   Prompt size: {len(prompt):,} characters\n")

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings=[
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
            ]
        )

        return {
            "success": True,
            "content": response.text,
            "plugin_name": plugin_name,
            "pack_config": pack_config
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "plugin_name": plugin_name,
            "pack_config": pack_config
        }

def parse_generated_files(content: str) -> dict:
    """Parse generated files from Vertex AI output"""
    files = {}
    current_file = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('---FILE:'):
            # Save previous file
            if current_file:
                files[current_file] = '\n'.join(current_content)

            # Start new file
            current_file = line.replace('---FILE:', '').strip()
            current_content = []
        elif line.startswith('---END FILE'):
            # Save current file
            if current_file:
                files[current_file] = '\n'.join(current_content)
                current_file = None
                current_content = []
        elif current_file:
            current_content.append(line)

    # Save last file if exists
    if current_file and current_content:
        files[current_file] = '\n'.join(current_content)

    return files

def save_generated_files(files: dict, plugin_name: str):
    """Save generated files to disk"""
    plugin_dir = OUTPUT_DIR / plugin_name

    print(f"\n📁 Creating plugin directory: {plugin_dir}")
    plugin_dir.mkdir(parents=True, exist_ok=True)

    files_created = 0

    for file_path, content in files.items():
        # Remove "plugins/life-sciences/{plugin_name}/" prefix if present
        clean_path = file_path
        for prefix in [f"plugins/life-sciences/{plugin_name}/", f"{plugin_name}/"]:
            if clean_path.startswith(prefix):
                clean_path = clean_path[len(prefix):]

        full_path = plugin_dir / clean_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        files_created += 1
        print(f"   ✅ {clean_path} ({len(content):,} bytes)")

    print(f"\n✅ Created {files_created} files in {plugin_dir}")
    return files_created

def main():
    parser = argparse.ArgumentParser(
        description="Generate life sciences MCP plugin packs with Vertex AI"
    )
    parser.add_argument(
        "--pack",
        required=True,
        choices=list(PLUGIN_PACKS.keys()),
        help="Plugin pack to generate"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for generated plugins"
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"  Life Sciences MCP Plugin Generator")
    print(f"  Using Vertex AI Gemini 2.0 Flash")
    print(f"{'='*80}\n")

    # Initialize Vertex AI
    model = init_vertex_ai()

    # Load research context
    print("📖 Loading research documents...")
    context = load_research_docs()
    print(f"   Context size: {len(context):,} characters\n")

    # Generate plugin pack
    result = generate_plugin_pack(model, args.pack, context)

    if not result["success"]:
        print(f"❌ Generation failed: {result['error']}")
        sys.exit(1)

    print(f"✅ Generation successful!")
    print(f"   Response size: {len(result['content']):,} characters\n")

    # Parse generated files
    print("🔍 Parsing generated files...")
    files = parse_generated_files(result["content"])
    print(f"   Found {len(files)} files\n")

    if len(files) == 0:
        print("⚠️  No files found in output. Saving raw response for debugging...")
        debug_file = OUTPUT_DIR / f"{result['plugin_name']}_debug_output.txt"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'w') as f:
            f.write(result['content'])
        print(f"   Saved to: {debug_file}")
        sys.exit(1)

    # Save files
    files_created = save_generated_files(files, result["plugin_name"])

    # Summary
    pack = result["pack_config"]
    print(f"\n{'='*80}")
    print(f"✅ SUCCESS: {pack['display_name']}")
    print(f"{'='*80}")
    print(f"\n📊 Generation Summary:")
    print(f"   Plugin name: {result['plugin_name']}")
    print(f"   Files created: {files_created}")
    print(f"   Expected tools: {pack['tools_count']}")
    print(f"   Expected skills: {pack['skills_count']}")
    print(f"   Expected commands: {pack['commands_count']}")
    print(f"   Expected agents: {pack['agents_count']}")

    plugin_dir = OUTPUT_DIR / result["plugin_name"]
    print(f"\n📁 Plugin directory: {plugin_dir}")

    print(f"\n🔧 Next steps:")
    print(f"   cd {plugin_dir}")
    print(f"   pnpm install")
    print(f"   pnpm build")
    print(f"   pnpm test")

    print(f"\n✅ Done!\n")

if __name__ == "__main__":
    main()
