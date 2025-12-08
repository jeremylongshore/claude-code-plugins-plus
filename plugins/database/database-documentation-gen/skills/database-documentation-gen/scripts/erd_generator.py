#!/usr/bin/env python3
"""
ERD (Entity Relationship Diagram) Generator
Generates ERD diagrams from database schema using Mermaid or PlantUML syntax.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ERDGenerator:
    """Generates Entity Relationship Diagrams from database schema."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = None
        self.schema = {}

    def load_config(self) -> bool:
        """Load the configuration file."""
        if not self.config_path.exists():
            print(f"❌ Configuration file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return False

    def load_schema(self, schema_file: Optional[str] = None) -> bool:
        """Load database schema from file or generate sample schema."""
        if schema_file and Path(schema_file).exists():
            try:
                with open(schema_file, 'r') as f:
                    self.schema = json.load(f)
                return True
            except Exception as e:
                print(f"⚠️  Could not load schema file: {e}")

        # Generate sample schema for demonstration
        self.schema = self.generate_sample_schema()
        return True

    def generate_sample_schema(self) -> Dict:
        """Generate a sample database schema for demonstration."""
        return {
            "database": self.config.get('database', {}).get('database', 'sample_db'),
            "tables": {
                "users": {
                    "columns": {
                        "id": {"type": "INTEGER", "primary_key": True},
                        "username": {"type": "VARCHAR(50)", "unique": True, "not_null": True},
                        "email": {"type": "VARCHAR(100)", "unique": True, "not_null": True},
                        "created_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    }
                },
                "posts": {
                    "columns": {
                        "id": {"type": "INTEGER", "primary_key": True},
                        "user_id": {"type": "INTEGER", "foreign_key": "users.id"},
                        "title": {"type": "VARCHAR(200)", "not_null": True},
                        "content": {"type": "TEXT"},
                        "published": {"type": "BOOLEAN", "default": "FALSE"},
                        "created_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    }
                },
                "comments": {
                    "columns": {
                        "id": {"type": "INTEGER", "primary_key": True},
                        "post_id": {"type": "INTEGER", "foreign_key": "posts.id"},
                        "user_id": {"type": "INTEGER", "foreign_key": "users.id"},
                        "content": {"type": "TEXT", "not_null": True},
                        "created_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    }
                },
                "categories": {
                    "columns": {
                        "id": {"type": "INTEGER", "primary_key": True},
                        "name": {"type": "VARCHAR(50)", "unique": True, "not_null": True},
                        "description": {"type": "TEXT"}
                    }
                },
                "post_categories": {
                    "columns": {
                        "post_id": {"type": "INTEGER", "foreign_key": "posts.id"},
                        "category_id": {"type": "INTEGER", "foreign_key": "categories.id"}
                    }
                }
            }
        }

    def generate_mermaid_erd(self) -> str:
        """Generate ERD in Mermaid format."""
        lines = ["```mermaid", "erDiagram"]

        # Add table definitions
        for table_name, table_info in self.schema.get('tables', {}).items():
            lines.append(f"    {table_name} {{")

            for col_name, col_info in table_info.get('columns', {}).items():
                col_type = col_info.get('type', 'VARCHAR')
                pk = " PK" if col_info.get('primary_key') else ""
                fk = " FK" if col_info.get('foreign_key') else ""
                uk = " UK" if col_info.get('unique') else ""

                # Clean type for Mermaid
                clean_type = col_type.split('(')[0]
                lines.append(f"        {clean_type} {col_name}{pk}{fk}{uk}")

            lines.append("    }")

        # Add relationships
        relationships = self.extract_relationships()
        for rel in relationships:
            lines.append(f"    {rel['from_table']} ||--o{{ {rel['to_table']} : {rel['relation']}")

        lines.append("```")
        return "\n".join(lines)

    def generate_plantuml_erd(self) -> str:
        """Generate ERD in PlantUML format."""
        lines = [
            "@startuml",
            "!define primary_key(x) <b><color:b8861b><&key></color> x</b>",
            "!define foreign_key(x) <color:aaaaaa><&key></color> x",
            "!define column(x) <color:efefef><&media-record></color> x",
            "!define table(x) entity x << (T, white) >>",
            "",
            "skinparam backgroundColor #EEEEEE",
            ""
        ]

        # Add table entities
        for table_name, table_info in self.schema.get('tables', {}).items():
            lines.append(f"table({table_name}) {{")

            for col_name, col_info in table_info.get('columns', {}).items():
                col_type = col_info.get('type', 'VARCHAR')

                if col_info.get('primary_key'):
                    lines.append(f"  primary_key({col_name}): {col_type}")
                elif col_info.get('foreign_key'):
                    lines.append(f"  foreign_key({col_name}): {col_type}")
                else:
                    lines.append(f"  column({col_name}): {col_type}")

            lines.append("}")
            lines.append("")

        # Add relationships
        relationships = self.extract_relationships()
        for rel in relationships:
            lines.append(f"{rel['from_table']} ||--o{{ {rel['to_table']}")

        lines.append("@enduml")
        return "\n".join(lines)

    def generate_dbml(self) -> str:
        """Generate ERD in DBML (Database Markup Language) format."""
        lines = [f"// Database: {self.schema.get('database', 'database')}", ""]

        # Add table definitions
        for table_name, table_info in self.schema.get('tables', {}).items():
            lines.append(f"Table {table_name} {{")

            for col_name, col_info in table_info.get('columns', {}).items():
                col_type = col_info.get('type', 'VARCHAR')
                attributes = []

                if col_info.get('primary_key'):
                    attributes.append('pk')
                if col_info.get('unique'):
                    attributes.append('unique')
                if col_info.get('not_null'):
                    attributes.append('not null')
                if col_info.get('default'):
                    attributes.append(f"default: {col_info['default']}")

                attr_str = f" [{', '.join(attributes)}]" if attributes else ""
                lines.append(f"  {col_name} {col_type}{attr_str}")

            lines.append("}")
            lines.append("")

        # Add relationships
        relationships = self.extract_relationships()
        for rel in relationships:
            lines.append(f"Ref: {rel['from_table']}.{rel['from_column']} > {rel['to_table']}.id")

        return "\n".join(lines)

    def extract_relationships(self) -> List[Dict]:
        """Extract foreign key relationships from schema."""
        relationships = []

        for table_name, table_info in self.schema.get('tables', {}).items():
            for col_name, col_info in table_info.get('columns', {}).items():
                if 'foreign_key' in col_info:
                    fk_parts = col_info['foreign_key'].split('.')
                    if len(fk_parts) == 2:
                        relationships.append({
                            'from_table': table_name,
                            'from_column': col_name,
                            'to_table': fk_parts[0],
                            'to_column': fk_parts[1],
                            'relation': f"{col_name}_fk"
                        })

        return relationships

    def save_diagram(self, content: str, format_type: str, output_dir: Path):
        """Save the generated diagram to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"erd_{self.schema.get('database', 'database')}_{timestamp}.{format_type}"
        filepath = output_dir / filename

        with open(filepath, 'w') as f:
            f.write(content)

        print(f"✓ Generated {format_type.upper()} diagram: {filepath}")
        return filepath

    def generate_all_formats(self, output_dir: Path):
        """Generate ERD in all supported formats."""
        formats = {
            'mermaid': ('md', self.generate_mermaid_erd),
            'plantuml': ('puml', self.generate_plantuml_erd),
            'dbml': ('dbml', self.generate_dbml)
        }

        generated_files = []
        for format_name, (ext, generator) in formats.items():
            try:
                content = generator()
                filepath = self.save_diagram(content, ext, output_dir)
                generated_files.append(filepath)
            except Exception as e:
                print(f"⚠️  Error generating {format_name}: {e}")

        return generated_files

def main():
    parser = argparse.ArgumentParser(description='Generate ERD diagrams from database schema')
    parser.add_argument('--config', '-c', required=True, help='Path to configuration file')
    parser.add_argument('--schema', '-s', help='Path to schema JSON file (optional)')
    parser.add_argument('--format', '-f', choices=['mermaid', 'plantuml', 'dbml', 'all'],
                       default='all', help='Output format (default: all)')
    parser.add_argument('--output', '-o', help='Output directory (default: ./diagrams)')

    args = parser.parse_args()

    # Initialize generator
    generator = ERDGenerator(args.config)

    # Load configuration
    if not generator.load_config():
        return 1

    print(f"\n🎨 Generating ERD for database: {generator.config.get('database', {}).get('database', 'Unknown')}")
    print("=" * 60)

    # Load or generate schema
    generator.load_schema(args.schema)

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        # Use diagrams directory in project structure
        output_dir = Path(args.config).parent / 'diagrams'

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate diagrams
    if args.format == 'all':
        generated = generator.generate_all_formats(output_dir)
        print(f"\n✅ Generated {len(generated)} diagram(s)")
    else:
        format_ext = {
            'mermaid': 'md',
            'plantuml': 'puml',
            'dbml': 'dbml'
        }
        generator_func = {
            'mermaid': generator.generate_mermaid_erd,
            'plantuml': generator.generate_plantuml_erd,
            'dbml': generator.generate_dbml
        }

        content = generator_func[args.format]()
        filepath = generator.save_diagram(content, format_ext[args.format], output_dir)
        print(f"\n✅ Generated {args.format.upper()} diagram")

    print("\n📝 Next steps:")
    print("1. View generated diagrams in:", output_dir)
    print("2. For Mermaid: Copy content to any Markdown file or Mermaid Live Editor")
    print("3. For PlantUML: Use PlantUML server or IDE plugin to render")
    print("4. For DBML: Use dbdiagram.io or dbdocs.io to visualize")

    return 0

if __name__ == '__main__':
    sys.exit(main())