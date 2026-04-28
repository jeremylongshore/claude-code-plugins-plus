#!/usr/bin/env python3
"""
batch-remediate.py — Bulk-fix script for SKILL.md frontmatter migrations.

Currently supports:
  --migrate-compatible-with   Translate the deprecated `compatible-with` CSV
                              platform list into the spec-aligned `compatibility`
                              free-text field per agentskills.io/specification.

Translation rules (idempotent — running twice on the same file is safe):

  compatible-with: claude-code
    → compatibility: Designed for Claude Code

  compatible-with: claude-code, codex, openclaw
    → compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw

  compatible-with: ["claude-code"]
    → compatibility: Designed for Claude Code

  compatible-with:           (empty)
    → field removed

If `compatibility` already exists in the file, the existing value wins and
`compatible-with` is removed without overwrite. This makes re-runs safe.

Usage:
  python3 scripts/batch-remediate.py --migrate-compatible-with [--dry-run] [--root PATH]

By default, scans the current working directory recursively for SKILL.md files.
Use --root to point at a specific tree (e.g. ~/.claude/skills).

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


# Platform display-name lookup. Used to render the migration target nicely.
# Anything not in this map falls back to the raw string the user wrote.
PLATFORM_DISPLAY = {
    'claude-code': 'Claude Code',
    'codex': 'Codex',
    'openclaw': 'OpenClaw',
    'aider': 'Aider',
    'continue': 'Continue',
    'cursor': 'Cursor',
    'windsurf': 'Windsurf',
}


def normalize_platform_list(raw) -> List[str]:
    """Coerce the YAML value into a list of normalized platform strings."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(p).strip().lower() for p in raw if str(p).strip()]
    if isinstance(raw, str):
        return [p.strip().lower() for p in raw.split(',') if p.strip()]
    # Unknown shape — give up gracefully.
    return []


def render_compatibility_value(platforms: List[str]) -> str:
    """Render the AgentSkills.io-style free-text compatibility string."""
    if not platforms:
        return ''
    display = [PLATFORM_DISPLAY.get(p, p) for p in platforms]
    if len(display) == 1:
        return f"Designed for {display[0]}"
    head = display[0]
    tail = display[1:]
    if len(tail) == 1:
        return f"Designed for {head}, also compatible with {tail[0]}"
    # Oxford-comma list: "A, B, and C"
    joined = ", ".join(tail[:-1]) + f" and {tail[-1]}"
    return f"Designed for {head}, also compatible with {joined}"


def split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    """Return (frontmatter_yaml_text, body) or (None, text) if no frontmatter."""
    m = RE_FRONTMATTER.match(text)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def migrate_compatible_with(content: str) -> Tuple[str, Optional[str]]:
    """
    Apply the compatible-with → compatibility migration to a file's full text.
    Returns (new_content, change_summary). change_summary is None if untouched.

    Idempotent: if `compatibility` already present, removes `compatible-with`
    without overwriting. If `compatible-with` absent, no change.
    """
    fm_text, body = split_frontmatter(content)
    if fm_text is None:
        return content, None

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        return content, f"YAML parse error: {exc}"

    if not isinstance(fm, dict):
        return content, None

    if 'compatible-with' not in fm:
        return content, None

    existing_compatibility = fm.get('compatibility')
    raw = fm.pop('compatible-with')
    platforms = normalize_platform_list(raw)
    new_value = render_compatibility_value(platforms)

    summary_parts: List[str] = []
    if existing_compatibility:
        # Already migrated; just remove the legacy key.
        summary_parts.append(
            f"removed `compatible-with` (existing `compatibility` "
            f"`{existing_compatibility}` preserved)"
        )
    elif new_value:
        fm['compatibility'] = new_value
        summary_parts.append(f"compatible-with: {raw!r} → compatibility: {new_value!r}")
    else:
        # Empty platform list — drop the field outright.
        summary_parts.append("removed empty `compatible-with`")

    new_fm_text = yaml.safe_dump(fm, sort_keys=False, default_flow_style=False).rstrip()
    new_content = f"---\n{new_fm_text}\n---\n{body}"
    return new_content, "; ".join(summary_parts)


def find_skill_files(root: Path) -> List[Path]:
    """Find all SKILL.md files under root."""
    return sorted(root.rglob("SKILL.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        "--migrate-compatible-with",
        action="store_true",
        help="Translate deprecated `compatible-with` CSV into spec-aligned `compatibility` free-text.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory to scan for SKILL.md files. Default: current directory.",
    )
    args = parser.parse_args()

    if not args.migrate_compatible_with:
        parser.print_help()
        print("\nERROR: pick at least one migration flag (e.g. --migrate-compatible-with).", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: --root not found: {root}", file=sys.stderr)
        return 1

    files = find_skill_files(root)
    if not files:
        print(f"No SKILL.md files found under {root}.")
        return 0

    print(f"Scanning {len(files)} SKILL.md files under {root}")
    if args.dry_run:
        print("(dry-run — no files will be written)\n")

    changed = 0
    skipped = 0
    errors = 0
    for path in files:
        try:
            original = path.read_text(encoding='utf-8')
        except OSError as exc:
            print(f"  ! {path}: read error: {exc}")
            errors += 1
            continue

        new_content, summary = migrate_compatible_with(original)
        if summary is None:
            skipped += 1
            continue
        if summary.startswith("YAML parse error"):
            print(f"  ! {path.relative_to(root)}: {summary}")
            errors += 1
            continue

        rel = path.relative_to(root)
        print(f"  ~ {rel}: {summary}")
        if not args.dry_run:
            path.write_text(new_content, encoding='utf-8')
        changed += 1

    print(f"\nSummary: {changed} changed, {skipped} unchanged, {errors} errors")
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
