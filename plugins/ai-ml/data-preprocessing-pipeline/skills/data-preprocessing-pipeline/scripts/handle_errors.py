#!/usr/bin/env python3
"""
Error handling script for data preprocessing pipeline.

Manages and logs errors during preprocessing including:
- Exception tracking
- Error categorization
- Logging to files
- Error statistics
- Recovery recommendations
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import traceback


class ErrorHandler:
    """Handles and logs errors in preprocessing pipeline."""

    ERROR_CATEGORIES = {
        'validation': 'Data validation errors',
        'transformation': 'Data transformation errors',
        'io': 'File I/O errors',
        'type': 'Type conversion errors',
        'missing': 'Missing data errors',
        'duplicate': 'Duplicate data errors',
        'schema': 'Schema mismatch errors',
        'unknown': 'Unknown errors',
    }

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize error handler.

        Args:
            log_file: Path to log file (optional)
        """
        self.log_file = log_file
        self.errors = []
        self.error_stats = {cat: 0 for cat in self.ERROR_CATEGORIES.keys()}
        self.session_id = datetime.now().isoformat()

    def log_error(
        self,
        error: Exception,
        category: str = 'unknown',
        context: Optional[Dict[str, Any]] = None,
        stack_trace: bool = True
    ) -> Dict[str, Any]:
        """
        Log an error.

        Args:
            error: Exception object
            category: Error category
            context: Additional context data
            stack_trace: Include stack trace

        Returns:
            Error record dictionary
        """
        if category not in self.ERROR_CATEGORIES:
            category = 'unknown'

        error_record = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'message': str(error),
            'type': type(error).__name__,
            'context': context or {},
        }

        if stack_trace:
            error_record['stack_trace'] = traceback.format_exc()

        self.errors.append(error_record)
        self.error_stats[category] += 1

        # Write to log file if configured
        if self.log_file:
            self._write_to_log(error_record)

        return error_record

    def _write_to_log(self, error_record: Dict[str, Any]) -> None:
        """Write error record to log file."""
        try:
            path = Path(self.log_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_record) + '\n')
        except Exception as e:
            print(f"Failed to write to log file: {str(e)}", file=sys.stderr)

    def validate_data_integrity(
        self,
        data: List[Dict[str, Any]],
        max_errors: int = 100
    ) -> Dict[str, Any]:
        """
        Validate data integrity and log issues.

        Args:
            data: List of data rows
            max_errors: Maximum errors to report

        Returns:
            Integrity report
        """
        integrity_issues = {
            'empty_rows': [],
            'null_values': [],
            'duplicates': [],
            'type_mismatches': [],
        }

        seen_rows = set()
        error_count = 0

        for idx, row in enumerate(data):
            if error_count >= max_errors:
                break

            # Check for empty rows
            if not row:
                integrity_issues['empty_rows'].append(idx)
                error_count += 1
                continue

            # Check for null values
            null_fields = [k for k, v in row.items() if v is None or v == '']
            if null_fields:
                if len(integrity_issues['null_values']) < max_errors:
                    integrity_issues['null_values'].append({
                        'row': idx,
                        'fields': null_fields
                    })
                    error_count += 1

            # Check for duplicates
            row_str = json.dumps(row, sort_keys=True, default=str)
            if row_str in seen_rows:
                if len(integrity_issues['duplicates']) < max_errors:
                    integrity_issues['duplicates'].append(idx)
                    error_count += 1
            else:
                seen_rows.add(row_str)

        return {
            'total_rows': len(data),
            'issues': integrity_issues,
            'issue_count': sum(len(v) for v in integrity_issues.values()),
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        return {
            'session_id': self.session_id,
            'total_errors': len(self.errors),
            'error_stats': self.error_stats,
            'errors': self.errors[-100:],  # Last 100 errors
        }

    def generate_recovery_recommendations(self) -> List[str]:
        """Generate recovery recommendations based on errors."""
        recommendations = []

        if self.error_stats['validation'] > 0:
            recommendations.append(
                "Validation errors detected. Review data against schema constraints."
            )

        if self.error_stats['missing'] > 0:
            recommendations.append(
                "Missing values detected. Consider imputation strategies (mean, median, forward-fill)."
            )

        if self.error_stats['duplicate'] > 0:
            recommendations.append(
                "Duplicate records detected. Remove duplicates or keep unique identifiers."
            )

        if self.error_stats['type'] > 0:
            recommendations.append(
                "Type conversion errors detected. Verify field types match expected schema."
            )

        if self.error_stats['io'] > 0:
            recommendations.append(
                "I/O errors detected. Check file permissions and storage availability."
            )

        if not recommendations:
            recommendations.append("No errors detected. Data appears clean.")

        return recommendations

    def save_error_report(self, output_file: str) -> None:
        """
        Save comprehensive error report.

        Args:
            output_file: Output file path
        """
        try:
            report = {
                'metadata': {
                    'session_id': self.session_id,
                    'generated_at': datetime.now().isoformat(),
                },
                'summary': self.get_error_summary(),
                'recommendations': self.generate_recovery_recommendations(),
                'categories': self.ERROR_CATEGORIES,
            }

            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            print(f"Failed to save error report: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage and log errors during data preprocessing pipeline'
    )
    parser.add_argument(
        'action',
        choices=['test', 'analyze', 'summary'],
        help='Action to perform'
    )
    parser.add_argument(
        '-l', '--log-file',
        help='Path to error log file',
        default=None
    )
    parser.add_argument(
        '-d', '--data-file',
        help='Path to data file for integrity checking'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file for error report'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed error information'
    )

    args = parser.parse_args()

    try:
        handler = ErrorHandler(log_file=args.log_file)

        if args.action == 'test':
            # Test error logging
            try:
                raise ValueError("Test validation error")
            except ValueError as e:
                handler.log_error(e, category='validation', context={'test': True})

            try:
                raise KeyError("Test missing field")
            except KeyError as e:
                handler.log_error(e, category='missing', context={'field': 'test'})

            print("Test errors logged successfully")

        elif args.action == 'analyze':
            # Analyze data file for integrity issues
            if not args.data_file:
                print("Error: --data-file required for analyze action", file=sys.stderr)
                sys.exit(1)

            path = Path(args.data_file)
            if not path.exists():
                print(f"Error: File not found: {args.data_file}", file=sys.stderr)
                sys.exit(1)

            # Load data
            data = []
            try:
                if path.suffix.lower() == '.json':
                    with open(args.data_file, 'r') as f:
                        content = json.load(f)
                        data = content if isinstance(content, list) else [content]
                else:
                    print(f"Error: Unsupported file format: {path.suffix}", file=sys.stderr)
                    sys.exit(1)
            except json.JSONDecodeError as e:
                handler.log_error(e, category='io')

            integrity_report = handler.validate_data_integrity(data)
            if args.verbose:
                print(json.dumps(integrity_report, indent=2))

        elif args.action == 'summary':
            # Generate error summary
            summary = handler.get_error_summary()
            recommendations = handler.generate_recovery_recommendations()

            report = {
                'summary': summary,
                'recommendations': recommendations,
            }

            if args.output:
                handler.save_error_report(args.output)
                print(f"Error report saved to: {args.output}")
            else:
                print(json.dumps(report, indent=2))

        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
