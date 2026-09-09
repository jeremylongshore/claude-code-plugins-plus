#!/usr/bin/env python3
"""Compare regex vs semantic detection on real session data.

This script runs both regex and semantic detection on user messages from
Claude Code session files and generates a comparison report.

Usage:
    python scripts/compare_detection.py [session_files...]
    python scripts/compare_detection.py ~/.claude/projects/*/session*.jsonl
    python scripts/compare_detection.py --project .  # Current project sessions

Options:
    --project PATH   Find session files for a specific project
    --limit N        Limit to N messages (default: 100)
    --no-semantic    Skip semantic analysis (regex only)
    --verbose        Show all messages, not just differences
    --output FILE    Write report to file instead of stdout
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.reflect_utils import detect_patterns, extract_user_messages
from lib.semantic_detector import semantic_analyze

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        cls.GREEN = cls.RED = cls.YELLOW = cls.BLUE = cls.BOLD = cls.END = ''


def find_project_sessions(project_path: str) -> List[Path]:
    """Find session files for a project."""
    project_path = os.path.abspath(project_path)
    project_name = os.path.basename(project_path)

    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return []

    # Try to find matching project folder
    for folder in claude_projects.iterdir():
        if project_name.lower() in folder.name.lower():
            return list(folder.glob("*.jsonl"))

    # Try with hyphens instead of underscores
    project_name_hyphen = project_name.replace('_', '-')
    for folder in claude_projects.iterdir():
        if project_name_hyphen.lower() in folder.name.lower():
            return list(folder.glob("*.jsonl"))

    return []


def analyze_message(text: str, use_semantic: bool = True) -> Dict[str, Any]:
    """Analyze a message with both regex and optionally semantic detection."""
    result = {
        "text": text,
        "regex": None,
        "semantic": None,
    }

    # Regex detection
    item_type, patterns, confidence, sentiment, decay = detect_patterns(text)
    if item_type:
        result["regex"] = {
            "is_learning": True,
            "type": item_type,
            "patterns": patterns,
            "confidence": confidence,
            "sentiment": sentiment,
        }
    else:
        result["regex"] = {
            "is_learning": False,
            "type": None,
            "patterns": "",
            "confidence": 0.0,
        }

    # Semantic detection (if enabled)
    if use_semantic:
        sem_result = semantic_analyze(text)
        if sem_result:
            result["semantic"] = sem_result
        else:
            result["semantic"] = {"error": "Analysis failed or unavailable"}

    return result


def compare_results(results: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Compare regex vs semantic results and categorize."""
    categories = {
        "both_learning": [],      # Both agree it's a learning
        "both_not_learning": [],  # Both agree it's not a learning
        "regex_only": [],         # Regex says learning, semantic disagrees
        "semantic_only": [],      # Semantic says learning, regex missed
        "confidence_diff": [],    # Both agree but different confidence
        "semantic_error": [],     # Semantic analysis failed
    }

    for r in results:
        text = r["text"]
        regex = r["regex"]
        semantic = r["semantic"]

        if semantic is None or "error" in semantic:
            categories["semantic_error"].append(r)
            continue

        regex_is_learning = regex.get("is_learning", False)
        semantic_is_learning = semantic.get("is_learning", False)

        if regex_is_learning and semantic_is_learning:
            # Check confidence difference
            regex_conf = regex.get("confidence", 0)
            semantic_conf = semantic.get("confidence", 0)
            if abs(regex_conf - semantic_conf) > 0.2:
                categories["confidence_diff"].append(r)
            else:
                categories["both_learning"].append(r)
        elif not regex_is_learning and not semantic_is_learning:
            categories["both_not_learning"].append(r)
        elif regex_is_learning and not semantic_is_learning:
            categories["regex_only"].append(r)
        else:  # not regex_is_learning and semantic_is_learning
            categories["semantic_only"].append(r)

    return categories


