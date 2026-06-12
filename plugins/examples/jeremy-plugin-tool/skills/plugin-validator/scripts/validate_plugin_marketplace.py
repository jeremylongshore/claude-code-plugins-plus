#!/usr/bin/env python3
"""
Jeremy Plugin Tool — Marketplace-Grade Validator (thin delegating wrapper).

This script used to carry its own 725-line validation implementation with a
6-field required set (missing compatibility + tags) that diverged from the
authoritative validator. It now delegates to scripts/validate-skills-schema.py
at the repository root, run at the marketplace tier (the IS 8-field required
set + 100-point rubric).

CLI surface (preserved from the previous implementation):
    python3 validate_plugin_marketplace.py [plugin_path] [--verbose|-v] [--fail-on-warn]

plugin_path defaults to "." (current directory, validated in plugin mode).
Exit codes: 0 = pass, 1 = errors (unchanged).

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_main_validator() -> Path | None:
    """Resolve scripts/validate-skills-schema.py by walking up from this file."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "scripts" / "validate-skills-schema.py"
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Jeremy Plugin Tool - Marketplace-Grade Validator (delegates to validate-skills-schema.py)"
    )
    parser.add_argument("plugin_path", nargs="?", default=".", help="Plugin directory or repository root")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-file OK lines")
    parser.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    print(
        "DEPRECATED: this wrapper delegates to scripts/validate-skills-schema.py "
        "(the authoritative validator); invoke it directly for the full flag surface.",
        file=sys.stderr,
    )

    target = Path(args.plugin_path)
    if not target.exists():
        print(f"ERROR: Path does not exist: {target.resolve()}", file=sys.stderr)
        return 1

    validator = find_main_validator()
    if validator is None:
        print(
            "ERROR: Cannot find scripts/validate-skills-schema.py — run from within the claude-code-plugins repo",
            file=sys.stderr,
        )
        return 1

    cmd = [sys.executable, str(validator), "--marketplace"]
    if args.verbose:
        cmd.append("--verbose")
    if args.fail_on_warn:
        cmd.append("--fail-on-warn")
    cmd.append(str(target))

    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
