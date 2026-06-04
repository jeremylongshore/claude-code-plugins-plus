#!/usr/bin/env python3
"""PR component classifier — CLI entry point.

Reads a list of changed-file paths (from stdin, --file, or positional args),
optionally reads a unified diff (from --diff-file) for catalog/sources entry
parsing, applies the deterministic ruleset in rules.py, and emits the
classification JSON to stdout.

Typical CI invocation:

    git diff --name-only origin/main..HEAD | \\
        python3 scripts/pr-classifier/detect_components.py --stdin

With diff for catalog detection:

    python3 scripts/pr-classifier/detect_components.py \\
        --stdin \\
        --diff-file /tmp/pr-diff.patch

Exit codes:
    0 — classification produced (even if unknown=true)
    2 — input error (no files supplied, file not readable)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Resolve the package import whether invoked as `python3 detect_components.py`
# or via `python3 -m scripts.pr-classifier.detect_components`.
_SELF = Path(__file__).resolve()
sys.path.insert(0, str(_SELF.parents[1]))

try:
    from pr_classifier.rules import classify_files, to_json  # type: ignore[import-not-found]
except ImportError:
    # Fallback for hyphenated dir name — load rules.py as a sibling module.
    import importlib.util as _ilu

    _rules_path = _SELF.parent / "rules.py"
    _spec = _ilu.spec_from_file_location("pr_classifier_rules", _rules_path)
    _rules = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_rules)
    classify_files = _rules.classify_files
    to_json = _rules.to_json


def _read_files_from(args: argparse.Namespace) -> list[str]:
    if args.file:
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"error: cannot read --file {args.file}: {e}", file=sys.stderr)
            sys.exit(2)
        return [l.strip() for l in text.splitlines() if l.strip()]

    if args.stdin:
        return [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]

    if args.files:
        return list(args.files)

    print(
        "error: no input. Provide --stdin, --file FILE, or positional file paths.",
        file=sys.stderr,
    )
    sys.exit(2)


def _read_diff(diff_file: str | None) -> str | None:
    if not diff_file:
        return None
    try:
        return Path(diff_file).read_text(encoding="utf-8")
    except OSError as e:
        print(f"error: cannot read --diff-file {diff_file}: {e}", file=sys.stderr)
        sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Changed file paths (positional). Mutually exclusive with --stdin/--file.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read file paths from stdin, one per line.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Read file paths from FILE, one per line.",
    )
    parser.add_argument(
        "--diff-file",
        default=None,
        help="Read unified-diff text from FILE for catalog/sources detection.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the output JSON (default: compact one-line).",
    )

    args = parser.parse_args(argv)
    files = _read_files_from(args)
    diff_text = _read_diff(args.diff_file)

    result = classify_files(files, diff_text=diff_text)
    print(to_json(result, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
