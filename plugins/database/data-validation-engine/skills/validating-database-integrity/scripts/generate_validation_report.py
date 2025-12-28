#!/usr/bin/env python3
"""
Generate comprehensive report of data validation results.

This script creates detailed HTML, JSON, or Markdown reports from validation results,
including statistics, identified issues, trend analysis, and recommendations.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ValidationReportGenerator:
    """Generates comprehensive validation reports."""

    def __init__(self):
        """Initialize report generator."""
        self.results = []
        self.metadata = {}

    def load_results(self, filepath: str) -> bool:
        """
        Load validation results from JSON file.

        Args:
            filepath: Path to JSON results file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.results = data.get("validations", [])
            self.metadata = {
                "table": data.get("table", "unknown"),
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
                "statistics": data.get("statistics", {})
            }

            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading results: {e}", file=sys.stderr)
            return False

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics from results.

        Returns:
            Dictionary with summary stats
        """
        if not self.results:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "issues": []
            }

        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("valid", False))
        failed = total - passed

        issues = []
        for result in self.results:
            if not result.get("valid", False):
                details = result.get("details", {})
                issues.append({
                    "rule": details.get("rule", "unknown"),
                    "column": details.get("column", "unknown"),
                    "severity": self._determine_severity(details.get("rule"))
                })

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "issues": issues,
            "critical_issues": sum(1 for i in issues if i["severity"] == "critical"),
            "high_issues": sum(1 for i in issues if i["severity"] == "high"),
            "medium_issues": sum(1 for i in issues if i["severity"] == "medium")
        }

    def _determine_severity(self, rule: str) -> str:
        """
        Determine issue severity based on rule type.

        Args:
            rule: Validation rule name

        Returns:
            Severity level (critical, high, medium, low)
        """
        critical_rules = ["not_null", "unique", "foreign_key"]
        high_rules = ["range", "pattern"]
        medium_rules = ["custom"]

        if rule in critical_rules:
            return "critical"
        elif rule in high_rules:
            return "high"
        elif rule in medium_rules:
            return "medium"
        else:
            return "low"

    def generate_json_report(self) -> str:
        """Generate JSON report."""
        summary = self.generate_summary()

        report = {
            "metadata": self.metadata,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "validations": self.results
        }

        return json.dumps(report, indent=2)

    def generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        summary = self.generate_summary()

        md = []
        md.append(f"# Data Validation Report")
        md.append(f"\n**Table:** {self.metadata.get('table', 'Unknown')}")
        md.append(f"**Generated:** {datetime.now().isoformat()}")
        md.append("")

        # Summary section
        md.append("## Executive Summary\n")
        md.append(f"| Metric | Value |")
        md.append(f"|--------|-------|")
        md.append(f"| Total Checks | {summary['total']} |")
        md.append(f"| Passed | {summary['passed']} |")
        md.append(f"| Failed | {summary['failed']} |")
        md.append(f"| Pass Rate | {summary['pass_rate']:.1f}% |")
        md.append("")

        # Table statistics
        stats = self.metadata.get("statistics", {})
        if stats and "error" not in stats:
            md.append("## Table Statistics\n")
            md.append(f"- **Total Rows:** {stats.get('row_count', 'N/A')}")
            md.append(f"- **Total Columns:** {stats.get('column_count', 'N/A')}")
            md.append("")

        # Issues section
        if summary['failed'] > 0:
            md.append("## Issues Identified\n")

            if summary['critical_issues'] > 0:
                md.append("### Critical Issues\n")
                for issue in summary['issues']:
                    if issue['severity'] == 'critical':
                        md.append(f"- **{issue['rule']}** on column `{issue['column']}`")
                md.append("")

            if summary['high_issues'] > 0:
                md.append("### High Priority Issues\n")
                for issue in summary['issues']:
                    if issue['severity'] == 'high':
                        md.append(f"- **{issue['rule']}** on column `{issue['column']}`")
                md.append("")

            if summary['medium_issues'] > 0:
                md.append("### Medium Priority Issues\n")
                for issue in summary['issues']:
                    if issue['severity'] == 'medium':
                        md.append(f"- **{issue['rule']}** on column `{issue['column']}`")
                md.append("")

        # Detailed results
        if summary['failed'] > 0:
            md.append("## Detailed Validation Results\n")
            for result in self.results:
                if not result.get("valid", False):
                    details = result.get("details", {})
                    rule = details.get("rule", "unknown")
                    column = details.get("column", "N/A")

                    md.append(f"### {rule.replace('_', ' ').title()} - {column}\n")

                    if "error" in details:
                        md.append(f"**Error:** {details['error']}\n")
                    elif rule == "not_null":
                        md.append(f"**Issue:** Found {details.get('null_count', 0)} NULL values\n")
                    elif rule == "unique":
                        md.append(f"**Issue:** Found {details.get('duplicate_count', 0)} "
                                f"duplicate groups\n")
                    elif rule == "range":
                        md.append(f"**Issue:** {details.get('out_of_range_count', 0)} values "
                                f"outside range [{details.get('min')}, {details.get('max')}]\n")

        # Recommendations
        md.append("## Recommendations\n")
        if summary['critical_issues'] > 0:
            md.append("1. **Immediately address critical issues** - These indicate data integrity problems")
        if summary['high_issues'] > 0:
            md.append("2. **Resolve high priority issues within 1 week** - These affect data quality")
        if summary['failed'] == 0:
            md.append("✅ **All validations passed!** - Data integrity is maintained")
        else:
            md.append("3. **Review validation rules** - Ensure they match business requirements")
            md.append("4. **Implement data quality monitoring** - Set up alerts for recurring issues")

        md.append("")
        md.append("---")
        md.append("*Report generated by Data Validation Engine*")

        return "\n".join(md)

    def generate_html_report(self) -> str:
        """Generate HTML report."""
        summary = self.generate_summary()
        stats = self.metadata.get("statistics", {})

        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>Data Validation Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            ".container { max-width: 1000px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }",
            "h2 { color: #555; margin-top: 30px; }",
            "table { width: 100%; border-collapse: collapse; margin: 15px 0; }",
            "th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }",
            "th { background-color: #007bff; color: white; }",
            "tr:hover { background-color: #f9f9f9; }",
            ".summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }",
            ".metric { background-color: #f0f0f0; padding: 15px; border-radius: 5px; }",
            ".metric .value { font-size: 24px; font-weight: bold; color: #007bff; }",
            ".metric .label { color: #666; margin-top: 5px; }",
            ".critical { color: #dc3545; font-weight: bold; }",
            ".high { color: #ff6b6b; font-weight: bold; }",
            ".medium { color: #ffc107; font-weight: bold; }",
            ".success { color: #28a745; font-weight: bold; }",
            ".issue-list { margin: 15px 0; }",
            ".issue { background-color: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; border-radius: 3px; }",
            ".footer { text-align: center; color: #999; margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            f"<h1>Data Validation Report</h1>",
            f"<p><strong>Table:</strong> {self.metadata.get('table', 'Unknown')}</p>",
            f"<p><strong>Generated:</strong> {datetime.now().isoformat()}</p>"
        ]

        # Summary metrics
        html.append("<h2>Summary</h2>")
        html.append("<div class='summary'>")
        html.append(f"<div class='metric'><div class='value'>{summary['total']}</div><div class='label'>Total Checks</div></div>")
        html.append(f"<div class='metric'><div class='value success'>{summary['passed']}</div><div class='label'>Passed</div></div>")
        html.append(f"<div class='metric'><div class='value critical'>{summary['failed']}</div><div class='label'>Failed</div></div>")
        html.append(f"<div class='metric'><div class='value'>{summary['pass_rate']:.1f}%</div><div class='label'>Pass Rate</div></div>")
        html.append("</div>")

        # Table statistics
        if stats and "error" not in stats:
            html.append("<h2>Table Statistics</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Value</th></tr>")
            html.append(f"<tr><td>Total Rows</td><td>{stats.get('row_count', 'N/A')}</td></tr>")
            html.append(f"<tr><td>Total Columns</td><td>{stats.get('column_count', 'N/A')}</td></tr>")
            html.append("</table>")

        # Issues
        if summary['failed'] > 0:
            html.append("<h2>Issues</h2>")
            html.append("<div class='issue-list'>")

            for issue in summary['issues']:
                severity_class = issue['severity']
                html.append(
                    f"<div class='issue'>"
                    f"<span class='{severity_class}'>{issue['severity'].upper()}</span>: "
                    f"<strong>{issue['rule']}</strong> on column <code>{issue['column']}</code>"
                    f"</div>"
                )

            html.append("</div>")
        else:
            html.append("<h2>Results</h2>")
            html.append("<p class='success'>✅ All validations passed!</p>")

        # Footer
        html.append("<div class='footer'>")
        html.append("<p>Report generated by Data Validation Engine</p>")
        html.append("</div>")

        html.append("</div>")
        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)


def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive data validation reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --results validation.json
  %(prog)s --results validation.json --format markdown
  %(prog)s --results validation.json --format html --output report.html
  %(prog)s --results validation.json --format json --output report.json
        """
    )

    parser.add_argument(
        "--results",
        required=True,
        help="Path to JSON file containing validation results"
    )
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["json", "markdown", "html"],
        help="Report format"
    )
    parser.add_argument(
        "--output",
        help="Output file for report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    try:
        generator = ValidationReportGenerator()

        # Load results
        if args.verbose:
            print(f"Loading results from {args.results}...", file=sys.stderr)

        if not generator.load_results(args.results):
            sys.exit(1)

        # Generate report
        if args.format == "json":
            report = generator.generate_json_report()
        elif args.format == "html":
            report = generator.generate_html_report()
        else:  # markdown
            report = generator.generate_markdown_report()

        # Print report
        print(report)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)

            if args.verbose:
                print(f"\nReport saved to {args.output}", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
