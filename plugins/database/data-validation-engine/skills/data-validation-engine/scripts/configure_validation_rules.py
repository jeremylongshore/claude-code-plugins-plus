#!/usr/bin/env python3
"""
Interactively configure data validation rules for a database table.

This script allows users to define and customize validation rules for database tables,
which are then saved in a configuration file for use by other validation scripts.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ValidationRuleConfigurator:
    """Interactively configure validation rules."""

    def __init__(self):
        """Initialize configurator."""
        self.rules = []
        self.table_name = ""
        self.database = ""

    def add_not_null_rule(self, column: str):
        """
        Add a NOT NULL validation rule.

        Args:
            column: Column name
        """
        self.rules.append({
            "rule": "not_null",
            "column": column,
            "description": f"Column {column} must not contain NULL values"
        })

    def add_unique_rule(self, column: str):
        """
        Add a UNIQUE validation rule.

        Args:
            column: Column name
        """
        self.rules.append({
            "rule": "unique",
            "column": column,
            "description": f"Column {column} must contain unique values"
        })

    def add_range_rule(
        self,
        column: str,
        min_value: float,
        max_value: float
    ):
        """
        Add a RANGE validation rule.

        Args:
            column: Column name
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.rules.append({
            "rule": "range",
            "column": column,
            "min": min_value,
            "max": max_value,
            "description": f"Column {column} values must be between {min_value} and {max_value}"
        })

    def add_pattern_rule(self, column: str, pattern: str):
        """
        Add a PATTERN (regex) validation rule.

        Args:
            column: Column name
            pattern: Regular expression pattern
        """
        self.rules.append({
            "rule": "pattern",
            "column": column,
            "pattern": pattern,
            "description": f"Column {column} values must match pattern: {pattern}"
        })

    def add_custom_rule(self, column: str, query: str):
        """
        Add a custom SQL validation rule.

        Args:
            column: Column name
            query: Custom SQL query
        """
        self.rules.append({
            "rule": "custom",
            "column": column,
            "query": query,
            "description": f"Custom validation on {column}"
        })

    def remove_rule(self, index: int) -> bool:
        """
        Remove a rule by index.

        Args:
            index: Rule index

        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.rules):
            del self.rules[index]
            return True
        return False

    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "table": self.table_name,
            "database": self.database,
            "created_at": datetime.now().isoformat(),
            "validations": self.rules
        }

    def load_config(self, filepath: str) -> bool:
        """
        Load configuration from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)

            self.table_name = config.get("table", "")
            self.database = config.get("database", "")
            self.rules = config.get("validations", [])

            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return False

    def save_config(self, filepath: str) -> bool:
        """
        Save configuration to JSON file.

        Args:
            filepath: Path to save JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.get_config_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            return False


def interactive_mode(configurator: ValidationRuleConfigurator):
    """
    Run interactive configuration mode.

    Args:
        configurator: ValidationRuleConfigurator instance
    """
    print("\n" + "="*60)
    print("Data Validation Rule Configurator")
    print("="*60 + "\n")

    # Get table and database info
    configurator.table_name = input("Enter table name: ").strip()
    if not configurator.table_name:
        print("Error: Table name is required")
        sys.exit(1)

    configurator.database = input("Enter database name (optional): ").strip()

    print("\nConfigure validation rules for this table.")
    print("Enter 'help' for rule descriptions, 'done' when finished.\n")

    while True:
        print("\nAvailable rules:")
        print("  1. not-null   - Column cannot contain NULL values")
        print("  2. unique     - Column values must be unique")
        print("  3. range      - Column values must be within min/max")
        print("  4. pattern    - Column values must match regex pattern")
        print("  5. custom     - Custom SQL validation query")
        print("  6. list       - Show current rules")
        print("  7. remove     - Remove a rule")
        print("  8. done       - Finish configuration")

        choice = input("\nEnter rule type (1-8): ").strip().lower()

        if choice in ["done", "8"]:
            break
        elif choice == "help":
            print_help()
        elif choice in ["1", "not-null"]:
            column = input("Enter column name: ").strip()
            if column:
                configurator.add_not_null_rule(column)
                print(f"✓ Added NOT NULL rule for {column}")
        elif choice in ["2", "unique"]:
            column = input("Enter column name: ").strip()
            if column:
                configurator.add_unique_rule(column)
                print(f"✓ Added UNIQUE rule for {column}")
        elif choice in ["3", "range"]:
            column = input("Enter column name: ").strip()
            try:
                min_val = float(input("Enter minimum value: "))
                max_val = float(input("Enter maximum value: "))
                configurator.add_range_rule(column, min_val, max_val)
                print(f"✓ Added RANGE rule for {column} [{min_val}, {max_val}]")
            except ValueError:
                print("Error: Invalid numeric values")
        elif choice in ["4", "pattern"]:
            column = input("Enter column name: ").strip()
            pattern = input("Enter regex pattern: ").strip()
            if column and pattern:
                configurator.add_pattern_rule(column, pattern)
                print(f"✓ Added PATTERN rule for {column}")
        elif choice in ["5", "custom"]:
            column = input("Enter column name: ").strip()
            query = input("Enter SQL query: ").strip()
            if column and query:
                configurator.add_custom_rule(column, query)
                print(f"✓ Added CUSTOM rule for {column}")
        elif choice in ["6", "list"]:
            list_rules(configurator)
        elif choice in ["7", "remove"]:
            list_rules(configurator)
            try:
                idx = int(input("Enter rule number to remove: ")) - 1
                if configurator.remove_rule(idx):
                    print(f"✓ Removed rule {idx + 1}")
                else:
                    print("Error: Invalid rule number")
            except ValueError:
                print("Error: Invalid input")
        else:
            print("Invalid choice. Please try again.")

    # Summary and save
    print("\n" + "="*60)
    print("Configuration Summary")
    print("="*60)
    print(f"Table: {configurator.table_name}")
    print(f"Database: {configurator.database or '(none specified)'}")
    print(f"Total Rules: {len(configurator.rules)}\n")

    list_rules(configurator)

    # Save configuration
    save_choice = input("\nSave configuration? (y/n): ").strip().lower()
    if save_choice in ["y", "yes"]:
        filepath = input("Enter filename to save (default: validation_rules.json): ").strip()
        if not filepath:
            filepath = "validation_rules.json"

        if configurator.save_config(filepath):
            print(f"✓ Configuration saved to {filepath}")
        else:
            print("Error: Failed to save configuration")
            sys.exit(1)


def list_rules(configurator: ValidationRuleConfigurator):
    """
    Display configured rules.

    Args:
        configurator: ValidationRuleConfigurator instance
    """
    if not configurator.rules:
        print("No rules configured yet.")
        return

    print("\nConfigured Rules:")
    print("-" * 60)
    for i, rule in enumerate(configurator.rules, 1):
        rule_type = rule.get("rule", "unknown").upper()
        column = rule.get("column", "N/A")
        description = rule.get("description", "")

        print(f"{i}. [{rule_type}] {column}")
        print(f"   {description}")

        # Show additional details based on rule type
        if rule.get("rule") == "range":
            print(f"   Range: [{rule.get('min')}, {rule.get('max')}]")
        elif rule.get("rule") == "pattern":
            print(f"   Pattern: {rule.get('pattern')}")
        elif rule.get("rule") == "custom":
            print(f"   Query: {rule.get('query')}")

    print("-" * 60)


def print_help():
    """Print help information."""
    help_text = r"""
