#!/usr/bin/env python3
"""Fail closed when marketplace compliance debt grows beyond the pinned baseline.

Blueprint 727 E6.3, phase R1: compare the validator's triple-keyed marketplace
findings with ``scripts/.marketplace-compliance-baseline.json``. Existing
baseline debt is tolerated; a new (path, rule, field) triple fails the gate.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "scripts" / ".marketplace-compliance-baseline.json"
VALIDATOR = ROOT / "scripts" / "validate-skills-schema.py"
BASELINE_PATH = "scripts/.marketplace-compliance-baseline.json"
CAPTURE_BRANCH_PREFIX = "automation/compliance-baseline-"


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


def metric_drift(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Return violations of the E6.7 monotone marketplace metrics.

    R2 prevents a fix from increasing the total number of validator errors.
    R4 prevents corpus dilution by requiring the A-plus-B share to hold or
    improve.  These checks deliberately compare the emitted totals rather than
    recomputing them here, keeping the canonical validator the sole owner of
    metric classification.
    """

    errors: list[str] = []
    baseline_totals = baseline.get("totals")
    current_totals = current.get("totals")
    if not isinstance(baseline_totals, dict) or not isinstance(current_totals, dict):
        return ["baseline and live payload must declare object totals"]

    for key in ("errors", "grade_A_plus_B_pct"):
        baseline_value = baseline_totals.get(key)
        current_value = current_totals.get(key)
        if isinstance(baseline_value, bool) or not isinstance(baseline_value, (int, float)):
            errors.append(f"baseline totals.{key} must be a finite number")
            continue
        if isinstance(current_value, bool) or not isinstance(current_value, (int, float)):
            errors.append(f"live totals.{key} must be a finite number")
            continue
        if not math.isfinite(baseline_value):
            errors.append(f"baseline totals.{key} must be a finite number")
            continue
        if not math.isfinite(current_value):
            errors.append(f"live totals.{key} must be a finite number")
            continue
        if baseline_value < 0 or current_value < 0:
            errors.append(f"totals.{key} must be non-negative")
            continue
        if key == "errors" and current_value > baseline_value:
            errors.append(
                f"totals.errors increased: baseline={baseline_value:g}, live={current_value:g}"
            )
        elif key == "grade_A_plus_B_pct" and current_value < baseline_value:
            errors.append(
                "totals.grade_A_plus_B_pct fell: "
                f"baseline={baseline_value:g}, live={current_value:g}"
            )
    return errors


def baseline_growth_error(
    base: dict[str, Any], current: dict[str, Any], changed_paths: set[str], head_ref: str
) -> str | None:
    """Return an E6.6 violation when a regular PR grows pinned debt."""
    growth = entries(current) - entries(base)
    if not growth:
        return None
    if changed_paths != {BASELINE_PATH}:
        return "baseline growth may only occur in a one-file baseline-only pull request"
    if not head_ref.startswith(CAPTURE_BRANCH_PREFIX):
        return f"baseline growth may only occur on the dedicated CI capture branch ({CAPTURE_BRANCH_PREFIX}<run-id>)"
    return None


def baseline_at_ref(repo_root: Path, ref: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{BASELINE_PATH}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"could not read baseline at {ref}")
    return json.loads(result.stdout)


def changed_paths_since(repo_root: Path, base_ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"could not diff against {base_ref}")
    return {path for path in result.stdout.splitlines() if path}


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
    parser.add_argument("--base", help="git base ref for the E6.6 PR baseline-growth check")
    parser.add_argument("--head-ref", default="", help="PR head branch for the E6.6 growth check")
    parser.add_argument(
        "--check-growth-only",
        action="store_true",
        help="check a PR diff for unauthorized baseline growth without emitting the corpus",
    )
    args = parser.parse_args()

    try:
        repo_root = args.repo_root.resolve()
        if args.check_growth_only:
            if not args.base:
                raise ValueError("--check-growth-only requires --base")
            baseline = baseline_at_ref(repo_root, args.base)
            current = json.loads(args.baseline.read_text(encoding="utf-8"))
            violation = baseline_growth_error(
                baseline,
                current,
                changed_paths_since(repo_root, args.base),
                args.head_ref,
            )
            if violation:
                print(f"marketplace-compliance-ratchet: FAIL — {violation}", file=sys.stderr)
                return 1
            print("marketplace-compliance-ratchet: OK (no unauthorized baseline growth)")
            return 0
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        current = json.loads(args.current.read_text(encoding="utf-8")) if args.current else emit_current(repo_root)
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

    metric_failures = metric_drift(baseline, current)
    if metric_failures:
        print("marketplace-compliance-ratchet: FAIL — non-monotone marketplace metrics:", file=sys.stderr)
        for error in metric_failures:
            print(f"  {error}", file=sys.stderr)
        return 1

    if newcomers:
        print("marketplace-compliance-ratchet: FAIL — new marketplace debt:", file=sys.stderr)
        for entry in newcomers:
            print(f"  {entry}", file=sys.stderr)
        return 1

    print(f"marketplace-compliance-ratchet: OK ({len(entries(current))} live triples; no entries outside baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
