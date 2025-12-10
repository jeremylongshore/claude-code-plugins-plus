#!/usr/bin/env python3
"""
Generate conventional commit messages based on code diffs.

This script analyzes git diffs and generates appropriate commit messages
following the conventional commits specification. It examines the types
of changes made and suggests an appropriate message format.
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path
from typing import Tuple, Optional


def get_git_diff(staged_only: bool = False) -> str:
    """
    Get the current git diff.

    Args:
        staged_only: If True, get only staged changes. Otherwise get unstaged.

    Returns:
        The git diff output as a string
    """
    try:
        cmd = ['git', 'diff']
        if staged_only:
            cmd.append('--cached')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return ""

        return result.stdout
    except FileNotFoundError:
        return ""


def get_diff_from_file(filepath: str) -> str:
    """
    Read diff from a file.

    Args:
        filepath: Path to the diff file

    Returns:
        The diff content as a string
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_diff(diff_content: str) -> Tuple[str, str, str]:
    """
    Analyze diff content to suggest commit type and scope.

    Args:
        diff_content: The git diff content

    Returns:
        Tuple of (commit_type, scope, description)
    """
    # Initialize counters for different change types
    has_tests = False
    has_docs = False
    has_style = False
    has_feature = False
    has_fix = False
    files_changed = []

    lines = diff_content.split('\n')

    for line in lines:
        # Track which files are being modified
        if line.startswith('diff --git'):
            # Extract filename
            parts = line.split(' ')
            if len(parts) >= 4:
                filepath = parts[3]
                files_changed.append(filepath)

        # Detect test files
        if 'test' in line.lower() or 'spec' in line.lower():
            has_tests = True

        # Detect documentation changes
        if any(x in line.lower() for x in ['.md', 'readme', 'docs/', 'documentation']):
            has_docs = True

        # Detect style changes (formatting, whitespace)
        if line.startswith('-') and line.lstrip('-').strip():
            if len(line.lstrip('-').strip()) < 20:  # Short lines likely style
                has_style = True

        # Detect feature additions (new functions, classes)
        if any(x in line for x in ['def ', 'class ', 'function ', 'const ', 'let ']):
            if line.startswith('+'):
                has_feature = True

        # Detect bug fixes (removing problematic code)
        if 'bug' in line.lower() or 'fix' in line.lower():
            has_fix = True

    # Determine commit type
    if has_fix:
        commit_type = 'fix'
    elif has_feature:
        commit_type = 'feat'
    elif has_tests:
        commit_type = 'test'
    elif has_docs:
        commit_type = 'docs'
    elif has_style:
        commit_type = 'style'
    else:
        commit_type = 'refactor'

    # Determine scope from files changed
    scope = ''
    if files_changed:
        # Extract directory or module name from first file
        first_file = files_changed[0]
        parts = Path(first_file).parts
        if len(parts) > 1:
            scope = parts[0]

    # Create description
    description = f"Update code based on diff analysis"

    return commit_type, scope, description


def generate_message(
    commit_type: str,
    scope: Optional[str],
    subject: str,
    body: Optional[str] = None,
    footer: Optional[str] = None
) -> str:
    """
    Generate a conventional commit message.

    Args:
        commit_type: Type of commit (feat, fix, docs, etc.)
        scope: Optional scope of the change
        subject: Brief description of the change
        body: Optional detailed body
        footer: Optional footer (e.g., Closes #123)

    Returns:
        Formatted conventional commit message
    """
    # Build the subject line
    if scope:
        subject_line = f"{commit_type}({scope}): {subject}"
    else:
        subject_line = f"{commit_type}: {subject}"

    # Ensure subject starts with lowercase
    parts = subject_line.split(': ', 1)
    if len(parts) == 2:
        subject_line = f"{parts[0]}: {parts[1][0].lower()}{parts[1][1:] if len(parts[1]) > 1 else ''}"

    # Build full message
    message = subject_line

    if body:
        message += f"\n\n{body}"

    if footer:
        message += f"\n\n{footer}"

    return message


def main():
    """Main entry point for the commit message generation script."""
    parser = argparse.ArgumentParser(
        description="Generate conventional commit messages based on code diffs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from staged changes
  %(prog)s --staged

  # Generate from unstaged changes
  %(prog)s --unstaged

  # Generate from a diff file
  %(prog)s --file changes.diff

  # Generate with custom subject
  %(prog)s --staged --subject "implement new authentication"

  # Output as JSON
  %(prog)s --staged --format json
        """
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '--staged',
        action='store_true',
        help='Analyze staged changes (default)'
    )
    input_group.add_argument(
        '--unstaged',
        action='store_true',
        help='Analyze unstaged changes'
    )
    input_group.add_argument(
        '--file',
        type=str,
        help='Path to diff file'
    )

    parser.add_argument(
        '--subject',
        type=str,
        help='Custom subject for the commit message'
    )
    parser.add_argument(
        '--body',
        type=str,
        help='Optional body text'
    )
    parser.add_argument(
        '--footer',
        type=str,
        help='Optional footer (e.g., Closes #123)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Get diff content
    if args.file:
        diff_content = get_diff_from_file(args.file)
    elif args.unstaged:
        diff_content = get_git_diff(staged_only=False)
    else:  # Default to staged
        diff_content = get_git_diff(staged_only=True)

    if not diff_content:
        print("Error: No changes to analyze", file=sys.stderr)
        return 1

    # Analyze the diff
    commit_type, scope, _ = analyze_diff(diff_content)

    # Use custom subject if provided
    subject = args.subject or "update code"

    # Generate message
    message = generate_message(
        commit_type,
        scope if scope else None,
        subject,
        args.body,
        args.footer
    )

    # Output result
    if args.format == 'json':
        output = {
            'type': commit_type,
            'scope': scope or None,
            'subject': subject,
            'body': args.body,
            'footer': args.footer,
            'message': message
        }
        print(json.dumps(output, indent=2))
    else:
        print(message)

    return 0


if __name__ == '__main__':
    sys.exit(main())
