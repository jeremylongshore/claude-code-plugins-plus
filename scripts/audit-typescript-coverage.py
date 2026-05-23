#!/usr/bin/env python3
"""Audit TypeScript files in plugins/ for typecheck coverage.

The repo runs `pnpm --filter '*' typecheck` at the workspace level — but only
plugins whose package.json declares a `typecheck` script are actually checked.
This script finds .ts files inside plugin dirs that DON'T have a typecheck
script defined in the nearest enclosing package.json, and reports them.

Use as a CI gate (initial mode: --report-only) to flag the gap, then a
follow-up cleanup pass adds typecheck scripts to each affected plugin.

Exit code 0 if all TS files have typecheck coverage (or in --report-only mode).
Exit code 1 if uncovered TS files found AND not in --report-only mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_nearest_package_json(path: Path, root: Path) -> Path | None:
    """Walk up from `path` until we find a package.json or hit `root`."""
    current = path.parent if path.is_file() else path
    while current >= root:
        pkg = current / "package.json"
        if pkg.exists():
            return pkg
        if current == root:
            return None
        current = current.parent
    return None


def has_typecheck(pkg_path: Path) -> bool:
    try:
        with pkg_path.open() as f:
            d = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    scripts = d.get("scripts", {})
    return "typecheck" in scripts or "type-check" in scripts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="plugins", help="Root dir to scan")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print findings but always exit 0",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        return 1

    repo_root = root.parent

    ts_files = sorted(p for p in root.rglob("*.ts") if "node_modules" not in p.parts and not p.name.endswith(".d.ts"))

    if not ts_files:
        print("No .ts files under plugins/ (excluding node_modules + .d.ts).")
        return 0

    uncovered: list[Path] = []
    no_pkg: list[Path] = []
    covered_count = 0

    for ts in ts_files:
        pkg = find_nearest_package_json(ts, repo_root)
        if pkg is None:
            no_pkg.append(ts)
            continue
        if has_typecheck(pkg):
            covered_count += 1
            if args.verbose:
                print(f"  OK  {ts.relative_to(repo_root)} (via {pkg.relative_to(repo_root)})")
        else:
            uncovered.append(ts)

    print()
    print(f"Total .ts files scanned:       {len(ts_files)}")
    print(f"Covered by a typecheck script: {covered_count}")
    print(f"Uncovered (no typecheck):      {len(uncovered)}")
    print(f"No enclosing package.json:     {len(no_pkg)}")

    if uncovered:
        print()
        print("Uncovered .ts files (parent package.json missing 'typecheck' script):")
        # Group by enclosing package
        by_pkg: dict[Path, list[Path]] = {}
        for ts in uncovered:
            pkg = find_nearest_package_json(ts, repo_root)
            if pkg:
                by_pkg.setdefault(pkg, []).append(ts)
        for pkg, files in sorted(by_pkg.items()):
            print(f"  {pkg.relative_to(repo_root)}  ({len(files)} file(s))")
            for f in files[:5]:
                print(f"    - {f.relative_to(repo_root)}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")

    if no_pkg:
        print()
        print("Files with no enclosing package.json (consider adding one):")
        for ts in no_pkg[:10]:
            print(f"  {ts.relative_to(repo_root)}")
        if len(no_pkg) > 10:
            print(f"  ... and {len(no_pkg) - 10} more")

    has_issues = bool(uncovered or no_pkg)
    if not has_issues:
        print("\nAll TypeScript files in plugins/ are covered by a typecheck script.")
        return 0

    if args.report_only:
        print("\n(--report-only: exiting 0 despite findings)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
