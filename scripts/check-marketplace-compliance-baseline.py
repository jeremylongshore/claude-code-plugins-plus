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


def metadata_drift(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Return baseline-contract changes that require a conscious re-baseline.

    Triple comparison alone cannot distinguish an intentional validator-rule
    change from legacy debt.  The emitted schema version and rule inventory are
    therefore part of the pinned contract: either changing them must fail the
    ratchet until the dedicated baseline-capture transaction has been reviewed.
    """
    errors: list[str] = []
    baseline_schema = baseline.get("schema_version")
    current_schema = current.get("schema_version")
    if not isinstance(baseline_schema, str) or not isinstance(current_schema, str):
        errors.append("baseline and live payload must declare string schema_version values")
    elif baseline_schema != current_schema:
        errors.append(f"schema_version drift: baseline={baseline_schema}, live={current_schema}")

    baseline_rules = baseline.get("rule_inventory")
    current_rules = current.get("rule_inventory")
    if not isinstance(baseline_rules, list) or not all(isinstance(rule, str) for rule in baseline_rules):
        errors.append("baseline rule_inventory must be a list of rule ids")
    elif not isinstance(current_rules, list) or not all(isinstance(rule, str) for rule in current_rules):
        errors.append("live rule_inventory must be a list of rule ids")
    elif set(baseline_rules) != set(current_rules):
        added = sorted(set(current_rules) - set(baseline_rules))
        removed = sorted(set(baseline_rules) - set(current_rules))
        if added:
            errors.append(f"unknown live rule id(s): {', '.join(added)}")
        if removed:
            errors.append(f"baseline rule id(s) absent from live inventory: {', '.join(removed)}")
    return errors


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
        drift = metadata_drift(baseline, current)
        newcomers = compare(baseline, current)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"marketplace-compliance-ratchet: ERROR: {error}", file=sys.stderr)
        return 2

    if drift:
        print("marketplace-compliance-ratchet: FAIL — baseline contract drift:", file=sys.stderr)
        for error in drift:
            print(f"  {error}", file=sys.stderr)
        return 1

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
