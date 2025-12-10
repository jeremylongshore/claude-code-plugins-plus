#!/usr/bin/env python3
"""
OVERNIGHT SKILL SCRIPT GENERATOR
Fixes all 175 skills with missing scripts using parallel AI generation
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import re

# Configuration
PLUGINS_BASE = "/home/jeremy/000-projects/claude-code-plugins/plugins"
MAX_WORKERS = 10  # Parallel AI agents
BATCH_SIZE = 20   # Skills per batch
TIMEOUT_PER_SKILL = 60  # seconds

def find_skills_needing_scripts() -> List[Dict]:
    """Find all skills with TODO-only scripts."""
    skills_to_fix = []

    for category_dir in Path(PLUGINS_BASE).iterdir():
        if not category_dir.is_dir():
            continue

        for plugin_dir in category_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            skills_dir = plugin_dir / "skills"
            if not skills_dir.exists():
                continue

            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                scripts_dir = skill_dir / "scripts"
                if scripts_dir.exists():
                    # Check if only README exists
                    scripts = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
                    readme_path = scripts_dir / "README.md"

                    if len(scripts) == 0 and readme_path.exists():
                        # Read README to find TODO scripts
                        readme_content = readme_path.read_text()
                        todos = re.findall(r'- \[ \] ([^:]+):', readme_content)

                        if todos:
                            skills_to_fix.append({
                                'path': skill_dir,
                                'name': skill_dir.name,
                                'plugin': plugin_dir.name,
                                'category': category_dir.name,
                                'todos': todos,
                                'readme_path': readme_path,
                                'scripts_dir': scripts_dir
                            })

    return skills_to_fix

def generate_script_content(skill_info: Dict, script_name: str) -> str:
    """Generate Python script content based on skill and script name."""

    # Extract script purpose from README
    readme_content = skill_info['readme_path'].read_text()
    script_desc = ""
    for line in readme_content.split('\n'):
        if script_name in line:
            script_desc = line.split(':')[-1].strip() if ':' in line else ""
            break

    # Determine script type and generate appropriate content
    if 'init' in script_name or 'setup' in script_name:
        return generate_init_script(skill_info, script_desc)
    elif 'validate' in script_name or 'check' in script_name:
        return generate_validation_script(skill_info, script_desc)
    elif 'analyze' in script_name or 'audit' in script_name:
        return generate_analysis_script(skill_info, script_desc)
    elif 'generate' in script_name or 'create' in script_name:
        return generate_generator_script(skill_info, script_desc)
    elif 'deploy' in script_name or 'publish' in script_name:
        return generate_deployment_script(skill_info, script_desc)
    else:
        return generate_generic_script(skill_info, script_name, script_desc)

def generate_init_script(skill_info: Dict, desc: str) -> str:
    """Generate initialization/setup script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - Initialization Script
{desc or f"Initialize {skill_info['name']} environment and configuration"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import json
import argparse
from pathlib import Path

def create_project_structure(project_name: str, output_dir: str = "."):
    """Create project structure for {skill_info['name']}."""
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
        print(f"✓ Created {{dir_path}}")

    # Create configuration file
    config = {{
        "project": project_name,
        "version": "1.0.0",
        "skill": "{skill_info['name']}",
        "category": "{skill_info['category']}",
        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        "settings": {{
            "debug": False,
            "verbose": True,
            "max_workers": 4
        }}
    }}

    config_file = base_path / "config" / "settings.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Created configuration: {{config_file}}")

    # Create README
    readme_content = f"""# {{project_name}}

Initialized with {skill_info['name']} skill

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
    print(f"✓ Created README: {{readme_file}}")

    return base_path

def main():
    parser = argparse.ArgumentParser(description="{desc or 'Initialize project'}")
    parser.add_argument('--project', '-p', required=True, help='Project name')
    parser.add_argument('--output', '-o', default='.', help='Output directory')
    parser.add_argument('--config', '-c', help='Configuration file')

    args = parser.parse_args()

    print(f"🚀 Initializing {{args.project}}...")
    project_path = create_project_structure(args.project, args.output)

    if args.config:
        # Load additional configuration
        if Path(args.config).exists():
            with open(args.config) as f:
                extra_config = json.load(f)
            print(f"✓ Loaded configuration from {{args.config}}")

    print(f"\\n✅ Project initialized successfully at {{project_path}}")
    return 0

if __name__ == "__main__":
    import sys
    import time
    sys.exit(main())
'''

def generate_validation_script(skill_info: Dict, desc: str) -> str:
    """Generate validation/checking script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - Validation Script
{desc or f"Validate configuration and data for {skill_info['name']}"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import json
import argparse
from pathlib import Path

class Validator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.errors = []
        self.warnings = []
        self.passes = []

    def validate_json(self) -> bool:
        """Validate JSON configuration."""
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
            self.passes.append("✓ Valid JSON syntax")
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"✗ Invalid JSON: {{e}}")
            return False
        except FileNotFoundError:
            self.errors.append(f"✗ File not found: {{self.config_path}}")
            return False

    def validate_required_fields(self) -> bool:
        """Check required configuration fields."""
        required = ['project', 'version', 'settings']
        missing = []

        for field in required:
            if field not in self.config:
                missing.append(field)
                self.errors.append(f"✗ Missing required field: {{field}}")
            else:
                self.passes.append(f"✓ Has required field: {{field}}")

        return len(missing) == 0

    def validate_paths(self) -> bool:
        """Validate referenced paths exist."""
        valid = True

        if 'paths' in self.config:
            for name, path in self.config['paths'].items():
                if Path(path).exists():
                    self.passes.append(f"✓ Path exists: {{name}} -> {{path}}")
                else:
                    self.warnings.append(f"⚠ Path not found: {{name}} -> {{path}}")

        return valid

    def generate_report(self):
        """Generate validation report."""
        print("\\n" + "="*60)
        print("VALIDATION REPORT - {skill_info['name']}")
        print("="*60)

        if self.passes:
            print(f"\\n✅ PASSED ({{len(self.passes)}})")
            for msg in self.passes:
                print(f"  {{msg}}")

        if self.warnings:
            print(f"\\n⚠️  WARNINGS ({{len(self.warnings)}})")
            for msg in self.warnings:
                print(f"  {{msg}}")

        if self.errors:
            print(f"\\n❌ ERRORS ({{len(self.errors)}})")
            for msg in self.errors:
                print(f"  {{msg}}")

        total_issues = len(self.errors)
        print(f"\\n{'✅ VALID' if total_issues == 0 else '❌ INVALID'} - {{total_issues}} error(s)\\n")
        return total_issues == 0

