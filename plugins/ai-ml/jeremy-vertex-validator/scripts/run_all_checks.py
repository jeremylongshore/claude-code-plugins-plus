#!/usr/bin/env python3
"""Orchestrator for all Vertex AI Agent Builder validation checks.

Runs Security, Monitoring, Performance, and Compliance validators,
produces a combined JSON report, and calculates a weighted score.

Weights:
  - Security:       30%
  - Monitoring:     20%
  - Performance:    25%
  - Compliance:     15%
  - Best Practices: 10%

Usage:
  python3 run_all_checks.py --project my-project
  python3 run_all_checks.py --project my-project --dry-run
  python3 run_all_checks.py --project my-project --output report.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

# ── Colors ───────────────────────────────────────────────────────────────────

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── Import validators (graceful) ─────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

_import_errors: list[str] = []

try:
    from validate_security import run_security_checks
except ImportError as exc:
    run_security_checks = None  # type: ignore[assignment]
    _import_errors.append(f"validate_security: {exc}")

try:
    from validate_monitoring import run_monitoring_checks
except ImportError as exc:
    run_monitoring_checks = None  # type: ignore[assignment]
    _import_errors.append(f"validate_monitoring: {exc}")

try:
    from validate_performance import run_performance_checks
except ImportError as exc:
    run_performance_checks = None  # type: ignore[assignment]
    _import_errors.append(f"validate_performance: {exc}")

try:
    from validate_compliance import run_compliance_checks
except ImportError as exc:
    run_compliance_checks = None  # type: ignore[assignment]
    _import_errors.append(f"validate_compliance: {exc}")

# ── Scoring ──────────────────────────────────────────────────────────────────

CATEGORY_WEIGHTS = {
    "Security": 0.30,
    "Monitoring": 0.20,
    "Performance": 0.25,
    "Compliance": 0.15,
    "Best Practices": 0.10,
}

# Points awarded per status
STATUS_POINTS = {
    "PASS": 1.0,
    "WARNING": 0.5,
    "FAIL": 0.0,
    "SKIP": None,  # Not counted — excluded from scoring
}


def compute_category_score(results: list[dict[str, Any]], category: str) -> float | None:
    """Compute score for a single category (0.0 to 1.0).

    SKIP results are excluded from scoring. Returns None if all checks
    were skipped.
    """
    category_results = [r for r in results if r["category"] == category]
    if not category_results:
        return None

    scored = []
    for r in category_results:
        points = STATUS_POINTS.get(r["status"])
        if points is not None:
            scored.append(points)

    if not scored:
        return None  # All skipped

    return sum(scored) / len(scored)


def compute_weighted_score(results: list[dict[str, Any]]) -> tuple[float, dict[str, float | None]]:
    """Compute the overall weighted score across all categories.

    Returns:
        Tuple of (weighted_score, category_scores_dict).
        weighted_score is 0-100.
    """
    category_scores: dict[str, float | None] = {}
    weighted_sum = 0.0
    weight_sum = 0.0

    for category, weight in CATEGORY_WEIGHTS.items():
        score = compute_category_score(results, category)
        category_scores[category] = score
        if score is not None:
            weighted_sum += score * weight
            weight_sum += weight

    # Normalize if some categories were entirely skipped
    if weight_sum > 0:
        overall = (weighted_sum / weight_sum) * 100
    else:
        overall = 0.0

    return overall, category_scores


# ── Best Practices (lightweight inline checks) ──────────────────────────────


def run_best_practices_checks(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Lightweight best-practice checks that don't need external APIs.

    These supplement the main validator categories.
    """
    results: list[dict[str, Any]] = []

    def _result(check: str, status: str, evidence: str, remediation: str = "") -> dict[str, Any]:
        color = {"PASS": GREEN, "FAIL": RED, "WARNING": YELLOW, "SKIP": YELLOW}.get(status, RESET)
        print(f"  {color}[{status}]{RESET} {check}: {evidence}")
        r = {
            "category": "Best Practices",
            "check": check,
            "status": status,
            "evidence": evidence,
            "remediation": remediation,
        }
        results.append(r)
        return r

    if dry_run:
        print("\n[DRY RUN] Best Practices checks that would run:")
        _result("Project ID Format", "SKIP", "dry-run mode — no checks made")
        _result("Region Selection", "SKIP", "dry-run mode — no checks made")
        return results

    print(f"\n{'=' * 60}")
    print(f"  Best Practices — project={project}")
    print(f"{'=' * 60}")

    # Check 1: Project ID naming convention
    # Ref: https://cloud.google.com/resource-manager/docs/creating-managing-projects
    if project.startswith("project-") or project == "my-project":
        _result(
            "Project ID Format",
            "WARNING",
            f"Project ID '{project}' looks like a placeholder",
            "Use a descriptive project ID that identifies the environment (e.g., myapp-prod)",
        )
    elif "-prod" in project or "-production" in project:
        _result(
            "Project ID Format",
            "PASS",
            f"Project ID '{project}' includes environment identifier",
        )
    else:
        _result(
            "Project ID Format",
            "PASS",
            f"Project ID '{project}' format is acceptable",
        )

    # Check 2: Region selection
    # Ref: https://cloud.google.com/vertex-ai/docs/general/locations
    tier1_regions = {"us-central1", "europe-west4", "asia-east1"}
    if location in tier1_regions:
        _result(
            "Region Selection",
            "PASS",
            f"Region '{location}' is a Tier 1 Vertex AI region (full feature availability)",
        )
    else:
        _result(
            "Region Selection",
            "WARNING",
            f"Region '{location}' may not have all Vertex AI features available",
            "Consider us-central1, europe-west4, or asia-east1 for full feature coverage: "
            "https://cloud.google.com/vertex-ai/docs/general/locations",
        )

    return results


