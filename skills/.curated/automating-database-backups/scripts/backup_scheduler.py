#!/usr/bin/env python3
"""
Backup Scheduler

Creates and manages cron job entries for automated database backups.
Supports standard cron syntax and common schedule presets.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class CronEntry:
    """Cron job entry."""

    schedule: str
    command: str
    user: Optional[str]
    comment: str
    log_file: Optional[str]


# Common schedule presets
SCHEDULE_PRESETS = {
    "hourly": "0 * * * *",
    "daily": "0 2 * * *",
    "daily-midnight": "0 0 * * *",
    "twice-daily": "0 2,14 * * *",
    "every-6-hours": "0 */6 * * *",
    "every-4-hours": "0 */4 * * *",
    "weekly": "0 2 * * 0",
    "weekly-saturday": "0 2 * * 6",
    "monthly": "0 2 1 * *",
    "quarterly": "0 2 1 1,4,7,10 *",
}


def validate_cron_expression(expression: str) -> bool:
    """Validate cron expression format."""
    parts = expression.split()
    if len(parts) != 5:
        return False

    # Basic validation of each field
    ranges = [
        (0, 59),  # minute
        (0, 23),  # hour
        (1, 31),  # day of month
        (1, 12),  # month
        (0, 6),  # day of week
    ]

    for part, (min_val, max_val) in zip(parts, ranges):
        if part == "*":
            continue
        if "/" in part:
            base, step = part.split("/")
            if base != "*" and not base.replace("-", "").replace(",", "").isdigit():
                return False
            if not step.isdigit():
                return False
        elif "-" in part:
            start, end = part.split("-")
            if not (start.isdigit() and end.isdigit()):
                return False
        elif "," in part:
            for val in part.split(","):
                if not val.isdigit():
                    return False
        elif not part.isdigit():
            return False

    return True


def format_cron_line(entry: CronEntry) -> str:
    """Format a cron entry as a crontab line."""
    command = entry.command

    # Add logging if specified
    if entry.log_file:
        command = f"{command} >> {entry.log_file} 2>&1"

    # Format with optional comment
    lines = []
    if entry.comment:
        lines.append(f"# {entry.comment}")
    lines.append(f"{entry.schedule} {command}")

    return "\n".join(lines)


def get_current_crontab(user: Optional[str] = None) -> str:
    """Get current crontab contents."""
    cmd = ["crontab", "-l"]
    if user:
        cmd.extend(["-u", user])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        return ""
    except Exception:
        return ""


def install_cron_entry(entry: CronEntry, dry_run: bool = False) -> bool:
    """Install a cron entry."""
    current = get_current_crontab(entry.user)
    new_line = format_cron_line(entry)

    # Check if entry already exists
    if entry.command in current:
        print(f"Cron entry already exists for: {entry.command}")
        return True

    # Append new entry
    new_crontab = current.rstrip() + "\n\n" + new_line + "\n"

    if dry_run:
        print("DRY RUN - Would install crontab entry:")
        print("-" * 40)
        print(new_line)
        print("-" * 40)
        return True

    # Install new crontab
    cmd = ["crontab", "-"]
    if entry.user:
        cmd = ["sudo", "crontab", "-u", entry.user, "-"]

    try:
        result = subprocess.run(cmd, input=new_crontab, capture_output=True, text=True)
        if result.returncode == 0:
            print("Cron entry installed successfully")
            return True
        else:
            print(f"Failed to install cron entry: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error installing cron entry: {e}")
        return False


def list_cron_entries(user: Optional[str] = None) -> None:
    """List current cron entries."""
    current = get_current_crontab(user)
    if current:
        print(f"Current crontab{' for ' + user if user else ''}:")
        print("-" * 40)
        print(current)
    else:
        print("No crontab entries found")


def remove_cron_entry(pattern: str, user: Optional[str] = None, dry_run: bool = False) -> bool:
    """Remove cron entries matching pattern."""
    current = get_current_crontab(user)
    if not current:
        print("No crontab entries found")
        return True

    lines = current.split("\n")
    new_lines = []
    removed = []

    for i, line in enumerate(lines):
        if pattern in line:
            removed.append(line)
            # Also remove preceding comment
            if i > 0 and new_lines and new_lines[-1].startswith("#"):
                removed.insert(0, new_lines.pop())
        else:
            new_lines.append(line)

    if not removed:
        print(f"No entries matching '{pattern}' found")
        return True

    if dry_run:
        print("DRY RUN - Would remove:")
        for line in removed:
            print(f"  {line}")
        return True

    new_crontab = "\n".join(new_lines)
    cmd = ["crontab", "-"]
    if user:
        cmd = ["sudo", "crontab", "-u", user, "-"]

    try:
        result = subprocess.run(cmd, input=new_crontab, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Removed {len(removed)} cron entries")
            return True
        else:
            print(f"Failed to update crontab: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error updating crontab: {e}")
        return False


def generate_crontab_file(entries: list, output_file: str) -> None:
    """Generate a crontab file with multiple entries."""
    header = """# Database Backup Schedule
