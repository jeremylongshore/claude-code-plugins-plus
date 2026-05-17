#!/usr/bin/env python3
"""Reject PRs that reformat .claude-plugin/marketplace.extended.json beyond
the line budget implied by structural changes.

Background: contributors sometimes run prettier (or an IDE format-on-save) over
the catalog file, which collapses every multi-line `keywords: [...]` array into
a single line across the entire 11k-line file. The net diff then shows -1200
lines for a PR that only adds one logical plugin entry. Reformatting wrecks
merge bases for any other PR touching the same file, so we reject it at CI.

Heuristic: count net new/removed/modified plugin entries (by `name`). Each
added/removed entry has an expected line budget; modifications are smaller.
If the file's actual net line delta exceeds budget by a fixed tolerance,
flag as reformat.

Usage:
    python3 scripts/check-catalog-format.py [BASE_REF]

BASE_REF defaults to "origin/main". Exits non-zero on suspected reformat.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

CATALOG = ".claude-plugin/marketplace.extended.json"
# Per-entry line budgets — generous to allow real edits.
LINES_PER_ADDED = 80
LINES_PER_REMOVED = 80
LINES_PER_MODIFIED = 20
TOLERANCE = 300  # absolute line-count slack before we call it a reformat


def main(argv: list[str]) -> int:
    base_ref = argv[1] if len(argv) > 1 else "origin/main"

    try:
        base_json = subprocess.check_output(
            ["git", "show", f"{base_ref}:{CATALOG}"],
            stderr=subprocess.PIPE,
        ).decode()
    except subprocess.CalledProcessError as e:
        print(f"check-catalog-format: could not read {base_ref}:{CATALOG} — {e.stderr.decode().strip()}", file=sys.stderr)
        # No base = new repo; nothing to compare against.
        return 0

    head_path = pathlib.Path(CATALOG)
    if not head_path.exists():
        print(f"check-catalog-format: {CATALOG} not present in working tree", file=sys.stderr)
        return 0
    head_json = head_path.read_text()

    if base_json == head_json:
        print("check-catalog-format: catalog unchanged — OK")
        return 0

    try:
        base = json.loads(base_json)
        head = json.loads(head_json)
    except json.JSONDecodeError as e:
        print(f"::error file={CATALOG}::Catalog is not valid JSON: {e}")
        return 1

    base_entries = {p["name"]: p for p in base.get("plugins", []) if p.get("name")}
    head_entries = {p["name"]: p for p in head.get("plugins", []) if p.get("name")}

    added = set(head_entries) - set(base_entries)
    removed = set(base_entries) - set(head_entries)
    common = set(base_entries) & set(head_entries)
    modified = {n for n in common if base_entries[n] != head_entries[n]}

    base_lines = base_json.count("\n")
    head_lines = head_json.count("\n")
    net = head_lines - base_lines
    budget = (
        LINES_PER_ADDED * len(added)
        - LINES_PER_REMOVED * len(removed)
        + LINES_PER_MODIFIED * len(modified)
    )

    delta = abs(net - budget)
    print(
        f"check-catalog-format: net {net:+d} lines "
        f"(budget {budget:+d}±{TOLERANCE}, delta {delta}) "
        f"for {len(added)} added / {len(modified)} modified / {len(removed)} removed entries"
    )

    if delta > TOLERANCE:
        msg = (
            f"Catalog churn ({net:+d} lines net) far exceeds budget "
            f"({budget:+d}±{TOLERANCE}) for {len(added)} added, {len(modified)} modified, "
            f"{len(removed)} removed entries. Suggests a formatter pass ran over the file. "
            "Please revert whitespace-only changes — the catalog's multi-line layout is load-bearing "
            "(see .prettierignore). If your changes are intentional, open an issue first."
        )
        print(f"::error file={CATALOG}::{msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
