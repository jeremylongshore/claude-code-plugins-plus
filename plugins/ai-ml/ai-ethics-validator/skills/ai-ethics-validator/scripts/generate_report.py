#!/usr/bin/env python3
"""
Generate detailed ethics validation reports for AI/ML models and datasets.

This script generates comprehensive ethics validation reports in both
markdown and JSON formats, combining model and dataset validation results.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def generate_markdown_report(
    title: str,
    summary: Dict,
    model_results: Optional[Dict] = None,
    dataset_results: Optional[Dict] = None,
    custom_sections: Optional[List[Dict]] = None
) -> str:
    """
    Generate a markdown format ethics report.

    Args:
        title: Report title
        summary: Summary dictionary with overall findings
        model_results: Optional model validation results
        dataset_results: Optional dataset validation results
        custom_sections: Optional list of custom sections

    Returns:
        Formatted markdown report
    """
    report = []

    # Header
    report.append(f"# {title}")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Executive Summary
    report.append("\n## Executive Summary\n")
    if summary.get('overall_score'):
        report.append(f"**Overall Ethics Score:** {summary['overall_score']:.1f}/100")

    if summary.get('key_findings'):
        report.append("\n### Key Findings")
        for finding in summary['key_findings']:
            report.append(f"- {finding}")

    if summary.get('critical_issues'):
        report.append("\n### Critical Issues")
        for issue in summary['critical_issues']:
            report.append(f"- ✗ {issue}")

    # Model Validation Results
    if model_results:
        report.append("\n## Model Validation\n")

        if 'file' in model_results:
            report.append(f"**Model File:** `{model_results['file']}`")
        elif 'endpoint' in model_results:
            report.append(f"**API Endpoint:** {model_results['endpoint']}")

        if 'format_detected' in model_results:
            report.append(f"**Format:** {model_results['format_detected']}")

        report.append(f"**Ethics Score:** {model_results.get('ethics_score', 0):.1f}/100\n")

        if model_results.get('issues'):
            report.append("### Issues")
            for issue in model_results['issues']:
                report.append(f"- {issue}")

        if model_results.get('warnings'):
            report.append("\n### Warnings")
            for warning in model_results['warnings']:
                report.append(f"- {warning}")

    # Dataset Validation Results
    if dataset_results:
        report.append("\n## Dataset Validation\n")

        report.append(f"**Dataset File:** `{dataset_results['file']}`")
        report.append(f"**Format:** {dataset_results['format']}")
        report.append(f"**Records:** {dataset_results['rows']}")
        report.append(f"**Features:** {dataset_results['columns']}\n")
        report.append(f"**Fairness Score:** {dataset_results.get('fairness_score', 0):.1f}/100\n")

        if dataset_results.get('class_distribution'):
            report.append("### Class Distribution")
            report.append("| Class | Count | Percentage |")
            report.append("|-------|-------|-----------|")
            for cls, data in dataset_results['class_distribution'].items():
                report.append(f"| {cls} | {data['count']} | {data['percentage']:.1f}% |")
            report.append()

        if dataset_results.get('missing_values'):
            report.append("### Missing Values")
            report.append("| Feature | Missing | Percentage |")
            report.append("|---------|---------|-----------|")
            for col, data in dataset_results['missing_values'].items():
                report.append(f"| {col} | {data['count']} | {data['percentage']:.1f}% |")
            report.append()

        if dataset_results.get('issues'):
            report.append("### Issues")
            for issue in dataset_results['issues']:
                report.append(f"- {issue}")

        if dataset_results.get('warnings'):
            report.append("\n### Warnings")
            for warning in dataset_results['warnings']:
                report.append(f"- {warning}")

    # Recommendations
    report.append("\n## Recommendations\n")

    all_recommendations = []
    if model_results and model_results.get('recommendations'):
        all_recommendations.extend(model_results['recommendations'])
    if dataset_results and dataset_results.get('recommendations'):
        all_recommendations.extend(dataset_results['recommendations'])

    if all_recommendations:
        for i, rec in enumerate(all_recommendations, 1):
            report.append(f"{i}. {rec}")
    else:
        report.append("No specific recommendations at this time.")

    # Custom Sections
    if custom_sections:
        for section in custom_sections:
            report.append(f"\n## {section['title']}\n")
            report.append(section['content'])

    # Footer
    report.append("\n---")
    report.append(f"*Report generated by AI Ethics Validator on {datetime.now().isoformat()}*")

    return "\n".join(report)


def generate_json_report(
    title: str,
    summary: Dict,
    model_results: Optional[Dict] = None,
    dataset_results: Optional[Dict] = None,
    custom_sections: Optional[List[Dict]] = None
) -> str:
    """
    Generate a JSON format ethics report.

    Args:
        title: Report title
        summary: Summary dictionary
        model_results: Optional model validation results
        dataset_results: Optional dataset validation results
        custom_sections: Optional custom sections

    Returns:
        JSON formatted report string
    """
    report = {
        'title': title,
        'generated': datetime.now().isoformat(),
        'summary': summary,
        'model_validation': model_results,
        'dataset_validation': dataset_results,
        'custom_sections': custom_sections or []
    }

    return json.dumps(report, indent=2, default=str)


def calculate_overall_score(
    model_results: Optional[Dict] = None,
    dataset_results: Optional[Dict] = None
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate overall ethics score from validation results.

    Args:
        model_results: Optional model validation results
        dataset_results: Optional dataset validation results

    Returns:
        Tuple of (overall_score, key_findings, critical_issues)
    """
    scores = []
    findings = []
    issues = []

    if model_results:
        model_score = model_results.get('ethics_score', 0)
        scores.append(model_score)

        if model_results.get('issues'):
            issues.extend(model_results['issues'])
            findings.append(f"Model has {len(model_results['issues'])} critical issue(s)")

        if model_score < 50:
            findings.append("Model ethics score is below acceptable threshold")

    if dataset_results:
        dataset_score = dataset_results.get('fairness_score', 0)
        scores.append(dataset_score)

        if dataset_results.get('issues'):
            issues.extend(dataset_results['issues'])
            findings.append(f"Dataset has {len(dataset_results['issues'])} critical issue(s)")

        if dataset_score < 50:
            findings.append("Dataset fairness score is below acceptable threshold")

    # Calculate average
    overall_score = sum(scores) / len(scores) if scores else 0

    return overall_score, findings, issues


