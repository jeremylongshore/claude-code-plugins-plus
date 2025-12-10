#!/usr/bin/env python3
"""
Performance Budget Violation Reporter Script

Generates reports and sends alerts when performance budgets are violated.
Supports multiple output formats and integrations with monitoring systems.

Usage:
    report_violation.py --report validation_report.json
    report_violation.py --report validation_report.json --output violations.html
    report_violation.py --report validation_report.json --slack webhook_url
    report_violation.py --report validation_report.json --email team@example.com
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import re


class ViolationReporter:
    """Reports performance budget violations."""

    def __init__(self):
        """Initialize violation reporter."""
        self.violations = []
        self.warnings = []
        self.passed = []

    def parse_report(self, report: Dict[str, Any]) -> None:
        """Parse validation report."""
        self.violations = report.get("violations", [])
        self.warnings = report.get("warnings", [])
        self.passed = report.get("passed_checks", [])

    def generate_text_report(self) -> str:
        """Generate text format report."""
        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE BUDGET VIOLATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total Violations: {len(self.violations)}")
        lines.append(f"Warnings: {len(self.warnings)}")
        lines.append(f"Passed Checks: {len(self.passed)}")
        lines.append("")

        # Critical violations
        critical = [v for v in self.violations if v.get("severity") == "critical"]
        if critical:
            lines.append("CRITICAL VIOLATIONS")
            lines.append("-" * 70)
            for violation in critical:
                lines.append(f"\nMetric: {violation.get('metric')}")
                lines.append(f"  Budget:    {violation.get('budget')} {violation.get('unit', '')}")
                lines.append(f"  Actual:    {violation.get('actual')} {violation.get('unit', '')}")
                lines.append(f"  Over:      {violation.get('percentage_over', 'N/A')}%")
                if violation.get('difference'):
                    lines.append(f"  Excess:    {violation.get('difference')} {violation.get('unit', '')}")
            lines.append("")

        # Other violations
        other_violations = [v for v in self.violations if v.get("severity") != "critical"]
        if other_violations:
            lines.append("VIOLATIONS")
            lines.append("-" * 70)
            for violation in other_violations:
                lines.append(f"\nMetric: {violation.get('metric')}")
                lines.append(f"  Budget: {violation.get('budget')} {violation.get('unit', '')}")
                lines.append(f"  Actual: {violation.get('actual')} {violation.get('unit', '')}")
            lines.append("")

        # Warnings
        if self.warnings:
            lines.append("WARNINGS")
            lines.append("-" * 70)
            for warning in self.warnings:
                lines.append(f"- {warning.get('message', str(warning))}")
            lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        if len(self.violations) > 0:
            lines.append("1. Address critical violations immediately")
            lines.append("2. Implement performance optimizations")
            lines.append("3. Review deployment process for performance regressions")
        else:
            lines.append("✓ All performance metrics within budget")

        lines.append("=" * 70)
        return "\n".join(lines)

    def generate_html_report(self) -> str:
        """Generate HTML format report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<meta charset='utf-8'>")
        html.append("<title>Performance Budget Violation Report</title>")
        html.append("<style>")
        html.append("""
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 30px; }
            .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
            .summary-item { background: #f9f9f9; padding: 15px; border-left: 4px solid #007bff; }
            .summary-item.violations { border-left-color: #dc3545; }
            .summary-item.warnings { border-left-color: #ffc107; }
            .summary-item.passed { border-left-color: #28a745; }
            .summary-item h3 { margin: 0 0 5px 0; font-size: 14px; color: #666; }
            .summary-item .value { font-size: 24px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #007bff; color: white; font-weight: bold; }
            tr:hover { background: #f5f5f5; }
            .critical { color: #dc3545; font-weight: bold; }
            .warning { color: #ffc107; }
            .passed { color: #28a745; }
            .metric { font-family: monospace; background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
            .percentage { font-weight: bold; }
            .recommendations { background: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin-top: 20px; }
            .recommendations ul { margin: 10px 0; padding-left: 20px; }
            .recommendations li { margin: 8px 0; }
            .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<div class='container'>")

        # Header
        html.append("<h1>Performance Budget Violation Report</h1>")
        html.append(f"<p>Generated: {datetime.now().isoformat()}</p>")

        # Summary
        html.append("<div class='summary'>")
        html.append(f"<div class='summary-item violations'><h3>Violations</h3><div class='value'>{len(self.violations)}</div></div>")
        html.append(f"<div class='summary-item warnings'><h3>Warnings</h3><div class='value'>{len(self.warnings)}</div></div>")
        html.append(f"<div class='summary-item passed'><h3>Passed</h3><div class='value'>{len(self.passed)}</div></div>")
        html.append(f"<div class='summary-item'><h3>Total</h3><div class='value'>{len(self.violations) + len(self.warnings) + len(self.passed)}</div></div>")
        html.append("</div>")

        # Critical violations
        critical = [v for v in self.violations if v.get("severity") == "critical"]
        if critical:
            html.append("<h2>Critical Violations</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Budget</th><th>Actual</th><th>Over</th><th>Unit</th></tr>")
            for violation in critical:
                html.append("<tr class='critical'>")
                html.append(f"<td class='metric'>{violation.get('metric')}</td>")
                html.append(f"<td>{violation.get('budget')}</td>")
                html.append(f"<td>{violation.get('actual')}</td>")
                html.append(f"<td class='percentage'>{violation.get('percentage_over', 'N/A')}%</td>")
                html.append(f"<td>{violation.get('unit', '')}</td>")
                html.append("</tr>")
            html.append("</table>")

        # Other violations
        other_violations = [v for v in self.violations if v.get("severity") != "critical"]
        if other_violations:
            html.append("<h2>Violations</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Budget</th><th>Actual</th><th>Severity</th><th>Unit</th></tr>")
            for violation in other_violations:
                html.append("<tr>")
                html.append(f"<td class='metric'>{violation.get('metric')}</td>")
                html.append(f"<td>{violation.get('budget')}</td>")
                html.append(f"<td>{violation.get('actual')}</td>")
                html.append(f"<td>{violation.get('severity', 'unknown')}</td>")
                html.append(f"<td>{violation.get('unit', '')}</td>")
                html.append("</tr>")
            html.append("</table>")

        # Warnings
        if self.warnings:
            html.append("<h2>Warnings</h2>")
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Message</th></tr>")
            for warning in self.warnings:
                html.append("<tr class='warning'>")
                html.append(f"<td class='metric'>{warning.get('metric', 'N/A')}</td>")
                html.append(f"<td>{warning.get('message', str(warning))}</td>")
                html.append("</tr>")
            html.append("</table>")

        # Passed checks (summary)
        if self.passed:
            html.append(f"<h2>Passed Checks ({len(self.passed)})</h2>")
            html.append(f"<p class='passed'>✓ {len(self.passed)} metrics are within budget</p>")

        # Recommendations
        html.append("<div class='recommendations'>")
        html.append("<h2>Recommendations</h2>")
        html.append("<ul>")
        if len(self.violations) > 0:
            html.append("<li>Address critical violations immediately</li>")
            html.append("<li>Implement performance optimizations for over-budget metrics</li>")
            html.append("<li>Review recent changes that may have caused regressions</li>")
            html.append("<li>Consider increasing budget if performance targets have changed</li>")
        else:
            html.append("<li>✓ All performance metrics are within budget</li>")
        html.append("</ul>")
        html.append("</div>")

        # Footer
        html.append("<div class='footer'>")
        html.append(f"<p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append("</div>")

        html.append("</div>")
        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON format report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "violations": self.violations,
            "warnings": self.warnings,
            "passed_checks": self.passed,
            "summary": {
                "total_violations": len(self.violations),
                "critical_violations": len([v for v in self.violations if v.get("severity") == "critical"]),
                "warnings": len(self.warnings),
                "passed": len(self.passed)
            }
        }

    def generate_slack_message(self) -> Dict[str, Any]:
        """Generate Slack message payload."""
        critical_count = len([v for v in self.violations if v.get("severity") == "critical"])
        violation_count = len(self.violations)

        color = "#28a745" if violation_count == 0 else "#ffc107" if critical_count == 0 else "#dc3545"
        status = "✓ PASSED" if violation_count == 0 else f"⚠ {violation_count} VIOLATION(S)"

        fields = []

        # Summary
        fields.append({
            "title": "Violations",
            "value": str(len(self.violations)),
            "short": True
        })
        fields.append({
            "title": "Critical",
            "value": str(critical_count),
            "short": True
        })
        fields.append({
            "title": "Warnings",
            "value": str(len(self.warnings)),
            "short": True
        })
        fields.append({
            "title": "Passed",
            "value": str(len(self.passed)),
            "short": True
        })

        # Top violations
        if critical_count > 0:
            top_violations = sorted(self.violations, key=lambda x: x.get("percentage_over", 0), reverse=True)[:3]
            violations_text = "\n".join([
                f"• {v.get('metric')}: {v.get('percentage_over', 'N/A')}% over ({v.get('actual')}/{v.get('budget')} {v.get('unit', '')})"
                for v in top_violations
            ])
            fields.append({
                "title": "Top Violations",
                "value": violations_text,
                "short": False
            })

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"Performance Budget Report - {status}",
                    "text": f"Performance budget validation at {datetime.now().isoformat()}",
                    "fields": fields,
                    "footer": "Performance Budget Validator",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

    def send_slack(self, webhook_url: str) -> bool:
        """Send report to Slack."""
        try:
            import urllib.request
            import json as json_module

            message = self.generate_slack_message()
            data = json_module.dumps(message).encode('utf-8')

            req = urllib.request.Request(webhook_url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error sending to Slack: {e}", file=sys.stderr)
            return False

    def generate_csv_report(self) -> str:
        """Generate CSV format report."""
        lines = []
        lines.append("Type,Metric,Budget,Actual,Difference,Percentage,Unit,Severity")

        for violation in self.violations:
            lines.append(f"Violation,{violation.get('metric')},{violation.get('budget')},{violation.get('actual')},{violation.get('difference', '')},{violation.get('percentage_over', '')},{violation.get('unit', '')},{violation.get('severity', '')}")

        for warning in self.warnings:
            lines.append(f"Warning,{warning.get('metric', '')},{warning.get('budget', '')},{warning.get('actual', '')},{warning.get('difference', '')},{warning.get('percentage_over', '')},{warning.get('unit', '')},{warning.get('severity', '')}")

        for passed in self.passed:
            lines.append(f"Passed,{passed.get('metric')},{passed.get('budget')},{passed.get('actual')},0,0%,{passed.get('unit', '')},passed")

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate reports for performance budget violations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  report_violation.py --report validation.json --output report.html
  report_violation.py --report validation.json --format text
  report_violation.py --report validation.json --format csv --output violations.csv
  report_violation.py --report validation.json --slack https://hooks.slack.com/...
        """
    )

    parser.add_argument(
        "-r", "--report",
        type=str,
        required=True,
        help="Path to validation report JSON file"
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["text", "html", "json", "csv"],
        default="text",
        help="Report format (default: text)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file (stdout if not specified)"
    )
    parser.add_argument(
        "-s", "--slack",
        type=str,
        help="Slack webhook URL for sending report"
    )
    parser.add_argument(
        "-e", "--email",
        type=str,
        help="Email address to send report to"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        # Load validation report
        report_path = Path(args.report)
        if not report_path.exists():
            print(f"Error: Report file not found: {args.report}", file=sys.stderr)
            return 1

        with open(report_path, 'r') as f:
            report_data = json.load(f)

        # Create reporter
        reporter = ViolationReporter()
        reporter.parse_report(report_data)

        # Generate report
        if args.format == "text":
            output_text = reporter.generate_text_report()
        elif args.format == "html":
            output_text = reporter.generate_html_report()
        elif args.format == "json":
            output_text = json.dumps(reporter.generate_json_report(), indent=2)
        elif args.format == "csv":
            output_text = reporter.generate_csv_report()
        else:
            output_text = reporter.generate_text_report()

        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output_text)
            print(f"Report written to: {args.output}")
        else:
            print(output_text)

        # Send to Slack if specified
        if args.slack:
            if reporter.send_slack(args.slack):
                print("Report sent to Slack successfully")
            else:
                print("Failed to send report to Slack", file=sys.stderr)
                return 1

        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in report: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
