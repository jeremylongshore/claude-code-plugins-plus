#!/usr/bin/env python3
"""
Skill Validator — Wrapper around validate-skills-schema.py for skill-creator.

Provides --grade flag for single-file validation with full grade report.
Delegates to the main validator in the repository root.

Usage:
    python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py <SKILL.md>
    python3 ${CLAUDE_SKILL_DIR}/scripts/validate-skill.py --grade <SKILL.md>
"""

import os
import subprocess
import sys


def find_repo_validator():
    """Find the main validate-skills-schema.py in the repository."""
    # Try relative to this script (inside the plugin repo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Walk up to find scripts/validate-skills-schema.py
    current = script_dir
    for _ in range(10):
        candidate = os.path.join(current, "scripts", "validate-skills-schema.py")
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Try common locations
    home = os.path.expanduser("~")
    for path in [
        os.path.join(home, "000-projects", "claude-code-plugins", "scripts", "validate-skills-schema.py"),
    ]:
        if os.path.exists(path):
            return path

    return None


def main():
    args = sys.argv[1:]

    if not args or args == ["--help"] or args == ["-h"]:
        print(__doc__)
        sys.exit(0)

    # Parse our flags
    grade = "--grade" in args
    verbose = "--verbose" in args or "-v" in args
    skill_path = None

    for arg in args:
        if not arg.startswith("-"):
            skill_path = arg
            break

    if not skill_path:
        print("ERROR: No SKILL.md path provided", file=sys.stderr)
        print("Usage: validate-skill.py [--grade] <path/to/SKILL.md>")
        sys.exit(1)

    if not os.path.exists(skill_path):
        print(f"ERROR: File not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    validator = find_repo_validator()
    if not validator:
        print("ERROR: Cannot find validate-skills-schema.py", file=sys.stderr)
        print("Make sure you're running from within the claude-code-plugins repo")
        sys.exit(1)

    # Build command
    cmd = [sys.executable, validator]
    if verbose or grade:
        cmd.append("--verbose")
    cmd.append(skill_path)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
