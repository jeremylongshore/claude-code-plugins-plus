"""Deterministic file-path → component-type classification rules.

This module is the entire ruleset. The classifier is just the
application of these rules over a file list.

Adding a new contribution type means:
    1. Add a row to RULE_DESCRIPTIONS describing the rule.
    2. Add the detection logic to classify_files().
    3. Add a unit test in tests/pr-classifier/test_classifier.py.

Don't add detection logic without a corresponding rule description —
the description IS the audit trail for why a file got classified.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import PurePosixPath
from typing import Any

# --- Rule descriptions ------------------------------------------------------


RULE_DESCRIPTIONS: tuple[tuple[str, str], ...] = (
    (
        "skill",
        "Matches plugins/<category>/<plugin>/skills/<skill-name>/SKILL.md "
        "(depth-4 file under skills/). Each match adds <skill-name> to "
        "affected_skills.",
    ),
    ("agent", "Matches plugins/<category>/<plugin>/agents/<agent>.md. Each match adds <agent> to affected_agents."),
    (
        "mcp",
        "Matches plugins/mcp/<name>/** OR plugins/<category>/<plugin>/.mcp.json "
        "OR plugins/<category>/<plugin>/mcpServers/**. Each match adds the "
        "MCP server identifier to affected_mcp.",
    ),
    ("hook", "Matches plugins/<category>/<plugin>/hooks/hooks.json. Each match adds the plugin to affected_hooks."),
    (
        "plugin",
        "ANY change inside plugins/<category>/<plugin>/ — adds the plugin path "
        "to plugin_paths. Subset markers (skill/agent/mcp/hook) are independent.",
    ),
    (
        "catalog_add",
        "Catches additions to .claude-plugin/marketplace.extended.json that "
        "introduce new top-level plugin entries — parsed from the diff to "
        "capture name + source + category.",
    ),
    (
        "sources_add",
        "Catches additions to sources.yaml that introduce new entries for external source synchronization.",
    ),
    ("ci", "Touches .github/workflows/*.yml or .github/workflows/*.yaml. Marks touches_workflows: true."),
    ("frontend", "Touches marketplace/src/** — Astro frontend. Marks touches_frontend: true."),
    ("script", "Touches scripts/** — repo-level Python or Node scripts. Marks touches_scripts: true."),
    (
        "doc",
        "Touches *.md or *.mdx files OUTSIDE any plugin directory (top-level "
        "docs, contributing guides, README, etc.). Plugin-internal docs are "
        "captured under the plugin marker, not as standalone doc.",
    ),
    ("test", "Touches tests/** or **/tests/** or test_*.py — test-only changes."),
    (
        "unknown",
        "Set to true when at least one file in the input list matched no rule. "
        "Surfaces unrecognized patterns for ruleset extension.",
    ),
)


# --- Helpers ----------------------------------------------------------------


def _is_plugin_path(path: PurePosixPath) -> bool:
    """plugins/<cat>/<name>/... — at least 3 parts under plugins/"""
    return len(path.parts) >= 3 and path.parts[0] == "plugins"


def _plugin_root(path: PurePosixPath) -> str | None:
    """Return 'plugins/<cat>/<name>' for a file under that tree, else None."""
    if not _is_plugin_path(path):
        return None
    return "/".join(path.parts[:3])


def _file_extension(path: PurePosixPath) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "(none)"


# --- Catalog diff parsing ---------------------------------------------------


_CATALOG_ENTRY_OBJECT = re.compile(r'^\+\s*\{\s*$|^\+\s*\{\s*"name"\s*:\s*"(?P<inline_name>[^"]+)"', re.M)


def _count_unquoted_braces(text: str) -> tuple[int, int]:
    """Count `{` and `}` in text, ignoring braces inside string literals.

    Reviewer flagged (PR #838 review): naive `text.count("{")` is broken when
    a string value contains literal braces — e.g. a `"description"` field with
    template placeholders like `"Uses {amazing} things"` (balanced, OK) or
    `"Uses {foo {bar} patterns"` (unbalanced, drives depth counter wrong and
    silently drops the entire catalog entry). Walk the string char-by-char
    with quote-state tracking so braces inside `"..."` literals don't count.
    Honors `\"` escape so `"a\"b"` is one continuous string.
    """
    opens = 0
    closes = 0
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            opens += 1
        elif ch == "}":
            closes += 1
    return opens, closes


def parse_catalog_additions_from_diff(diff_text: str) -> list[dict[str, str]]:
    """Extract added catalog entries from a unified-diff text.

    Looks for added object blocks within `.claude-plugin/marketplace.extended.json`
    diff chunks. Captures `name`, `source`, and `category` when present.

    Returns one dict per added entry. Order matches diff order.
    """
    if "marketplace.extended.json" not in diff_text:
        return []

    out: list[dict[str, str]] = []
    in_catalog_diff = False
    current: dict[str, str] = {}
    open_brace_depth = 0
    in_added_block = False

    for line in diff_text.splitlines():
        # Track when we're inside a catalog file's diff hunk
        if line.startswith("diff --git ") and "marketplace.extended.json" in line:
            in_catalog_diff = True
            continue
        if line.startswith("diff --git ") and "marketplace.extended.json" not in line:
            in_catalog_diff = False
            continue
        if not in_catalog_diff:
            continue

        # Only consider added lines
        if not line.startswith("+") or line.startswith("+++"):
            # Closing brace ends an added block we were tracking
            if in_added_block and line.startswith(" ") and "}" in line:
                if current:
                    out.append(dict(current))
                current = {}
                in_added_block = False
                open_brace_depth = 0
            continue

        added_content = line[1:].strip()

        # Count braces OUTSIDE string literals only (reviewer fix PR #838).
        line_opens, line_closes = _count_unquoted_braces(added_content)

        if line_opens > 0 and not in_added_block:
            in_added_block = True
            open_brace_depth = line_opens - line_closes
            current = {}
            continue

        if in_added_block:
            open_brace_depth += line_opens - line_closes
            for field in ("name", "source", "category", "version"):
                m = re.match(rf'^"{field}"\s*:\s*"([^"]+)"', added_content)
                if m:
                    current[field] = m.group(1)
            if open_brace_depth <= 0:
                if current:
                    out.append(dict(current))
                current = {}
                in_added_block = False

    return out


def parse_sources_additions_from_diff(diff_text: str) -> list[dict[str, str]]:
    """Extract added entries from the ROOT-LEVEL sources.yaml diff text.

    Captures top-level YAML entries that look like `- name: foo` or
    `- repo: foo/bar` additions. Restricted to the root-level `sources.yaml`
    to match the touch-detection rule in classify_files (reviewer fix PR #838:
    `config/sources.yaml` or other non-root files should NOT fire sources_add).
    """
    # Match diff header that targets root-level sources.yaml — `a/sources.yaml`
    # or `b/sources.yaml` (no intermediate directories).
    if not re.search(r"diff --git a/sources\.yaml b/sources\.yaml", diff_text):
        return []

    out: list[dict[str, str]] = []
    in_sources_diff = False
    current: dict[str, str] = {}

    def flush() -> None:
        nonlocal current
        if current:
            out.append(dict(current))
            current = {}

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # Strict root-level match — `a/sources.yaml b/sources.yaml`. Reject
            # `a/config/sources.yaml` and similar non-root paths.
            if re.search(r"a/sources\.yaml\s+b/sources\.yaml", line):
                in_sources_diff = True
            else:
                in_sources_diff = False
                flush()
            continue
        if not in_sources_diff:
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        if content.startswith("- "):
            flush()
            kv = content[2:].strip()
            if ":" in kv:
                k, _, v = kv.partition(":")
                current[k.strip()] = v.strip().strip('"').strip("'")
        elif content.startswith("  ") and ":" in content:
            kv = content.strip()
            k, _, v = kv.partition(":")
            current[k.strip()] = v.strip().strip('"').strip("'")
    flush()
    return out


# --- Main classifier --------------------------------------------------------


def classify_files(files: list[str], diff_text: str | None = None) -> dict[str, Any]:
    """Apply the ruleset to a list of changed files.

    Args:
        files: list of repo-relative file paths (forward-slash).
        diff_text: optional unified diff text; required for catalog/sources
            additions to be detected. Without it, catalog_additions and
            sources_additions will always be empty.

    Returns the structured classification dict described in RULE_DESCRIPTIONS.
    """
    contribution_types: set[str] = set()
    plugin_paths: set[str] = set()
    affected_skills: set[str] = set()
    affected_agents: set[str] = set()
    affected_mcp: set[str] = set()
    affected_hooks: set[str] = set()
    file_categories: Counter[str] = Counter()
    touches_workflows = False
    touches_frontend = False
    touches_scripts = False
    touches_tests = False
    unmatched: list[str] = []

    for raw in files:
        if not raw:
            continue
        path = PurePosixPath(raw)
        matched = False
        ext = _file_extension(path)
        file_categories[ext] += 1

        # --- Plugin-internal matches ---
        plugin_root = _plugin_root(path)
        if plugin_root is not None:
            plugin_paths.add(plugin_root)
            contribution_types.add("plugin")
            matched = True

            # Skill match: <plugin-root>/skills/<skill>/SKILL.md at ANY depth.
            # Reviewer fix PR #838: the prior depth-4-only check missed
            # sub-vendored layouts like
            # plugins/saas-packs/<vendor>/<sub>/skills/<x>/SKILL.md.
            # Walk the tail of the path for the `skills/<name>/SKILL.md`
            # signature instead of hardcoding parts[3].
            if (
                len(path.parts) >= 3
                and path.parts[-1] == "SKILL.md"
                and len(path.parts) >= 3
                and path.parts[-3] == "skills"
            ):
                affected_skills.add(path.parts[-2])
                contribution_types.add("skill")

            # Agent match: <plugin-root>/agents/<agent>.md at ANY depth
            # (same depth-flex fix as skills above).
            elif len(path.parts) >= 2 and ext == "md" and len(path.parts) >= 3 and path.parts[-2] == "agents":
                affected_agents.add(path.parts[-1].rsplit(".", 1)[0])
                contribution_types.add("agent")

            # MCP — either plugins/mcp/<name>/** or .mcp.json or mcpServers
            if path.parts[1] == "mcp":
                affected_mcp.add(path.parts[2])
                contribution_types.add("mcp")
            elif path.name == ".mcp.json":
                affected_mcp.add(plugin_root.split("/")[-1])
                contribution_types.add("mcp")
            elif len(path.parts) >= 5 and path.parts[3] == "mcpServers":
                affected_mcp.add(plugin_root.split("/")[-1])
                contribution_types.add("mcp")

            # Hooks
            if len(path.parts) >= 5 and path.parts[3] == "hooks" and path.name == "hooks.json":
                affected_hooks.add(plugin_root.split("/")[-1])
                contribution_types.add("hook")

        # --- Non-plugin matches ---
        if path.parts and path.parts[0] == ".github":
            if len(path.parts) >= 3 and path.parts[1] == "workflows" and ext in ("yml", "yaml"):
                touches_workflows = True
                contribution_types.add("ci")
                matched = True

        if path.parts and path.parts[0] == "marketplace":
            if len(path.parts) >= 3 and path.parts[1] == "src":
                touches_frontend = True
                contribution_types.add("frontend")
                matched = True

        if path.parts and path.parts[0] == "scripts":
            touches_scripts = True
            contribution_types.add("script")
            matched = True

        # Tests
        if path.parts and (path.parts[0] == "tests" or "tests" in path.parts or path.name.startswith("test_")):
            touches_tests = True
            contribution_types.add("test")
            matched = True

        # Standalone docs (md/mdx outside any plugin)
        if ext in ("md", "mdx") and plugin_root is None:
            is_frontend_doc = (
                path.parts and path.parts[0] == "marketplace" and len(path.parts) >= 2 and path.parts[1] == "src"
            )
            if path.parts and path.parts[0] in ("000-docs", "docs"):
                contribution_types.add("doc")
                matched = True
            elif len(path.parts) == 1:
                contribution_types.add("doc")
                matched = True
            elif path.parts[0] in (".github", "scripts", "tests"):
                # CI / script / test docs stay under their own category
                pass
            elif is_frontend_doc:
                # marketplace/src/**.md is content under the frontend route tree;
                # the frontend marker already fired so don't double-classify.
                pass
            else:
                # marketplace/<not src>/**.md and any other top-level dir's docs
                contribution_types.add("doc")
                matched = True

        # Catalog file itself (without being a catalog-add: we detect that
        # via diff parsing, but a touch is still classified).
        if (
            len(path.parts) >= 2
            and path.parts[0] == ".claude-plugin"
            and path.name in ("marketplace.extended.json", "marketplace.json")
        ):
            contribution_types.add("catalog")
            matched = True

        # sources.yaml touch
        if path.parts == ("sources.yaml",) or (len(path.parts) == 1 and path.name == "sources.yaml"):
            contribution_types.add("sources")
            matched = True

        if not matched:
            unmatched.append(raw)

    # --- Catalog + sources diff parsing ---
    catalog_additions: list[dict[str, str]] = []
    sources_additions: list[dict[str, str]] = []
    if diff_text:
        catalog_additions = parse_catalog_additions_from_diff(diff_text)
        sources_additions = parse_sources_additions_from_diff(diff_text)
        if catalog_additions:
            contribution_types.add("catalog_add")
        if sources_additions:
            contribution_types.add("sources_add")

    # file_categories sorted for determinism — reviewer fix PR #838. Counter
    # preserves insertion order, which depends on the input file-list ordering.
    # to_json(..., sort_keys=True) hides this at serialization, but the
    # in-memory dict was non-deterministic. Sort by key for both surfaces.
    return {
        "contribution_types": sorted(contribution_types),
        "plugin_paths": sorted(plugin_paths),
        "affected_skills": sorted(affected_skills),
        "affected_agents": sorted(affected_agents),
        "affected_mcp": sorted(affected_mcp),
        "affected_hooks": sorted(affected_hooks),
        "catalog_additions": catalog_additions,
        "sources_additions": sources_additions,
        "file_categories": dict(sorted(file_categories.items())),
        "touches_workflows": touches_workflows,
        "touches_frontend": touches_frontend,
        "touches_scripts": touches_scripts,
        "touches_tests": touches_tests,
        "unknown": len(unmatched) > 0,
        "unmatched": sorted(unmatched),
    }


def to_json(result: dict[str, Any], pretty: bool = False) -> str:
    """Render a classify_files() result as JSON."""
    if pretty:
        return json.dumps(result, indent=2, sort_keys=True)
    return json.dumps(result, sort_keys=True)
