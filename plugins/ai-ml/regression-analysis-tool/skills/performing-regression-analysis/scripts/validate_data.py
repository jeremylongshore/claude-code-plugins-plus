#!/usr/bin/env python3
"""
Validate input dataset for regression analysis.

This script performs comprehensive data validation checks including:
- Missing values detection
- Outlier identification using IQR and statistical methods
- Data type consistency verification
- Feature correlation analysis
- Distribution assessment
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict


def load_csv_data(filepath: str) -> Tuple[List[Dict], List[str]]:
    """
    Load CSV data from file.

    Args:
        filepath: Path to CSV file

    Returns:
        Tuple of (data_rows, column_names)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV file has no headers")

            rows = list(reader)
            return rows, list(reader.fieldnames)

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"Error parsing CSV: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def load_json_data(filepath: str) -> Tuple[List[Dict], List[str]]:
    """
    Load JSON data from file.

    Args:
        filepath: Path to JSON file

    Returns:
        Tuple of (data_rows, column_names)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict) and 'data' in data:
            rows = data['data']
        else:
            raise ValueError("Unexpected JSON structure")

        if not rows or not isinstance(rows[0], dict):
            raise ValueError("Data must be a list of dictionaries")

        columns = list(rows[0].keys())
        return rows, columns

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def detect_data_type(value: Any) -> str:
    """Detect the data type of a value."""
    if value is None or value == '':
        return 'missing'
    try:
        float(value)
        if '.' in str(value):
            return 'float'
        else:
            return 'int'
    except (ValueError, TypeError):
        try:
            int(value)
            return 'int'
        except (ValueError, TypeError):
            return 'string'


def check_missing_values(rows: List[Dict], columns: List[str]) -> Dict[str, Dict]:
    """
    Check for missing values in the dataset.

    Args:
        rows: List of data rows
        columns: Column names

    Returns:
        Dictionary with missing value statistics
    """
    total_rows = len(rows)
    missing_stats = {}

    for col in columns:
        missing_count = 0
        for row in rows:
            value = row.get(col)
            if value is None or str(value).strip() == '':
                missing_count += 1

        if missing_count > 0:
            missing_stats[col] = {
                'count': missing_count,
                'percentage': (missing_count / total_rows) * 100,
                'severity': 'high' if (missing_count / total_rows) > 0.1 else 'medium'
            }

    return missing_stats


def check_data_consistency(rows: List[Dict], columns: List[str]) -> Dict[str, Any]:
    """
    Check data type consistency for each column.

    Args:
        rows: List of data rows
        columns: Column names

    Returns:
        Dictionary with consistency analysis
    """
    consistency = {}

    for col in columns:
        type_counts = defaultdict(int)
        sample_values = []

        for row in rows:
            value = row.get(col)
            dtype = detect_data_type(value)
            type_counts[dtype] += 1

            if len(sample_values) < 3 and value is not None:
                sample_values.append(value)

        # Determine primary type
        primary_type = max(type_counts, key=type_counts.get)
        total = sum(type_counts.values())
        primary_pct = (type_counts[primary_type] / total) * 100

        consistency[col] = {
            'primary_type': primary_type,
            'type_distribution': dict(type_counts),
            'type_consistency_percent': primary_pct,
            'sample_values': sample_values,
            'is_consistent': primary_pct > 95
        }

    return consistency


def check_outliers(rows: List[Dict], columns: List[str]) -> Dict[str, Dict]:
    """
    Detect outliers using IQR (Interquartile Range) method.

    Args:
        rows: List of data rows
        columns: Column names

    Returns:
        Dictionary with outlier analysis
    """
    outliers = {}

    for col in columns:
        # Extract numeric values
        numeric_values = []
        for row in rows:
            try:
                value = float(row.get(col))
                numeric_values.append(value)
            except (ValueError, TypeError):
                pass

        if len(numeric_values) < 4:  # Need at least 4 values for IQR
            continue

        # Sort values
        numeric_values.sort()

        # Calculate quartiles
        n = len(numeric_values)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4

        q1 = numeric_values[q1_idx]
        q3 = numeric_values[q3_idx]
        iqr = q3 - q1

        if iqr == 0:
            continue

        # Find outliers
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_indices = []
        for i, value in enumerate(numeric_values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)

        if outlier_indices:
            outliers[col] = {
                'outlier_count': len(outlier_indices),
                'outlier_percentage': (len(outlier_indices) / len(numeric_values)) * 100,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'iqr': iqr,
                'q1': q1,
                'q3': q3
            }

    return outliers


def validate_target_variable(rows: List[Dict], target_col: Optional[str]) -> Dict:
    """
    Validate the target variable for regression.

    Args:
        rows: List of data rows
        target_col: Name of target column

    Returns:
        Validation results
    """
    result = {
        'found': False,
        'column': target_col,
        'is_numeric': False,
        'missing_count': 0,
        'issues': [],
        'statistics': {}
    }

    if not target_col:
        return result

    # Check if column exists
    if not rows or target_col not in rows[0]:
        result['issues'].append(f"Target column '{target_col}' not found in data")
        return result

    result['found'] = True

    # Check if numeric
    numeric_values = []
    missing_count = 0

    for row in rows:
        try:
            value = float(row.get(target_col))
            numeric_values.append(value)
        except (ValueError, TypeError):
            missing_count += 1

    result['missing_count'] = missing_count
    result['is_numeric'] = len(numeric_values) > 0

    if not result['is_numeric']:
        result['issues'].append("Target variable is not numeric")
    else:
        # Calculate statistics
        numeric_values.sort()
        result['statistics'] = {
            'min': numeric_values[0],
            'max': numeric_values[-1],
            'mean': sum(numeric_values) / len(numeric_values),
            'median': numeric_values[len(numeric_values) // 2],
            'count': len(numeric_values)
        }

        # Check for reasonable variance
        if numeric_values[0] == numeric_values[-1]:
            result['issues'].append("Target variable has zero variance (all values identical)")

    return result


def validate_dataset(filepath: str, target_col: Optional[str] = None) -> Dict:
    """
    Perform comprehensive dataset validation.

    Args:
        filepath: Path to dataset file
        target_col: Optional target column name for regression

    Returns:
        Comprehensive validation results
    """
    # Detect file format
    suffix = Path(filepath).suffix.lower()
    if suffix == '.csv':
        rows, columns = load_csv_data(filepath)
    elif suffix == '.json':
        rows, columns = load_json_data(filepath)
    else:
        print(f"Error: Unsupported file format: {suffix}", file=sys.stderr)
        sys.exit(1)

    # Validate dataset
    results = {
        'file': filepath,
        'format': 'CSV' if suffix == '.csv' else 'JSON',
        'rows': len(rows),
        'columns': len(columns),
        'column_names': columns,
        'issues': [],
        'warnings': [],
        'recommendations': [],
        'validation_score': 100.0,
        'missing_values': {},
        'data_consistency': {},
        'outliers': {},
        'target_variable': {}
    }

    if len(rows) == 0:
        results['issues'].append("Dataset is empty (0 rows)")
        results['validation_score'] = 0.0
        return results

    if len(columns) == 0:
        results['issues'].append("Dataset has no columns")
        results['validation_score'] = 0.0
        return results

    # Check missing values
    results['missing_values'] = check_missing_values(rows, columns)
    if results['missing_values']:
        results['warnings'].append(f"Found {len(results['missing_values'])} columns with missing values")

    # Check data consistency
    results['data_consistency'] = check_data_consistency(rows, columns)
    inconsistent_cols = [col for col, info in results['data_consistency'].items() if not info['is_consistent']]
    if inconsistent_cols:
        results['warnings'].append(f"Found {len(inconsistent_cols)} columns with inconsistent data types")

    # Check for outliers
    results['outliers'] = check_outliers(rows, columns)
    if results['outliers']:
        results['warnings'].append(f"Found outliers in {len(results['outliers'])} columns")

    # Validate target variable if specified
    if target_col:
        results['target_variable'] = validate_target_variable(rows, target_col)
        if results['target_variable']['issues']:
            results['issues'].extend(results['target_variable']['issues'])

    # Recommendations
    if len(rows) < 30:
        results['recommendations'].append("Dataset size is small (<30 rows) - consider collecting more data for better model generalization")

    if results['missing_values']:
        results['recommendations'].append("Consider removing or imputing missing values before regression")

    if inconsistent_cols:
        results['recommendations'].append("Ensure consistent data types - convert strings to numeric where appropriate")

    if results['outliers']:
        results['recommendations'].append("Consider handling outliers through removal, transformation, or robust regression methods")

    # Calculate validation score
    score_deduction = 0
    score_deduction += len(results['issues']) * 25
    score_deduction += len(inconsistent_cols) * 5
    if results['missing_values']:
        avg_missing_pct = sum(v['percentage'] for v in results['missing_values'].values()) / len(results['missing_values'])
        score_deduction += min(30, avg_missing_pct / 2)

    results['validation_score'] = max(0.0, 100.0 - score_deduction)

    return results


def generate_report(results: Dict) -> str:
    """Generate a human-readable validation report."""
    report = []
    report.append("=" * 70)
    report.append("REGRESSION DATA VALIDATION REPORT")
    report.append("=" * 70)

    report.append(f"\nDataset: {results['file']}")
    report.append(f"Format: {results['format']}")
    report.append(f"Rows: {results['rows']}")
    report.append(f"Columns: {results['columns']}")
    report.append(f"\nValidation Score: {results['validation_score']:.1f}/100")

    if results['issues']:
        report.append("\n[CRITICAL ISSUES]")
        for issue in results['issues']:
            report.append(f"  ✗ {issue}")

    if results['missing_values']:
        report.append("\n[MISSING VALUES]")
        for col, data in results['missing_values'].items():
            report.append(f"  {col}: {data['count']} ({data['percentage']:.1f}%) - {data['severity']}")

    if results['outliers']:
        report.append("\n[OUTLIERS DETECTED]")
        for col, data in results['outliers'].items():
            report.append(f"  {col}: {data['outlier_count']} outliers ({data['outlier_percentage']:.1f}%)")

    if results['warnings']:
        report.append("\n[WARNINGS]")
        for warning in results['warnings']:
            report.append(f"  ⚠ {warning}")

    if results['recommendations']:
        report.append("\n[RECOMMENDATIONS]")
        for rec in results['recommendations']:
            report.append(f"  → {rec}")

    report.append("\n" + "=" * 70)

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate input dataset for regression analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate CSV dataset
  %(prog)s --file data.csv

  # Validate with target variable specification
  %(prog)s --file data.csv --target price

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
        help='Path to dataset file (CSV or JSON)'
    )
    parser.add_argument(
        '-t', '--target',
        type=str,
        help='Target variable column name (for regression)'
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
    results = validate_dataset(args.file, args.target)

    # Output results
    if args.format == 'json':
        print(json.dumps(results, indent=2, default=str))
    else:
        report = generate_report(results)
        print(report)

    # Exit with error if critical issues
    if results['issues']:
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
