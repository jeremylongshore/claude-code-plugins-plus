#!/usr/bin/env python3
"""
Performance Budget Validator Script

Executes performance budget validation logic by comparing actual metrics
against configured budgets. Supports multiple metric types and integration
with build processes.

Usage:
    validate_budget.py --budget budget.json --metrics metrics.json
    validate_budget.py --budget budget.json --lighthouse lighthouse.json --output report.json
    validate_budget.py --config config.json --fail-on-violation
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class PerformanceBudgetValidator:
    """Validates performance metrics against defined budgets."""

    METRIC_UNITS = {
        "page_load_time": "ms",
        "first_contentful_paint": "ms",
        "largest_contentful_paint": "ms",
        "time_to_interactive": "ms",
        "bundle_size": "KB",
        "js_bundle_size": "KB",
        "css_bundle_size": "KB",
        "image_size": "KB",
        "api_response_time": "ms",
        "lighthouse_score": "score (0-100)",
        "memory_usage": "MB",
        "cpu_usage": "%"
    }

    def __init__(self):
        """Initialize budget validator."""
        self.violations = []
        self.warnings = []
        self.passed_checks = []

    def validate_metrics(
        self,
        budget: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate performance metrics against budget.

        Args:
            budget: Budget configuration dictionary
            metrics: Actual performance metrics dictionary

        Returns:
            Validation report dictionary
        """
        self.violations = []
        self.warnings = []
        self.passed_checks = []

        if not budget:
            return {
                "valid": False,
                "error": "Empty budget configuration",
                "timestamp": datetime.now().isoformat()
            }

        if not metrics:
            return {
                "valid": False,
                "error": "No metrics provided",
                "timestamp": datetime.now().isoformat()
            }

        # Validate each budget constraint
        budget_items = budget.get("budgets", [])
        if not budget_items:
            budget_items = budget  # Support flat structure

        for item_name, budget_value in budget_items.items() if isinstance(budget_items, dict) else enumerate(budget_items):
            if isinstance(budget_items, dict):
                # Named budget
                self._validate_metric(item_name, budget_value, metrics)
            else:
                # List of budgets
                self._validate_budget_item(budget_value, metrics)

        return self._generate_report(budget, metrics)

    def _validate_metric(
        self,
        metric_name: str,
        budget_value: Any,
        metrics: Dict[str, Any]
    ) -> None:
        """Validate a single metric against budget."""
        actual_value = metrics.get(metric_name)

        if actual_value is None:
            self.warnings.append({
                "severity": "warning",
                "metric": metric_name,
                "issue": f"Metric '{metric_name}' not found in metrics",
                "budget": budget_value
            })
            return

        # Handle budget as dict with thresholds
        if isinstance(budget_value, dict):
            self._validate_threshold_budget(metric_name, budget_value, actual_value)
        else:
            # Simple comparison
            if actual_value > budget_value:
                self.violations.append({
                    "severity": "violation",
                    "metric": metric_name,
                    "budget": budget_value,
                    "actual": actual_value,
                    "difference": actual_value - budget_value,
                    "percentage_over": round((actual_value - budget_value) / budget_value * 100, 2),
                    "unit": self.METRIC_UNITS.get(metric_name, "units"),
                    "message": f"{metric_name}: {actual_value} exceeds budget of {budget_value}"
                })
            else:
                self.passed_checks.append({
                    "metric": metric_name,
                    "budget": budget_value,
                    "actual": actual_value,
                    "margin": budget_value - actual_value,
                    "unit": self.METRIC_UNITS.get(metric_name, "units")
                })

    def _validate_threshold_budget(
        self,
        metric_name: str,
        budget_config: Dict[str, Any],
        actual_value: float
    ) -> None:
        """Validate metric against threshold-based budget."""
        critical = budget_config.get("critical")
        warning = budget_config.get("warning")

        if critical is not None and actual_value > critical:
            self.violations.append({
                "severity": "critical",
                "metric": metric_name,
                "budget_critical": critical,
                "actual": actual_value,
                "difference": actual_value - critical,
                "percentage_over": round((actual_value - critical) / critical * 100, 2),
                "unit": self.METRIC_UNITS.get(metric_name, "units"),
                "message": f"{metric_name}: {actual_value} CRITICAL (exceeds {critical})"
            })
        elif warning is not None and actual_value > warning:
            self.warnings.append({
                "severity": "warning",
                "metric": metric_name,
                "budget_warning": warning,
                "actual": actual_value,
                "difference": actual_value - warning,
                "percentage_over": round((actual_value - warning) / warning * 100, 2),
                "unit": self.METRIC_UNITS.get(metric_name, "units"),
                "message": f"{metric_name}: {actual_value} WARNING (exceeds {warning})"
            })
        else:
            self.passed_checks.append({
                "metric": metric_name,
                "budget_critical": critical,
                "budget_warning": warning,
                "actual": actual_value,
                "unit": self.METRIC_UNITS.get(metric_name, "units")
            })

    def _validate_budget_item(
        self,
        item: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> None:
        """Validate a budget item from list format."""
        metric_name = item.get("name") or item.get("metric")
        budget_value = item.get("budget") or item.get("threshold")
        item_type = item.get("type", "metric")

        if not metric_name or budget_value is None:
            return

        actual_value = metrics.get(metric_name)
        if actual_value is None:
            self.warnings.append({
                "severity": "warning",
                "metric": metric_name,
                "issue": f"Metric not found: {metric_name}"
            })
            return

        # Handle different comparison types
        comparison = item.get("comparison", ">")
        if comparison == ">":
            exceeds = actual_value > budget_value
        elif comparison == "<":
            exceeds = actual_value < budget_value
        elif comparison == ">=":
            exceeds = actual_value >= budget_value
        elif comparison == "<=":
            exceeds = actual_value <= budget_value
        else:
            exceeds = actual_value > budget_value

        if exceeds:
            difference = abs(actual_value - budget_value)
            if budget_value != 0:
                percentage = round(difference / budget_value * 100, 2)
            else:
                percentage = 0

            self.violations.append({
                "severity": item.get("severity", "violation"),
                "metric": metric_name,
                "type": item_type,
                "comparison": comparison,
                "budget": budget_value,
                "actual": actual_value,
                "difference": difference,
                "percentage_difference": percentage,
                "unit": item.get("unit", self.METRIC_UNITS.get(metric_name, "units")),
                "message": f"{metric_name}: {actual_value} {comparison} {budget_value}"
            })
        else:
            self.passed_checks.append({
                "metric": metric_name,
                "budget": budget_value,
                "actual": actual_value,
                "unit": item.get("unit", self.METRIC_UNITS.get(metric_name, "units"))
            })

    def _generate_report(
        self,
        budget: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate validation report."""
        total_checks = len(self.violations) + len(self.warnings) + len(self.passed_checks)
        critical_violations = len([v for v in self.violations if v.get("severity") == "critical"])
        violation_count = len(self.violations)

        return {
            "timestamp": datetime.now().isoformat(),
            "valid": violation_count == 0,
            "summary": {
                "total_checks": total_checks,
                "passed": len(self.passed_checks),
                "warnings": len(self.warnings),
                "violations": violation_count,
                "critical_violations": critical_violations,
                "pass_rate": round(len(self.passed_checks) / total_checks * 100, 2) if total_checks > 0 else 100
            },
            "budget_name": budget.get("name", "Performance Budget"),
            "budget_version": budget.get("version", "1.0.0"),
            "passed_checks": self.passed_checks,
            "warnings": self.warnings,
            "violations": self.violations,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if len(self.violations) > 0:
            recommendations.append(f"Fix {len(self.violations)} performance budget violation(s)")

            # Categorize violations
            by_metric = {}
            for violation in self.violations:
                metric = violation.get("metric", "unknown")
                if metric not in by_metric:
                    by_metric[metric] = 0
                by_metric[metric] += 1

            for metric, count in sorted(by_metric.items(), key=lambda x: x[1], reverse=True):
                if count >= 2:
                    recommendations.append(f"Focus on reducing {metric} ({count} violations)")

        if any("bundle_size" in v.get("metric", "") for v in self.violations):
            recommendations.append("Consider code splitting or lazy loading to reduce bundle size")

        if any("paint" in v.get("metric", "") for v in self.violations):
            recommendations.append("Optimize critical rendering path and defer non-critical resources")

        if any("api_response_time" in v.get("metric", "") for v in self.violations):
            recommendations.append("Review API performance, caching strategies, and database queries")

        if not recommendations:
            recommendations.append("Performance metrics are within budget")

        return recommendations

    def generate_summary(self) -> str:
        """Generate a text summary of the validation."""
        lines = []
        lines.append("=" * 60)
        lines.append("Performance Budget Validation Report")
        lines.append("=" * 60)

        if len(self.violations) == 0 and len(self.warnings) == 0:
            lines.append("✓ All performance metrics within budget")
        else:
            if len(self.violations) > 0:
                lines.append(f"\n✗ {len(self.violations)} Budget Violations:")
                for violation in self.violations:
                    metric = violation.get("metric", "unknown")
                    actual = violation.get("actual", "N/A")
                    budget = violation.get("budget", "N/A")
                    unit = violation.get("unit", "")
                    pct = violation.get("percentage_over", 0)
                    lines.append(f"  - {metric}: {actual}{unit} (budget: {budget}{unit}, {pct}% over)")

            if len(self.warnings) > 0:
                lines.append(f"\n⚠ {len(self.warnings)} Warnings:")
                for warning in self.warnings:
                    lines.append(f"  - {warning.get('message', str(warning))}")

        lines.append(f"\n✓ {len(self.passed_checks)} Metrics Passed")
        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate performance metrics against defined budgets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  validate_budget.py --budget budget.json --metrics metrics.json
  validate_budget.py --budget budget.json --metrics metrics.json --output report.json
  validate_budget.py --budget budget.json --metrics metrics.json --fail-on-violation
  validate_budget.py --config config.json
        """
    )

    parser.add_argument(
        "-b", "--budget",
        type=str,
        help="Path to budget configuration JSON file"
    )
    parser.add_argument(
        "-m", "--metrics",
        type=str,
        help="Path to metrics JSON file"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to combined config file (budget + metrics)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file for JSON report"
    )
    parser.add_argument(
        "-s", "--summary",
        action="store_true",
        help="Print text summary to console"
    )
    parser.add_argument(
        "-f", "--fail-on-violation",
        action="store_true",
        help="Exit with error code 1 if violations found"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        # Load configuration
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"Error: Config file not found: {args.config}", file=sys.stderr)
                return 1

            with open(config_path, 'r') as f:
                config = json.load(f)

            budget = config.get("budget", config)
            metrics = config.get("metrics", {})
        else:
            if not args.budget or not args.metrics:
                parser.error("Either --config or both --budget and --metrics are required")

            budget_path = Path(args.budget)
            metrics_path = Path(args.metrics)

            if not budget_path.exists():
                print(f"Error: Budget file not found: {args.budget}", file=sys.stderr)
                return 1

            if not metrics_path.exists():
                print(f"Error: Metrics file not found: {args.metrics}", file=sys.stderr)
                return 1

            with open(budget_path, 'r') as f:
                budget = json.load(f)

            with open(metrics_path, 'r') as f:
                metrics = json.load(f)

        # Validate metrics
        validator = PerformanceBudgetValidator()
        report = validator.validate_metrics(budget, metrics)

        # Output report
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report written to: {args.output}")

        # Print summary if requested
        if args.summary or not args.output:
            print(validator.generate_summary())

        # JSON output if no output file
        if not args.output and not args.summary:
            print(json.dumps(report, indent=2))

        # Return appropriate exit code
        if not report.get("valid") and args.fail_on_violation:
            return 1

        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