# ── Summary Table ────────────────────────────────────────────────────────────


def print_summary(
    overall_score: float,
    category_scores: dict[str, float | None],
    results: list[dict[str, Any]],
) -> None:
    """Print a colored summary table to stdout."""
    # Count statuses
    status_counts = {"PASS": 0, "FAIL": 0, "WARNING": 0, "SKIP": 0}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"{BOLD}  VALIDATION SUMMARY{RESET}")
    print(f"{'=' * 60}")
    print()

    # Category scores
    print(f"  {'Category':<20} {'Weight':<10} {'Score':<10}")
    print(f"  {'-' * 40}")
    for category, weight in CATEGORY_WEIGHTS.items():
        score = category_scores.get(category)
        weight_pct = f"{weight:.0%}"
        if score is None:
            score_str = f"{YELLOW}N/A{RESET}"
        elif score >= 0.8:
            score_str = f"{GREEN}{score:.0%}{RESET}"
        elif score >= 0.5:
            score_str = f"{YELLOW}{score:.0%}{RESET}"
        else:
            score_str = f"{RED}{score:.0%}{RESET}"
        print(f"  {category:<20} {weight_pct:<10} {score_str}")

    print()

    # Overall score
    if overall_score >= 80:
        score_color = GREEN
    elif overall_score >= 50:
        score_color = YELLOW
    else:
        score_color = RED

    print(f"  {BOLD}Overall Score: {score_color}{overall_score:.1f}/100{RESET}")
    print()

    # Status counts
    print(
        f"  {GREEN}PASS: {status_counts['PASS']}{RESET}  "
        f"{YELLOW}WARN: {status_counts['WARNING']}{RESET}  "
        f"{RED}FAIL: {status_counts['FAIL']}{RESET}  "
        f"SKIP: {status_counts['SKIP']}  "
        f"Total: {total}"
    )
    print(f"{'=' * 60}\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def run_all(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
    output: str | None = None,
) -> dict[str, Any]:
    """Run all validators and produce a combined report.

    Args:
        project: GCP project ID.
        agent_id: Optional Vertex AI Agent ID.
        location: GCP region.
        dry_run: If True, list checks without making API calls.
        output: Optional file path to write JSON report.

    Returns:
        Combined report dict.
    """
    if _import_errors:
        print(f"\n{YELLOW}[WARN]{RESET} Some validators could not be imported:")
        for err in _import_errors:
            print(f"       - {err}")
        print()

    print(f"\n{BOLD}{CYAN}Vertex AI Agent Builder — Full Validation Suite{RESET}")
    print(f"  Project:  {project}")
    print(f"  Location: {location}")
    print(f"  Agent:    {agent_id or '(not specified)'}")
    print(f"  Mode:     {'DRY RUN' if dry_run else 'LIVE'}")

    all_results: list[dict[str, Any]] = []

    # Run each validator category
    validators = [
        ("Security", run_security_checks),
        ("Monitoring", run_monitoring_checks),
        ("Performance", run_performance_checks),
        ("Compliance", run_compliance_checks),
    ]

    for name, fn in validators:
        if fn is None:
            print(f"\n{RED}[SKIP]{RESET} {name} — validator failed to import")
            continue
        try:
            results = fn(
                project=project,
                agent_id=agent_id,
                location=location,
                dry_run=dry_run,
            )
            all_results.extend(results)
        except Exception as exc:
            print(f"\n{RED}[ERROR]{RESET} {name} validator crashed: {exc}")

    # Best Practices (inline)
    bp_results = run_best_practices_checks(
        project=project,
        agent_id=agent_id,
        location=location,
        dry_run=dry_run,
    )
    all_results.extend(bp_results)

    # Compute scores
    overall_score, category_scores = compute_weighted_score(all_results)

    # Print summary
    print_summary(overall_score, category_scores, all_results)

    # Build report
    report = {
        "project": project,
        "location": location,
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "overall_score": round(overall_score, 1),
        "category_scores": {k: round(v, 3) if v is not None else None for k, v in category_scores.items()},
        "weights": CATEGORY_WEIGHTS,
        "checks": all_results,
        "summary": {
            "total": len(all_results),
            "pass": sum(1 for r in all_results if r["status"] == "PASS"),
            "fail": sum(1 for r in all_results if r["status"] == "FAIL"),
            "warning": sum(1 for r in all_results if r["status"] == "WARNING"),
            "skip": sum(1 for r in all_results if r["status"] == "SKIP"),
        },
    }

    # Write output file
    if output:
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"{GREEN}[OK]{RESET} Report written to {output}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run all Vertex AI Agent Builder validation checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Dry run (no API calls)
  python3 run_all_checks.py --project my-project --dry-run

  # Full validation
  python3 run_all_checks.py --project my-project --agent-id 12345

  # Save JSON report
  python3 run_all_checks.py --project my-project --output report.json

  # Specific region
  python3 run_all_checks.py --project my-project --location europe-west4