def load_validation_results(filepath: str) -> Dict:
    """
    Load validation results from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        Parsed validation results
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate detailed ethics validation reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report from model and dataset validation results
  %(prog)s --title "Ethics Audit" --model model_results.json --dataset dataset_results.json

  # Generate markdown report
  %(prog)s --title "Audit Report" --model results.json --output report.md

  # Generate JSON report
  %(prog)s --title "Audit Report" --model results.json --output report.json --format json

  # Generate with model only
  %(prog)s --title "Model Ethics Review" --model model_results.json
        """
    )

    parser.add_argument(
        '--title',
        type=str,
        default='AI Ethics Validation Report',
        help='Report title'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Path to model validation results (JSON)'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        help='Path to dataset validation results (JSON)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (if not specified, outputs to stdout)'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='Report format (default: markdown)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Load validation results
    model_results = None
    dataset_results = None

    if args.model:
        model_results = load_validation_results(args.model)
        if args.verbose:
            print(f"Loaded model results from {args.model}", file=sys.stderr)

    if args.dataset:
        dataset_results = load_validation_results(args.dataset)
        if args.verbose:
            print(f"Loaded dataset results from {args.dataset}", file=sys.stderr)

    if not model_results and not dataset_results:
        print("Error: Please provide at least --model or --dataset", file=sys.stderr)
        return 1

    # Calculate overall score
    overall_score, findings, critical_issues = calculate_overall_score(
        model_results,
        dataset_results
    )

    summary = {
        'overall_score': overall_score,
        'key_findings': findings,
        'critical_issues': critical_issues
    }

    # Generate report
    if args.format == 'json':
        report = generate_json_report(
            args.title,
            summary,
            model_results,
            dataset_results
        )
    else:
        report = generate_markdown_report(
            args.title,
            summary,
            model_results,
            dataset_results
        )

    # Output report
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            if args.verbose:
                print(f"Report written to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(report)

    return 0


if __name__ == '__main__':
    sys.exit(main())
