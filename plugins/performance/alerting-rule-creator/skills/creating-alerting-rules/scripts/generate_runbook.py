#!/usr/bin/env python3
"""
Generates a basic runbook based on the alert type and potential causes.

This script creates runbook documentation for responding to specific alert types,
including diagnosis steps, remediation procedures, and escalation paths.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


# Common alert patterns and their runbook templates
ALERT_TEMPLATES = {
    "cpu_high": {
        "title": "High CPU Utilization Alert",
        "description": "CPU usage has exceeded configured threshold",
        "common_causes": [
            "Unexpected spike in application requests",
            "Long-running or infinite loops in application code",
            "Memory exhaustion causing excessive swapping",
            "External process consuming resources",
            "Inefficient database queries"
        ],
        "diagnosis_steps": [
            "Check system CPU utilization across cores: `top -b -n 1`",
            "Identify top CPU consuming processes: `ps aux --sort=-%cpu | head -20`",
            "Review application logs for errors or warnings",
            "Check for pending requests in application queue",
            "Monitor memory usage: `free -h`",
            "Check disk I/O: `iostat -x 1 5`"
        ],
        "remediation": [
            "If application issue: Review application logs and restart service if needed",
            "If query issue: Optimize slow queries or add indexes",
            "If load issue: Consider horizontal scaling or caching layer",
            "Kill long-running processes if they're hung: `kill -9 <PID>`",
            "Clear disk cache if needed: `sync && echo 3 > /proc/sys/vm/drop_caches`"
        ],
        "escalation": [
            "If CPU remains high after initial remediation: Contact platform team",
            "If related to database: Escalate to database team",
            "If affecting multiple services: Page on-call engineer"
        ]
    },
    "memory_high": {
        "title": "High Memory Utilization Alert",
        "description": "Memory usage has exceeded configured threshold",
        "common_causes": [
            "Memory leak in application",
            "Insufficient swap space",
            "Large dataset processing",
            "Database cache misconfiguration",
            "Too many concurrent connections"
        ],
        "diagnosis_steps": [
            "Check current memory usage: `free -h`",
            "View memory by process: `ps aux --sort=-%mem | head -20`",
            "Check for memory leaks: `valgrind --leak-check=full <process>`",
            "Review application cache settings",
            "Monitor memory over time: `watch -n 1 free -h`",
            "Check swap usage: `swapon -s`"
        ],
        "remediation": [
            "Restart affected service to clear memory",
            "Reduce cache size or TTL if overallocated",
            "Optimize data structures for memory efficiency",
            "Increase available memory if possible",
            "Implement memory limits per process: `ulimit -v <bytes>`"
        ],
        "escalation": [
            "If memory issue persists: Contact infrastructure team",
            "If application memory leak confirmed: Escalate to development team",
            "If system-wide memory issue: Request hardware upgrade"
        ]
    },
    "disk_space_low": {
        "title": "Low Disk Space Alert",
        "description": "Disk space usage has exceeded threshold",
        "common_causes": [
            "Application logs not being rotated",
            "Temporary files not being cleaned up",
            "Database grow beyond allocated space",
            "Old backups not being deleted",
            "Container or VM images consuming space"
        ],
        "diagnosis_steps": [
            "Check disk usage: `df -h`",
            "Find large files: `du -sh /* | sort -rh`",
            "Check log file sizes: `ls -lhS /var/log/ | head -20`",
            "Review application temp directories",
            "Check inode usage: `df -i`",
            "Monitor disk growth: `du -sh . && sleep 60 && du -sh .`"
        ],
        "remediation": [
            "Remove old log files: `find /var/log -type f -mtime +30 -delete`",
            "Compress old logs: `gzip /var/log/*.log`",
            "Clear temp directory: `rm -rf /tmp/* /var/tmp/*`",
            "Remove old backups or Docker images",
            "Archive application data if possible"
        ],
        "escalation": [
            "If unable to free space: Contact infrastructure team",
            "If database is consuming space: Escalate to DBA",
            "If persistent issue: Request storage expansion"
        ]
    },
    "response_time_high": {
        "title": "High Response Time Alert",
        "description": "API or service response time has exceeded threshold",
        "common_causes": [
            "High request concurrency",
            "Slow database queries",
            "Insufficient server resources",
            "Network latency or congestion",
            "External service dependency slowdown"
        ],
        "diagnosis_steps": [
            "Check request queue depth: Review application metrics",
            "Identify slow requests: Review application request logs",
            "Check database performance: `mysql> SHOW PROCESSLIST;`",
            "Monitor network latency: `mtr <destination>`",
            "Check dependencies: Verify external service health",
            "Review recent deployments or configuration changes"
        ],
        "remediation": [
            "Optimize slow queries or add database indexes",
            "Increase application server capacity or worker threads",
            "Enable caching for frequently accessed data",
            "Use connection pooling for database connections",
            "Consider circuit breaker for slow dependencies",
            "Scale horizontally if load is high"
        ],
        "escalation": [
            "If performance doesn't improve: Contact development team",
            "If database issue: Escalate to database team",
            "If infrastructure bottleneck: Contact infrastructure team"
        ]
    },
    "error_rate_high": {
        "title": "High Error Rate Alert",
        "description": "Application error rate has exceeded threshold",
        "common_causes": [
            "Bad deployment or configuration change",
            "Database connectivity issues",
            "External service failure",
            "Resource exhaustion",
            "Bug in application code"
        ],
        "diagnosis_steps": [
            "Check application error logs for patterns",
            "Review recent deployments: `git log --oneline -5`",
            "Check database connectivity: `nc -zv <db-host> <port>`",
            "Verify external service availability",
            "Check system resources (CPU, memory, disk)",
            "Look for error spikes correlated with deployments"
        ],
        "remediation": [
            "If recent deployment: Consider rollback",
            "Check database connections and restart if needed",
            "Verify configuration values are correct",
            "Check application health: `curl http://localhost:8080/health`",
            "Review logs for specific error messages",
            "Restart affected service if appropriate"
        ],
        "escalation": [
            "If errors persist: Initiate incident response",
            "If database issue: Escalate to database team",
            "If external service issue: Contact vendor support"
        ]
    }
}


def load_custom_templates(filepath: str) -> Dict[str, Any]:
    """
    Load custom runbook templates from JSON file.

    Args:
        filepath: Path to JSON file with custom templates

    Returns:
        Dictionary of templates

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Templates file not found: {filepath}")

        with open(path, 'r') as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def get_alert_template(
    alert_type: str,
    custom_templates: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get runbook template for alert type.

    Args:
        alert_type: Type of alert (cpu_high, memory_high, etc.)
        custom_templates: Optional custom templates dictionary

    Returns:
        Template dictionary for the alert type
    """
    # Check custom templates first
    if custom_templates and alert_type in custom_templates:
        return custom_templates[alert_type]

    # Return built-in template or generic template
    if alert_type in ALERT_TEMPLATES:
        return ALERT_TEMPLATES[alert_type]

    # Generic template for unknown alert types
    return {
        "title": f"Alert: {alert_type}",
        "description": f"Alert of type {alert_type} has been triggered",
        "common_causes": [
            "Check application health and recent changes",
            "Review system resources and dependencies"
        ],
        "diagnosis_steps": [
            "Check application logs for errors",
            "Review system metrics (CPU, memory, disk)",
            "Verify external dependencies are healthy",
            "Check for recent configuration or deployment changes"
        ],
        "remediation": [
            "Identify the root cause from logs",
            "Take appropriate action based on findings",
            "Restart services if needed",
            "Monitor for issue recurrence"
        ],
        "escalation": [
            "If issue persists, escalate to on-call engineer",
            "Contact relevant team (development, infrastructure, database)"
        ]
    }


def generate_runbook(
    alert_type: str,
    severity: str,
    alert_name: Optional[str] = None,
    custom_templates: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Generate a runbook for an alert type.

    Args:
        alert_type: Type of alert
        severity: Severity level (critical, high, medium, low)
        alert_name: Optional human-readable alert name
        custom_templates: Optional custom templates
        include_metadata: Whether to include metadata

    Returns:
        Runbook dictionary
    """
    template = get_alert_template(alert_type, custom_templates)

    runbook = {
        "alert_type": alert_type,
        "alert_name": alert_name or template.get("title"),
        "severity": severity,
        "description": template.get("description", ""),
        "common_causes": template.get("common_causes", []),
        "diagnosis_steps": template.get("diagnosis_steps", []),
        "remediation": template.get("remediation", []),
        "escalation": template.get("escalation", [])
    }

    if include_metadata:
        runbook["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0"
        }

    return runbook


def format_runbook_markdown(runbook: Dict[str, Any]) -> str:
    """
    Format runbook as Markdown document.

    Args:
        runbook: Runbook dictionary

    Returns:
        Markdown formatted string
    """
    md = []

    md.append(f"# {runbook['alert_name']}")
    md.append(f"\n**Alert Type:** {runbook['alert_type']}")
    md.append(f"**Severity:** {runbook['severity'].upper()}\n")

    if runbook.get("metadata"):
        md.append(f"*Generated: {runbook['metadata']['generated_at']}*\n")

    md.append(f"## Description\n{runbook['description']}\n")

    md.append("## Common Causes\n")
    for cause in runbook["common_causes"]:
        md.append(f"- {cause}")
    md.append("")

    md.append("## Diagnosis Steps\n")
    for step in runbook["diagnosis_steps"]:
        md.append(f"1. {step}")
    md.append("")

    md.append("## Remediation\n")
    for remedy in runbook["remediation"]:
        md.append(f"- {remedy}")
    md.append("")

    md.append("## Escalation\n")
    for escalation in runbook["escalation"]:
        md.append(f"- {escalation}")
    md.append("")

    md.append("---")
    md.append("*This runbook was automatically generated. Update as needed based on your environment.*")

    return "\n".join(md)


def main():
    """Main entry point for runbook generation."""
    parser = argparse.ArgumentParser(
        description="Generate runbooks for alert types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --alert-type cpu_high --severity critical
  %(prog)s --alert-type memory_high --severity high --name "Memory Alert"
  %(prog)s --alert-type response_time_high --output runbook.md --format markdown
  %(prog)s --alert-type custom_alert --templates custom.json --output runbook.json
        """
    )

    parser.add_argument(
        "--alert-type",
        required=True,
        help="Type of alert (e.g., cpu_high, memory_high, error_rate_high)"
    )
    parser.add_argument(
        "--severity",
        default="high",
        choices=["critical", "high", "medium", "low"],
        help="Alert severity level"
    )
    parser.add_argument(
        "--name",
        help="Human-readable alert name"
    )
    parser.add_argument(
        "--templates",
        help="Path to JSON file with custom templates"
    )
    parser.add_argument(
        "--output",
        help="Output file for runbook"
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "markdown"],
        help="Output format"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    try:
        # Load custom templates if provided
        custom_templates = None
        if args.templates:
            if args.verbose:
                print(f"Loading custom templates from {args.templates}...", file=sys.stderr)
            custom_templates = load_custom_templates(args.templates)

        # Generate runbook
        runbook = generate_runbook(
            args.alert_type,
            args.severity,
            args.name,
            custom_templates
        )

        # Format output
        if args.format == "markdown":
            output_content = format_runbook_markdown(runbook)
            content_type = "Markdown"
        else:
            output_content = json.dumps(runbook, indent=2)
            content_type = "JSON"

        # Print to stdout
        print(output_content)

        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_content)

            if args.verbose:
                print(f"\nRunbook saved to {args.output} ({content_type})", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