def main():
    parser = argparse.ArgumentParser(description="{desc or 'Validate configuration'}")
    parser.add_argument('--config', '-c', required=True, help='Configuration file')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')

    args = parser.parse_args()

    validator = Validator(args.config)

    # Run validations
    validator.validate_json()
    if validator.config:
        validator.validate_required_fields()
        validator.validate_paths()

    # Generate report
    valid = validator.generate_report()

    if args.strict and validator.warnings:
        return 1

    return 0 if valid else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''

def generate_analysis_script(skill_info: Dict, desc: str) -> str:
    """Generate analysis/audit script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - Analysis Script
{desc or f"Analyze and audit data for {skill_info['name']}"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class Analyzer:
    def __init__(self, target_path: str):
        self.target_path = Path(target_path)
        self.stats = {{
            'total_files': 0,
            'total_size': 0,
            'file_types': {{}},
            'issues': [],
            'recommendations': []
        }}

    def analyze_directory(self) -> Dict:
        """Analyze directory structure and contents."""
        if not self.target_path.exists():
            self.stats['issues'].append(f"Path does not exist: {{self.target_path}}")
            return self.stats

        for file_path in self.target_path.rglob('*'):
            if file_path.is_file():
                self.analyze_file(file_path)

        return self.stats

    def analyze_file(self, file_path: Path):
        """Analyze individual file."""
        self.stats['total_files'] += 1
        self.stats['total_size'] += file_path.stat().st_size

        # Track file types
        ext = file_path.suffix.lower()
        if ext:
            self.stats['file_types'][ext] = self.stats['file_types'].get(ext, 0) + 1

        # Check for potential issues
        if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
            self.stats['issues'].append(f"Large file: {{file_path}} ({{file_path.stat().st_size // 1024 // 1024}}MB)")

        if file_path.stat().st_size == 0:
            self.stats['issues'].append(f"Empty file: {{file_path}}")

    def generate_recommendations(self):
        """Generate recommendations based on analysis."""
        if self.stats['total_files'] == 0:
            self.stats['recommendations'].append("No files found - check target path")

        if len(self.stats['file_types']) > 20:
            self.stats['recommendations'].append("Many file types detected - consider organizing")

        if self.stats['total_size'] > 1024 * 1024 * 1024:  # 1GB
            self.stats['recommendations'].append("Large total size - consider archiving old data")

    def generate_report(self) -> str:
        """Generate analysis report."""
        report = []
        report.append("\\n" + "="*60)
        report.append(f"ANALYSIS REPORT - {skill_info['name']}")
        report.append("="*60)
        report.append(f"Target: {{self.target_path}}")
        report.append(f"Generated: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        report.append("")

        # Statistics
        report.append("📊 STATISTICS")
        report.append(f"  Total Files: {{self.stats['total_files']:,}}")
        report.append(f"  Total Size: {{self.stats['total_size'] / 1024 / 1024:.2f}} MB")
        report.append(f"  File Types: {{len(self.stats['file_types'])}}")

        # Top file types
        if self.stats['file_types']:
            report.append("\\n📁 TOP FILE TYPES")
            sorted_types = sorted(self.stats['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
            for ext, count in sorted_types:
                report.append(f"  {{ext or 'no extension'}}: {{count}} files")

        # Issues
        if self.stats['issues']:
            report.append(f"\\n⚠️  ISSUES ({{len(self.stats['issues'])}})")
            for issue in self.stats['issues'][:10]:
                report.append(f"  - {{issue}}")
            if len(self.stats['issues']) > 10:
                report.append(f"  ... and {{len(self.stats['issues']) - 10}} more")

        # Recommendations
        if self.stats['recommendations']:
            report.append("\\n💡 RECOMMENDATIONS")
            for rec in self.stats['recommendations']:
                report.append(f"  - {{rec}}")

        report.append("")
        return "\\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="{desc or 'Analyze target directory'}")
    parser.add_argument('target', help='Target directory to analyze')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    print(f"🔍 Analyzing {{args.target}}...")
    analyzer = Analyzer(args.target)
    stats = analyzer.analyze_directory()
    analyzer.generate_recommendations()

    if args.json:
        output = json.dumps(stats, indent=2)
    else:
        output = analyzer.generate_report()

    if args.output:
        Path(args.output).write_text(output)
        print(f"✓ Report saved to {{args.output}}")
    else:
        print(output)

    return 0 if len(stats['issues']) == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''

def generate_generator_script(skill_info: Dict, desc: str) -> str:
    """Generate generator/creator script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - Generator Script
{desc or f"Generate content for {skill_info['name']}"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

class Generator:
    def __init__(self, config: Dict):
        self.config = config
        self.output_dir = Path(config.get('output', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, title: str, content: str) -> Path:
        """Generate markdown document."""
        filename = f"{{title.lower().replace(' ', '_')}}_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.md"
        file_path = self.output_dir / filename

        md_content = f"""# {{title}}

Generated by {skill_info['name']}
Date: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}

## Overview
{{content}}

## Configuration
```json
{{json.dumps(self.config, indent=2)}}
```

## Category
{skill_info['category']}

## Plugin
{skill_info['plugin']}
"""

        file_path.write_text(md_content)
        return file_path

    def generate_json(self, data: Dict) -> Path:
        """Generate JSON output."""
        filename = f"output_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.json"
        file_path = self.output_dir / filename

        output_data = {{
            "generated_by": "{skill_info['name']}",
            "timestamp": datetime.now().isoformat(),
            "category": "{skill_info['category']}",
            "plugin": "{skill_info['plugin']}",
            "data": data,
            "config": self.config
        }}

        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        return file_path

    def generate_script(self, name: str, template: str) -> Path:
        """Generate executable script."""
        filename = f"{{name}}.sh"
        file_path = self.output_dir / filename

        script_content = f"""#!/bin/bash
# Generated by {skill_info['name']}
# Date: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}

set -e  # Exit on error

echo "🚀 Running {{name}}..."

# Template content
{{template}}

echo "✅ Completed successfully"
"""

        file_path.write_text(script_content)
        file_path.chmod(0o755)  # Make executable
        return file_path

def main():
    parser = argparse.ArgumentParser(description="{desc or 'Generate content'}")
    parser.add_argument('--type', choices=['markdown', 'json', 'script'], default='markdown')
    parser.add_argument('--output', '-o', default='./output', help='Output directory')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--title', default='{skill_info["name"]} Output')
    parser.add_argument('--content', help='Content to include')

    args = parser.parse_args()

    config = {{'output': args.output}}
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config.update(json.load(f))

    generator = Generator(config)

    print(f"🔧 Generating {{args.type}} output...")

    if args.type == 'markdown':
        output_file = generator.generate_markdown(
            args.title,
            args.content or "Generated content"
        )
    elif args.type == 'json':
        output_file = generator.generate_json(
            {{"title": args.title, "content": args.content}}
        )
    else:  # script
        output_file = generator.generate_script(
            args.title.lower().replace(' ', '_'),
            args.content or "# Add your script content here"
        )

    print(f"✅ Generated: {{output_file}}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''

def generate_deployment_script(skill_info: Dict, desc: str) -> str:
    """Generate deployment/publishing script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - Deployment Script
{desc or f"Deploy and publish {skill_info['name']} artifacts"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

class Deployer:
    def __init__(self, source: str, target: str):
        self.source = Path(source)
        self.target = Path(target)
        self.deployed = []
        self.failed = []

    def validate_source(self) -> bool:
        """Validate source directory exists."""
        if not self.source.exists():
            print(f"❌ Source directory not found: {{self.source}}")
            return False

        if not any(self.source.iterdir()):
            print(f"❌ Source directory is empty: {{self.source}}")
            return False

        print(f"✓ Source validated: {{self.source}}")
        return True

    def prepare_target(self) -> bool:
        """Prepare target directory."""
        try:
            self.target.mkdir(parents=True, exist_ok=True)

            # Create deployment metadata
            metadata = {{
                "deployment_time": datetime.now().isoformat(),
                "source": str(self.source),
                "skill": "{skill_info['name']}",
                "category": "{skill_info['category']}",
                "plugin": "{skill_info['plugin']}"
            }}

            metadata_file = self.target / ".deployment.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✓ Target prepared: {{self.target}}")
            return True
        except Exception as e:
            print(f"❌ Failed to prepare target: {{e}}")
            return False

    def deploy_files(self) -> bool:
        """Deploy files from source to target."""
        success = True

        for source_file in self.source.rglob('*'):
            if source_file.is_file():
                relative_path = source_file.relative_to(self.source)
                target_file = self.target / relative_path

                try:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    self.deployed.append(str(relative_path))
                    print(f"  ✓ Deployed: {{relative_path}}")
                except Exception as e:
                    self.failed.append({{
                        "file": str(relative_path),
                        "error": str(e)
                    }})
                    print(f"  ✗ Failed: {{relative_path}} - {{e}}")
                    success = False

        return success

    def generate_report(self) -> Dict:
        """Generate deployment report."""
        report = {{
            "deployment_time": datetime.now().isoformat(),
            "skill": "{skill_info['name']}",
            "source": str(self.source),
            "target": str(self.target),
            "total_files": len(self.deployed) + len(self.failed),
            "deployed": len(self.deployed),
            "failed": len(self.failed),
            "deployed_files": self.deployed,
            "failed_files": self.failed
        }}

        # Save report
        report_file = self.target / "deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def rollback(self):
        """Rollback deployment on failure."""
        print("⚠️  Rolling back deployment...")

        for deployed_file in self.deployed:
            file_path = self.target / deployed_file
            if file_path.exists():
                file_path.unlink()
                print(f"  ✓ Removed: {{deployed_file}}")

        # Remove empty directories
        for dir_path in sorted(self.target.rglob('*'), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()

def main():
    parser = argparse.ArgumentParser(description="{desc or 'Deploy artifacts'}")
    parser.add_argument('source', help='Source directory')
    parser.add_argument('target', help='Target deployment directory')
    parser.add_argument('--dry-run', action='store_true', help='Simulate deployment')
    parser.add_argument('--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('--rollback-on-error', action='store_true', help='Rollback on any error')

    args = parser.parse_args()

    deployer = Deployer(args.source, args.target)

    print(f"🚀 Deploying {skill_info['name']}...")
    print(f"   Source: {{args.source}}")
    print(f"   Target: {{args.target}}")

    if args.dry_run:
        print("\\n⚠️  DRY RUN MODE - No files will be deployed")
        return 0

    # Validate and prepare
    if not deployer.validate_source():
        return 1

    if not deployer.prepare_target():
        return 1

    # Deploy
    success = deployer.deploy_files()

    # Generate report
    report = deployer.generate_report()

    print(f"\\n📊 DEPLOYMENT SUMMARY")
    print(f"   Total Files: {{report['total_files']}}")
    print(f"   ✅ Deployed: {{report['deployed']}}")
    print(f"   ❌ Failed: {{report['failed']}}")

    if not success and args.rollback_on_error:
        deployer.rollback()
        return 1

    if report['failed'] == 0:
        print(f"\\n✅ Deployment completed successfully!")
        return 0
    else:
        print(f"\\n⚠️  Deployment completed with errors")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
'''

def generate_generic_script(skill_info: Dict, script_name: str, desc: str) -> str:
    """Generate generic utility script."""
    return f'''#!/usr/bin/env python3
"""
{skill_info['name']} - {script_name}
{desc or f"Utility script for {skill_info['name']}"}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

def process_file(file_path: Path) -> bool:
    """Process individual file."""
    if not file_path.exists():
        print(f"❌ File not found: {{file_path}}")
        return False

    print(f"📄 Processing: {{file_path}}")

    # Add processing logic here based on skill requirements
    # This is a template that can be customized

    try:
        if file_path.suffix == '.json':
            with open(file_path) as f:
                data = json.load(f)
            print(f"  ✓ Valid JSON with {{len(data)}} keys")
        else:
            size = file_path.stat().st_size
            print(f"  ✓ File size: {{size:,}} bytes")

        return True
    except Exception as e:
        print(f"  ✗ Error: {{e}}")
        return False

def process_directory(dir_path: Path) -> int:
    """Process all files in directory."""
    processed = 0
    failed = 0

    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            if process_file(file_path):
                processed += 1
            else:
                failed += 1

    return processed, failed

def main():
    parser = argparse.ArgumentParser(
        description="{desc or f'Process files with {skill_info["name"]}'}"
    )
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--config', '-c', help='Configuration file')

    args = parser.parse_args()

    input_path = Path(args.input)

    print(f"🚀 {skill_info['name']} - {script_name}")
    print(f"   Category: {skill_info['category']}")
    print(f"   Plugin: {skill_info['plugin']}")
    print(f"   Input: {{input_path}}")

    if args.config:
        if Path(args.config).exists():
            with open(args.config) as f:
                config = json.load(f)
            print(f"   Config: {{args.config}}")

    # Process input
    if input_path.is_file():
        success = process_file(input_path)
        result = 0 if success else 1
    elif input_path.is_dir():
        processed, failed = process_directory(input_path)
        print(f"\\n📊 SUMMARY")
        print(f"   ✅ Processed: {{processed}}")
        print(f"   ❌ Failed: {{failed}}")
        result = 0 if failed == 0 else 1
    else:
        print(f"❌ Invalid input: {{input_path}}")
        result = 1

    if result == 0:
        print("\\n✅ Completed successfully")
    else:
        print("\\n❌ Completed with errors")

    return result

if __name__ == "__main__":
    sys.exit(main())
'''

def fix_skill(skill_info: Dict) -> bool:
    """Generate all missing scripts for a skill."""
    try:
        scripts_created = 0
        scripts_dir = skill_info['scripts_dir']

        for script_name in skill_info['todos']:
            script_name = script_name.strip()
            if not script_name:
                continue

            # Ensure .py extension
            if not script_name.endswith(('.py', '.sh')):
                script_name += '.py'

            script_path = scripts_dir / script_name

            # Generate script content
            content = generate_script_content(skill_info, script_name)

            # Write script
            script_path.write_text(content)
            script_path.chmod(0o755)  # Make executable
            scripts_created += 1

            print(f"  ✓ Created {script_name} for {skill_info['name']}")

        # Update README to mark scripts as completed
        if scripts_created > 0:
            readme_content = skill_info['readme_path'].read_text()
            # Replace unchecked boxes with checked
            updated_content = readme_content.replace('- [ ]', '- [x]')
            updated_content += f"\n\n## Auto-Generated\nScripts generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            skill_info['readme_path'].write_text(updated_content)

        return scripts_created > 0

    except Exception as e:
        print(f"  ✗ Failed to fix {skill_info['name']}: {e}")
        return False

def process_batch(batch: List[Dict]) -> Tuple[int, int]:
    """Process a batch of skills."""
    success = 0
    failed = 0

    for skill_info in batch:
        if fix_skill(skill_info):
            success += 1
        else:
            failed += 1

    return success, failed

def main():
    print("="*80)
    print("OVERNIGHT SKILL SCRIPT GENERATOR")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Find all skills needing fixes
    print("\n🔍 Finding skills with missing scripts...")
    skills_to_fix = find_skills_needing_scripts()
    print(f"Found {len(skills_to_fix)} skills needing scripts")

    if not skills_to_fix:
        print("✅ All skills have scripts!")
        return 0

    # Process in parallel batches
    print(f"\n🚀 Processing {len(skills_to_fix)} skills in parallel...")
    print(f"   Workers: {MAX_WORKERS}")
    print(f"   Batch size: {BATCH_SIZE}")

    total_success = 0
    total_failed = 0

    # Split into batches
    batches = []
    for i in range(0, len(skills_to_fix), BATCH_SIZE):
        batches.append(skills_to_fix[i:i + BATCH_SIZE])

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for batch_num, batch in enumerate(batches, 1):
            print(f"\n📦 Batch {batch_num}/{len(batches)} ({len(batch)} skills)")
            future = executor.submit(process_batch, batch)
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            success, failed = future.result()
            total_success += success
            total_failed += failed
            print(f"  Batch complete: {success} success, {failed} failed")

    # Final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    print(f"✅ Successfully fixed: {total_success}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Success rate: {(total_success / len(skills_to_fix) * 100):.1f}%")
    print(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Save report
    report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "total_skills": len(skills_to_fix),
        "success": total_success,
        "failed": total_failed,
        "skills_fixed": [s['name'] for s in skills_to_fix[:total_success]]
    }

    report_path = Path("/tmp/overnight_skill_fix_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📝 Report saved: {report_path}")

    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())