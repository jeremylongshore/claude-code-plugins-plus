#!/usr/bin/env python3
"""
Evaluate the performance of trained regression models.

This script evaluates regression model performance using metrics such as:
- R-squared (coefficient of determination)
- Mean Squared Error (MSE) and Root Mean Squared Error (RMSE)
- Mean Absolute Error (MAE)
- Mean Absolute Percentage Error (MAPE)
- Residual analysis and diagnostics
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def load_model(filepath: str) -> Dict:
    """Load a trained model from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Model file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing model JSON: {e}", file=sys.stderr)
        sys.exit(1)


def load_csv_data(filepath: str, target_col: str) -> Tuple[List[List[float]], List[float], List[str]]:
    """Load CSV data for evaluation."""
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

                except (ValueError, KeyError):
                    pass  # Skip invalid rows

        if not features or not targets:
            print("Error: No valid data could be loaded", file=sys.stderr)
            sys.exit(1)

        return features, targets, feature_names

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def predict(model: Dict, features: List[List[float]]) -> List[float]:
    """Make predictions with a trained model."""
    predictions = []
    means = model.get('normalization', {}).get('means', [])
    stds = model.get('normalization', {}).get('stds', [])

    for row in features:
        # Normalize features
        normalized_row = row.copy()
        if means and stds:
            normalized_row = [
                (row[i] - means[i]) / stds[i] if stds[i] > 0 else 0
                for i in range(len(row))
            ]

        if model['type'] == 'linear':
            pred = model['intercept']
            for i, coef in enumerate(model['coefficients']):
                if i < len(normalized_row):
                    pred += coef * normalized_row[i]
            predictions.append(pred)

        elif model['type'] == 'polynomial':
            poly_row = normalized_row.copy()
            for d in range(2, model['degree'] + 1):
                for val in normalized_row[:len(model['feature_names'])]:
                    poly_row.append(val ** d)

            pred = model['intercept']
            for i, coef in enumerate(model['coefficients']):
                if i < len(poly_row):
                    pred += coef * poly_row[i]
            predictions.append(pred)

    return predictions


def calculate_metrics(targets: List[float], predictions: List[float]) -> Dict[str, float]:
    """Calculate evaluation metrics."""
    n = len(targets)

    if n == 0:
        return {}

    # Basic metrics
    mean_target = sum(targets) / n

    # Sum of squares
    ss_res = sum((targets[i] - predictions[i]) ** 2 for i in range(n))
    ss_tot = sum((t - mean_target) ** 2 for t in targets)

    # R-squared
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # MSE and RMSE
    mse = ss_res / n
    rmse = mse ** 0.5

    # MAE
    mae = sum(abs(targets[i] - predictions[i]) for i in range(n)) / n

    # MAPE (Mean Absolute Percentage Error)
    mape_sum = 0
    valid_mape = 0
    for i in range(n):
        if targets[i] != 0:
            mape_sum += abs((targets[i] - predictions[i]) / targets[i])
            valid_mape += 1
    mape = (mape_sum / valid_mape * 100) if valid_mape > 0 else 0

    # Adjusted R-squared (for multiple features)
    # adj_r2 = 1 - ((1 - r2) * (n - 1) / (n - k - 1)) where k is number of features

    return {
        'r_squared': r_squared,
        'mse': mse,
        'rmse': rmse,
        'mae': mae,
        'mape': mape,
        'mean_target': mean_target,
        'std_target': (sum((t - mean_target) ** 2 for t in targets) / n) ** 0.5
    }


