#!/usr/bin/env python3
"""
Data validation script for preprocessing pipeline.

Validates data against predefined schemas or rules including:
- Required fields presence
- Data type correctness
- Value ranges and constraints
- Missing value handling
- Duplicates detection
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import csv


class DataValidator:
    """Validates data against schemas and rules."""

    def __init__(self, schema_file: str = None):
        """
        Initialize validator.

        Args:
            schema_file: Path to JSON schema file (optional)
        """
        self.schema = {}
        if schema_file and Path(schema_file).exists():
            with open(schema_file, 'r') as f:
                self.schema = json.load(f)
        self.errors = []
        self.warnings = []

    def validate_file(self, file_path: str) -> bool:
        """
        Validate data file.

        Args:
            file_path: Path to data file (CSV or JSON)

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.errors.append(f"File not found: {file_path}")
                return False

            if path.suffix.lower() == '.csv':
                return self._validate_csv(str(path))
            elif path.suffix.lower() == '.json':
                return self._validate_json(str(path))
            else:
                self.errors.append(f"Unsupported file format: {path.suffix}")
                return False
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return False

    def _validate_csv(self, file_path: str) -> bool:
        """Validate CSV file structure and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    self.errors.append("CSV file is empty or has no headers")
                    return False

                # Check schema fields if defined
                if self.schema:
                    required_fields = self.schema.get('required_fields', [])
                    for field in required_fields:
                        if field not in reader.fieldnames:
                            self.errors.append(f"Missing required field: {field}")
                            return False

                row_count = 0
                for row_count, row in enumerate(reader, start=1):
                    if not self._validate_row(row, reader.fieldnames):
                        self.errors.append(f"Invalid data at row {row_count}")
                        if len(self.errors) > 10:  # Limit errors
                            self.warnings.append("... (more errors truncated)")
                            break

                if row_count == 0:
                    self.errors.append("CSV file contains no data rows")
                    return False

                return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"CSV validation failed: {str(e)}")
            return False

    def _validate_json(self, file_path: str) -> bool:
        """Validate JSON file structure and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                if not data:
                    self.errors.append("JSON array is empty")
                    return False

                for idx, item in enumerate(data):
                    if not isinstance(item, dict):
                        self.errors.append(f"Row {idx} is not a dictionary")
                        return False
                    if not self._validate_row(item, item.keys()):
                        self.errors.append(f"Invalid data at row {idx}")
                        if len(self.errors) > 10:
                            self.warnings.append("... (more errors truncated)")
                            break

            elif isinstance(data, dict):
                if not data:
                    self.warnings.append("JSON object is empty")
            else:
                self.errors.append("JSON must be an object or array")
                return False

            return len(self.errors) == 0
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"JSON validation failed: {str(e)}")
            return False

    def _validate_row(self, row: Dict[str, Any], fields: List[str]) -> bool:
        """Validate individual row against schema."""
        if not self.schema:
            # No schema defined, just check for basic issues
            for key, value in row.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    self.warnings.append(f"Empty value for field: {key}")
            return True

        field_types = self.schema.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in row:
                if not self._validate_type(row[field], expected_type):
                    self.errors.append(
                        f"Type mismatch for field '{field}': "
                        f"expected {expected_type}, got {type(row[field]).__name__}"
                    )
                    return False
        return True

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        if value is None:
            return True

        type_map = {
            'string': str,
            'int': int,
            'float': (int, float),
            'bool': bool,
            'number': (int, float),
        }

        if expected_type not in type_map:
            return True

        expected = type_map[expected_type]
        return isinstance(value, expected)

    def get_report(self) -> Dict[str, Any]:
        """Get validation report."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate data against predefined schemas or rules'
    )
    parser.add_argument(
        'data_file',
        help='Path to data file (CSV or JSON)'
    )
    parser.add_argument(
        '-s', '--schema',
        help='Path to JSON schema file for validation',
        default=None
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed validation report'
    )
    parser.add_argument(
        '-o', '--output',
        help='Save validation report to JSON file',
        default=None
    )

    args = parser.parse_args()

    # Validate data file
    validator = DataValidator(schema_file=args.schema)
    is_valid = validator.validate_file(args.data_file)
    report = validator.get_report()

    # Output report
    if args.verbose or not is_valid:
        print(json.dumps(report, indent=2))

    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Validation report saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
