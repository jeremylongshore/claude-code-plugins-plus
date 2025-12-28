#!/usr/bin/env python3
"""
Performance Budget Creation Script

Assists in creating or updating performance budget configuration files.
Supports interactive mode, template-based creation, and baseline generation
from existing metrics.

Usage:
    create_budget.py --interactive
    create_budget.py --template default --output budget.json
    create_budget.py --baseline metrics.json --margin 10 --output budget.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class BudgetCreator:
    """Creates and manages performance budget configurations."""

    TEMPLATES = {
        "default": {
            "name": "Default Performance Budget",
            "version": "1.0.0",
            "budgets": {
                "page_load_time": 3000,
                "first_contentful_paint": 1500,
                "largest_contentful_paint": 2500,
                "time_to_interactive": 3500,
                "bundle_size": 200000,
                "js_bundle_size": 150000,
                "css_bundle_size": 50000
            },
            "description": "Default performance budgets for web applications"
        },
        "strict": {
            "name": "Strict Performance Budget",
            "version": "1.0.0",
            "budgets": {
                "page_load_time": 2000,
                "first_contentful_paint": 800,
                "largest_contentful_paint": 1500,
                "time_to_interactive": 2500,
                "bundle_size": 100000,
                "js_bundle_size": 75000,
                "css_bundle_size": 25000
            },
            "description": "Strict performance budgets for high-performance applications"
        },
        "mobile": {
            "name": "Mobile Performance Budget",
            "version": "1.0.0",
            "budgets": {
                "page_load_time": 5000,
                "first_contentful_paint": 2500,
                "largest_contentful_paint": 4000,
                "time_to_interactive": 5500,
                "bundle_size": 150000,
                "js_bundle_size": 100000,
                "css_bundle_size": 50000
            },
            "description": "Performance budgets optimized for mobile devices"
        },
        "api": {
            "name": "API Performance Budget",
            "version": "1.0.0",
            "budgets": {
                "api_response_time": 500,
                "p95_response_time": 2000,
                "p99_response_time": 5000,
                "error_rate": 0.5
            },
            "description": "Performance budgets for API services"
        }
    }

    def __init__(self):
        """Initialize budget creator."""
        self.budget = {}

    def create_interactive(self) -> Dict[str, Any]:
        """Create budget interactively."""
        print("\n" + "=" * 60)
        print("Performance Budget Creator - Interactive Mode")
        print("=" * 60)

        # Basic information
        name = input("\nBudget name: ").strip() or "Performance Budget"
        description = input("Description (optional): ").strip()
        version = input("Version (default: 1.0.0): ").strip() or "1.0.0"

        self.budget = {
            "name": name,
            "version": version,
            "created": datetime.now().isoformat(),
            "description": description,
            "budgets": {}
        }

        # Add metrics
        print("\n" + "-" * 60)
        print("Add Performance Metrics")
        print("-" * 60)
        print("\nAvailable metrics:")
        metrics_info = {
            "1": ("page_load_time", "ms", 3000),
            "2": ("first_contentful_paint", "ms", 1500),
            "3": ("largest_contentful_paint", "ms", 2500),
            "4": ("time_to_interactive", "ms", 3500),
            "5": ("bundle_size", "KB", 200),
            "6": ("js_bundle_size", "KB", 150),
            "7": ("css_bundle_size", "KB", 50),
            "8": ("api_response_time", "ms", 500),
            "9": ("memory_usage", "MB", 100),
            "10": ("custom metric", None, None)
        }

        for key, (metric_name, unit, default) in metrics_info.items():
            if default:
                print(f"  {key}. {metric_name} ({unit}) - default: {default}")
            else:
                print(f"  {key}. {metric_name}")

        while True:
            choice = input("\nSelect metrics (comma-separated, or 'done' to finish): ").strip()

            if choice.lower() == "done":
                break

            for selection in choice.split(","):
                selection = selection.strip()
                if selection in metrics_info:
                    metric_name, unit, default = metrics_info[selection]

                    if metric_name == "custom metric":
                        custom_name = input(f"  Custom metric name: ").strip()
                        custom_budget = input(f"  Budget value: ").strip()
                        custom_unit = input(f"  Unit (ms/KB/etc): ").strip()

                        if custom_name and custom_budget:
                            try:
                                self.budget["budgets"][custom_name] = float(custom_budget)
                                print(f"  ✓ Added {custom_name}")
                            except ValueError:
                                print(f"  ✗ Invalid budget value")
                    else:
                        budget_value = input(f"  Budget for {metric_name} (default: {default}): ").strip()

                        try:
                            if budget_value:
                                self.budget["budgets"][metric_name] = float(budget_value)
                            else:
                                self.budget["budgets"][metric_name] = default
                            print(f"  ✓ Added {metric_name}")
                        except ValueError:
                            print(f"  ✗ Invalid budget value, skipping")

        return self.budget

    def create_from_template(self, template_name: str) -> Dict[str, Any]:
        """Create budget from template."""
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.TEMPLATES[template_name].copy()
        template["created"] = datetime.now().isoformat()
        return template

    def create_from_baseline(
        self,
        metrics: Dict[str, Any],
        margin_percent: float = 10.0,
        percentile: float = 1.0
    ) -> Dict[str, Any]:
        """
        Create budget from baseline metrics with margin.

        Args:
            metrics: Current metrics dictionary
            margin_percent: Safety margin percentage (default: 10%)
            percentile: Percentile multiplier (e.g., 1.0 for p100, 0.95 for p95)

        Returns:
            Budget configuration
        """
        self.budget = {
            "name": "Generated Performance Budget",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "description": f"Auto-generated from baseline with {margin_percent}% margin",
            "baseline_metrics": metrics.copy(),
            "generation_params": {
                "margin_percent": margin_percent,
                "percentile": percentile
            },
            "budgets": {}
        }

        # Convert metrics to budgets with margin
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                # Apply percentile
                adjusted_value = metric_value * percentile

                # Add margin
                budget_value = adjusted_value * (1 + margin_percent / 100)

                self.budget["budgets"][metric_name] = round(budget_value, 2)

        return self.budget

    def create_tiered(
        self,
        metrics: Dict[str, Any],
        warning_margin: float = 5.0,
        critical_margin: float = 15.0
    ) -> Dict[str, Any]:
        """
        Create tiered budget with warning and critical thresholds.

        Args:
            metrics: Baseline metrics
            warning_margin: Margin for warning threshold
            critical_margin: Margin for critical threshold

        Returns:
            Tiered budget configuration
        """
        self.budget = {
            "name": "Tiered Performance Budget",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "description": f"Tiered thresholds: warning at {warning_margin}%, critical at {critical_margin}%",
            "budgets": {}
        }

        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                self.budget["budgets"][metric_name] = {
                    "baseline": metric_value,
                    "warning": round(metric_value * (1 + warning_margin / 100), 2),
                    "critical": round(metric_value * (1 + critical_margin / 100), 2)
                }

        return self.budget

    def add_metric(
        self,
        metric_name: str,
        budget_value: float,
        unit: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """Add a metric to the budget."""
        if not self.budget:
            self.budget = {
                "name": "Performance Budget",
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "budgets": {}
            }

        if isinstance(budget_value, dict):
            # Support threshold-based budgets
            self.budget["budgets"][metric_name] = budget_value
        else:
            self.budget["budgets"][metric_name] = float(budget_value)

    def save(self, output_path: str) -> None:
        """Save budget to file."""
        if not self.budget:
            raise ValueError("No budget to save")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w') as f:
            json.dump(self.budget, f, indent=2)

        print(f"Budget saved to: {output_path}")

    @staticmethod
    def list_templates() -> None:
        """List available templates."""
        print("\nAvailable Templates:")
        print("-" * 60)
        for name, template in BudgetCreator.TEMPLATES.items():
            print(f"\n{name}:")
            print(f"  Description: {template['description']}")
            print(f"  Metrics: {', '.join(template['budgets'].keys())}")

    def get_budget(self) -> Dict[str, Any]:
        """Get the current budget."""
        return self.budget


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create or update performance budget configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  create_budget.py --interactive
  create_budget.py --template default --output budget.json
  create_budget.py --template strict --output budget.json
  create_budget.py --baseline metrics.json --margin 15 --output budget.json
  create_budget.py --baseline metrics.json --tiered --output budget.json
  create_budget.py --list-templates
        """
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive budget creation"
    )
    parser.add_argument(
        "-t", "--template",
        type=str,
        choices=list(BudgetCreator.TEMPLATES.keys()),
        help="Use a predefined template"
    )
    parser.add_argument(
        "-b", "--baseline",
        type=str,
        help="Generate from baseline metrics file"
    )
    parser.add_argument(
        "-m", "--margin",
        type=float,
        default=10.0,
        help="Safety margin percentage for baseline (default: 10)"
    )
    parser.add_argument(
        "--tiered",
        action="store_true",
        help="Generate tiered budget (baseline, warning, critical)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output budget file"
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        creator = BudgetCreator()

        # List templates
        if args.list_templates:
            creator.list_templates()
            return 0

        # Create budget
        if args.interactive:
            budget = creator.create_interactive()
        elif args.baseline:
            baseline_path = Path(args.baseline)
            if not baseline_path.exists():
                print(f"Error: Baseline file not found: {args.baseline}", file=sys.stderr)
                return 1

            with open(baseline_path, 'r') as f:
                metrics = json.load(f)

            if args.tiered:
                budget = creator.create_tiered(metrics)
            else:
                budget = creator.create_from_baseline(metrics, args.margin)
        elif args.template:
            budget = creator.create_from_template(args.template)
        else:
            parser.error("One of --interactive, --template, or --baseline is required")

        # Output
        if args.output:
            creator.save(args.output)
        else:
            print(json.dumps(budget, indent=2))

        if args.verbose:
            print(f"\nBudget created with {len(budget.get('budgets', {}))} metrics")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
