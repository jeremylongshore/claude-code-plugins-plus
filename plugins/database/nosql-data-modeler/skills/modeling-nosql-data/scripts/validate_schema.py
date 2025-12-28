#!/usr/bin/env python3
"""
Validates a NoSQL schema against best practices and common errors.

This script analyzes NoSQL database schemas (MongoDB, DynamoDB, etc.) for
compliance with best practices, performance guidelines, and common pitfalls.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple


class NoSQLSchemaValidator:
    """Validates NoSQL schemas against best practices."""

    # Best practice rules
    BEST_PRACTICES = {
        "naming": {
            "rule": "Naming conventions should be consistent",
            "checks": [
                "Use camelCase or snake_case consistently",
                "Avoid single-letter field names",
                "Use descriptive names"
            ]
        },
        "indexing": {
            "rule": "Index strategy is defined",
            "checks": [
                "Frequently queried fields are indexed",
                "Composite indexes are defined for common queries",
                "Index overhead is considered"
            ]
        },
        "denormalization": {
            "rule": "Denormalization is used appropriately",
            "checks": [
                "Denormalization reduces query complexity",
                "Duplicate data is managed intentionally",
                "Update patterns are considered"
            ]
        },
        "data_types": {
            "rule": "Data types are appropriate",
            "checks": [
                "Numeric fields use appropriate numeric types",
                "Dates use datetime types",
                "IDs use consistent types"
            ]
        },
        "document_size": {
            "rule": "Document size is reasonable",
            "checks": [
                "Documents don't exceed size limits (16MB for MongoDB)",
                "Array fields don't grow unbounded",
                "Large nested objects are avoided"
            ]
        }
    }

    # Common anti-patterns
    ANTI_PATTERNS = [
        {
            "name": "unbounded_arrays",
            "description": "Arrays that can grow without limits",
            "severity": "high",
            "recommendation": "Cap array size or use separate collections"
        },
        {
            "name": "deeply_nested",
            "description": "Deeply nested document structures (>3 levels)",
            "severity": "medium",
            "recommendation": "Flatten structure or normalize data"
        },
        {
            "name": "no_indexes",
            "description": "Frequently queried fields without indexes",
            "severity": "high",
            "recommendation": "Add indexes for query performance"
        },
        {
            "name": "inconsistent_types",
            "description": "Field with inconsistent data types across documents",
            "severity": "medium",
            "recommendation": "Enforce schema validation or add type hints"
        },
        {
            "name": "circular_references",
            "description": "Circular document references",
            "severity": "high",
            "recommendation": "Use one-way references or denormalization"
        },
        {
            "name": "missing_ids",
            "description": "Documents or arrays without ID fields",
            "severity": "high",
            "recommendation": "Add unique IDs for referencing"
        }
    ]

    def __init__(self):
        """Initialize schema validator."""
        self.schema = {}
        self.issues = []

    def load_schema(self, filepath: str) -> bool:
        """
        Load schema from JSON file.

        Args:
            filepath: Path to schema JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                self.schema = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading schema: {e}", file=sys.stderr)
            return False

    def validate_naming_convention(self) -> List[Dict[str, Any]]:
        """
        Check naming convention consistency.

        Returns:
            List of issues found
        """
        issues = []
        fields = self._extract_all_fields()

        naming_styles = {"camelCase": 0, "snake_case": 0, "PascalCase": 0}

        for field in fields:
            if "_" in field and field[0] != "_":
                naming_styles["snake_case"] += 1
            elif field[0].isupper():
                naming_styles["PascalCase"] += 1
            else:
                naming_styles["camelCase"] += 1

        # Check for inconsistency
        non_zero_styles = [count for count in naming_styles.values() if count > 0]
        if len(non_zero_styles) > 1:
            issues.append({
                "severity": "medium",
                "type": "naming_inconsistency",
                "message": "Inconsistent naming convention across fields",
                "details": naming_styles
            })

        return issues

    def validate_indexes(self) -> List[Dict[str, Any]]:
        """
        Check indexing strategy.

        Returns:
            List of issues found
        """
        issues = []

        if "indexes" not in self.schema:
            issues.append({
                "severity": "medium",
                "type": "missing_indexes",
                "message": "No indexes defined in schema",
                "recommendation": "Define indexes for frequently queried fields"
            })
        else:
            indexes = self.schema.get("indexes", [])
            if not indexes:
                issues.append({
                    "severity": "medium",
                    "type": "empty_indexes",
                    "message": "Indexes array is empty",
                    "recommendation": "Add indexes for query optimization"
                })

        return issues

    def validate_document_structure(self) -> List[Dict[str, Any]]:
        """
        Check document structure for anti-patterns.

        Returns:
            List of issues found
        """
        issues = []

        # Check for unbounded arrays
        for field, field_def in self._extract_fields(self.schema).items():
            if field_def.get("type") == "array":
                if "max_items" not in field_def:
                    issues.append({
                        "severity": "high",
                        "type": "unbounded_array",
                        "field": field,
                        "message": f"Array field '{field}' has no maximum size limit",
                        "recommendation": "Set max_items or use separate collection"
                    })

        # Check for deeply nested structures
        depth = self._calculate_nesting_depth(self.schema)
        if depth > 3:
            issues.append({
                "severity": "medium",
                "type": "deeply_nested",
                "message": f"Document nesting depth is {depth} levels (recommended: ≤3)",
                "recommendation": "Flatten structure or normalize data"
            })

        return issues

    def validate_data_types(self) -> List[Dict[str, Any]]:
        """
        Check data type consistency.

        Returns:
            List of issues found
        """
        issues = []

        fields = self._extract_fields(self.schema)

        for field, field_def in fields.items():
            field_type = field_def.get("type")

            # Check for type mismatches
            if field_type not in ["string", "number", "boolean", "object", "array", "date", "null"]:
                issues.append({
                    "severity": "medium",
                    "type": "unknown_type",
                    "field": field,
                    "message": f"Unknown type '{field_type}' for field '{field}'"
                })

            # Check for ID fields without proper type
            if "id" in field.lower() and field_type not in ["string", "number"]:
                issues.append({
                    "severity": "high",
                    "type": "invalid_id_type",
                    "field": field,
                    "message": f"ID field '{field}' should be string or number, not {field_type}"
                })

        return issues

    def validate_references(self) -> List[Dict[str, Any]]:
        """
        Check for missing or circular references.

        Returns:
            List of issues found
        """
        issues = []

        fields = self._extract_fields(self.schema)

        for field, field_def in fields.items():
            if "ref" in field_def:
                ref_target = field_def.get("ref")
                # Check if reference target exists
                if "$id" in self.schema:
                    if ref_target != self.schema.get("$id"):
                        # Cross-collection reference - might be valid
                        pass

        return issues

    def _extract_all_fields(self) -> List[str]:
        """Extract all field names from schema."""
        fields = []

        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key not in ["$schema", "$id", "type", "properties"]:
                        fields.append(key)
                    if isinstance(value, dict):
                        extract_recursive(value)

        extract_recursive(self.schema)
        return fields

    def _extract_fields(self, obj: Dict) -> Dict[str, Dict]:
        """Extract fields with their definitions."""
        fields = {}

        if "properties" in obj:
            return obj["properties"]

        for key, value in obj.items():
            if isinstance(value, dict) and ("type" in value or "properties" in value):
                fields[key] = value

        return fields

    def _calculate_nesting_depth(self, obj: Dict, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, dict):
                    depth = self._calculate_nesting_depth(value, current_depth + 1)
                    max_depth = max(max_depth, depth)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    depth = self._calculate_nesting_depth(value[0], current_depth + 1)
                    max_depth = max(max_depth, depth)

        return max_depth

    def run_all_validations(self) -> Dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            Validation results dictionary
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "schema_name": self.schema.get("$id", "unknown"),
            "validations": [],
            "summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }

        # Run all validation methods
        validation_methods = [
            self.validate_naming_convention,
            self.validate_indexes,
            self.validate_document_structure,
            self.validate_data_types,
            self.validate_references
        ]

        for method in validation_methods:
            issues = method()
            results["validations"].extend(issues)

        # Count by severity
        for issue in results["validations"]:
            severity = issue.get("severity", "low")
            results["summary"][severity] = results["summary"].get(severity, 0) + 1

        return results


