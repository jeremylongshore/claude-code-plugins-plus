#!/usr/bin/env python3
"""
Configuration Validator for Database Documentation
Validates the configuration file and tests database connectivity.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

class ConfigValidator:
    """Validates database documentation configuration."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = None
        self.errors = []
        self.warnings = []

    def load_config(self) -> bool:
        """Load and parse the configuration file."""
        if not self.config_path.exists():
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print(f"✓ Configuration file loaded: {self.config_path}")
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading configuration: {e}")
            return False

    def validate_structure(self) -> bool:
        """Validate the configuration structure."""
        required_sections = ['project', 'database', 'documentation', 'export']

        for section in required_sections:
            if section not in self.config:
                self.errors.append(f"Missing required section: '{section}'")

        # Validate project section
        if 'project' in self.config:
            project_required = ['name']
            for field in project_required:
                if field not in self.config['project']:
                    self.errors.append(f"Missing required field 'project.{field}'")

        # Validate database section
        if 'database' in self.config:
            db_required = ['type']
            for field in db_required:
                if field not in self.config['database']:
                    self.errors.append(f"Missing required field 'database.{field}'")

            # Validate database type
            valid_db_types = ['postgresql', 'mysql', 'sqlite', 'sqlserver', 'oracle']
            db_type = self.config['database'].get('type', '')
            if db_type not in valid_db_types:
                self.errors.append(f"Invalid database type: '{db_type}'. Must be one of: {valid_db_types}")

        return len(self.errors) == 0

    def validate_connection(self) -> bool:
        """Validate database connection parameters."""
        if 'database' not in self.config or 'connection' not in self.config['database']:
            self.warnings.append("No database connection details provided")
            return True

        conn = self.config['database']['connection']
        db_type = self.config['database'].get('type', 'postgresql')

        # Check required fields based on database type
        if db_type != 'sqlite':
            if 'host' not in conn:
                self.warnings.append("Database host not specified (using 'localhost')")
            if 'database' not in conn:
                self.errors.append("Database name is required")

        # Check for credentials
        if 'user' not in conn and db_type != 'sqlite':
            self.warnings.append("Database user not specified")

        # Validate port if provided
        if 'port' in conn:
            try:
                port = int(conn['port'])
                if port < 1 or port > 65535:
                    self.errors.append(f"Invalid port number: {port}")
            except (ValueError, TypeError):
                self.errors.append(f"Port must be a number: {conn['port']}")

        return len(self.errors) == 0

    def validate_output_formats(self) -> bool:
        """Validate output format specifications."""
        if 'documentation' in self.config:
            doc_config = self.config['documentation']

            if 'output_format' in doc_config:
                valid_formats = ['markdown', 'html', 'pdf', 'json', 'xml']
                formats = doc_config['output_format']

                if isinstance(formats, list):
                    for fmt in formats:
                        if fmt not in valid_formats:
                            self.warnings.append(f"Unknown output format: '{fmt}'")
                elif isinstance(formats, str):
                    if formats not in valid_formats:
                        self.warnings.append(f"Unknown output format: '{formats}'")
                else:
                    self.errors.append("Output format must be a string or list of strings")

        if 'export' in self.config:
            export_config = self.config['export']

            if 'format' in export_config:
                valid_formats = ['markdown', 'html', 'json', 'csv']
                if export_config['format'] not in valid_formats:
                    self.warnings.append(f"Unknown export format: '{export_config['format']}'")

        return len(self.errors) == 0

    def validate_project_structure(self) -> bool:
        """Validate that the project directory structure exists."""
        if not self.config or 'project' not in self.config:
            return False

        # Check if we're in a documentation project directory
        project_dir = self.config_path.parent
        expected_dirs = ['schemas', 'tables', 'views', 'procedures', 'diagrams', 'exports']

        missing_dirs = []
        for dir_name in expected_dirs:
            dir_path = project_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            self.warnings.append(f"Missing project directories: {', '.join(missing_dirs)}")
            self.warnings.append("Run 'init_db_docs.py' to create project structure")

        return True

    def test_connectivity(self) -> bool:
        """Test database connectivity (placeholder for actual connection test)."""
        if 'database' not in self.config or 'connection' not in self.config['database']:
            self.warnings.append("Cannot test connectivity - no connection details")
            return True

        db_type = self.config['database'].get('type')
        conn = self.config['database']['connection']

        print(f"\n📡 Testing connectivity to {db_type} database...")
        print(f"   Host: {conn.get('host', 'localhost')}")
        print(f"   Port: {conn.get('port', 'default')}")
        print(f"   Database: {conn.get('database', 'N/A')}")

        # In a real implementation, this would attempt actual connection
        # For now, we'll just validate the parameters exist
        self.warnings.append("Database connectivity test not implemented (would require database drivers)")

        return True

    def generate_report(self) -> Tuple[bool, str]:
        """Generate validation report."""
        report_lines = []
        report_lines.append("\n" + "=" * 60)
        report_lines.append("CONFIGURATION VALIDATION REPORT")
        report_lines.append("=" * 60)

        if self.config:
            report_lines.append(f"\nProject: {self.config.get('project', {}).get('name', 'Unknown')}")
            report_lines.append(f"Config file: {self.config_path}")

        if self.errors:
            report_lines.append(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                report_lines.append(f"   • {error}")
        else:
            report_lines.append("\n✅ No errors found")

        if self.warnings:
            report_lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                report_lines.append(f"   • {warning}")
        else:
            report_lines.append("\n✅ No warnings")

        report_lines.append("\n" + "=" * 60)

        is_valid = len(self.errors) == 0
        if is_valid:
            report_lines.append("✅ CONFIGURATION IS VALID")
        else:
            report_lines.append("❌ CONFIGURATION HAS ERRORS - Please fix before proceeding")

        report_lines.append("=" * 60 + "\n")

        return is_valid, "\n".join(report_lines)

    def validate_all(self) -> bool:
        """Run all validation checks."""
        if not self.load_config():
            return False

        checks = [
            ("Structure", self.validate_structure),
            ("Connection", self.validate_connection),
            ("Output Formats", self.validate_output_formats),
            ("Project Structure", self.validate_project_structure),
            ("Connectivity", self.test_connectivity)
        ]

        print("\nRunning validation checks...")
        print("-" * 40)

        all_passed = True
        for check_name, check_func in checks:
            print(f"Checking {check_name}...", end=" ")
            if check_func():
                print("✓")
            else:
                print("✗")
                all_passed = False

        print("-" * 40)
        return all_passed

def main():
    parser = argparse.ArgumentParser(description='Validate database documentation configuration')
    parser.add_argument('--config', '-c', required=True, help='Path to configuration file')
    parser.add_argument('--output', '-o', help='Output validation report to file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output except errors')

    args = parser.parse_args()

    validator = ConfigValidator(args.config)

    # Run validation
    validator.validate_all()

    # Generate report
    is_valid, report = validator.generate_report()

    # Output report
    if not args.quiet:
        print(report)

    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")

    # Return appropriate exit code
    return 0 if is_valid else 1

if __name__ == '__main__':
    sys.exit(main())