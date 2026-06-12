#!/usr/bin/env python3
"""
Skill Validator — thin delegating wrapper around the repo's main validator.

This script used to carry its own 1,155-line validation + 100-point grading
implementation. That copy diverged from the authoritative validator (it was
missing the disallowed-tools and visibility fields, among others), so it now
delegates to scripts/validate-skills-schema.py at the repository root.
The main validator's marketplace tier carries the IS 100-point rubric.

CLI surface (preserved from the previous implementation):
    python3 validate-skill.py path/to/SKILL.md               # Standard (default)
    python3 validate-skill.py --enterprise path/to/SKILL.md  # Marketplace tier
    python3 validate-skill.py --grade path/to/SKILL.md       # Rubric grading
    python3 validate-skill.py --grade --json path/to/SKILL.md
    python3 validate-skill.py --json path/to/SKILL.md

Exit codes: 0 = valid / passing, 1 = errors (unchanged).
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
    parser = argparse.ArgumentParser(description="Validate SKILL.md files (delegates to validate-skills-schema.py)")
    parser.add_argument("path", help="Path to SKILL.md file")
    parser.add_argument(
        "--standard",
        action="store_true",
        help="Use Standard tier - AgentSkills.io minimum (default, kept for compatibility)",
    )
    parser.add_argument(
        "--enterprise",
        action="store_true",
        help="Use Enterprise tier (maps to the main validator's --marketplace tier)",
    )
    parser.add_argument("--grade", action="store_true", help="Run 100-point grading rubric (marketplace tier)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    print(
        "DEPRECATED: this wrapper delegates to scripts/validate-skills-schema.py "
        "(the authoritative validator); invoke it directly for the full flag surface.",
        file=sys.stderr,
    )

    target = Path(args.path)
    if not target.exists():
        print(f"Error: {target} not found", file=sys.stderr)
        return 1

    validator = find_main_validator()
    if validator is None:
        print(
            "ERROR: Cannot find scripts/validate-skills-schema.py — run from within the claude-code-plugins repo",
            file=sys.stderr,
        )
        return 1

    cmd = [sys.executable, str(validator)]
    # Tier mapping (at most one tier flag; main validator rejects combinations):
    #   --grade or --enterprise  -> --marketplace (rubric grading lives there)
    #   --standard (or default)  -> --standard
    # Previous behavior: --standard overrode --enterprise; --grade always graded.
    if args.grade or (args.enterprise and not args.standard):
        cmd.append("--marketplace")
    else:
        cmd.append("--standard")
    if args.json:
        cmd.append("--json")
    cmd.append(str(target))

    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
