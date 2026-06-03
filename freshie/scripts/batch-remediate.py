#!/usr/bin/env python3
"""
batch-remediate.py — Auto-fix common compliance gaps across the plugin ecosystem.

Reads from freshie/inventory.sqlite and applies targeted YAML frontmatter
patches to SKILL.md and agent .md files.

Usage:
    python3 freshie/scripts/batch-remediate.py --dry-run          # default
    python3 freshie/scripts/batch-remediate.py --fix-tags --execute
    python3 freshie/scripts/batch-remediate.py --fix-compatible-with --execute
    python3 freshie/scripts/batch-remediate.py --fix-agents --execute
    python3 freshie/scripts/batch-remediate.py --all --execute
    python3 freshie/scripts/batch-remediate.py --all --pack crypto --execute
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path("/home/jeremy/000-projects/claude-code-plugins")
DB_PATH = REPO_ROOT / "freshie" / "inventory.sqlite"
PLUGINS_ROOT = REPO_ROOT / "plugins"

# Fields that are no longer valid in agent frontmatter
DEPRECATED_AGENT_FIELDS = frozenset(
    [
        "capabilities",
        "expertise_level",
        "activation_priority",
        "activation_triggers",
        "color",
        "type",
        "category",
    ]
)

# Category directory → tags
TAG_MAP: dict[str, list[str]] = {
    "ai-ml": ["ai", "machine-learning"],
    "ai-agency": ["ai", "agents"],
    "api-development": ["api", "development"],
    "automation": ["automation", "workflow"],
    "business-tools": ["business", "productivity"],
    "community": ["community", "open-source"],
    "crypto": ["crypto", "blockchain", "web3"],
    "database": ["database", "sql"],
    "design": ["design", "ui-ux"],
    "devops": ["devops", "ci-cd", "infrastructure"],
    "examples": ["examples", "templates"],
    "finance": ["finance", "fintech"],
    "mcp": ["mcp", "tooling"],
    "packages": ["packages", "tooling"],
    "performance": ["performance", "optimization"],
    "productivity": ["productivity", "workflow"],
    "saas-packs": ["saas"],
    "security": ["security", "compliance"],
    "skill-enhancers": ["meta", "skills"],
    "testing": ["testing", "quality"],
}

# Service-name hints keyed on pack-name prefix (saas-packs only)
SAAS_SERVICE_HINTS: dict[str, list[str]] = {
    "adobe": ["design", "adobe"],
    "alchemy": ["blockchain", "web3"],
    "algolia": ["search", "algolia"],
    "anima": ["design", "anima"],
    "anthropic": ["ai", "anthropic"],
    "apify": ["scraping", "automation"],
    "apollo": ["sales", "apollo"],
    "appfolio": ["real-estate", "appfolio"],
    "apple-notes": ["productivity", "notes"],
    "assemblyai": ["ai", "speech-to-text"],
    "attio": ["crm", "attio"],
    "bamboohr": ["hr", "bamboohr"],
    "brightdata": ["scraping", "data"],
    "canva": ["design", "canva"],
    "castai": ["cloud", "kubernetes"],
    "clari": ["sales", "revenue"],
    "clay": ["data-enrichment", "clay"],
    "clerk": ["auth", "clerk"],
    "clickhouse": ["database", "analytics"],
    "clickup": ["productivity", "clickup"],
    "coderabbit": ["code-review", "ai"],
    "cohere": ["ai", "nlp"],
    "coreweave": ["cloud", "gpu"],
    "cursor": ["ide", "cursor"],
    "customerio": ["marketing", "email"],
    "databricks": ["data", "spark"],
    "deepgram": ["speech-to-text", "ai"],
    "documenso": ["documents", "e-signature"],
    "elevenlabs": ["voice", "ai"],
    "firecrawl": ["scraping", "data"],
    "freeagent": ["finance", "accounting"],
    "freshdesk": ["support", "helpdesk"],
    "github": ["devops", "github"],
    "gitlab": ["devops", "gitlab"],
    "google": ["google", "productivity"],
    "grafana": ["monitoring", "observability"],
    "greenhouse": ["hr", "recruiting"],
    "honeycomb": ["observability", "tracing"],
    "hubspot": ["crm", "marketing"],
    "intercom": ["support", "messaging"],
    "jira": ["project-management", "jira"],
    "knock": ["notifications", "knock"],
    "launchdarkly": ["feature-flags", "launchdarkly"],
    "lever": ["hr", "recruiting"],
    "linear": ["project-management", "linear"],
    "livekit": ["realtime", "video"],
    "mailchimp": ["email", "marketing"],
    "metabase": ["analytics", "bi"],
    "mixpanel": ["analytics", "product"],
    "mux": ["video", "streaming"],
    "notion": ["productivity", "notion"],
    "openai": ["ai", "openai"],
    "pagerduty": ["devops", "incident-management"],
    "perplexity": ["ai", "search"],
    "pinecone": ["vector-db", "ai"],
    "planetscale": ["database", "mysql"],
    "posthog": ["analytics", "product"],
    "quicknode": ["blockchain", "web3"],
    "ramp": ["finance", "fintech"],
    "remofirst": ["hr", "remote-work"],
    "replit": ["ide", "cloud"],
    "retellai": ["voice", "ai"],
    "runway": ["ai", "video"],
    "salesforce": ["crm", "salesforce"],
    "salesloft": ["sales", "outreach"],
    "sentry": ["monitoring", "error-tracking"],
    "serpapi": ["search", "seo"],
    "shopify": ["ecommerce", "shopify"],
    "snowflake": ["data-warehouse", "analytics"],
    "speak": ["language-learning", "ai"],
    "stackblitz": ["ide", "cloud"],
    "stripe": ["payments", "stripe"],
    "supabase": ["database", "backend"],
    "techsmith": ["screen-recording", "documentation"],
    "together": ["ai", "llm"],
    "twinmind": ["ai", "productivity"],
    "vastai": ["cloud", "gpu"],
    "veeva": ["pharma", "crm"],
    "vercel": ["deployment", "frontend"],
    "webflow": ["design", "no-code"],
    "windsurf": ["ide", "ai"],
    "wispr": ["voice", "productivity"],
    "workhuman": ["hr", "recognition"],
    "abridge": ["healthcare", "ai"],
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class Stats(NamedTuple):
    tags_added: int
    compatible_with_added: int
    agent_fields_removed: int
    files_modified: int
    files_skipped: int
    errors: int


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _category_from_path(file_path: Path) -> str | None:
    """Return the category directory name (e.g. 'ai-ml') for a plugin file."""
    try:
        rel = file_path.relative_to(PLUGINS_ROOT)
        return rel.parts[0]
    except (ValueError, IndexError):
        return None


def _pack_name_from_path(file_path: Path) -> str | None:
    """Return the pack directory name for a saas-packs file (e.g. 'stripe-pack')."""
    try:
        rel = file_path.relative_to(PLUGINS_ROOT)
        if rel.parts[0] == "saas-packs" and len(rel.parts) > 1:
            return rel.parts[1]  # e.g. 'stripe-pack'
    except (ValueError, IndexError):
        pass
    return None


def infer_tags(file_path: Path) -> list[str]:
    """Infer tags for a skill or agent file based on its directory path."""
    category = _category_from_path(file_path)
    if category is None:
        return []

    base_tags = list(TAG_MAP.get(category, []))

    if category == "saas-packs":
        pack_name = _pack_name_from_path(file_path)
        if pack_name:
            # strip trailing -pack  →  e.g. 'stripe-pack' → 'stripe'
            service = pack_name.removesuffix("-pack")
            # Match against SAAS_SERVICE_HINTS by longest prefix match
            extra: list[str] = []
            for key, hints in SAAS_SERVICE_HINTS.items():
                if service == key or service.startswith(key):
                    extra = hints
                    break
            # Add the service name itself if not already represented
            if service not in extra:
                extra = extra + [service]
            # Merge deduplicated, base_tags first
            seen: set[str] = set(base_tags)
            for tag in extra:
                if tag not in seen:
                    base_tags.append(tag)
                    seen.add(tag)

    return base_tags


# ---------------------------------------------------------------------------
# YAML frontmatter manipulation (string-level, no yaml.dump)
# ---------------------------------------------------------------------------


def _split_frontmatter(content: str) -> tuple[str, str, str] | None:
    """
    Split a file into (opening_delimiter, frontmatter_text, rest).

    Returns None if no valid YAML front-matter block is found.
    The returned frontmatter_text does NOT include the --- delimiters.
    rest starts with the closing --- line (inclusive) so we can reconstruct
    the file as:  opening_delimiter + frontmatter_text + rest
    Actually we return it as: "---\n" + fm + rest  where rest = "---\n" + body
    """
    if not content.startswith("---"):
        return None
    # Find closing ---
    # The opening --- must be on the first line
    first_newline = content.index("\n")
    after_open = content[first_newline + 1 :]
    # Find closing delimiter: a line that is exactly ---
    close_match = re.search(r"(?m)^---\s*$", after_open)
    if not close_match:
        return None
    fm_text = after_open[: close_match.start()]
    rest = after_open[close_match.start() :]  # starts with ---
    return ("---\n", fm_text, rest)


def _reconstruct(opening: str, fm_text: str, rest: str) -> str:
    return opening + fm_text + rest


def _has_field(fm_text: str, field: str) -> bool:
    """Return True if the frontmatter already has the given field key."""
    pattern = rf"(?m)^{re.escape(field)}\s*:"
    return bool(re.search(pattern, fm_text))


def _insert_field_line(fm_text: str, line: str) -> str:
    """
    Append a new field line just before the implicit end of the frontmatter text.
    We insert before the last non-empty line's trailing newline to keep it tidy,
    or simply append at the end (fm_text already ends without closing ---).
    """
    # Ensure line ends with newline
    if not line.endswith("\n"):
        line = line + "\n"
    return fm_text + line


def _remove_field_lines(fm_text: str, fields: set[str]) -> tuple[str, list[str]]:
    """
    Remove all lines belonging to the given field keys (including any
    indented continuation lines that immediately follow).  Returns
    (new_fm_text, list_of_removed_field_names).
    """
    lines = fm_text.split("\n")
    result: list[str] = []
    removed: list[str] = []
    skip_continuation = False

    for line in lines:
        # Check if this line starts a target field
        matched_field: str | None = None
        for field in fields:
            if re.match(rf"^{re.escape(field)}\s*:", line):
                matched_field = field
                break

        if matched_field is not None:
            removed.append(matched_field)
            skip_continuation = True
            # Skip this line
            continue

        # Skip continuation lines (indented or list items under a removed field)
        if skip_continuation:
            if line.startswith(" ") or line.startswith("\t") or line.strip().startswith("-"):
                continue
            else:
                skip_continuation = False

        result.append(line)

    return "\n".join(result), removed


def add_tags_to_file(file_path: Path, dry_run: bool) -> tuple[bool, str | None]:
    """
    Add a `tags:` line to the frontmatter of file_path if it is missing.

    Returns (changed: bool, error_message | None).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)

    parts = _split_frontmatter(content)
    if parts is None:
        return False, "no frontmatter found"

    opening, fm_text, rest = parts

    if _has_field(fm_text, "tags"):
        return False, None  # already present

    tags = infer_tags(file_path)
    if not tags:
        return False, "could not infer tags"

    tag_line = f"tags: [{', '.join(tags)}]\n"
    new_fm = _insert_field_line(fm_text, tag_line)
    new_content = _reconstruct(opening, new_fm, rest)

    if not dry_run:
        _backup_and_write(file_path, new_content)

    return True, None