def format_result(r: Dict[str, Any], verbose: bool = False) -> str:
    """Format a single result for display."""
    text = r["text"]
    if len(text) > 80:
        text = text[:77] + "..."

    regex = r["regex"]
    semantic = r["semantic"]

    lines = [f'  "{text}"']

    if regex.get("is_learning"):
        lines.append(f"    {Colors.BLUE}Regex:{Colors.END} ✓ type={regex['type']} conf={regex['confidence']:.2f} patterns={regex.get('patterns', '')}")
    else:
        lines.append(f"    {Colors.BLUE}Regex:{Colors.END} ✗ (no pattern match)")

    if semantic and "error" not in semantic:
        if semantic.get("is_learning"):
            extracted = semantic.get("extracted_learning", "")
            if extracted and len(extracted) > 50:
                extracted = extracted[:47] + "..."
            lines.append(f"    {Colors.YELLOW}Semantic:{Colors.END} ✓ type={semantic['type']} conf={semantic['confidence']:.2f}")
            if extracted:
                lines.append(f"             → \"{extracted}\"")
        else:
            reason = semantic.get("reasoning", "")
            if len(reason) > 60:
                reason = reason[:57] + "..."
            lines.append(f"    {Colors.YELLOW}Semantic:{Colors.END} ✗ ({reason})")
    elif semantic:
        lines.append(f"    {Colors.YELLOW}Semantic:{Colors.END} ⚠ {semantic.get('error', 'unavailable')}")

    return "\n".join(lines)


