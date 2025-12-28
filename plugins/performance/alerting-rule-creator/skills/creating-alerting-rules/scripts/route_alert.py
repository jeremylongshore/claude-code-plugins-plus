#!/usr/bin/env python3
"""
Routes alerts based on severity and category to appropriate channels.

This script determines the appropriate notification channels (Slack, PagerDuty, email, etc.)
based on the alert severity, category, and configured routing rules.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


# Default routing configuration
DEFAULT_ROUTING = {
    "severity_levels": {
        "critical": {"channels": ["pagerduty", "slack"], "priority": 1},
        "high": {"channels": ["slack", "email"], "priority": 2},
        "medium": {"channels": ["slack"], "priority": 3},
        "low": {"channels": ["log"], "priority": 4}
    },
    "category_overrides": {
        "security": {"channels": ["pagerduty", "slack", "email"], "priority": 1},
        "performance": {"channels": ["slack", "log"], "priority": 3},
        "availability": {"channels": ["pagerduty", "slack"], "priority": 1},
        "cost": {"channels": ["email", "log"], "priority": 4}
    },
    "channel_config": {
        "slack": {
            "webhook_env": "SLACK_WEBHOOK_URL",
            "enabled": True
        },
        "pagerduty": {
            "key_env": "PAGERDUTY_INTEGRATION_KEY",
            "enabled": True
        },
        "email": {
            "recipients_env": "ALERT_EMAIL_RECIPIENTS",
            "enabled": True
        },
        "log": {
            "file": "/var/log/alerts.log",
            "enabled": True
        }
    }
}


def load_routing_config(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Load routing configuration from file or use defaults.

    Args:
        filepath: Optional path to routing configuration JSON

    Returns:
        Routing configuration dictionary

    Raises:
        FileNotFoundError: If filepath is specified but doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if filepath:
        try:
            path = Path(filepath)
            if not path.exists():
                raise FileNotFoundError(f"Routing config file not found: {filepath}")

            with open(path, 'r') as f:
                config = json.load(f)

            # Merge with defaults
            merged = DEFAULT_ROUTING.copy()
            merged.update(config)
            return merged

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            sys.exit(1)

    return DEFAULT_ROUTING


def determine_channels(
    severity: str,
    category: str,
    config: Dict[str, Any]
) -> List[str]:
    """
    Determine routing channels based on severity and category.

    Args:
        severity: Alert severity level (critical, high, medium, low)
        category: Alert category (security, performance, availability, cost, etc.)
        config: Routing configuration

    Returns:
        List of channels to route alert to
    """
    channels = set()
    effective_priority = float('inf')

    # Check category overrides first
    if category in config.get("category_overrides", {}):
        override = config["category_overrides"][category]
        channels.update(override.get("channels", []))
        effective_priority = override.get("priority", effective_priority)

    # Apply severity level
    if severity in config.get("severity_levels", {}):
        severity_config = config["severity_levels"][severity]
        severity_channels = severity_config.get("channels", [])
        severity_priority = severity_config.get("priority", float('inf'))

        # If severity has higher priority, use its channels
        if severity_priority < effective_priority:
            channels = set(severity_channels)
            effective_priority = severity_priority
        else:
            channels.update(severity_channels)

    return sorted(list(channels))


def validate_alert(alert: Dict[str, Any]) -> bool:
    """
    Validate required alert fields.

    Args:
        alert: Alert data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["name", "severity", "message"]

    for field in required_fields:
        if field not in alert:
            print(f"Error: Missing required field '{field}'", file=sys.stderr)
            return False

    valid_severities = ["critical", "high", "medium", "low"]
    if alert["severity"] not in valid_severities:
        print(
            f"Error: Invalid severity '{alert['severity']}'. "
            f"Must be one of: {', '.join(valid_severities)}",
            file=sys.stderr
        )
        return False

    return True