def analyze_residuals(targets: List[float], predictions: List[float]) -> Dict:
    """Analyze residuals for model diagnostics."""
    residuals = [targets[i] - predictions[i] for i in range(len(targets))]

    if not residuals:
        return {}

    # Residual statistics
    mean_residual = sum(residuals) / len(residuals)
    std_residual = (sum((r - mean_residual) ** 2 for r in residuals) / len(residuals)) ** 0.5

    # Detect systematic bias
    positive_residuals = sum(1 for r in residuals if r > 0)
    negative_residuals = sum(1 for r in residuals if r < 0)
    bias_ratio = max(positive_residuals, negative_residuals) / len(residuals)

    # Heteroscedasticity: check if residual variance changes with prediction magnitude
    predictions_sorted = sorted(enumerate(predictions), key=lambda x: x[1])
    first_half_idx = [i for i, _ in predictions_sorted[:len(predictions)//2]]
    second_half_idx = [i for i, _ in predictions_sorted[len(predictions)//2:]]

    if first_half_idx and second_half_idx:
        var_first = sum((residuals[i] ** 2) for i in first_half_idx) / len(first_half_idx)
        var_second = sum((residuals[i] ** 2) for i in second_half_idx) / len(second_half_idx)
        heteroscedasticity_score = max(var_first, var_second) / min(var_first, var_second) if min(var_first, var_second) > 0 else 1.0
    else:
        heteroscedasticity_score = 1.0

    return {
        'mean': mean_residual,
        'std': std_residual,
        'min': min(residuals),
        'max': max(residuals),
        'positive_count': positive_residuals,
        'negative_count': negative_residuals,
        'bias_ratio': bias_ratio,
        'heteroscedasticity_score': heteroscedasticity_score
    }


def evaluate_model(
    model_file: str,
    data_file: str,
    target_col: str,
    output_file: Optional[str] = None,
    verbose: bool = False
) -> Dict:
    """
    Evaluate a trained regression model.

    Args:
        model_file: Path to trained model JSON
        data_file: Path to evaluation data
        target_col: Name of target column
        output_file: Optional output file
        verbose: Verbose output

    Returns:
        Evaluation results
    """
    results = {
        'status': 'evaluating',
        'model_file': model_file,
        'data_file': data_file,
        'metrics': {},
        'residuals': {},
        'diagnostics': [],
        'evaluation_log': []
    }

    # Load model
    if verbose:
        results['evaluation_log'].append("Loading model...")
    model = load_model(model_file)
    results['evaluation_log'].append(f"Loaded {model.get('type', 'unknown')} regression model")

    # Load evaluation data
    if verbose:
        results['evaluation_log'].append("Loading evaluation data...")
    features, targets, feature_names = load_csv_data(data_file, target_col)
    results['evaluation_log'].append(f"Loaded {len(features)} samples for evaluation")

    # Make predictions
    if verbose:
        results['evaluation_log'].append("Making predictions...")
    predictions = predict(model, features)

    # Calculate metrics
    if verbose:
        results['evaluation_log'].append("Calculating metrics...")
    metrics = calculate_metrics(targets, predictions)
    results['metrics'] = metrics

    # Analyze residuals
    if verbose:
        results['evaluation_log'].append("Analyzing residuals...")
    residuals = analyze_residuals(targets, predictions)
    results['residuals'] = residuals

    # Diagnostics
    results['diagnostics'] = []

    if metrics.get('r_squared', 0) < 0.5:
        results['diagnostics'].append("Model has poor explanatory power (R² < 0.5)")

    if metrics.get('mape', 0) > 20:
        results['diagnostics'].append(f"High Mean Absolute Percentage Error ({metrics['mape']:.1f}%)")

    if residuals.get('bias_ratio', 0) > 0.7:
        results['diagnostics'].append("Systematic bias detected in predictions")

    if residuals.get('heteroscedasticity_score', 1.0) > 3.0:
        results['diagnostics'].append("Heteroscedasticity detected (non-constant variance)")

    if not results['diagnostics']:
        results['diagnostics'].append("Model performance appears reasonable")

    results['status'] = 'completed'

    # Save results if requested
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            results['evaluation_log'].append(f"Results saved to {output_file}")
        except IOError as e:
            results['evaluation_log'].append(f"Warning: Could not save results: {e}")

    return results


def format_report(results: Dict) -> str:
    """Format evaluation results as a readable report."""
    report = []
    report.append("=" * 70)
    report.append("REGRESSION MODEL EVALUATION REPORT")
    report.append("=" * 70)

    report.append(f"\nModel: {results['model_file']}")
    report.append(f"Data: {results['data_file']}")

    metrics = results['metrics']
    report.append("\n[PERFORMANCE METRICS]")
    report.append(f"  R-squared: {metrics.get('r_squared', 0):.4f}")
    report.append(f"  RMSE: {metrics.get('rmse', 0):.4f}")
    report.append(f"  MAE: {metrics.get('mae', 0):.4f}")
    report.append(f"  MAPE: {metrics.get('mape', 0):.2f}%")

    residuals = results['residuals']
    if residuals:
        report.append("\n[RESIDUAL ANALYSIS]")
        report.append(f"  Mean Residual: {residuals.get('mean', 0):.4f}")
        report.append(f"  Std Residual: {residuals.get('std', 0):.4f}")
        report.append(f"  Bias Ratio: {residuals.get('bias_ratio', 0):.2f}")
        report.append(f"  Heteroscedasticity: {residuals.get('heteroscedasticity_score', 0):.2f}")

    if results['diagnostics']:
        report.append("\n[DIAGNOSTICS]")
        for diag in results['diagnostics']:
            report.append(f"  • {diag}")

    report.append("\n" + "=" * 70)

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate the performance of trained regression models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate a model on test data
  %(prog)s --model model.json --data test_data.csv --target price

  # Save evaluation results
  %(prog)s --model model.json --data test_data.csv --target price --output eval_results.json

  # Verbose output
  %(prog)s --model model.json --data test_data.csv --target price --verbose
        """
    )

    parser.add_argument(
        '-m', '--model',
        type=str,
        required=True,
        help='Path to trained model file (JSON)'
    )
    parser.add_argument(
        '-d', '--data',
        type=str,
        required=True,
        help='Path to evaluation data (CSV)'
    )
    parser.add_argument(
        '-t', '--target',
        type=str,
        required=True,
        help='Name of target column'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file to save evaluation results'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Evaluate model
    results = evaluate_model(
        args.model,
        args.data,
        args.target,
        args.output,
        args.verbose
    )

    # Output results
    if args.verbose or not args.output:
        report = format_report(results)
        print(report)

    if results['status'] != 'completed':
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