# Generated by backup_scheduler.py
# Install with: crontab {output_file}

SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=""

"""
    content = header.format(output_file=output_file)
    for entry in entries:
        content += format_cron_line(entry) + "\n\n"

    Path(output_file).write_text(content)
    print(f"Crontab file generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Create and manage cron jobs for database backups")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # Install subcommand
    install_parser = subparsers.add_parser("install", help="Install cron entry")
    install_parser.add_argument("--script", "-s", required=True, help="Backup script path")
    install_parser.add_argument(
        "--schedule", required=True, help="Cron schedule (expression or preset: hourly, daily, weekly, monthly)"
    )
    install_parser.add_argument("--user", "-u", help="Run as user")
    install_parser.add_argument("--comment", "-c", help="Comment for cron entry")
    install_parser.add_argument("--log", "-l", help="Log file path")
    install_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List cron entries")
    list_parser.add_argument("--user", "-u", help="User crontab to list")

    # Remove subcommand
    remove_parser = subparsers.add_parser("remove", help="Remove cron entry")
    remove_parser.add_argument("--pattern", "-p", required=True, help="Pattern to match")
    remove_parser.add_argument("--user", "-u", help="User crontab to modify")
    remove_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Generate crontab file")
    gen_parser.add_argument("--output", "-o", required=True, help="Output file")
    gen_parser.add_argument("--scripts", "-s", nargs="+", required=True, help="Backup scripts to schedule")
    gen_parser.add_argument("--schedule", default="daily", help="Schedule for all scripts (default: daily)")

    # Presets subcommand
    subparsers.add_parser("presets", help="Show schedule presets")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        return 1

    if args.action == "presets":
        print("Available schedule presets:")
        print("-" * 40)
        for name, expr in SCHEDULE_PRESETS.items():
            print(f"  {name:20} {expr}")
        return 0

    if args.action == "list":
        list_cron_entries(args.user)
        return 0

    if args.action == "remove":
        success = remove_cron_entry(args.pattern, args.user, args.dry_run)
        return 0 if success else 1

    if args.action == "install":
        # Resolve schedule
        schedule = SCHEDULE_PRESETS.get(args.schedule, args.schedule)
        if not validate_cron_expression(schedule):
            print(f"Invalid cron expression: {schedule}")
            print("Use 5-field format: minute hour day month weekday")
            print("Or a preset: " + ", ".join(SCHEDULE_PRESETS.keys()))
            return 1

        # Verify script exists
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"Script not found: {script_path}")
            return 1

        entry = CronEntry(
            schedule=schedule,
            command=str(script_path.absolute()),
            user=args.user,
            comment=args.comment or f"Backup: {script_path.name}",
            log_file=args.log,
        )

        success = install_cron_entry(entry, args.dry_run)
        return 0 if success else 1

    if args.action == "generate":
        schedule = SCHEDULE_PRESETS.get(args.schedule, args.schedule)
        if not validate_cron_expression(schedule):
            print(f"Invalid cron expression: {schedule}")
            return 1

        entries = []
        for script in args.scripts:
            script_path = Path(script)
            entries.append(
                CronEntry(
                    schedule=schedule,
                    command=str(script_path.absolute()),
                    user=None,
                    comment=f"Backup: {script_path.name}",
                    log_file=None,
                )
            )

        generate_crontab_file(entries, args.output)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
