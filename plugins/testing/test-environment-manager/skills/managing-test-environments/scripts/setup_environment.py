#!/usr/bin/env python3
"""
test-environment-manager - Initialization Script
Script to set up the test environment using Docker Compose and Testcontainers.
Generated: 2025-12-10 03:48:17
"""

import os
import json
import argparse
from pathlib import Path

def create_project_structure(project_name: str, output_dir: str = "."):
    """Create project structure for test-environment-manager."""
    base_path = Path(output_dir) / project_name

    # Create directories
    directories = [
        base_path,
        base_path / "config",
        base_path / "data",
        base_path / "output",
        base_path / "logs"
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")

    # Create configuration file
    config = {
        "project": project_name,
        "version": "1.0.0",
        "skill": "test-environment-manager",
        "category": "testing",
        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        "settings": {
            "debug": False,
            "verbose": True,
            "max_workers": 4
        }
    }

    config_file = base_path / "config" / "settings.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Created configuration: {config_file}")

    # Create README
    readme_content = f"""# {project_name}

Initialized with test-environment-manager skill

## Structure
- config/ - Configuration files
- data/ - Input data
- output/ - Generated output
- logs/ - Application logs

## Usage
See skill documentation for usage instructions.
"""

    readme_file = base_path / "README.md"
    readme_file.write_text(readme_content)
    print(f"✓ Created README: {readme_file}")

    return base_path

def main():
    parser = argparse.ArgumentParser(description="Script to set up the test environment using Docker Compose and Testcontainers.")
    parser.add_argument('--project', '-p', required=True, help='Project name')
    parser.add_argument('--output', '-o', default='.', help='Output directory')
    parser.add_argument('--config', '-c', help='Configuration file')

    args = parser.parse_args()

    print(f"🚀 Initializing {args.project}...")
    project_path = create_project_structure(args.project, args.output)

    if args.config:
        # Load additional configuration
        if Path(args.config).exists():
            with open(args.config) as f:
                extra_config = json.load(f)
            print(f"✓ Loaded configuration from {args.config}")

    print(f"\n✅ Project initialized successfully at {project_path}")
    return 0

if __name__ == "__main__":
    import sys
    import time
    sys.exit(main())
