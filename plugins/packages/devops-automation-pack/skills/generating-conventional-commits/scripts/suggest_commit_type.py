#!/usr/bin/env python3
"""
Suggest the appropriate commit type based on code changes.

This script analyzes code changes and suggests the most appropriate
commit type from the conventional commits specification (feat, fix,
docs, style, refactor, perf, test, chore, ci, build, revert).
"""

import argparse
import sys
import subprocess
import json
from typing import Tuple, Dict, List, Optional


def get_git_diff(staged_only: bool = False, ref: Optional[str] = None) -> str:
    """
    Get git diff content.

    Args:
        staged_only: If True, get staged changes only
        ref: Optional reference to compare against (e.g., 'main', 'HEAD~1')

    Returns:
        The git diff output
    """
    try:
        cmd = ['git', 'diff']
        if staged_only:
            cmd.append('--cached')
        if ref:
            cmd.append(ref)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        return result.stdout if result.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def get_diff_from_file(filepath: str) -> str:
    """Read diff from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_changes(diff_content: str) -> Dict[str, int]:
    """
    Count different types of changes in the diff.

    Args:
        diff_content: The git diff content

    Returns:
        Dictionary of change type counts
    """
    counts = {
        'test_additions': 0,
        'test_removals': 0,
        'doc_changes': 0,
        'style_changes': 0,
        'feature_additions': 0,
        'feature_removals': 0,
        'performance_changes': 0,
        'bug_references': 0,
        'refactor_changes': 0,
        'ci_changes': 0,
        'dependency_changes': 0,
        'total_additions': 0,
        'total_removals': 0,
    }

    lines = diff_content.split('\n')
    current_file = ''

    for i, line in enumerate(lines):
        # Track current file
        if line.startswith('diff --git'):
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file = parts[3]

        # Count additions and removals
        if line.startswith('+') and not line.startswith('+++'):
            counts['total_additions'] += 1

            # Analyze added lines
            content = line[1:]
            if 'test' in current_file.lower() or 'spec' in current_file.lower():
                counts['test_additions'] += 1
            elif 'package.json' in current_file or 'requirements.txt' in current_file:
                counts['dependency_changes'] += 1
            elif any(x in content.lower() for x in ['def ', 'class ', 'function ', 'const ', 'async ']):
                counts['feature_additions'] += 1
            elif any(x in content.lower() for x in ['optimize', 'performance', 'cache', 'lazy']):
                counts['performance_changes'] += 1

        elif line.startswith('-') and not line.startswith('---'):
            counts['total_removals'] += 1

            content = line[1:]
            if 'test' in current_file.lower() or 'spec' in current_file.lower():
                counts['test_removals'] += 1
            elif any(x in content.lower() for x in ['def ', 'class ', 'function ', 'const ']):
                counts['feature_removals'] += 1

        # Detect specific change patterns
        if any(x in line.lower() for x in ['.md', 'readme', 'docs/', 'documentation']):
            counts['doc_changes'] += 1

        # Style changes (mostly whitespace/formatting)
        if line.startswith('+') or line.startswith('-'):
            if len(line.lstrip('+-').strip()) < 10:  # Short lines
                counts['style_changes'] += 1

        # Bug/fix references
        if any(x in line.lower() for x in ['fix', 'bug', 'issue', 'closes #', 'fixes #']):
            counts['bug_references'] += 1

        # CI/CD changes
        if '.github/workflows' in current_file or '.gitlab-ci' in current_file or 'Jenkinsfile' in current_file:
            counts['ci_changes'] += 1
            if 'pipeline' in line.lower() or 'workflow' in line.lower():
                counts['ci_changes'] += 1

        # Refactoring (renaming, restructuring without functional change)
        if any(x in line.lower() for x in ['rename', 'reorganize', 'refactor', 'restructure']):
            counts['refactor_changes'] += 1

    return counts


def suggest_commit_type(diff_content: str) -> Tuple[str, float, str]:
    """
    Suggest the most appropriate commit type.

    Args:
        diff_content: The git diff content

    Returns:
        Tuple of (suggested_type, confidence, reasoning)
    """
    changes = analyze_changes(diff_content)

    # Scoring system: higher score = more confident
    scores = {
        'feat': 0.0,
        'fix': 0.0,
        'docs': 0.0,
        'style': 0.0,
        'refactor': 0.0,
        'perf': 0.0,
        'test': 0.0,
        'chore': 0.0,
        'ci': 0.0,
        'build': 0.0,
    }

    reasoning = []

    # Test changes
    if changes['test_additions'] > 0:
        scores['test'] += changes['test_additions'] * 2
        reasoning.append(f"Added {changes['test_additions']} test lines")

    # Documentation changes
    if changes['doc_changes'] > 0:
        scores['docs'] += changes['doc_changes'] * 1.5
        reasoning.append(f"Modified {changes['doc_changes']} documentation lines")

    # Bug fixes
    if changes['bug_references'] > 0:
        scores['fix'] += changes['bug_references'] * 3
        reasoning.append(f"Found {changes['bug_references']} bug/fix references")

    # Performance improvements
    if changes['performance_changes'] > 0:
        scores['perf'] += changes['performance_changes'] * 2
        reasoning.append(f"Found {changes['performance_changes']} performance improvements")

    # CI/CD changes
    if changes['ci_changes'] > 0:
        scores['ci'] += changes['ci_changes'] * 2
        reasoning.append(f"Modified CI/CD files ({changes['ci_changes']} lines)")

    # Dependency changes
    if changes['dependency_changes'] > 0:
        scores['build'] += changes['dependency_changes'] * 1.5
        reasoning.append(f"Modified dependencies ({changes['dependency_changes']} changes)")

    # Feature additions
    if changes['feature_additions'] > changes['feature_removals']:
        feature_ratio = changes['feature_additions'] / max(1, changes['feature_removals'])
        scores['feat'] += feature_ratio * 2
        reasoning.append(f"Added {changes['feature_additions']} feature lines")

    # Refactoring
    if changes['refactor_changes'] > 0:
        scores['refactor'] += changes['refactor_changes'] * 1.5
        reasoning.append(f"Found {changes['refactor_changes']} refactoring indicators")

    # Style changes
    if changes['style_changes'] > changes['total_additions'] * 0.3:
        scores['style'] += changes['style_changes']
        reasoning.append(f"Mostly style changes ({changes['style_changes']} lines)")

    # Fallback: determine based on change volume
    total_changes = changes['total_additions'] + changes['total_removals']
    if total_changes == 0:
        return 'chore', 0.5, "No meaningful changes detected"

    # If nothing scored highly, use refactor as catch-all
    if max(scores.values()) == 0:
        scores['refactor'] = 1.0
        reasoning.append("General code changes without specific category")

    # Find the highest scoring type
    suggested = max(scores, key=scores.get)
    confidence = scores[suggested] / max(1, total_changes)
    confidence = min(1.0, confidence)  # Cap at 1.0

    reasoning_str = " | ".join(reasoning) if reasoning else "General code changes"

    return suggested, confidence, reasoning_str


def format_output(
    suggested_type: str,
    confidence: float,
    reasoning: str,
    format_type: str = 'text'
) -> str:
    """Format the output based on requested format."""
    if format_type == 'json':
        return json.dumps({
            'type': suggested_type,
            'confidence': round(confidence, 2),
            'confidence_percent': f"{confidence * 100:.1f}%",
            'reasoning': reasoning
        }, indent=2)
    else:
        confidence_percent = f"{confidence * 100:.1f}%"
        return (
            f"Suggested commit type: {suggested_type}\n"
            f"Confidence: {confidence_percent}\n"
            f"Reasoning: {reasoning}"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Suggest the appropriate commit type based on code changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Suggest type from staged changes
  %(prog)s --staged

  # Suggest type from unstaged changes
  %(prog)s --unstaged

  # Suggest type from a diff file
  %(prog)s --file changes.diff

  # Compare against a specific branch
  %(prog)s --ref main

  # Output as JSON
  %(prog)s --staged --format json

  # Verbose output with detailed analysis
  %(prog)s --staged --verbose
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
        help='Path to diff file to analyze'
    )

    parser.add_argument(
        '--ref',
        type=str,
        help='Git reference to compare against (e.g., main, HEAD~1)'
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
        help='Enable verbose output with detailed analysis'
    )

    args = parser.parse_args()

    # Get diff content
    if args.file:
        diff_content = get_diff_from_file(args.file)
    elif args.unstaged:
        diff_content = get_git_diff(staged_only=False, ref=args.ref)
    else:  # Default to staged
        diff_content = get_git_diff(staged_only=True, ref=args.ref)

    if not diff_content:
        print("Error: No changes to analyze", file=sys.stderr)
        return 1

    # Suggest commit type
    suggested_type, confidence, reasoning = suggest_commit_type(diff_content)

    # Output result
    output = format_output(suggested_type, confidence, reasoning, args.format)
    print(output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
