#!/usr/bin/env python3
"""Extract repeated tool execution errors from session files.

Cross-platform compatible (Windows, macOS, Linux).

Usage:
    python extract_tool_errors.py <session-file> [session-file...]
    python extract_tool_errors.py --project <project-dir>
    python extract_tool_errors.py --all

Options:
    --min-count N       Minimum occurrences to report (default: 2)
    --include-all       Include all errors, not just project-specific patterns
    --project DIR       Scan all sessions for a specific project directory
    --all               Scan all sessions across all projects
    --json              Output as JSON instead of human-readable format
"""
import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.reflect_utils import (
    extract_tool_errors,
    aggregate_tool_errors,
    get_claude_dir,
    get_project_folder_name,
)


def find_session_files(project_dir: str = None, all_projects: bool = False) -> list:
    """Find session files to scan."""
    claude_dir = get_claude_dir()
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        return []

    if all_projects:
        # Scan all project directories
        session_files = list(projects_dir.glob("*/*.jsonl"))
    elif project_dir:
        # Find the project folder matching the directory
        folder_name = get_project_folder_name(project_dir)

        project_folder = projects_dir / folder_name
        if project_folder.exists():
            session_files = list(project_folder.glob("*.jsonl"))
        else:
            # Try partial match
            session_files = []
            for d in projects_dir.iterdir():
                if d.is_dir() and project_dir.split("/")[-1] in d.name:
                    session_files.extend(d.glob("*.jsonl"))
    else:
        session_files = []

    return sorted(session_files, key=lambda p: p.stat().st_mtime, reverse=True)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract repeated tool execution errors from session files"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Session file(s) to scan"
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="Minimum occurrences to report (default: 2)"
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all errors, not just project-specific patterns"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Scan all sessions for a specific project directory"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_projects",
        help="Scan all sessions across all projects"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Determine which session files to scan
    if args.files:
        session_files = [Path(f) for f in args.files]
    elif args.project or args.all_projects:
        session_files = find_session_files(args.project, args.all_projects)
    else:
        parser.print_help()
        return 1

    if not session_files:
        print("No session files found.", file=sys.stderr)
        return 1

    # Extract errors from all session files
    all_errors = []
    for session_file in session_files:
        if not session_file.exists():
            print(f"Warning: Session file not found: {session_file}", file=sys.stderr)
            continue

        errors = extract_tool_errors(
            session_file,
            project_specific_only=not args.include_all
        )
        all_errors.extend(errors)

    if not all_errors:
        if args.json:
            print("[]")
        else:
            print("No tool errors found matching project-specific patterns.")
        return 0

    # Aggregate by error type
    aggregated = aggregate_tool_errors(all_errors, min_occurrences=args.min_count)

    if not aggregated:
        if args.json:
            print("[]")
        else:
            print(f"No error patterns found with {args.min_count}+ occurrences.")
        return 0

    # Output results
    if args.json:
        import json
        print(json.dumps(aggregated, indent=2))
    else:
        print(f"=== Tool Execution Error Patterns (min {args.min_count} occurrences) ===\n")
        print(f"Scanned {len(session_files)} session file(s), found {len(all_errors)} matching errors\n")

        for agg in aggregated:
            print(f"[{agg['error_type']}] - {agg['count']} occurrences (confidence: {agg['confidence']:.2f})")
            if agg['suggested_guideline']:
                print(f"  Suggested guideline: {agg['suggested_guideline']}")
            print(f"  Sample error:")
            if agg['sample_errors']:
                print(f"    {agg['sample_errors'][0][:100]}...")
            print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
