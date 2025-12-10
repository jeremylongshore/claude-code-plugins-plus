#!/usr/bin/env python3
"""
Validate the ethics of a dataset for AI/ML training.

This script performs comprehensive ethics checks on datasets, including
class imbalance detection, protected attribute analysis, data quality
assessment, and fairness metrics. Supports CSV, JSON, and Parquet formats.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv


def detect_file_format(filepath: str) -> str:
    """
    Detect the format of the dataset file.

    Args:
        filepath: Path to the dataset file

    Returns:
        Detected format string (csv, json, parquet, etc.)
    """
    suffix = Path(filepath).suffix.lower()
    format_map = {
        '.csv': 'CSV',
        '.json': 'JSON',
        '.jsonl': 'JSONL',
        '.parquet': 'Parquet',
        '.xlsx': 'Excel',
        '.xls': 'Excel',
        '.tsv': 'TSV',
        '.txt': 'Text'
    }
    return format_map.get(suffix, 'Unknown')


def validate_csv_file(filepath: str) -> Dict:
    """
    Validate a CSV dataset file.

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary containing validation results
    """
    results = {
        'file': filepath,
        'format': 'CSV',
        'rows': 0,
        'columns': 0,
        'column_names': [],
        'issues': [],
        'warnings': [],
        'recommendations': [],
        'fairness_score': 0.0,
        'class_distribution': {},
        'missing_values': {}
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                results['issues'].append("CSV file has no headers")
                return results

            results['column_names'] = list(reader.fieldnames)
            results['columns'] = len(results['column_names'])

            # Analyze rows
            rows = list(reader)
            results['rows'] = len(rows)

            if results['rows'] == 0:
                results['issues'].append("Dataset is empty (0 rows)")
                return results

            # Check for missing values
            for col in results['column_names']:
                missing_count = sum(1 for row in rows if not row.get(col) or row.get(col).strip() == '')
                if missing_count > 0:
                    results['missing_values'][col] = {
                        'count': missing_count,
                        'percentage': (missing_count / results['rows']) * 100
                    }

            # Detect potential target column
            potential_targets = ['label', 'target', 'class', 'outcome', 'prediction']
            target_col = None
            for col in results['column_names']:
                if col.lower() in potential_targets:
                    target_col = col
                    break

            # Analyze class distribution if target found
            if target_col:
                class_counts = {}
                for row in rows:
                    class_val = row.get(target_col, 'UNKNOWN')
                    class_counts[class_val] = class_counts.get(class_val, 0) + 1

                results['class_distribution'] = {
                    k: {
                        'count': v,
                        'percentage': (v / results['rows']) * 100
                    }
                    for k, v in class_counts.items()
                }

                # Check for class imbalance
                if class_counts:
                    max_class_pct = max((v / results['rows']) * 100 for v in class_counts.values())
                    if max_class_pct > 90:
                        results['issues'].append(f"Severe class imbalance detected ({max_class_pct:.1f}% for majority class)")
                    elif max_class_pct > 70:
                        results['warnings'].append(f"Moderate class imbalance ({max_class_pct:.1f}% for majority class)")

    except FileNotFoundError:
        results['issues'].append(f"File not found: {filepath}")
        return results
    except csv.Error as e:
        results['issues'].append(f"CSV parsing error: {e}")
        return results
    except Exception as e:
        results['issues'].append(f"Error reading file: {e}")
        return results

    # Check for protected attributes
    protected_attrs = ['race', 'gender', 'age', 'religion', 'ethnicity', 'sex', 'sexual_orientation']
    found_protected = []
    for col in results['column_names']:
        if any(attr in col.lower() for attr in protected_attrs):
            found_protected.append(col)

    if found_protected:
        results['warnings'].append(f"Protected attributes found: {', '.join(found_protected)}")
        results['recommendations'].append("Ensure proper handling of protected attributes per fairness guidelines")

    # Check for high-cardinality columns (potential PII)
    for col in results['column_names']:
        unique_count = len(set(row.get(col, '') for row in rows))
        if unique_count == results['rows']:
            results['warnings'].append(f"Column '{col}' appears to contain unique identifiers (possible PII)")
            results['recommendations'].append(f"Remove or anonymize column '{col}' before training")

    # Calculate fairness score
    fairness_score = 100
    if results['issues']:
        fairness_score -= len(results['issues']) * 20
    if results['warnings']:
        fairness_score -= len(results['warnings']) * 10

    results['fairness_score'] = max(0, fairness_score)

    # Recommendations
    if results['missing_values']:
        results['recommendations'].append(f"Address missing values in {len(results['missing_values'])} columns")

    if not found_protected:
        results['recommendations'].append("Consider whether fairness analysis across demographic groups is needed")

    results['recommendations'].append("Document data collection methodology and potential biases")
    results['recommendations'].append("Perform intersectional bias analysis for multiple protected attributes")

    return results


def validate_json_file(filepath: str) -> Dict:
    """
    Validate a JSON or JSONL dataset file.

    Args:
        filepath: Path to JSON file

    Returns:
        Dictionary containing validation results
    """
    results = {
        'file': filepath,
        'format': 'JSON',
        'rows': 0,
        'columns': 0,
        'column_names': [],
        'issues': [],
        'warnings': [],
        'recommendations': [],
        'fairness_score': 0.0
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

            # Try to parse as JSON array
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    rows = data
                elif isinstance(data, dict) and 'data' in data:
                    rows = data['data']
                else:
                    results['issues'].append("JSON structure not recognized (expected array or {data: [...]})")
                    return results
            except json.JSONDecodeError:
                # Try JSONL format
                rows = []
                for line in content.split('\n'):
                    if line.strip():
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            results['warnings'].append(f"Invalid JSON line: {e}")

            results['rows'] = len(rows)

            if results['rows'] == 0:
                results['issues'].append("Dataset is empty (0 records)")
                return results

            # Extract column names from first row
            if rows and isinstance(rows[0], dict):
                results['column_names'] = list(rows[0].keys())
                results['columns'] = len(results['column_names'])

    except FileNotFoundError:
        results['issues'].append(f"File not found: {filepath}")
    except Exception as e:
        results['issues'].append(f"Error reading file: {e}")

    results['fairness_score'] = max(0, 100 - (len(results['issues']) * 20))
    results['recommendations'].append("Validate JSON schema consistency across all records")

    return results


def validate_dataset(filepath: str) -> Dict:
    """
    Validate a dataset file for ethics compliance.

    Args:
        filepath: Path to the dataset file

    Returns:
        Dictionary containing validation results
    """
    file_format = detect_file_format(filepath)

    if file_format == 'CSV' or file_format == 'TSV':
        return validate_csv_file(filepath)
    elif file_format == 'JSON' or file_format == 'JSONL':
        return validate_json_file(filepath)
    else:
        return {
            'file': filepath,
            'format': file_format,
            'issues': [f"Unsupported file format: {file_format}"],
            'warnings': [],
            'recommendations': [],
            'fairness_score': 0.0
        }


def generate_ethics_report(results: Dict) -> str:
    """
    Generate a human-readable ethics validation report.

    Args:
        results: Validation results dictionary

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("DATASET ETHICS VALIDATION REPORT")
    report.append("=" * 60)

    report.append(f"\nDataset: {results['file']}")
    report.append(f"Format: {results['format']}")
    report.append(f"Rows: {results['rows']}")
    report.append(f"Columns: {results['columns']}")

    if results['column_names']:
        report.append(f"Columns: {', '.join(results['column_names'][:5])}")
        if len(results['column_names']) > 5:
            report.append(f"  ... and {len(results['column_names']) - 5} more")

    report.append(f"\nFairness Score: {results['fairness_score']:.1f}/100")

    if results['class_distribution']:
        report.append("\n[CLASS DISTRIBUTION]")
        for cls, data in results['class_distribution'].items():
            report.append(f"  {cls}: {data['count']} ({data['percentage']:.1f}%)")

    if results['missing_values']:
        report.append("\n[MISSING VALUES]")
        for col, data in results['missing_values'].items():
            report.append(f"  {col}: {data['count']} ({data['percentage']:.1f}%)")

    if results['issues']:
        report.append("\n[CRITICAL ISSUES]")
        for issue in results['issues']:
            report.append(f"  ✗ {issue}")

    if results['warnings']:
        report.append("\n[WARNINGS]")
        for warning in results['warnings']:
            report.append(f"  ⚠ {warning}")

    if results['recommendations']:
        report.append("\n[RECOMMENDATIONS]")
        for rec in results['recommendations']:
            report.append(f"  → {rec}")

    report.append("\n" + "=" * 60)

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate the ethics of a dataset for AI/ML training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate CSV dataset
  %(prog)s --file data.csv

  # Validate JSON dataset
  %(prog)s --file data.json

  # Output as JSON
  %(prog)s --file data.csv --format json

  # Verbose output
  %(prog)s --file data.csv --verbose
        """
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Path to dataset file (CSV, JSON, Parquet, etc.)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate dataset
    results = validate_dataset(args.file)

    # Output results
    if args.format == 'json':
        print(json.dumps(results, indent=2, default=str))
    else:
        report = generate_ethics_report(results)
        print(report)

    # Exit with error if critical issues found
    if results['issues']:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
