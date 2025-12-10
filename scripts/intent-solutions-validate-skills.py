#!/usr/bin/env python3
"""
Claude Skills Validator (Strict Mode)

Enforces the Nixtla Claude Skills Standard with zero tolerance.
Any violation = error = non-zero exit = CI fails.

Usage:
    python scripts/validate_skills.py

Author: Nixtla Skills Pack
Version: 1.0.0
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

try:
    import yaml
except ImportError:
    print("Dependency required: pyyaml. Add it to requirements-dev.txt.", file=sys.stderr)
    sys.exit(1)


RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
RE_DESCRIPTION_USE_WHEN = re.compile(r"\bUse when\b", re.IGNORECASE)
RE_DESCRIPTION_TRIGGER_WITH = re.compile(r"\bTrigger with\b", re.IGNORECASE)
RE_ABSOLUTE_PATH = re.compile(r"(^/|[A-Za-z]:\\)")
RE_BASEDIR_SCRIPTS = re.compile(r"{baseDir}/scripts/([\w\-./]+)")
RE_FIRST_PERSON = re.compile(r"\b(I can|I will|I'm going to|I help)\b", re.IGNORECASE)
RE_SECOND_PERSON = re.compile(r"\bYou can\b", re.IGNORECASE)
FORBIDDEN_WORDS = ("anthropic", "claude")


def find_skill_files(root: Path) -> List[Path]:
    """Find all SKILL.md files, excluding archive and backup directories."""
    excluded_dirs = {"archive", "backups", "backup", ".git", "node_modules", "__pycache__", ".venv"}
    results = []
    for p in root.rglob("SKILL.md"):
        if p.is_file():
            # Check if any parent directory is in excluded list
            parts = p.relative_to(root).parts
            if not any(part in excluded_dirs for part in parts):
                results.append(p)
    return results


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    m = RE_FRONTMATTER.match(content)
    if not m:
        raise ValueError("Invalid or absent YAML frontmatter block at top of SKILL.md")
    front_str, body = m.groups()
    data = yaml.safe_load(front_str) or {}
    if not isinstance(data, dict):
        raise ValueError("Frontmatter is not a YAML mapping")
    return data, body


def validate_frontmatter(path: Path, fm: dict) -> List[str]:
    errors: List[str] = []

    required_keys = ["name", "description", "allowed-tools", "version"]
    for key in required_keys:
        if key not in fm:
            errors.append(f"[frontmatter] required key not present: '{key}'")

    name = str(fm.get("name", "")).strip()
    desc = (fm.get("description") or "").strip()

    # Basic existence
    if not name:
        errors.append("[frontmatter] 'name' must be non-empty")
    if not desc:
        errors.append("[frontmatter] 'description' must be non-empty")

    # name rules (hard)
    if name:
        if name != name.lower() or " " in name:
            errors.append("[frontmatter] 'name' must be lowercase-with-hyphens (no spaces)")
        if len(name) > 64:
            errors.append("[frontmatter] 'name' must be <= 64 characters")

    # description rules (hard)
    if len(desc) > 1024:
        errors.append("[frontmatter] 'description' must be <= 1024 characters")

    if not RE_DESCRIPTION_USE_WHEN.search(desc):
        errors.append("[frontmatter] 'description' must include 'Use when ...' per standard")

    if not RE_DESCRIPTION_TRIGGER_WITH.search(desc):
        errors.append("[frontmatter] 'description' must include 'Trigger with ...' per standard")

    if RE_FIRST_PERSON.search(desc):
        errors.append("[frontmatter] 'description' must NOT use first person (I can / I will / etc.)")

    if RE_SECOND_PERSON.search(desc):
        errors.append("[frontmatter] 'description' must NOT use second person ('You can'); use third person.")

    lowered = desc.lower()
    for bad in FORBIDDEN_WORDS:
        if bad in lowered:
            errors.append(f"[frontmatter] 'description' must not contain reserved word '{bad}'")

    # allowed-tools: basic sanity - no unscoped Bash
    allowed = str(fm.get("allowed-tools", "")).strip()
    if not allowed:
        errors.append("[frontmatter] 'allowed-tools' must be non-empty")

    if "Bash" in allowed and "(" not in allowed:
        errors.append("[frontmatter] 'allowed-tools' uses unscoped Bash; use scoped Bash(git:*) or similar")

    return errors


def validate_body(path: Path, body: str) -> List[str]:
    errors: List[str] = []
    lines = body.splitlines()

    # length hard limit
    if len(lines) > 500:
        errors.append(f"[body] SKILL.md has {len(lines)} lines (max 500). Apply progressive disclosure.")

    # required sections (hard)
    required_sections = [
        "# ",              # title line
        "## Overview",
        "## Prerequisites",
        "## Instructions",
        "## Output",
        "## Error Handling",
        "## Examples",
        "## Resources",
    ]
    for sec in required_sections:
        if sec not in body:
            errors.append(f"[body] required section heading not present: '{sec}'")

    # path checks (hard)
    for i, line in enumerate(lines, start=1):
        if RE_ABSOLUTE_PATH.search(line):
            errors.append(f"[body] line {i}: contains absolute/OS-specific path; must use '{{baseDir}}/...'")

        if "\\scripts\\" in line:
            errors.append(f"[body] line {i}: uses backslashes in path; must use forward slashes")

    return errors


def validate_scripts_exist(path: Path, body: str, repo_root: Path) -> List[str]:
    """
    HARD FAIL: every {baseDir}/scripts/... reference must point to a real file
    under the skill's scripts/ directory.
    """
    errors: List[str] = []
    skill_dir = path.parent

    referenced = set(m.group(1) for m in RE_BASEDIR_SCRIPTS.finditer(body))

    for rel in sorted(referenced):
        # Scripts are relative to the skill directory, not repo root
        script_path = (skill_dir / "scripts" / rel).resolve()

        # Ensure path doesn't escape skill directory
        try:
            script_path.relative_to(skill_dir)
        except ValueError:
            errors.append(f"[scripts] reference escapes skill directory: {rel}")
            continue

        if not script_path.exists():
            errors.append(
                f"[scripts] referenced script not found: '{{baseDir}}/scripts/{rel}' "
                f"(expected at {skill_dir.name}/scripts/{rel})"
            )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    skills = find_skill_files(repo_root)
    if not skills:
        print("No SKILL.md files found - nothing to validate.")
        return 0

    print(f"Found {len(skills)} SKILL.md files to validate.")

    total_errors = 0

    for skill in skills:
        rel = skill.relative_to(repo_root)
        print(f"\nValidating {rel} ...")
        content = skill.read_text(encoding="utf-8")

        file_errors: List[str] = []

        try:
            fm, body = parse_frontmatter(content)
        except Exception as e:
            file_errors.append(f"[frontmatter] {e}")
            fm, body = {}, content  # still run body checks to report more issues

        file_errors.extend(validate_frontmatter(skill, fm))
        file_errors.extend(validate_body(skill, body))
        file_errors.extend(validate_scripts_exist(skill, body, repo_root))

        if file_errors:
            for err in file_errors:
                print(f"  ERROR: {err}")
        else:
            print("  OK")

        total_errors += len(file_errors)

    print(f"\nSummary: {total_errors} error(s).")

    if total_errors > 0:
        print("Validation failed due to errors (strict mode).")
        return 1

    print("All SKILL.md files passed validation (strict mode).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
