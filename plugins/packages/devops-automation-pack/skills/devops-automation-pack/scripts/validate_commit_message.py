#!/usr/bin/env python3
"""
Validate commit messages against the Conventional Commits specification.

This script validates that commit messages follow the conventional commits
standard, which includes type(scope): subject format with proper structure.

The conventional commits specification defines:
- type: feat, fix, docs, style, refactor, perf, test, chore, ci, etc.
- scope: optional area of the codebase
- subject: brief description of the change
"""

import argparse
import sys
import re
from typing import Tuple


def validate_conventional_commit(message: str) -> Tuple[bool, str]:
    """
    Validate a commit message against conventional commits specification.

    Args:
        message: The commit message to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if message is valid, False otherwise
        - error_message: Description of validation error (empty if valid)
    """
    if not message or not message.strip():
        return False, "Commit message cannot be empty"

    message = message.strip()
    lines = message.split('\n')
    subject = lines[0]

    # Validate subject line format
    # Pattern: type(scope)?: subject or type: subject
    # Where type is required, scope is optional, and subject is required
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?!?: .{1,}$'

    if not re.match(pattern, subject):
        return False, (
            f"Invalid commit message format: '{subject}'\n"
            "Expected format: type(scope): subject\n"
            "Valid types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert\n"
            "Example: feat(auth): add login functionality"
        )

    # Validate subject line length (recommended max 50 chars)
    if len(subject) > 72:
        return False, (
            f"Subject line too long ({len(subject)} chars). "
            "Recommended maximum is 50 characters, hard limit is 72"
        )

    # Validate subject doesn't end with period
    if subject.endswith('.'):
        return False, "Subject line should not end with a period"

    # If there are multiple lines, validate blank line after subject
    if len(lines) > 1:
        if lines[1].strip() != '':
            return False, "Expected blank line between subject and body"

    return True, ""


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate commit messages against the Conventional Commits specification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a commit message from a file
  %(prog)s --file commit-msg.txt

  # Validate a commit message from command line
  %(prog)s --message "feat(api): add new endpoint"

  # Validate with verbose output
  %(prog)s --message "fix: resolve bug" --verbose
        """
    )

    # Create mutually exclusive group for input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-m', '--message',
        type=str,
        help='Commit message to validate'
    )
    input_group.add_argument(
        '-f', '--file',
        type=str,
        help='Path to file containing commit message'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Get the commit message
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                message = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 1
    else:
        message = args.message

    # Validate the message
    is_valid, error_msg = validate_conventional_commit(message)

    if is_valid:
        if args.verbose:
            print("✓ Commit message is valid")
        return 0
    else:
        print(f"✗ Validation failed:", file=sys.stderr)
        print(error_msg, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