Weights:
  Security 30% | Performance 25% | Monitoring 20% | Compliance 15% | Best Practices 10%
""",
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--agent-id", help="Vertex AI Agent (Reasoning Engine) ID")
    parser.add_argument("--location", default="us-central1", help="GCP region (default: us-central1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be checked without making API calls")
    parser.add_argument("--output", metavar="FILE", help="Write JSON report to file")
    parser.add_argument("--json", action="store_true", help="Print full JSON report to stdout")

    args = parser.parse_args()

    # When --json is used, suppress human-readable output
    if args.json:
        import io
        import contextlib

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            report = run_all(
                project=args.project,
                agent_id=args.agent_id,
                location=args.location,
                dry_run=args.dry_run,
                output=args.output,
            )
        print(json.dumps(report, indent=2))
    else:
        report = run_all(
            project=args.project,
            agent_id=args.agent_id,
            location=args.location,
            dry_run=args.dry_run,
            output=args.output,
        )

    # Exit code: 1 if any FAIL, 2 if all SKIP
    fail_count = report["summary"]["fail"]
    skip_count = report["summary"]["skip"]
    total = report["summary"]["total"]

    if fail_count > 0:
        sys.exit(1)
    elif skip_count == total:
        sys.exit(2)


if __name__ == "__main__":
    main()
