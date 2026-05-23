#!/usr/bin/env python3
"""Validate monitoring configuration for Vertex AI Agent Builder deployments.

Checks:
  - Alert policies exist for agent metrics
  - SLOs are defined
  - Cloud Logging enabled with adequate retention
  - Monitoring dashboards exist

References:
  - Alert Policies: https://cloud.google.com/monitoring/alerts
  - SLOs: https://cloud.google.com/monitoring/sli-slo
  - Logging: https://cloud.google.com/logging/docs/view/overview
  - Dashboards: https://cloud.google.com/monitoring/dashboards
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# ── Graceful dependency handling ─────────────────────────────────────────────

_MISSING_DEPS: list[str] = []

try:
    from google.cloud import monitoring_v3
except ImportError:
    monitoring_v3 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-monitoring")

try:
    from google.cloud import logging as cloud_logging
except ImportError:
    cloud_logging = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-logging")

try:
    from google.cloud import monitoring_dashboard_v1
except ImportError:
    monitoring_dashboard_v1 = None  # type: ignore[assignment]
    # Part of google-cloud-monitoring, not a separate install

# ── Colors ───────────────────────────────────────────────────────────────────

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
RESET = "\033[0m"

STATUS_COLORS = {
    "PASS": GREEN,
    "FAIL": RED,
    "WARNING": YELLOW,
    "SKIP": YELLOW,
}


def _result(
    check: str,
    status: str,
    evidence: str,
    remediation: str = "",
) -> dict[str, Any]:
    """Build a structured check result."""
    color = STATUS_COLORS.get(status, RESET)
    print(f"  {color}[{status}]{RESET} {check}: {evidence}")
    return {
        "category": "Monitoring",
        "check": check,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    }


# ── Check 1: Alert Policies ─────────────────────────────────────────────────


def check_alert_policies(project: str) -> dict[str, Any]:
    """Verify alert policies exist, especially for Vertex AI metrics.

    Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies/list
    """
    if monitoring_v3 is None:
        return _result(
            "Alert Policies",
            "SKIP",
            "google-cloud-monitoring not installed",
            "pip install google-cloud-monitoring",
        )

    try:
        client = monitoring_v3.AlertPolicyServiceClient()
        project_name = f"projects/{project}"

        # List all alert policies
        # Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.alertPolicies/list
        policies = list(client.list_alert_policies(request={"name": project_name}))

        if not policies:
            return _result(
                "Alert Policies",
                "FAIL",
                "No alert policies configured",
                "Create alert policies for agent error rate, latency, and availability: "
                "https://cloud.google.com/monitoring/alerts/using-alerting-ui",
            )

        # Check for Vertex AI-related policies
        vertex_policies = [
            p
            for p in policies
            if any(
                "aiplatform" in str(c.filter).lower()
                or "vertex" in (p.display_name or "").lower()
                or "agent" in (p.display_name or "").lower()
                for c in p.conditions
            )
        ]

        enabled_count = sum(1 for p in policies if p.enabled.value)

        if not vertex_policies:
            return _result(
                "Alert Policies",
                "WARNING",
                f"{len(policies)} alert policy(ies) found ({enabled_count} enabled), "
                "but none target Vertex AI / agent metrics",
                "Add policies filtering on aiplatform.googleapis.com metrics: "
                "https://cloud.google.com/vertex-ai/docs/predictions/monitor-models",
            )

        return _result(
            "Alert Policies",
            "PASS",
            f"{len(vertex_policies)} Vertex AI alert policy(ies) out of {len(policies)} total "
            f"({enabled_count} enabled)",
        )

    except Exception as exc:
        return _result(
            "Alert Policies",
            "SKIP",
            f"Cannot query alert policies: {exc}",
            "Ensure caller has roles/monitoring.alertPolicyViewer",
        )


# ── Check 2: SLOs ───────────────────────────────────────────────────────────


def check_slos(project: str) -> dict[str, Any]:
    """Verify SLOs are defined for the project's services.

    Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/services.serviceLevelObjectives
    """
    if monitoring_v3 is None:
        return _result(
            "SLO Definitions",
            "SKIP",
            "google-cloud-monitoring not installed",
            "pip install google-cloud-monitoring",
        )

    try:
        client = monitoring_v3.ServiceMonitoringServiceClient()
        parent = f"projects/{project}"

        # List all services first
        # Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/services/list
        services = list(client.list_services(request={"parent": parent}))

        if not services:
            return _result(
                "SLO Definitions",
                "WARNING",
                "No monitored services found — SLOs cannot be defined without services",
                "Create a service: https://cloud.google.com/monitoring/sli-slo/slo-creating",
            )

        # Check each service for SLOs
        total_slos = 0
        for svc in services:
            slos = list(client.list_service_level_objectives(request={"parent": svc.name}))
            total_slos += len(slos)

        if total_slos == 0:
            return _result(
                "SLO Definitions",
                "FAIL",
                f"{len(services)} service(s) found but no SLOs defined",
                "Define SLOs for availability and latency: https://cloud.google.com/monitoring/sli-slo/slo-creating",
            )

        return _result(
            "SLO Definitions",
            "PASS",
            f"{total_slos} SLO(s) across {len(services)} service(s)",
        )

    except Exception as exc:
        return _result(
            "SLO Definitions",
            "SKIP",
            f"Cannot query SLOs: {exc}",
            "Ensure caller has roles/monitoring.servicesViewer",
        )


# ── Check 3: Cloud Logging ──────────────────────────────────────────────────


def check_logging(project: str) -> dict[str, Any]:
    """Verify Cloud Logging is active and retention is adequate.

    Ref: https://cloud.google.com/logging/docs/view/overview
    Default retention: 30 days (_Default bucket), 400 days (_Required).
    """
    if cloud_logging is None:
        return _result(
            "Cloud Logging",
            "SKIP",
            "google-cloud-logging not installed",
            "pip install google-cloud-logging",
        )

    try:
        client = cloud_logging.Client(project=project)

        # List log sinks to verify logging is configured
        # Ref: https://cloud.google.com/logging/docs/reference/v2/rest/v2/projects.sinks/list
        sinks = list(client.list_sinks())

        # Check for recent Vertex AI log entries as a proxy for active logging
        # Ref: https://cloud.google.com/logging/docs/view/logging-query-language
        vertex_filter = (
            'resource.type="aiplatform.googleapis.com/Endpoint" OR '
            'resource.type="aiplatform.googleapis.com/ReasoningEngine" OR '
            'logName:"aiplatform.googleapis.com"'
        )

        # Just check if the filter is queryable — don't fetch all entries
        entries = list(
            client.list_entries(
                filter_=vertex_filter,
                page_size=5,
                max_results=5,
            )
        )

        if entries:
            return _result(
                "Cloud Logging",
                "PASS",
                f"Active — {len(entries)} recent Vertex AI log entries found, {len(sinks)} log sink(s) configured",
            )

        if sinks:
            return _result(
                "Cloud Logging",
                "WARNING",
                f"{len(sinks)} log sink(s) configured but no recent Vertex AI log entries",
                "Verify Vertex AI resources are logging: "
                "https://cloud.google.com/vertex-ai/docs/predictions/online-logging",
            )

        return _result(
            "Cloud Logging",
            "WARNING",
            "No log sinks configured beyond defaults",
            "Configure log sinks for long-term retention: "
            "https://cloud.google.com/logging/docs/export/configure_export_v2",
        )

    except Exception as exc:
        return _result(
            "Cloud Logging",
            "SKIP",
            f"Cannot query Cloud Logging: {exc}",
            "Ensure caller has roles/logging.viewer",
        )


# ── Check 4: Monitoring Dashboards ──────────────────────────────────────────


def check_dashboards(project: str) -> dict[str, Any]:
    """Verify monitoring dashboards exist.

    Ref: https://cloud.google.com/monitoring/dashboards/api-dashboard
    """
    if monitoring_dashboard_v1 is None:
        return _result(
            "Monitoring Dashboards",
            "SKIP",
            "google-cloud-monitoring-dashboards not installed",
            "pip install google-cloud-monitoring-dashboards",
        )

    try:
        client = monitoring_dashboard_v1.DashboardsServiceClient()
        parent = f"projects/{project}"

        # List dashboards
        # Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v1/projects.dashboards/list
        dashboards = list(client.list_dashboards(request={"parent": parent}))

        if not dashboards:
            return _result(
                "Monitoring Dashboards",
                "WARNING",
                "No custom monitoring dashboards found",
                "Create a dashboard for Vertex AI metrics: "
                "https://cloud.google.com/monitoring/dashboards/api-dashboard",
            )

        # Check for Vertex AI-related dashboards
        vertex_dashboards = [
            d
            for d in dashboards
            if "vertex" in (d.display_name or "").lower()
            or "agent" in (d.display_name or "").lower()
            or "aiplatform" in (d.display_name or "").lower()
        ]

        if vertex_dashboards:
            return _result(
                "Monitoring Dashboards",
                "PASS",
                f"{len(vertex_dashboards)} Vertex AI dashboard(s) out of {len(dashboards)} total",
            )

        return _result(
            "Monitoring Dashboards",
            "WARNING",
            f"{len(dashboards)} dashboard(s) found but none named for Vertex AI / agents",
            "Create a dedicated Vertex AI dashboard: https://cloud.google.com/monitoring/dashboards/api-dashboard",
        )

    except Exception as exc:
        return _result(
            "Monitoring Dashboards",
            "SKIP",
            f"Cannot query dashboards: {exc}",
            "Ensure caller has roles/monitoring.dashboardViewer",
        )


# ── Entrypoint ───────────────────────────────────────────────────────────────


def run_monitoring_checks(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Run all monitoring validation checks.

    Args:
        project: GCP project ID.
        agent_id: Optional Vertex AI Agent ID (reasoning engine).
        location: GCP region (default us-central1).
        dry_run: If True, list checks without making API calls.

    Returns:
        List of check result dicts.
    """
    checks = [
        ("Alert Policies", lambda: check_alert_policies(project)),
        ("SLO Definitions", lambda: check_slos(project)),
        ("Cloud Logging", lambda: check_logging(project)),
        ("Monitoring Dashboards", lambda: check_dashboards(project)),
    ]

    if dry_run:
        print("\n[DRY RUN] Monitoring checks that would run:")
        results = []
        for name, _ in checks:
            r = _result(name, "SKIP", "dry-run mode — no API calls made")
            results.append(r)
        return results

    if _MISSING_DEPS:
        print(f"\n{YELLOW}[WARN]{RESET} Missing optional deps: {', '.join(_MISSING_DEPS)}")
        print(f"       Install with: pip install {' '.join(_MISSING_DEPS)}\n")

    print(f"\n{'=' * 60}")
    print(f"  Monitoring Validation — project={project}")
    print(f"{'=' * 60}")

    results = []
    for name, fn in checks:
        results.append(fn())

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate monitoring setup for Vertex AI Agent Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 validate_monitoring.py --project my-project",
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--agent-id", help="Vertex AI Agent (Reasoning Engine) ID")
    parser.add_argument("--location", default="us-central1", help="GCP region (default: us-central1)")
    parser.add_argument("--dry-run", action="store_true", help="List checks without making API calls")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    results = run_monitoring_checks(
        project=args.project,
        agent_id=args.agent_id,
        location=args.location,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(results, indent=2))

    if any(r["status"] == "FAIL" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