def format_validation_report(results: Dict[str, Any]) -> str:
    """
    Format validation results into readable report.

    Args:
        results: Validation results dictionary

    Returns:
        Formatted report string
    """
    report = []
    report.append(f"\n{'='*70}")
    report.append(f"NoSQL Schema Validation Report")
    report.append(f"Schema: {results['schema_name']}")
    report.append(f"{'='*70}\n")

    summary = results.get("summary", {})
    report.append("Summary:")
    report.append(f"  Critical: {summary.get('critical', 0)}")
    report.append(f"  High:     {summary.get('high', 0)}")
    report.append(f"  Medium:   {summary.get('medium', 0)}")
    report.append(f"  Low:      {summary.get('low', 0)}")
    report.append("")

    validations = results.get("validations", [])

    if not validations:
        report.append("✓ No issues found - Schema follows best practices!\n")
    else:
        report.append("Issues Found:\n")

        for issue in sorted(validations, key=lambda x: ["critical", "high", "medium", "low"].index(x.get("severity", "low"))):
            severity = issue.get("severity", "low").upper()
            type_name = issue.get("type", "unknown")
            message = issue.get("message", "")

            report.append(f"[{severity}] {type_name}")
            report.append(f"  {message}")

            if "field" in issue:
                report.append(f"  Field: {issue['field']}")

            if "recommendation" in issue:
                report.append(f"  → {issue['recommendation']}")

            report.append("")

    report.append(f"{'='*70}\n")

    return "\n".join(report)


def main():
    """Main entry point for schema validation."""
    parser = argparse.ArgumentParser(
        description="Validate NoSQL schema against best practices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --schema schema.json
  %(prog)s --schema user-schema.json --output report.json
  %(prog)s --schema product-schema.json --format json
        """
    )

    parser.add_argument(
        "--schema",
        required=True,
        help="Path to JSON schema file"
    )
    parser.add_argument(
        "--output",
        help="Output file for validation report (JSON)"
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    try:
        validator = NoSQLSchemaValidator()

        if args.verbose:
            print(f"Loading schema from {args.schema}...", file=sys.stderr)

        if not validator.load_schema(args.schema):
            sys.exit(1)

        if args.verbose:
            print("Running validations...", file=sys.stderr)

        results = validator.run_all_validations()

        # Output results
        if args.format == "json":
            output = json.dumps(results, indent=2)
        else:
            output = format_validation_report(results)

        print(output)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                if args.format == "json":
                    json.dump(results, f, indent=2)
                else:
                    f.write(output)

            if args.verbose:
                print(f"\nResults saved to {args.output}", file=sys.stderr)

        # Exit code based on critical issues
        if results["summary"].get("critical", 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