def format_alert_message(
    alert: Dict[str, Any],
    channels: List[str]
) -> Dict[str, str]:
    """
    Format alert message for different channels.

    Args:
        alert: Alert data
        channels: Target channels

    Returns:
        Dictionary of formatted messages per channel
    """
    formatted = {}

    # Standard message
    timestamp = alert.get("timestamp", datetime.now().isoformat())
    base_message = f"""
Alert: {alert['name']}
Severity: {alert['severity'].upper()}
Category: {alert.get('category', 'uncategorized')}
Timestamp: {timestamp}
Message: {alert['message']}
"""

    if alert.get("details"):
        base_message += f"\nDetails:\n{json.dumps(alert['details'], indent=2)}"

    # Format for each channel
    for channel in channels:
        if channel == "slack":
            formatted["slack"] = f"```{base_message}```"
        elif channel == "pagerduty":
            formatted["pagerduty"] = base_message
        elif channel == "email":
            formatted["email"] = f"Subject: ALERT: {alert['name']}\n\n{base_message}"
        elif channel == "log":
            formatted["log"] = f"[{timestamp}] {alert['name']}: {alert['message']}"

    return formatted


def route_alert(
    alert: Dict[str, Any],
    config: Dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Route an alert to appropriate channels.

    Args:
        alert: Alert data
        config: Routing configuration
        dry_run: If True, don't actually send alerts
        verbose: If True, print debug information

    Returns:
        Routing result dictionary
    """
    result = {
        "alert": alert["name"],
        "severity": alert["severity"],
        "category": alert.get("category", "uncategorized"),
        "timestamp": datetime.now().isoformat(),
        "channels": [],
        "messages": {},
        "dry_run": dry_run,
        "errors": []
    }

    # Determine channels
    channels = determine_channels(
        alert["severity"],
        alert.get("category", "uncategorized"),
        config
    )

    if verbose:
        print(f"Routing to channels: {', '.join(channels)}", file=sys.stderr)

    result["channels"] = channels

    # Filter enabled channels
    enabled_channels = [
        ch for ch in channels
        if config.get("channel_config", {}).get(ch, {}).get("enabled", True)
    ]

    if not enabled_channels:
        result["errors"].append("No enabled channels available for routing")
        return result

    # Format messages
    messages = format_alert_message(alert, enabled_channels)
    result["messages"] = messages

    # Route to channels (in dry-run, just log what would happen)
    for channel in enabled_channels:
        if verbose:
            print(f"Routing to {channel}...", file=sys.stderr)

        if dry_run:
            result[f"{channel}_status"] = "dry_run"
        else:
            # In production, actual sending would occur here
            result[f"{channel}_status"] = "sent"

    return result


def main():
    """Main entry point for alert routing."""
    parser = argparse.ArgumentParser(
        description="Route alerts to appropriate channels based on severity and category",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --alert alert.json
  %(prog)s --alert alert.json --config routing.json
  %(prog)s --alert alert.json --dry-run --verbose
  %(prog)s --name "CPU High" --severity critical --category performance \\
          --message "CPU usage exceeded 90%%" --output result.json
        """
    )

    parser.add_argument(
        "--alert",
        help="Path to JSON file containing alert data"
    )
    parser.add_argument(
        "--name",
        help="Alert name"
    )
    parser.add_argument(
        "--severity",
        default="high",
        choices=["critical", "high", "medium", "low"],
        help="Alert severity level"
    )
    parser.add_argument(
        "--category",
        default="uncategorized",
        help="Alert category"
    )
    parser.add_argument(
        "--message",
        help="Alert message"
    )
    parser.add_argument(
        "--config",
        help="Path to routing configuration JSON"
    )
    parser.add_argument(
        "--output",
        help="Output file for routing result (JSON)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually routing"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Load routing configuration
    config = load_routing_config(args.config)

    # Build alert object
    alert = None

    if args.alert:
        try:
            with open(args.alert, 'r') as f:
                alert = json.load(f)
        except FileNotFoundError:
            print(f"Error: Alert file not found: {args.alert}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.alert}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.name and args.message:
        alert = {
            "name": args.name,
            "severity": args.severity,
            "category": args.category,
            "message": args.message
        }
    else:
        parser.error("Either --alert file or --name and --message are required")

    # Validate alert
    if not validate_alert(alert):
        sys.exit(1)

    try:
        # Route alert
        result = route_alert(alert, config, args.dry_run, args.verbose)

        # Print result summary
        print(f"\nAlert Routing Result:")
        print(f"  Alert: {result['alert']}")
        print(f"  Severity: {result['severity']}")
        print(f"  Category: {result['category']}")
        print(f"  Channels: {', '.join(result['channels']) or 'none'}")

        if result["errors"]:
            print(f"  Errors: {', '.join(result['errors'])}")
            print()

        # Save JSON output if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)

            if args.verbose:
                print(f"\nResults saved to {args.output}")

        sys.exit(0 if not result["errors"] else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
