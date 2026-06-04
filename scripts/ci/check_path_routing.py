#!/usr/bin/env python3
"""Workflow paths-filter dry-run / verifier.

Reads every .github/workflows/*.yml file, extracts its `pull_request.paths`
filter (if any), and reports which workflows would fire for a given list of
changed files.

Used as a regression gate for the workflow split (PR 2 of the new-track CI
overhaul). If a future PR breaks the paths routing — e.g., a typo in a glob
or a renamed file pattern that no workflow catches — the test_path_routing
pytest detects it before merge.

Usage:
    # Standalone (interactive):
    python3 scripts/ci/check_path_routing.py --changed-files /tmp/files.txt

    # With stdin:
    git diff --name-only origin/main..HEAD | \\
        python3 scripts/ci/check_path_routing.py --stdin

    # Pretty JSON output:
    ... --pretty

The output JSON is keyed by workflow name; each value is a list of files that
match that workflow's paths filter. Workflows with NO paths filter (fire on
every PR) are listed under the "_no_filter" key.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = _REPO_ROOT / ".github" / "workflows"


# --- Minimal YAML extraction --------------------------------------------------
#
# We don't depend on PyYAML — the runtime CI doesn't always have it. We need
# just two things: the workflow `name:` and the `pull_request.paths:` list.
# A bespoke line-oriented parser is sufficient for the well-known shape of
# our workflow files.


def extract_workflow_metadata(yaml_path: Path) -> dict[str, Any]:
    """Return {name, paths} for one workflow file.

    name: the top-level `name:` value (string) or the filename stem.
    paths: list of pull_request `paths:` globs (empty list = no filter).
    """
    text = yaml_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    workflow_name: str | None = None
    paths: list[str] = []

    in_pull_request = False
    in_pr_paths = False
    pr_paths_indent: int | None = None

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        # Top-level workflow name
        m = re.match(r"^name:\s*(.+?)\s*$", stripped)
        if m and workflow_name is None:
            workflow_name = m.group(1).strip('"').strip("'")
            continue

        # Detect `pull_request:` (top-level under `on:` — leading whitespace = 2)
        m = re.match(r"^(\s*)pull_request:\s*$", stripped)
        if m and len(m.group(1)) <= 2:
            in_pull_request = True
            in_pr_paths = False
            continue

        if in_pull_request:
            # Leaving pull_request when we hit a sibling top-level event
            # (e.g. `push:`) at the same indent
            m = re.match(r"^(\s*)([a-z_]+):\s*$", stripped)
            if m and len(m.group(1)) <= 2 and m.group(2) != "pull_request":
                in_pull_request = False
                in_pr_paths = False
                continue

            # Detect `paths:` inside pull_request
            m = re.match(r"^(\s*)paths:\s*$", stripped)
            if m:
                in_pr_paths = True
                pr_paths_indent = len(m.group(1))
                continue

            if in_pr_paths:
                # Continue collecting list items until we leave the indent block
                m = re.match(r"^(\s*)-\s*(.+?)\s*$", stripped)
                if m and pr_paths_indent is not None and len(m.group(1)) > pr_paths_indent:
                    item = m.group(2).strip('"').strip("'")
                    paths.append(item)
                    continue
                # Non-list-item line → we've left the paths block
                # but might still be inside pull_request
                if stripped.lstrip() and not stripped.lstrip().startswith("-"):
                    in_pr_paths = False

    return {
        "name": workflow_name or yaml_path.stem,
        "file": str(yaml_path.relative_to(_REPO_ROOT)),
        "paths": paths,
    }


# --- Glob matching ----------------------------------------------------------


def path_matches_filter(path: str, glob_patterns: list[str]) -> bool:
    """GitHub paths filter behavior: a file matches if ANY pattern matches.

    Uses fnmatch with GitHub's `**` extension. fnmatch's bare `*` already
    matches across `/`, but we explicitly normalize `**/<pat>` → `*<pat>`
    for clarity.
    """
    for pattern in glob_patterns:
        # GitHub's **/<x> matches "x at any depth"; fnmatch's * already does this.
        # Strip the leading "**/" if present.
        norm = pattern
        if norm.startswith("**/"):
            norm = norm[3:]
        if fnmatch.fnmatch(path, norm):
            return True
        # Also try matching with the original pattern (fnmatch handles "**" OK
        # in some cases via collapsed star semantics).
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


# --- Routing dry-run --------------------------------------------------------


def run_routing(changed_files: list[str]) -> dict[str, Any]:
    """Apply each workflow's paths filter to the changed-file list."""
    workflows: list[dict[str, Any]] = []
    for wf in sorted(_WORKFLOWS_DIR.glob("*.yml")):
        workflows.append(extract_workflow_metadata(wf))

    result: dict[str, Any] = {
        "_no_filter": [],   # workflows that fire on every PR
        "_changed_files": sorted(changed_files),
    }

    for wf in workflows:
        wf_name = wf["name"]
        if not wf["paths"]:
            result["_no_filter"].append(wf_name)
            continue
        matched = sorted([f for f in changed_files if path_matches_filter(f, wf["paths"])])
        if matched:
            result[wf_name] = {
                "file": wf["file"],
                "matched_files": matched,
            }

    return result


def list_all_workflows() -> list[dict[str, Any]]:
    return [extract_workflow_metadata(wf) for wf in sorted(_WORKFLOWS_DIR.glob("*.yml"))]


# --- CLI -------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--changed-files", default=None, help="File containing changed-file list (one per line)")
    p.add_argument("--stdin", action="store_true", help="Read changed files from stdin")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--list-workflows", action="store_true", help="List all workflows + their paths filters")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    if args.list_workflows:
        wfs = list_all_workflows()
        print(json.dumps(wfs, indent=2 if args.pretty else None))
        return 0

    if args.changed_files:
        files = [
            l.strip()
            for l in Path(args.changed_files).read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
    elif args.stdin:
        files = [l.strip() for l in sys.stdin.read().splitlines() if l.strip()]
    else:
        print("error: provide --changed-files FILE or --stdin", file=sys.stderr)
        return 2

    result = run_routing(files)
    print(json.dumps(result, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
