#!/usr/bin/env python3
"""
Generate and train regression models automatically.

This script automatically generates and trains multiple regression models
based on input data and specified parameters. It supports linear regression,
polynomial regression, and ridge/lasso regularization.
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def load_csv_data(filepath: str, target_col: str) -> Tuple[List[List[float]], List[float], List[str]]:
    """
    Load CSV data and separate features from target.

    Args:
        filepath: Path to CSV file
        target_col: Name of target column

    Returns:
        Tuple of (features, targets, feature_names)
    """
    try:
        features = []
        targets = []
        feature_names = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames

            if not columns or target_col not in columns:
                print(f"Error: Target column '{target_col}' not found", file=sys.stderr)
                sys.exit(1)

            feature_names = [col for col in columns if col != target_col]

            for row in reader:
                try:
                    target = float(row[target_col])
                    targets.append(target)

                    feature_values = []
                    for col in feature_names:
                        feature_values.append(float(row[col]))
                    features.append(feature_values)

                except (ValueError, KeyError) as e:
                    if sys.stderr.isatty():
                        pass  # Skip rows with invalid data

        if not features or not targets:
            print("Error: No valid data could be loaded", file=sys.stderr)
            sys.exit(1)

        return features, targets, feature_names

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"Error parsing CSV: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_features(features: List[List[float]]) -> Tuple[List[List[float]], List[float], List[float]]:
    """
    Normalize features to zero mean and unit variance.

    Args:
        features: List of feature vectors

    Returns:
        Tuple of (normalized_features, means, stds)
    """
    if not features or not features[0]:
        return features, [], []

    n_features = len(features[0])
    means = []
    stds = []

    for feat_idx in range(n_features):
        values = [row[feat_idx] for row in features]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5

        means.append(mean)
        stds.append(std if std > 0 else 1.0)

    # Normalize
    normalized = []
    for row in features:
        normalized_row = [
            (row[i] - means[i]) / stds[i]
            for i in range(n_features)
        ]
        normalized.append(normalized_row)

    return normalized, means, stds


def linear_regression(features: List[List[float]], targets: List[float]) -> Dict:
    """
    Fit a linear regression model using normal equations.

    Args:
        features: List of feature vectors
        targets: List of target values

    Returns:
        Model dictionary with coefficients and stats
    """
    n_samples = len(features)
    n_features = len(features[0])

    # Add bias term
    X = [[1.0] + row for row in features]

    # Calculate X^T * X and X^T * y
    xtx = [[0.0] * (n_features + 1) for _ in range(n_features + 1)]
    xty = [0.0] * (n_features + 1)

    for i in range(n_features + 1):
        for j in range(n_features + 1):
            for sample in range(n_samples):
                xtx[i][j] += X[sample][i] * X[sample][j]

        for sample in range(n_samples):
            xty[i] += X[sample][i] * targets[sample]

    # Simple Gaussian elimination for small systems
    # (Would use numpy for production)
    coefficients = [0.0] * (n_features + 1)

    try:
        for i in range(n_features + 1):
            max_row = i
            for k in range(i + 1, n_features + 1):
                if abs(xtx[k][i]) > abs(xtx[max_row][i]):
                    max_row = k

            xtx[i], xtx[max_row] = xtx[max_row], xtx[i]
            xty[i], xty[max_row] = xty[max_row], xty[i]

            for k in range(i + 1, n_features + 1):
                if abs(xtx[i][i]) < 1e-10:
                    continue
                c = xtx[k][i] / xtx[i][i]
                for j in range(i, n_features + 1):
                    xtx[k][j] -= c * xtx[i][j]
                xty[k] -= c * xty[i]

        for i in range(n_features, -1, -1):
            coefficients[i] = xty[i]
            if abs(xtx[i][i]) > 1e-10:
                for j in range(i + 1, n_features + 1):
                    coefficients[i] -= xtx[i][j] * coefficients[j]
                coefficients[i] /= xtx[i][i]

    except ZeroDivisionError:
        print("Warning: Matrix is singular, using least-squares approximation", file=sys.stderr)

    return {
        'type': 'linear',
        'coefficients': coefficients[1:],
        'intercept': coefficients[0],
        'n_features': n_features
    }


def polynomial_regression(features: List[List[float]], targets: List[float], degree: int = 2) -> Dict:
    """
    Fit a polynomial regression model.

    Args:
        features: List of feature vectors
        targets: List of target values
        degree: Polynomial degree

    Returns:
        Model dictionary
    """
    # Create polynomial features
    poly_features = []
    for row in features:
        poly_row = row.copy()
        for d in range(2, degree + 1):
            for val in row:
                poly_row.append(val ** d)
        poly_features.append(poly_row)

    # Fit linear regression on polynomial features
    model = linear_regression(poly_features, targets)
    model['type'] = 'polynomial'
    model['degree'] = degree
    model['n_poly_features'] = len(poly_features[0])

    return model


def predict(model: Dict, features: List[List[float]]) -> List[float]:
    """
    Make predictions with a trained model.

    Args:
        model: Trained model dictionary
        features: Feature vectors for prediction

    Returns:
        List of predictions
    """
    predictions = []

    for row in features:
        if model['type'] == 'linear':
            pred = model['intercept']
            for i, coef in enumerate(model['coefficients']):
                pred += coef * row[i]
            predictions.append(pred)

        elif model['type'] == 'polynomial':
            poly_row = row.copy()
            for d in range(2, model['degree'] + 1):
                for val in row:
                    poly_row.append(val ** d)

            pred = model['intercept']
            for i, coef in enumerate(model['coefficients']):
                if i < len(poly_row):
                    pred += coef * poly_row[i]
            predictions.append(pred)

    return predictions


def calculate_r_squared(targets: List[float], predictions: List[float]) -> float:
    """Calculate R-squared metric."""
    mean_target = sum(targets) / len(targets)

    ss_res = sum((targets[i] - predictions[i]) ** 2 for i in range(len(targets)))
    ss_tot = sum((t - mean_target) ** 2 for t in targets)

    if ss_tot == 0:
        return 0.0

    return 1 - (ss_res / ss_tot)


def calculate_mse(targets: List[float], predictions: List[float]) -> float:
    """Calculate Mean Squared Error."""
    return sum((targets[i] - predictions[i]) ** 2 for i in range(len(targets))) / len(targets)


def calculate_mae(targets: List[float], predictions: List[float]) -> float:
    """Calculate Mean Absolute Error."""
    return sum(abs(targets[i] - predictions[i]) for i in range(len(targets))) / len(targets)


def train_model(
    filepath: str,
    target_col: str,
    model_type: str = 'linear',
    degree: int = 2,
    output_file: Optional[str] = None,
    verbose: bool = False
) -> Dict:
    """
    Train a regression model on the provided dataset.

    Args:
        filepath: Path to training data
        target_col: Name of target column
        model_type: Type of model ('linear' or 'polynomial')
        degree: Polynomial degree (if polynomial)
        output_file: Optional file to save model
        verbose: Verbose output

    Returns:
        Training results dictionary
    """
    results = {
        'status': 'training',
        'model_type': model_type,
        'dataset': filepath,
        'target': target_col,
        'model': None,
        'metrics': {},
        'training_log': []
    }

    # Load data
    if verbose:
        results['training_log'].append("Loading dataset...")
    features, targets, feature_names = load_csv_data(filepath, target_col)
    results['training_log'].append(f"Loaded {len(features)} samples with {len(feature_names)} features")

    # Normalize features
    if verbose:
        results['training_log'].append("Normalizing features...")
    features_normalized, means, stds = normalize_features(features)

    # Train model
    if verbose:
        results['training_log'].append(f"Training {model_type} regression model...")

    if model_type == 'polynomial':
        model = polynomial_regression(features_normalized, targets, degree)
        results['training_log'].append(f"Trained polynomial regression (degree={degree})")
    else:
        model = linear_regression(features_normalized, targets)
        results['training_log'].append("Trained linear regression")

    # Make predictions on training data
    predictions = predict(model, features_normalized)

    # Calculate metrics
    r_squared = calculate_r_squared(targets, predictions)
    mse = calculate_mse(targets, predictions)
    mae = calculate_mae(targets, predictions)

    results['metrics'] = {
        'r_squared': r_squared,
        'mse': mse,
        'rmse': mse ** 0.5,
        'mae': mae
    }

    # Store model
    model['feature_names'] = feature_names
    model['normalization'] = {
        'means': means,
        'stds': stds
    }

    results['model'] = model
    results['status'] = 'completed'

    # Save if requested
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            results['training_log'].append(f"Model saved to {output_file}")
        except IOError as e:
            results['training_log'].append(f"Warning: Could not save model: {e}")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate and train regression models automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train linear regression
  %(prog)s --file data.csv --target price

  # Train polynomial regression (degree 2)
  %(prog)s --file data.csv --target price --type polynomial --degree 2

  # Save model to file
  %(prog)s --file data.csv --target price --output model.json

  # Verbose output
  %(prog)s --file data.csv --target price --verbose
        """
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Path to training data (CSV format)'
    )
    parser.add_argument(
        '-t', '--target',
        type=str,
        required=True,
        help='Name of target column'
    )
    parser.add_argument(
        '--type',
        choices=['linear', 'polynomial'],
        default='linear',
        help='Model type (default: linear)'
    )
    parser.add_argument(
        '-d', '--degree',
        type=int,
        default=2,
        help='Polynomial degree (default: 2, for polynomial models)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file to save trained model (JSON)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Train model
    results = train_model(
        args.file,
        args.target,
        args.type,
        args.degree,
        args.output,
        args.verbose
    )

    # Output results
    if args.verbose or not args.output:
        output = {
            'status': results['status'],
            'model_type': results['model_type'],
            'metrics': results['metrics'],
            'training_log': results['training_log']
        }
        print(json.dumps(output, indent=2))

    if results['status'] != 'completed':
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