def add_compatible_with_to_file(file_path: Path, dry_run: bool) -> tuple[bool, str | None]:
    """
    Add `compatible-with: claude-code` if the field is missing.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, str(exc)

    parts = _split_frontmatter(content)
    if parts is None:
        return False, "no frontmatter found"

    opening, fm_text, rest = parts

    if _has_field(fm_text, "compatible-with"):
        return False, None

    compat_line = "compatible-with: claude-code\n"
    new_fm = _insert_field_line(fm_text, compat_line)
    new_content = _reconstruct(opening, new_fm, rest)

    if not dry_run:
        _backup_and_write(file_path, new_content)

    return True, None


def remove_deprecated_agent_fields(file_path: Path, dry_run: bool) -> tuple[bool, list[str], str | None]:
    """
    Remove deprecated fields from an agent frontmatter.

    Returns (changed, removed_field_names, error | None).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, [], str(exc)

    parts = _split_frontmatter(content)
    if parts is None:
        return False, [], "no frontmatter found"

    opening, fm_text, rest = parts

    new_fm, removed = _remove_field_lines(fm_text, DEPRECATED_AGENT_FIELDS)

    if not removed:
        return False, [], None

    new_content = _reconstruct(opening, new_fm, rest)

    if not dry_run:
        _backup_and_write(file_path, new_content)

    return True, removed, None


