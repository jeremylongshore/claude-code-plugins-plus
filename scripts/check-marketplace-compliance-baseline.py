#!/usr/bin/env python3
"""Fail closed when marketplace compliance debt grows beyond the pinned baseline.

Blueprint 727 E6.3, phase R1: compare the validator's triple-keyed marketplace
findings with ``scripts/.marketplace-compliance-baseline.json``. Existing
baseline debt is tolerated; a new (path, rule, field) triple fails the gate.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "scripts" / ".marketplace-compliance-baseline.json"
VALIDATOR = ROOT / "scripts" / "validate-skills-schema.py"


def entries(payload: dict[str, Any]) -> set[str]:
    values = payload.get("entries")
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("baseline entries must be a list of triple-key strings")
    return set(values)


def compare(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Return sorted live triples absent from the pinned baseline."""
    return sorted(entries(current) - entries(baseline))


def emit_current(repo_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--emit-baseline", "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "marketplace baseline emitter failed")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--current", type=Path, help="test-only emitted baseline JSON")
    args = parser.parse_args()

    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        current = (
            json.loads(args.current.read_text(encoding="utf-8"))
            if args.current
            else emit_current(args.repo_root.resolve())
        )
        newcomers = compare(baseline, current)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"marketplace-compliance-ratchet: ERROR: {error}", file=sys.stderr)
        return 2

    if newcomers:
        print("marketplace-compliance-ratchet: FAIL — new marketplace debt:", file=sys.stderr)
        for entry in newcomers:
            print(f"  {entry}", file=sys.stderr)
        return 1

    print(
        "marketplace-compliance-ratchet: OK "
        f"({len(entries(current))} live triples; no entries outside baseline)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