def generate_report(categories: Dict[str, List], verbose: bool = False) -> str:
    """Generate comparison report."""
    lines = []
    total = sum(len(v) for v in categories.values())

    lines.append("")
    lines.append(f"{Colors.BOLD}{'═' * 60}{Colors.END}")
    lines.append(f"{Colors.BOLD}DETECTION COMPARISON REPORT{Colors.END}")
    lines.append(f"{Colors.BOLD}{'═' * 60}{Colors.END}")
    lines.append("")
    lines.append(f"Total messages analyzed: {total}")
    lines.append("")

    # Summary table
    lines.append("┌─────────────────────────┬───────┬────────────────────────────────┐")
    lines.append("│ Category                │ Count │ Description                    │")
    lines.append("├─────────────────────────┼───────┼────────────────────────────────┤")

    rows = [
        ("Both agree: learning", len(categories["both_learning"]), "Regex + semantic both detect"),
        ("Both agree: not learning", len(categories["both_not_learning"]), "Neither detects a learning"),
        ("Regex only (potential FP)", len(categories["regex_only"]), "Regex detected, semantic rejected"),
        ("Semantic only (new!)", len(categories["semantic_only"]), "Semantic found, regex missed"),
        ("Confidence differs", len(categories["confidence_diff"]), "Both detect, scores differ >0.2"),
        ("Semantic unavailable", len(categories["semantic_error"]), "Claude CLI error/timeout"),
    ]

    for name, count, desc in rows:
        lines.append(f"│ {name:<23} │ {count:>5} │ {desc:<30} │")

    lines.append("└─────────────────────────┴───────┴────────────────────────────────┘")
    lines.append("")

    # Detailed sections for interesting cases

    # Semantic-only (new detections regex missed)
    if categories["semantic_only"]:
        lines.append(f"{Colors.GREEN}{Colors.BOLD}SEMANTIC-ONLY DETECTIONS ({len(categories['semantic_only'])}){Colors.END}")
        lines.append("These are corrections that regex missed but semantic caught:")
        lines.append("")
        for r in categories["semantic_only"][:10]:
            lines.append(format_result(r, verbose))
            lines.append("")
        if len(categories["semantic_only"]) > 10:
            lines.append(f"  ... and {len(categories['semantic_only']) - 10} more")
            lines.append("")

    # Regex-only (potential false positives)
    if categories["regex_only"]:
        lines.append(f"{Colors.RED}{Colors.BOLD}REGEX-ONLY DETECTIONS ({len(categories['regex_only'])}){Colors.END}")
        lines.append("These may be false positives that semantic correctly rejected:")
        lines.append("")
        for r in categories["regex_only"][:10]:
            lines.append(format_result(r, verbose))
            lines.append("")
        if len(categories["regex_only"]) > 10:
            lines.append(f"  ... and {len(categories['regex_only']) - 10} more")
            lines.append("")

    # Confidence differences
    if categories["confidence_diff"]:
        lines.append(f"{Colors.YELLOW}{Colors.BOLD}CONFIDENCE DIFFERENCES ({len(categories['confidence_diff'])}){Colors.END}")
        lines.append("Both detected as learning, but confidence scores differ significantly:")
        lines.append("")
        for r in categories["confidence_diff"][:5]:
            lines.append(format_result(r, verbose))
            lines.append("")

    # Verbose: show all categories
    if verbose:
        if categories["both_learning"]:
            lines.append(f"{Colors.BOLD}BOTH AGREE: LEARNING ({len(categories['both_learning'])}){Colors.END}")
            for r in categories["both_learning"][:5]:
                lines.append(format_result(r, verbose))
                lines.append("")
            if len(categories["both_learning"]) > 5:
                lines.append(f"  ... and {len(categories['both_learning']) - 5} more")
                lines.append("")

    # Summary
    lines.append(f"{Colors.BOLD}{'═' * 60}{Colors.END}")
    lines.append(f"{Colors.BOLD}SUMMARY{Colors.END}")
    lines.append(f"{Colors.BOLD}{'═' * 60}{Colors.END}")

    semantic_found = len(categories["semantic_only"])
    regex_fp = len(categories["regex_only"])

    if semantic_found > 0:
        lines.append(f"  {Colors.GREEN}✓ Semantic found {semantic_found} learnings that regex missed{Colors.END}")
    if regex_fp > 0:
        lines.append(f"  {Colors.RED}✗ Semantic rejected {regex_fp} potential false positives from regex{Colors.END}")
    if semantic_found == 0 and regex_fp == 0:
        lines.append("  ≈ Regex and semantic detection agree on most cases")

    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare regex vs semantic detection on session data"
    )
    parser.add_argument("files", nargs="*", help="Session files to analyze")
    parser.add_argument("--project", help="Find sessions for a project path")
    parser.add_argument("--limit", type=int, default=100, help="Max messages to analyze")
    parser.add_argument("--no-semantic", action="store_true", help="Skip semantic analysis")
    parser.add_argument("--verbose", action="store_true", help="Show all categories")
    parser.add_argument("--output", help="Write report to file")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")

    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Find session files
    session_files = []

    if args.project:
        session_files = find_project_sessions(args.project)
        if not session_files:
            print(f"No session files found for project: {args.project}")
            sys.exit(1)
    elif args.files:
        session_files = [Path(f) for f in args.files if Path(f).exists()]
    else:
        # Default: current project
        session_files = find_project_sessions(".")

    if not session_files:
        print("No session files specified. Usage:")
        print("  python scripts/compare_detection.py ~/.claude/projects/*/*.jsonl")
        print("  python scripts/compare_detection.py --project .")
        sys.exit(1)

    print(f"Found {len(session_files)} session file(s)")

    # Extract messages
    all_messages = []
    for sf in session_files:
        messages = extract_user_messages(sf, corrections_only=False)
        all_messages.extend(messages)

    print(f"Extracted {len(all_messages)} user messages")

    # Limit messages if needed
    if len(all_messages) > args.limit:
        print(f"Limiting to {args.limit} messages")
        all_messages = all_messages[:args.limit]

    # Analyze each message
    print("Analyzing messages...")
    results = []
    use_semantic = not args.no_semantic

    for i, msg in enumerate(all_messages):
        if i > 0 and i % 10 == 0:
            print(f"  {i}/{len(all_messages)}...")

        result = analyze_message(msg, use_semantic=use_semantic)
        results.append(result)

    # Compare and report
    if use_semantic:
        categories = compare_results(results)
        report = generate_report(categories, verbose=args.verbose)
    else:
        # Regex-only report
        learnings = [r for r in results if r["regex"].get("is_learning")]
        report = f"\nRegex-only analysis: {len(learnings)} learnings detected out of {len(results)} messages\n"
        for r in learnings[:20]:
            report += f"\n  \"{r['text'][:60]}...\" → {r['regex']['patterns']}"

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
