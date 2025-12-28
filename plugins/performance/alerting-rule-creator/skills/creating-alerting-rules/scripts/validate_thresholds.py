#!/usr/bin/env python3
"""
Validates alerting thresholds against historical data to prevent false positives.

This script analyzes historical metrics and validates proposed alerting thresholds
to ensure they don't trigger false positives or false negatives under normal operation.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any


def load_historical_data(filepath: str) -> List[Dict[str, Any]]:
    """
    Load historical metric data from a JSON file.

    Args:
        filepath: Path to JSON file containing historical data

    Returns:
        List of data points with timestamp and value

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Historical data file not found: {filepath}")

        with open(path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Historical data must be a list of data points")

        return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate statistical metrics from a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with min, max, mean, std_dev, p95, p99
    """
    if not values:
        return {
            "min": 0,
            "max": 0,
            "mean": 0,
            "std_dev": 0,
            "p95": 0,
            "p99": 0
        }

    sorted_values = sorted(values)
    n = len(sorted_values)

    # Calculate mean
    mean = sum(values) / n

    # Calculate standard deviation
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = variance ** 0.5

    # Calculate percentiles
    p95_idx = int(n * 0.95)
    p99_idx = int(n * 0.99)

    return {
        "min": min(values),
        "max": max(values),
        "mean": mean,
        "std_dev": std_dev,
        "p95": sorted_values[p95_idx] if p95_idx < n else sorted_values[-1],
        "p99": sorted_values[p99_idx] if p99_idx < n else sorted_values[-1]
    }


def validate_threshold(
    stats: Dict[str, float],
    threshold: float,
    threshold_type: str = "upper"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate if a threshold is appropriate based on historical statistics.

    Args:
        stats: Dictionary of statistical metrics
        threshold: Proposed threshold value
        threshold_type: Either 'upper' or 'lower'

    Returns:
        Tuple of (is_valid, validation_details)
    """
    details = {
        "threshold": threshold,
        "type": threshold_type,
        "warnings": [],
        "recommendations": []
    }

    if threshold_type == "upper":
        # Check if threshold is too close to max
        if threshold <= stats["max"]:
            details["warnings"].append(
                f"Threshold {threshold} is at or below historical max {stats['max']}. "
                "This may cause frequent alerts."
            )

        # Check if threshold is reasonable relative to p99
        if threshold <= stats["p99"]:
            details["warnings"].append(
                f"Threshold {threshold} is at or below p99 {stats['p99']}. "
                "Alert may trigger during normal spikes."
            )

        # Recommendations
        if threshold < stats["mean"] + (3 * stats["std_dev"]):
            details["recommendations"].append(
                f"Consider raising threshold to {stats['mean'] + (3 * stats['std_dev']):.2f} "
                "(mean + 3 std devs) to reduce false positives."
            )

    elif threshold_type == "lower":
        # Check if threshold is too close to min
        if threshold >= stats["min"]:
            details["warnings"].append(
                f"Threshold {threshold} is at or above historical min {stats['min']}. "
                "This may cause frequent alerts."
            )

        # Check if threshold is reasonable relative to p1
        if threshold >= stats["min"] + (stats["std_dev"] * 0.5):
            details["warnings"].append(
                f"Threshold {threshold} may be too high. "
                "Alert could miss actual anomalies."
            )

        # Recommendations
        if threshold > stats["mean"] - (3 * stats["std_dev"]):
            details["recommendations"].append(
                f"Consider lowering threshold to {stats['mean'] - (3 * stats['std_dev']):.2f} "
                "(mean - 3 std devs) to improve detection."
            )

    is_valid = len(details["warnings"]) == 0

    return is_valid, details


def format_report(
    metric_name: str,
    stats: Dict[str, float],
    validations: List[Tuple[float, str, Tuple[bool, Dict]]]
) -> str:
    """
    Format validation results into a readable report.

    Args:
        metric_name: Name of the metric being validated
        stats: Statistical metrics
        validations: List of (threshold, type, validation) tuples

    Returns:
        Formatted report string
    """
    report = []
    report.append(f"\n{'='*70}")
    report.append(f"Threshold Validation Report: {metric_name}")
    report.append(f"{'='*70}\n")

    report.append("Historical Data Statistics:")
    report.append(f"  Min:     {stats['min']:.2f}")
    report.append(f"  Max:     {stats['max']:.2f}")
    report.append(f"  Mean:    {stats['mean']:.2f}")
    report.append(f"  Std Dev: {stats['std_dev']:.2f}")
    report.append(f"  P95:     {stats['p95']:.2f}")
    report.append(f"  P99:     {stats['p99']:.2f}\n")

    for threshold, threshold_type, (is_valid, details) in validations:
        status = "VALID" if is_valid else "WARNINGS"
        report.append(f"{status}: {threshold_type.upper()} threshold = {threshold:.2f}")

        if details["warnings"]:
            report.append("  Warnings:")
            for warning in details["warnings"]:
                report.append(f"    - {warning}")

        if details["recommendations"]:
            report.append("  Recommendations:")
            for rec in details["recommendations"]:
                report.append(f"    - {rec}")

        report.append("")

    report.append(f"{'='*70}\n")

    return "\n".join(report)


def main():
    """Main entry point for threshold validation."""
    parser = argparse.ArgumentParser(
        description="Validate alerting thresholds against historical data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --metric cpu_usage --data history.json --upper 85.0
  %(prog)s --metric memory_used --data history.json --lower 1000 --upper 8000
  %(prog)s --metric response_time --data metrics.json --upper 500 --output report.json
        """
    )

    parser.add_argument(
        "--metric",
        required=True,
        help="Name of the metric to validate"
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to JSON file containing historical data"
    )
    parser.add_argument(
        "--upper",
        type=float,
        help="Upper threshold to validate"
    )
    parser.add_argument(
        "--lower",
        type=float,
        help="Lower threshold to validate"
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

    # Validate that at least one threshold is provided
    if not args.upper and not args.lower:
        parser.error("At least one of --upper or --lower must be specified")

    try:
        # Load historical data
        if args.verbose:
            print(f"Loading historical data from {args.data}...", file=sys.stderr)

        data = load_historical_data(args.data)

        # Extract numeric values
        values = []
        for point in data:
            if isinstance(point, dict) and "value" in point:
                values.append(float(point["value"]))
            elif isinstance(point, (int, float)):
                values.append(float(point))

        if not values:
            print("Error: No numeric values found in data", file=sys.stderr)
            sys.exit(1)

        # Calculate statistics
        stats = calculate_statistics(values)

        if args.verbose:
            print(f"Analyzed {len(values)} data points", file=sys.stderr)

        # Validate thresholds
        validations = []

        if args.upper:
            is_valid, details = validate_threshold(stats, args.upper, "upper")
            validations.append((args.upper, "upper", (is_valid, details)))

        if args.lower:
            is_valid, details = validate_threshold(stats, args.lower, "lower")
            validations.append((args.lower, "lower", (is_valid, details)))

        # Generate report
        report = format_report(args.metric, stats, validations)

        # Print report
        print(report)

        # Save JSON output if requested
        if args.output:
            output_data = {
                "metric": args.metric,
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "validations": [
                    {
                        "threshold": threshold,
                        "type": threshold_type,
                        "valid": is_valid,
                        "details": details
                    }
                    for threshold, threshold_type, (is_valid, details) in validations
                ]
            }

            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)

            if args.verbose:
                print(f"Results saved to {args.output}", file=sys.stderr)

        # Exit with appropriate code
        all_valid = all(is_valid for _, _, (is_valid, _) in validations)
        sys.exit(0 if all_valid else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
