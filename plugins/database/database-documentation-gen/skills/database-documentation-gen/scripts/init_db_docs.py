#!/usr/bin/env python3
"""
Database Documentation Initializer
Initializes a database documentation project with proper structure and configuration.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

def create_project_structure(project_name, output_dir):
    """Create the documentation project directory structure."""
    base_path = Path(output_dir) / project_name

    # Create directory structure
    directories = [
        base_path,
        base_path / 'schemas',
        base_path / 'tables',
        base_path / 'views',
        base_path / 'procedures',
        base_path / 'diagrams',
        base_path / 'exports'
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

    return base_path

def create_config_file(base_path, db_type, connection_details):
    """Create the configuration file for the documentation project."""
    config = {
        "project": {
            "name": base_path.name,
            "created": datetime.now().isoformat(),
            "version": "1.0.0"
        },
        "database": {
            "type": db_type,
            "connection": connection_details
        },
        "documentation": {
            "include_schemas": True,
            "include_tables": True,
            "include_views": True,
            "include_procedures": True,
            "generate_erd": True,
            "output_format": ["markdown", "html", "pdf"]
        },
        "export": {
            "format": "markdown",
            "include_metadata": True,
            "include_indexes": True,
            "include_constraints": True
        }
    }

    config_path = base_path / 'db_docs_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Created configuration file: {config_path}")
    return config_path

def create_readme(base_path, project_name):
    """Create a README file for the documentation project."""
    readme_content = f"""# {project_name} Database Documentation

## Overview
This directory contains the automatically generated documentation for the {project_name} database.

## Structure
- `schemas/` - Schema documentation
- `tables/` - Table definitions and documentation
- `views/` - View definitions
- `procedures/` - Stored procedures and functions
- `diagrams/` - ERD and other diagrams
- `exports/` - Exported documentation in various formats

## Configuration
See `db_docs_config.json` for project configuration.

## Generated
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    readme_path = base_path / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"✓ Created README: {readme_path}")
    return readme_path

def main():
    parser = argparse.ArgumentParser(description='Initialize database documentation project')
    parser.add_argument('--project', '-p', required=True, help='Project name')
    parser.add_argument('--output', '-o', default='.', help='Output directory (default: current directory)')
    parser.add_argument('--db-type', '-t', default='postgresql',
                       choices=['postgresql', 'mysql', 'sqlite', 'sqlserver', 'oracle'],
                       help='Database type (default: postgresql)')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, help='Database port')
    parser.add_argument('--database', '-d', help='Database name')
    parser.add_argument('--user', '-u', help='Database user')

    args = parser.parse_args()

    # Set default ports based on database type
    if not args.port:
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'sqlite': None,
            'sqlserver': 1433,
            'oracle': 1521
        }
        args.port = default_ports.get(args.db_type)

    # Prepare connection details
    connection_details = {
        'host': args.host,
        'port': args.port,
        'database': args.database or args.project,
        'user': args.user or 'dbuser'
    }

    # Remove None values
    connection_details = {k: v for k, v in connection_details.items() if v is not None}

    print(f"\n🚀 Initializing database documentation project: {args.project}")
    print("=" * 60)

    # Create project structure
    base_path = create_project_structure(args.project, args.output)

    # Create configuration file
    config_path = create_config_file(base_path, args.db_type, connection_details)

    # Create README
    readme_path = create_readme(base_path, args.project)

    print("=" * 60)
    print(f"✅ Project initialized successfully at: {base_path}")
    print(f"\nNext steps:")
    print(f"1. Update connection details in: {config_path}")
    print(f"2. Run: python validate_config.py --config {config_path}")
    print(f"3. Generate ERD: python erd_generator.py --config {config_path}")

    return 0

if __name__ == '__main__':
    sys.exit(main())