Rule Types:

NOT NULL
  Description: Ensures column contains no NULL values
  Example: Validate that 'user_id' is never NULL

UNIQUE
  Description: Ensures all values in column are unique
  Example: Email addresses must be unique for user table

RANGE
  Description: Ensures numeric values fall within min/max bounds
  Example: Age must be between 0 and 150
           Price must be between 0 and 999999

PATTERN
  Description: Ensures values match a regular expression
  Example: Email format: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
           Phone: ^\+?1?\d{9,15}$

CUSTOM
  Description: Run custom SQL query for complex validations
  Example: SELECT COUNT(*) FROM users WHERE created_at > updated_at
           (Ensures created_at is always before updated_at)
"""
    print(help_text)


def create_from_args(args: argparse.Namespace) -> ValidationRuleConfigurator:
    """
    Create configurator from command-line arguments.

    Args:
        args: Parsed arguments

    Returns:
        Configured ValidationRuleConfigurator
    """
    configurator = ValidationRuleConfigurator()
    configurator.table_name = args.table
    configurator.database = args.database

    # Add rules from arguments
    if args.not_null:
        for column in args.not_null.split(","):
            configurator.add_not_null_rule(column.strip())

    if args.unique:
        for column in args.unique.split(","):
            configurator.add_unique_rule(column.strip())

    if args.range:
        # Format: "column:min:max" or "column:min:max,column2:min2:max2"
        for range_spec in args.range.split(","):
            parts = range_spec.split(":")
            if len(parts) == 3:
                try:
                    column = parts[0].strip()
                    min_val = float(parts[1].strip())
                    max_val = float(parts[2].strip())
                    configurator.add_range_rule(column, min_val, max_val)
                except ValueError:
                    print(f"Warning: Invalid range specification: {range_spec}")

    return configurator


def main():
    """Main entry point for rule configuration."""
    parser = argparse.ArgumentParser(
        description="Configure data validation rules for database tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  %(prog)s

  # Command-line mode with single table
  %(prog)s --table users --database mydb \\
    --not-null id,email \\
    --unique email \\
    --output rules.json

  # With range validation
  %(prog)s --table products --database catalog \\
    --range "price:0:10000,quantity:0:1000000" \\
    --output rules.json

  # Load and modify existing rules
  %(prog)s --load rules.json --not-null phone --output rules.json
        """
    )

    parser.add_argument(
        "--table",
        help="Table name for non-interactive mode"
    )
    parser.add_argument(
        "--database",
        help="Database name"
    )
    parser.add_argument(
        "--not-null",
        help="Comma-separated columns that must not be NULL"
    )
    parser.add_argument(
        "--unique",
        help="Comma-separated columns that must be unique"
    )
    parser.add_argument(
        "--range",
        help="Range validations in format: col:min:max,col2:min2:max2"
    )
    parser.add_argument(
        "--load",
        help="Load existing configuration file"
    )
    parser.add_argument(
        "--output",
        help="Output file for configuration (JSON)"
    )

    args = parser.parse_args()

    try:
        # Determine mode
        if args.load:
            # Load existing config
            configurator = ValidationRuleConfigurator()
            if not configurator.load_config(args.load):
                sys.exit(1)
            print(f"Loaded configuration from {args.load}")
            list_rules(configurator)
        elif args.table:
            # Command-line mode
            configurator = create_from_args(args)
        else:
            # Interactive mode
            configurator = ValidationRuleConfigurator()
            interactive_mode(configurator)
            sys.exit(0)

        # If table specified, save configuration
        if args.table or args.load:
            if args.table and not configurator.table_name:
                configurator.table_name = args.table

            output_file = args.output or "validation_rules.json"

            if configurator.save_config(output_file):
                print(f"\n✓ Configuration saved to {output_file}")
                print(f"Total rules: {len(configurator.rules)}")
                sys.exit(0)
            else:
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
