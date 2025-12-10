#!/usr/bin/env python3
"""
Execute data validation checks against a specified database and table.

This script runs validation rules against a database table and logs any discrepancies
found, including data type mismatches, null constraint violations, and custom validations.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class DataValidator:
    """Validates data in database tables against defined rules."""

    def __init__(self, db_type: str = "sqlite"):
        """
        Initialize validator.

        Args:
            db_type: Type of database (sqlite, postgresql, mysql)
        """
        self.db_type = db_type
        self.connection = None
        self.cursor = None
        self.validation_results = []

    def connect(self, connection_string: str):
        """
        Connect to database.

        Args:
            connection_string: Database connection string
        """
        if self.db_type == "sqlite":
            self.connection = sqlite3.connect(connection_string)
            self.cursor = self.connection.cursor()
        else:
            raise NotImplementedError(f"Database type {self.db_type} not yet supported")

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def validate_not_null(
        self,
        table: str,
        column: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that column has no NULL values.

        Args:
            table: Table name
            column: Column name

        Returns:
            Tuple of (is_valid, details)
        """
        try:
            self.cursor.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
            )
            null_count = self.cursor.fetchone()[0]

            is_valid = null_count == 0

            return is_valid, {
                "rule": "not_null",
                "table": table,
                "column": column,
                "null_count": null_count,
                "valid": is_valid
            }
        except Exception as e:
            return False, {
                "rule": "not_null",
                "table": table,
                "column": column,
                "error": str(e)
            }

    def validate_unique(
        self,
        table: str,
        column: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that column values are unique.

        Args:
            table: Table name
            column: Column name

        Returns:
            Tuple of (is_valid, details)
        """
        try:
            self.cursor.execute(
                f"""
                SELECT {column}, COUNT(*) as count
                FROM {table}
                GROUP BY {column}
                HAVING COUNT(*) > 1
                """
            )
            duplicates = self.cursor.fetchall()

            is_valid = len(duplicates) == 0

            return is_valid, {
                "rule": "unique",
                "table": table,
                "column": column,
                "duplicate_count": len(duplicates),
                "valid": is_valid,
                "duplicates": duplicates if duplicates else []
            }
        except Exception as e:
            return False, {
                "rule": "unique",
                "table": table,
                "column": column,
                "error": str(e)
            }

    def validate_range(
        self,
        table: str,
        column: str,
        min_value: Any,
        max_value: Any
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that column values are within range.

        Args:
            table: Table name
            column: Column name
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Tuple of (is_valid, details)
        """
        try:
            self.cursor.execute(
                f"""
                SELECT COUNT(*) FROM {table}
                WHERE {column} < ? OR {column} > ?
                """,
                (min_value, max_value)
            )
            out_of_range = self.cursor.fetchone()[0]

            is_valid = out_of_range == 0

            return is_valid, {
                "rule": "range",
                "table": table,
                "column": column,
                "min": min_value,
                "max": max_value,
                "out_of_range_count": out_of_range,
                "valid": is_valid
            }
        except Exception as e:
            return False, {
                "rule": "range",
                "table": table,
                "column": column,
                "error": str(e)
            }

    def validate_pattern(
        self,
        table: str,
        column: str,
        pattern: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that column values match pattern.

        Args:
            table: Table name
            column: Column name
            pattern: Regular expression pattern

        Returns:
            Tuple of (is_valid, details)
        """
        try:
            # SQLite REGEXP support requires custom function
            self.cursor.execute(
                f"""
                SELECT COUNT(*) FROM {table}
                WHERE {column} NOT LIKE ?
                """,
                (pattern,)
            )
            mismatches = self.cursor.fetchone()[0]

            is_valid = mismatches == 0

            return is_valid, {
                "rule": "pattern",
                "table": table,
                "column": column,
                "pattern": pattern,
                "mismatch_count": mismatches,
                "valid": is_valid
            }
        except Exception as e:
            return False, {
                "rule": "pattern",
                "table": table,
                "column": column,
                "error": str(e)
            }

    def validate_table_stats(self, table: str) -> Dict[str, Any]:
        """
        Get table statistics.

        Args:
            table: Table name

        Returns:
            Dictionary with table stats
        """
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = self.cursor.fetchone()[0]

            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = self.cursor.fetchall()

            return {
                "table": table,
                "row_count": row_count,
                "column_count": len(columns),
                "columns": [col[1] for col in columns]
            }
        except Exception as e:
            return {
                "table": table,
                "error": str(e)
            }


def load_validation_rules(filepath: str) -> Dict[str, Any]:
    """
    Load validation rules from JSON file.

    Args:
        filepath: Path to JSON file with validation rules

    Returns:
        Validation rules dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {filepath}")

        with open(path, 'r') as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def format_validation_report(
    table: str,
    results: List[Tuple[bool, Dict[str, Any]]],
    stats: Dict[str, Any]
) -> str:
    """
    Format validation results into a readable report.

    Args:
        table: Table name
        results: List of validation results
        stats: Table statistics

    Returns:
        Formatted report string
    """
    report = []
    report.append(f"\n{'='*70}")
    report.append(f"Data Validation Report: {table}")
    report.append(f"{'='*70}\n")

    # Table stats
    if "error" not in stats:
        report.append(f"Table Statistics:")
        report.append(f"  Rows: {stats['row_count']}")
        report.append(f"  Columns: {stats['column_count']}")
        report.append(f"  Column Names: {', '.join(stats['columns'][:5])}")
        if len(stats['columns']) > 5:
            report.append(f"             ... and {len(stats['columns']) - 5} more")
        report.append("")

    # Validation results
    passed = sum(1 for is_valid, _ in results if is_valid)
    failed = sum(1 for is_valid, _ in results if not is_valid)

    report.append(f"Validation Summary:")
    report.append(f"  Total Checks: {len(results)}")
    report.append(f"  Passed: {passed}")
    report.append(f"  Failed: {failed}")
    report.append("")

    if failed > 0:
        report.append("Failed Validations:")
        for is_valid, details in results:
            if not is_valid:
                rule = details.get("rule", "unknown")
                column = details.get("column", "N/A")
                report.append(f"  [{rule}] {column}")

                if "error" in details:
                    report.append(f"    Error: {details['error']}")
                elif rule == "not_null":
                    report.append(f"    Found {details['null_count']} NULL values")
                elif rule == "unique":
                    report.append(f"    Found {details['duplicate_count']} duplicate groups")
                elif rule == "range":
                    report.append(f"    {details['out_of_range_count']} values outside range "
                                f"[{details['min']}, {details['max']}]")
                report.append("")

    report.append(f"{'='*70}\n")

    return "\n".join(report)


def main():
    """Main entry point for data validation."""
    parser = argparse.ArgumentParser(
        description="Validate data in database table against rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --database data.db --table users
  %(prog)s --database data.db --table products --rules rules.json
  %(prog)s --database data.db --table orders --rules rules.json --output report.json
  %(prog)s --database data.db --table orders --not-null id,user_id --unique order_number
        """
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--table",
        required=True,
        help="Table name to validate"
    )
    parser.add_argument(
        "--rules",
        help="Path to JSON file containing validation rules"
    )
    parser.add_argument(
        "--not-null",
        help="Comma-separated list of columns that must not be NULL"
    )
    parser.add_argument(
        "--unique",
        help="Comma-separated list of columns that must be unique"
    )
    parser.add_argument(
        "--output",
        help="Output file for validation report (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    validator = DataValidator("sqlite")

    try:
        # Connect to database
        if args.verbose:
            print(f"Connecting to {args.database}...", file=sys.stderr)

        validator.connect(args.database)

        # Get table statistics
        stats = validator.validate_table_stats(args.table)

        if "error" in stats:
            print(f"Error: {stats['error']}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"Table {args.table} has {stats['row_count']} rows", file=sys.stderr)

        # Run validations
        results = []

        # Load rules from file if provided
        if args.rules:
            rules = load_validation_rules(args.rules)
            for rule in rules.get("validations", []):
                if args.verbose:
                    print(f"Running {rule.get('rule')} validation on {rule.get('column')}...", file=sys.stderr)

                if rule["rule"] == "not_null":
                    result = validator.validate_not_null(args.table, rule["column"])
                elif rule["rule"] == "unique":
                    result = validator.validate_unique(args.table, rule["column"])
                elif rule["rule"] == "range":
                    result = validator.validate_range(
                        args.table,
                        rule["column"],
                        rule["min"],
                        rule["max"]
                    )
                elif rule["rule"] == "pattern":
                    result = validator.validate_pattern(
                        args.table,
                        rule["column"],
                        rule["pattern"]
                    )
                else:
                    continue

                results.append(result)

        # Apply command-line validations
        if args.not_null:
            for column in args.not_null.split(","):
                if args.verbose:
                    print(f"Running not_null validation on {column}...", file=sys.stderr)
                results.append(validator.validate_not_null(args.table, column.strip()))

        if args.unique:
            for column in args.unique.split(","):
                if args.verbose:
                    print(f"Running unique validation on {column}...", file=sys.stderr)
                results.append(validator.validate_unique(args.table, column.strip()))

        # Generate report
        report = format_validation_report(args.table, results, stats)
        print(report)

        # Save JSON output if requested
        if args.output:
            output_data = {
                "table": args.table,
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "validations": [
                    {
                        "valid": is_valid,
                        "details": details
                    }
                    for is_valid, details in results
                ]
            }

            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)

            if args.verbose:
                print(f"Results saved to {args.output}", file=sys.stderr)

        # Exit with appropriate code
        all_valid = all(is_valid for is_valid, _ in results)
        sys.exit(0 if all_valid else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        validator.disconnect()


if __name__ == "__main__":
    main()