def _backup_and_write(file_path: Path, new_content: str) -> None:
    """Copy file to file.bak, then write new_content."""
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup)
    file_path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Database queries
# ---------------------------------------------------------------------------


def _open_db() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None
    try:
        return sqlite3.connect(str(DB_PATH))
    except sqlite3.Error:
        return None


def get_skills_missing_tags(db: sqlite3.Connection) -> list[Path]:
    cur = db.cursor()
    cur.execute("SELECT skill_path FROM skill_compliance WHERE missing_fields LIKE '%tags%'")
    return [Path(row[0]) for row in cur.fetchall()]


def get_skills_missing_compatible_with(db: sqlite3.Connection) -> list[Path]:
    cur = db.cursor()
    cur.execute("SELECT skill_path FROM skill_compliance WHERE missing_fields LIKE '%compatible-with%'")
    return [Path(row[0]) for row in cur.fetchall()]


def get_agents_with_invalid_fields(db: sqlite3.Connection) -> list[Path]:
    cur = db.cursor()
    cur.execute("SELECT agent_path FROM agent_compliance WHERE has_invalid_fields = 1")
    return [Path(row[0]) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Filesystem walk fallback
# ---------------------------------------------------------------------------


def _walk_skill_files() -> list[Path]:
    results: list[Path] = []
    for root, _dirs, files in os.walk(PLUGINS_ROOT):
        for fname in files:
            if fname == "SKILL.md":
                results.append(Path(root) / fname)
    return results


def _walk_agent_files() -> list[Path]:
    results: list[Path] = []
    for root, _dirs, files in os.walk(PLUGINS_ROOT):
        rp = Path(root)
        if rp.name == "agents":
            for fname in files:
                if fname.endswith(".md"):
                    results.append(rp / fname)
    return results


def _skills_missing_tags_from_fs() -> list[Path]:
    return [p for p in _walk_skill_files() if not _file_has_field(p, "tags")]


def _skills_missing_compat_from_fs() -> list[Path]:
    return [p for p in _walk_skill_files() if not _file_has_field(p, "compatible-with")]


def _agents_with_invalid_fields_from_fs() -> list[Path]:
    """Return agent files that have at least one deprecated field."""
    results = []
    for p in _walk_agent_files():
        try:
            content = p.read_text(encoding="utf-8")
        except OSError:
            continue
        parts = _split_frontmatter(content)
        if parts is None:
            continue
        _, fm_text, _ = parts
        for field in DEPRECATED_AGENT_FIELDS:
            if _has_field(fm_text, field):
                results.append(p)
                break
    return results


def _file_has_field(file_path: Path, field: str) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return True  # treat unreadable as "has field" to avoid false positives
    parts = _split_frontmatter(content)
    if parts is None:
        return True
    _, fm_text, _ = parts
    return _has_field(fm_text, field)


# ---------------------------------------------------------------------------
# Pack filter
# ---------------------------------------------------------------------------


def _filter_by_pack(paths: list[Path], pack: str | None) -> list[Path]:
    """Restrict paths to those whose plugin path contains the given pack name."""
    if pack is None:
        return paths
    return [p for p in paths if pack in str(p)]


# ---------------------------------------------------------------------------
# Remediation runners
# ---------------------------------------------------------------------------


def run_fix_tags(paths: list[Path], dry_run: bool, verbose: bool) -> tuple[int, int, int]:
    """Returns (added, skipped, errors)."""
    added = skipped = errors = 0
    for p in paths:
        if not p.exists():
            if verbose:
                print(f"  SKIP (not found): {p}")
            skipped += 1
            continue
        changed, err = add_tags_to_file(p, dry_run)
        if err and not changed:
            if verbose:
                print(f"  SKIP ({err}): {p}")
            skipped += 1
        elif changed:
            added += 1
            if verbose:
                action = "DRY-RUN" if dry_run else "FIXED"
                tags = infer_tags(p)
                print(f"  {action} tags={tags}: {p}")
        else:
            skipped += 1
    return added, skipped, errors


def run_fix_compatible_with(paths: list[Path], dry_run: bool, verbose: bool) -> tuple[int, int, int]:
    added = skipped = errors = 0
    for p in paths:
        if not p.exists():
            if verbose:
                print(f"  SKIP (not found): {p}")
            skipped += 1
            continue
        changed, err = add_compatible_with_to_file(p, dry_run)
        if err and not changed:
            if verbose:
                print(f"  SKIP ({err}): {p}")
            skipped += 1
        elif changed:
            added += 1
            if verbose:
                action = "DRY-RUN" if dry_run else "FIXED"
                print(f"  {action} compatible-with: {p}")
        else:
            skipped += 1
    return added, skipped, errors


def run_fix_agents(paths: list[Path], dry_run: bool, verbose: bool) -> tuple[int, int, int]:
    removed_count = skipped = errors = 0
    for p in paths:
        if not p.exists():
            if verbose:
                print(f"  SKIP (not found): {p}")
            skipped += 1
            continue
        changed, removed, err = remove_deprecated_agent_fields(p, dry_run)
        if err and not changed:
            if verbose:
                print(f"  ERROR ({err}): {p}")
            errors += 1
        elif changed:
            removed_count += 1
            if verbose:
                action = "DRY-RUN" if dry_run else "FIXED"
                print(f"  {action} removed={removed}: {p}")
        else:
            skipped += 1
    return removed_count, skipped, errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch-remediate compliance gaps in plugin SKILL.md and agent files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually write files (default is dry-run — no writes).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Explicit dry-run flag (same as omitting --execute).",
    )
    parser.add_argument(
        "--fix-tags",
        action="store_true",
        help="Add missing tags: field to SKILL.md files.",
    )
    parser.add_argument(
        "--fix-compatible-with",
        action="store_true",
        help="Add missing compatible-with: claude-code to SKILL.md files.",
    )
    parser.add_argument(
        "--fix-agents",
        action="store_true",
        help="Remove deprecated fields from agent .md files.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enable all fixers (--fix-tags + --fix-compatible-with + --fix-agents).",
    )
    parser.add_argument(
        "--pack",
        metavar="PACK",
        default=None,
        help="Restrict changes to paths containing this pack/category name.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each file action.",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip DB lookup and use filesystem walk only.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Resolve dry_run: write only when --execute is passed
    dry_run = not args.execute

    # Resolve which fixers to run
    fix_tags = args.fix_tags or args.all
    fix_compat = args.fix_compatible_with or args.all
    fix_agents = args.fix_agents or args.all

    if not (fix_tags or fix_compat or fix_agents):
        parser.error("Specify at least one fixer: --fix-tags, --fix-compatible-with, --fix-agents, or --all")

    mode_label = "DRY RUN (no files written)" if dry_run else "EXECUTE MODE (files will be modified)"
    print(f"\n=== BATCH REMEDIATION — {mode_label} ===\n")

    # Open DB (with filesystem fallback)
    db: sqlite3.Connection | None = None
    use_db = not args.no_db
    if use_db:
        db = _open_db()
        if db is None:
            print(f"WARNING: DB not found at {DB_PATH} — falling back to filesystem walk.\n")
            use_db = False

    # Accumulators
    total_tags_added = 0
    total_compat_added = 0
    total_agent_fields_removed = 0
    total_files_modified = 0
    total_skipped = 0
    total_errors = 0

    # --- Fix tags ---
    if fix_tags:
        print("[1/3] Fixing missing tags...")
        if use_db and db is not None:
            skill_paths = get_skills_missing_tags(db)
            print(f"      DB reports {len(skill_paths)} skills missing tags.")
        else:
            skill_paths = _skills_missing_tags_from_fs()
            print(f"      Filesystem walk found {len(skill_paths)} skills missing tags.")

        skill_paths = _filter_by_pack(skill_paths, args.pack)
        added, skipped, errors = run_fix_tags(skill_paths, dry_run, args.verbose)
        total_tags_added += added
        total_skipped += skipped
        total_errors += errors
        total_files_modified += added
        print(f"      Added: {added}  Skipped: {skipped}  Errors: {errors}\n")

    # --- Fix compatible-with ---
    if fix_compat:
        print("[2/3] Fixing missing compatible-with...")
        if use_db and db is not None:
            compat_paths = get_skills_missing_compatible_with(db)
            print(f"      DB reports {len(compat_paths)} skills missing compatible-with.")
        else:
            compat_paths = _skills_missing_compat_from_fs()
            print(f"      Filesystem walk found {len(compat_paths)} skills missing compatible-with.")

        compat_paths = _filter_by_pack(compat_paths, args.pack)
        added, skipped, errors = run_fix_compatible_with(compat_paths, dry_run, args.verbose)
        total_compat_added += added
        total_skipped += skipped
        total_errors += errors
        total_files_modified += added
        print(f"      Added: {added}  Skipped: {skipped}  Errors: {errors}\n")

    # --- Fix agents ---
    if fix_agents:
        print("[3/3] Fixing deprecated agent fields...")
        if use_db and db is not None:
            agent_paths = get_agents_with_invalid_fields(db)
            print(f"      DB reports {len(agent_paths)} agents with invalid fields.")
        else:
            agent_paths = _agents_with_invalid_fields_from_fs()
            print(f"      Filesystem walk found {len(agent_paths)} agents with invalid fields.")

        agent_paths = _filter_by_pack(agent_paths, args.pack)
        removed, skipped, errors = run_fix_agents(agent_paths, dry_run, args.verbose)
        total_agent_fields_removed += removed
        total_skipped += skipped
        total_errors += errors
        total_files_modified += removed
        print(f"      Fixed: {removed}  Skipped: {skipped}  Errors: {errors}\n")

    if db is not None:
        db.close()

    # --- Summary ---
    print("=== BATCH REMEDIATION REPORT ===")
    print(f"Tags added:                {total_tags_added:>6,}")
    print(f"Compatible-with added:     {total_compat_added:>6,}")
    print(f"Agent fields removed:      {total_agent_fields_removed:>6,}")
    print(f"Files modified:            {total_files_modified:>6,}")
    print(f"Files skipped (compliant): {total_skipped:>6,}")
    print(f"Errors:                    {total_errors:>6,}")

    if dry_run:
        print("\nNOTE: Dry-run complete. Re-run with --execute to apply changes.")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
