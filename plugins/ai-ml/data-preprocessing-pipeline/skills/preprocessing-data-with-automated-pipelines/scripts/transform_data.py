#!/usr/bin/env python3
"""
Data transformation script for preprocessing pipeline.

Applies transformations to data including:
- Normalization (min-max, z-score)
- Scaling (standard, robust)
- Categorical encoding (one-hot, label)
- Missing value imputation
- Feature engineering
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import csv
from statistics import mean, stdev


class DataTransformer:
    """Applies transformations to data."""

    def __init__(self):
        """Initialize transformer."""
        self.transformations = []
        self.statistics = {}

    def load_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load data from file.

        Args:
            file_path: Path to CSV or JSON file

        Returns:
            List of data rows as dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        data = []
        try:
            if path.suffix.lower() == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            elif path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    data = content if isinstance(content, list) else [content]
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        except Exception as e:
            raise IOError(f"Failed to load data: {str(e)}")

        return data

    def normalize(
        self,
        data: List[Dict[str, Any]],
        field: str,
        method: str = 'minmax'
    ) -> List[Dict[str, Any]]:
        """
        Normalize numeric field.

        Args:
            data: List of data rows
            field: Field name to normalize
            method: 'minmax' or 'zscore'

        Returns:
            Transformed data
        """
        try:
            values = []
            for row in data:
                if field in row and row[field] is not None:
                    try:
                        values.append(float(row[field]))
                    except (ValueError, TypeError):
                        continue

            if not values:
                raise ValueError(f"No valid numeric values for field: {field}")

            if method == 'minmax':
                min_val = min(values)
                max_val = max(values)
                if min_val == max_val:
                    for row in data:
                        if field in row:
                            row[f"{field}_normalized"] = 0.5
                else:
                    for row in data:
                        if field in row and row[field] is not None:
                            try:
                                val = float(row[field])
                                normalized = (val - min_val) / (max_val - min_val)
                                row[f"{field}_normalized"] = round(normalized, 4)
                            except (ValueError, TypeError):
                                row[f"{field}_normalized"] = None

                self.statistics[field] = {'method': 'minmax', 'min': min_val, 'max': max_val}

            elif method == 'zscore':
                if len(values) > 1:
                    mean_val = mean(values)
                    std_val = stdev(values)
                    if std_val == 0:
                        for row in data:
                            if field in row:
                                row[f"{field}_normalized"] = 0.0
                    else:
                        for row in data:
                            if field in row and row[field] is not None:
                                try:
                                    val = float(row[field])
                                    normalized = (val - mean_val) / std_val
                                    row[f"{field}_normalized"] = round(normalized, 4)
                                except (ValueError, TypeError):
                                    row[f"{field}_normalized"] = None

                    self.statistics[field] = {
                        'method': 'zscore',
                        'mean': round(mean_val, 4),
                        'stdev': round(std_val, 4)
                    }
            else:
                raise ValueError(f"Unknown normalization method: {method}")

            self.transformations.append(
                f"Normalized field '{field}' using {method}"
            )

        except Exception as e:
            raise ValueError(f"Normalization failed: {str(e)}")

        return data

    def encode_categorical(
        self,
        data: List[Dict[str, Any]],
        field: str,
        method: str = 'label'
    ) -> List[Dict[str, Any]]:
        """
        Encode categorical field.

        Args:
            data: List of data rows
            field: Field name to encode
            method: 'label' or 'onehot'

        Returns:
            Transformed data
        """
        try:
            categories = {}
            for row in data:
                if field in row and row[field] is not None:
                    val = str(row[field])
                    if val not in categories:
                        categories[val] = len(categories)

            if not categories:
                raise ValueError(f"No categorical values found for field: {field}")

            if method == 'label':
                for row in data:
                    if field in row and row[field] is not None:
                        val = str(row[field])
                        row[f"{field}_encoded"] = categories.get(val)
                    else:
                        row[f"{field}_encoded"] = None

                self.transformations.append(
                    f"Label encoded field '{field}' ({len(categories)} categories)"
                )

            elif method == 'onehot':
                for row in data:
                    for cat, code in categories.items():
                        col_name = f"{field}_{cat}"
                        if field in row and row[field] is not None:
                            val = str(row[field])
                            row[col_name] = 1 if val == cat else 0
                        else:
                            row[col_name] = 0

                self.transformations.append(
                    f"One-hot encoded field '{field}' ({len(categories)} categories)"
                )
            else:
                raise ValueError(f"Unknown encoding method: {method}")

            self.statistics[field] = {
                'method': method,
                'categories': categories
            }

        except Exception as e:
            raise ValueError(f"Categorical encoding failed: {str(e)}")

        return data

    def impute_missing(
        self,
        data: List[Dict[str, Any]],
        field: str,
        method: str = 'mean'
    ) -> List[Dict[str, Any]]:
        """
        Impute missing values.

        Args:
            data: List of data rows
            field: Field name for imputation
            method: 'mean', 'median', or 'forward_fill'

        Returns:
            Transformed data
        """
        try:
            if method in ('mean', 'median'):
                values = []
                for row in data:
                    if field in row and row[field] is not None:
                        try:
                            values.append(float(row[field]))
                        except (ValueError, TypeError):
                            continue

                if not values:
                    raise ValueError(f"No numeric values for imputation in field: {field}")

                if method == 'mean':
                    fill_value = mean(values)
                else:  # median
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    fill_value = (
                        sorted_vals[n // 2]
                        if n % 2 == 1
                        else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
                    )

                for row in data:
                    if field not in row or row[field] is None or row[field] == '':
                        row[field] = round(fill_value, 4)

                self.statistics[field] = {'method': method, 'fill_value': fill_value}

            elif method == 'forward_fill':
                last_value = None
                for row in data:
                    if field in row and row[field] is not None:
                        last_value = row[field]
                    elif last_value is not None:
                        row[field] = last_value

                self.statistics[field] = {'method': 'forward_fill'}

            else:
                raise ValueError(f"Unknown imputation method: {method}")

            self.transformations.append(
                f"Imputed missing values in field '{field}' using {method}"
            )

        except Exception as e:
            raise ValueError(f"Imputation failed: {str(e)}")

        return data

    def save_data(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save transformed data.

        Args:
            data: Transformed data
            output_file: Output file path
        """
        try:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            if path.suffix.lower() == '.csv':
                if data:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            elif path.suffix.lower() == '.json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported output format: {path.suffix}")

        except Exception as e:
            raise IOError(f"Failed to save data: {str(e)}")

    def get_summary(self) -> Dict[str, Any]:
        """Get transformation summary."""
        return {
            'transformations': self.transformations,
            'statistics': self.statistics,
            'transformation_count': len(self.transformations),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Apply transformations to data (normalization, encoding, imputation)'
    )
    parser.add_argument(
        'input_file',
        help='Path to input data file (CSV or JSON)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to output transformed data file'
    )
    parser.add_argument(
        '-n', '--normalize',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Normalize field (minmax or zscore)'
    )
    parser.add_argument(
        '-e', '--encode',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Encode categorical field (label or onehot)'
    )
    parser.add_argument(
        '-i', '--impute',
        nargs=2,
        metavar=('FIELD', 'METHOD'),
        action='append',
        help='Impute missing values (mean, median, or forward_fill)'
    )
    parser.add_argument(
        '-s', '--summary',
        help='Save transformation summary to JSON file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print transformation details'
    )

    args = parser.parse_args()

    try:
        transformer = DataTransformer()

        # Load data
        data = transformer.load_data(args.input_file)
        if args.verbose:
            print(f"Loaded {len(data)} rows")

        # Apply transformations
        if args.normalize:
            for field, method in args.normalize:
                transformer.normalize(data, field, method)
                if args.verbose:
                    print(f"Normalized '{field}' using {method}")

        if args.encode:
            for field, method in args.encode:
                transformer.encode_categorical(data, field, method)
                if args.verbose:
                    print(f"Encoded '{field}' using {method}")

        if args.impute:
            for field, method in args.impute:
                transformer.impute_missing(data, field, method)
                if args.verbose:
                    print(f"Imputed missing values in '{field}' using {method}")

        # Save output
        transformer.save_data(data, args.output)
        if args.verbose:
            print(f"Saved {len(data)} rows to {args.output}")

        # Save summary if requested
        if args.summary:
            summary = transformer.get_summary()
            with open(args.summary, 'w') as f:
                json.dump(summary, f, indent=2)
            if args.verbose:
                print(f"Saved summary to {args.summary}")

        sys.exit(0)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
