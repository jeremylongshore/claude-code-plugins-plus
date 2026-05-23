#!/usr/bin/env python3
"""Enforce report-only-gate deadlines in CI.

Scans `.github/workflows/*.yml` for markers of the form:

    # REPORT-ONLY-UNTIL: YYYY-MM-DD

Each marker represents a CI gate that's been intentionally relaxed to
report-only mode but MUST be flipped to blocking (or the gate fixed, or
the deadline extended) by the named date. The marker is a contract with
future-us: "I deferred this; here's when it costs me."

If today > the marker date, this script exits 1 and prints a clear
remediation message. The script is invoked from CI; after the deadline,
every PR fails until the maintainer takes action.

Exit codes:
  0   — all markers are in the future (or no markers found)
  1   — one or more markers have lapsed (deadline passed)
  2   — usage / parse error

Usage:
  python3 scripts/check-ci-deadlines.py
  python3 scripts/check-ci-deadlines.py --workflows .github/workflows
  python3 scripts/check-ci-deadlines.py --warn-days 14   # also warn if <N days out
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

MARKER_RE = re.compile(
    r"#\s*REPORT-ONLY-UNTIL:\s*(\d{4}-\d{2}-\d{2})\s*(?:\(([^)]*)\))?",
    re.IGNORECASE,
)


def scan_workflows(workflow_dir: Path) -> list[tuple[Path, int, dt.date, str]]:
    """Return list of (file, line_no, deadline_date, note)."""
    out: list[tuple[Path, int, dt.date, str]] = []
    for f in sorted(workflow_dir.glob("*.yml")):
        for line_no, line in enumerate(f.read_text().splitlines(), 1):
            m = MARKER_RE.search(line)
            if not m:
                continue
            try:
                d = dt.date.fromisoformat(m.group(1))
            except ValueError:
                print(
                    f"::error file={f},line={line_no}::Invalid REPORT-ONLY-UNTIL date '{m.group(1)}' (expected YYYY-MM-DD)"
                )
                sys.exit(2)
            note = (m.group(2) or "").strip()
            out.append((f, line_no, d, note))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflows",
        default=".github/workflows",
        help="Directory containing workflow YAML files",
    )
    parser.add_argument(
        "--warn-days",
        type=int,
        default=7,
        help="Warn (don't fail) when a deadline is N days or fewer away (default: 7)",
    )
    args = parser.parse_args()

    workflow_dir = Path(args.workflows)
    if not workflow_dir.is_dir():
        print(f"workflows dir not found: {workflow_dir}", file=sys.stderr)
        return 2

    markers = scan_workflows(workflow_dir)
    if not markers:
        print("No REPORT-ONLY-UNTIL markers found. Nothing to enforce.")
        return 0

    today = dt.date.today()
    expired: list[tuple[Path, int, dt.date, str]] = []
    upcoming: list[tuple[Path, int, dt.date, str]] = []
    future: list[tuple[Path, int, dt.date, str]] = []

    for entry in markers:
        _, _, d, _ = entry
        days = (d - today).days
        if days < 0:
            expired.append(entry)
        elif days <= args.warn_days:
            upcoming.append(entry)
        else:
            future.append(entry)

    print(f"CI deadline check — {today.isoformat()} (today)")
    print(f"  Total markers:  {len(markers)}")
    print(f"  Expired:        {len(expired)}")
    print(f"  Upcoming (≤{args.warn_days}d): {len(upcoming)}")
    print(f"  Future:         {len(future)}")
    print()

    if upcoming:
        print("UPCOMING deadlines (act soon):")
        for f, ln, d, note in sorted(upcoming, key=lambda x: x[2]):
            days = (d - today).days
            extra = f" — {note}" if note else ""
            print(f"  ⚠  {f}:{ln}  {d.isoformat()}  ({days} day(s) left){extra}")
            print(f"     ::warning file={f},line={ln}::Report-only gate deadline in {days} day(s)")
        print()

    if future:
        print("Future deadlines:")
        for f, ln, d, note in sorted(future, key=lambda x: x[2]):
            days = (d - today).days
            extra = f" — {note}" if note else ""
            print(f"  ✓  {f}:{ln}  {d.isoformat()}  ({days} day(s) out){extra}")
        print()

    if expired:
        print("EXPIRED deadlines (this is what fails the build):")
        for f, ln, d, note in sorted(expired, key=lambda x: x[2]):
            days_over = (today - d).days
            extra = f" — {note}" if note else ""
            print(f"  ✗  {f}:{ln}  {d.isoformat()}  ({days_over} day(s) overdue){extra}")
            print(
                f"     ::error file={f},line={ln}::Report-only deadline lapsed {days_over} day(s) ago. Flip to blocking, fix the gate, or extend the deadline."
            )
        print()
        print("Remediation options for each expired marker:")
        print("  1. Fix the underlying issues, then flip the gate to blocking")
        print("     (remove --report-only / change `exit 0` to `exit $fail`).")
        print("  2. Extend the deadline by editing the date in the YAML")
        print("     (commit message: 'chore(ci): extend deadline for <gate> to YYYY-MM-DD because <reason>').")
        print("  3. Remove the gate entirely if it's no longer needed.")
        return 1

    print("All deadlines are in the future. Build passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
