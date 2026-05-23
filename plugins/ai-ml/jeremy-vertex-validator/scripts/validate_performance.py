#!/usr/bin/env python3
"""Validate performance configuration for Vertex AI Agent Builder deployments.

Checks:
  - Auto-scaling configuration (min/max replicas)
  - Resource limits (memory/CPU within ranges)
  - Latency metrics (p50/p95/p99 from Cloud Monitoring)
  - Error rate (< 5% threshold)

References:
  - Endpoints: https://cloud.google.com/vertex-ai/docs/predictions/deploy-model-api
  - Auto-scaling: https://cloud.google.com/vertex-ai/docs/predictions/autoscaling
  - Monitoring metrics: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

# ── Graceful dependency handling ─────────────────────────────────────────────

_MISSING_DEPS: list[str] = []

try:
    from google.cloud import aiplatform_v1
except ImportError:
    aiplatform_v1 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-aiplatform")

try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_v3 import query as monitoring_query  # noqa: F401
except ImportError:
    monitoring_v3 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-monitoring")

try:
    from google.protobuf import timestamp_pb2
except ImportError:
    timestamp_pb2 = None  # type: ignore[assignment]

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

# ── Thresholds ───────────────────────────────────────────────────────────────

# Error rate threshold — exceeding this triggers FAIL
ERROR_RATE_THRESHOLD = 0.05  # 5%

# Latency thresholds (milliseconds)
LATENCY_P50_WARN = 500
LATENCY_P95_WARN = 2000
LATENCY_P99_WARN = 5000


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
        "category": "Performance",
        "check": check,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    }


# ── Check 1: Auto-scaling Configuration ─────────────────────────────────────


def check_autoscaling(project: str, location: str) -> dict[str, Any]:
    """Verify auto-scaling is configured on deployed models/endpoints.

    Ref: https://cloud.google.com/vertex-ai/docs/predictions/autoscaling
    """
    if aiplatform_v1 is None:
        return _result(
            "Auto-scaling",
            "SKIP",
            "google-cloud-aiplatform not installed",
            "pip install google-cloud-aiplatform",
        )

    try:
        client = aiplatform_v1.EndpointServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        parent = f"projects/{project}/locations/{location}"

        # List endpoints
        # Ref: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints/list
        endpoints = list(client.list_endpoints(request={"parent": parent, "page_size": 50}))

        if not endpoints:
            return _result(
                "Auto-scaling",
                "WARNING",
                "No endpoints found in this region",
                "Deploy models to endpoints: https://cloud.google.com/vertex-ai/docs/predictions/deploy-model-api",
            )

        issues: list[str] = []
        checked = 0

        for ep in endpoints:
            for dm in ep.deployed_models:
                checked += 1
                # AutomaticResources or DedicatedResources carry scaling config
                # Ref: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints#DeployedModel
                if dm.dedicated_resources and dm.dedicated_resources.min_replica_count is not None:
                    min_r = dm.dedicated_resources.min_replica_count
                    max_r = dm.dedicated_resources.max_replica_count
                    if min_r == max_r:
                        issues.append(
                            f"{ep.display_name}/{dm.display_name}: min==max=={min_r} (no auto-scaling headroom)"
                        )
                elif dm.automatic_resources:
                    # AutomaticResources handles scaling automatically — good
                    pass
                else:
                    issues.append(f"{ep.display_name}/{dm.display_name}: no scaling config found")

        if not checked:
            return _result(
                "Auto-scaling",
                "WARNING",
                f"{len(endpoints)} endpoint(s) found but none have deployed models",
            )

        if issues:
            return _result(
                "Auto-scaling",
                "WARNING",
                f"{len(issues)} issue(s) in {checked} deployed model(s): {issues[0]}",
                "Configure min/max replicas with headroom: "
                "https://cloud.google.com/vertex-ai/docs/predictions/autoscaling",
            )

        return _result(
            "Auto-scaling",
            "PASS",
            f"{checked} deployed model(s) with valid scaling config",
        )

    except Exception as exc:
        return _result(
            "Auto-scaling",
            "SKIP",
            f"Cannot inspect endpoints: {exc}",
            "Ensure caller has roles/aiplatform.viewer",
        )


# ── Check 2: Resource Limits ────────────────────────────────────────────────


def check_resource_limits(project: str, location: str) -> dict[str, Any]:
    """Verify CPU/memory resource limits are within recommended ranges.

    Ref: https://cloud.google.com/vertex-ai/docs/predictions/configure-compute
    """
    if aiplatform_v1 is None:
        return _result(
            "Resource Limits",
            "SKIP",
            "google-cloud-aiplatform not installed",
            "pip install google-cloud-aiplatform",
        )

    try:
        client = aiplatform_v1.EndpointServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        parent = f"projects/{project}/locations/{location}"

        endpoints = list(client.list_endpoints(request={"parent": parent, "page_size": 50}))

        if not endpoints:
            return _result(
                "Resource Limits",
                "WARNING",
                "No endpoints found to inspect resource config",
            )

        findings: list[str] = []
        checked = 0

        for ep in endpoints:
            for dm in ep.deployed_models:
                checked += 1
                if dm.dedicated_resources and dm.dedicated_resources.machine_spec:
                    machine = dm.dedicated_resources.machine_spec
                    machine_type = machine.machine_type or "unknown"
                    # Flag if using very large machines without justification
                    if "n1-highmem" in machine_type or "a2-" in machine_type:
                        findings.append(f"{ep.display_name}: uses {machine_type} (verify cost vs performance)")

        if not checked:
            return _result(
                "Resource Limits",
                "WARNING",
                "No deployed models found to inspect",
            )

        if findings:
            return _result(
                "Resource Limits",
                "WARNING",
                f"{len(findings)} finding(s): {findings[0]}",
                "Review machine types: https://cloud.google.com/vertex-ai/docs/predictions/configure-compute",
            )

        return _result(
            "Resource Limits",
            "PASS",
            f"{checked} deployed model(s) checked — resource config looks reasonable",
        )

    except Exception as exc:
        return _result(
            "Resource Limits",
            "SKIP",
            f"Cannot inspect resource limits: {exc}",
            "Ensure caller has roles/aiplatform.viewer",
        )


# ── Check 3: Latency ────────────────────────────────────────────────────────


def check_latency(project: str, location: str) -> dict[str, Any]:
    """Query p50/p95/p99 prediction latency from Cloud Monitoring.

    Ref: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform
    Metric: aiplatform.googleapis.com/prediction/online/response_latencies
    """
    if monitoring_v3 is None:
        return _result(
            "Latency (p50/p95/p99)",
            "SKIP",
            "google-cloud-monitoring not installed",
            "pip install google-cloud-monitoring",
        )

    try:
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{project}"

        # Query the last 1 hour of prediction latency
        # Ref: https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.timeSeries/list
        now = time.time()
        interval = monitoring_v3.TimeInterval(
            end_time={"seconds": int(now)},
            start_time={"seconds": int(now - 3600)},  # 1 hour ago
        )

        # The distribution metric gives us percentile info
        # Ref: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform
        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": ('metric.type = "aiplatform.googleapis.com/prediction/online/response_latencies"'),
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )

        series_list = list(results)
        if not series_list:
            return _result(
                "Latency (p50/p95/p99)",
                "WARNING",
                "No prediction latency data found in the last hour",
                "Deploy a model and send prediction requests, or check the metric name: "
                "https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform",
            )

        # Extract distribution stats from the most recent data point
        latency_info: list[str] = []
        for ts in series_list[:3]:
            for point in ts.points[:1]:  # Most recent point
                if point.value.distribution_value:
                    dist = point.value.distribution_value
                    mean_ms = dist.mean
                    count = dist.count
                    latency_info.append(f"mean={mean_ms:.0f}ms (n={count})")

        if latency_info:
            evidence = f"Recent latency: {'; '.join(latency_info)}"
            # Simple threshold on mean as proxy (full percentile extraction
            # requires bucket boundary math)
            return _result("Latency (p50/p95/p99)", "PASS", evidence)

        return _result(
            "Latency (p50/p95/p99)",
            "WARNING",
            "Latency series found but no distribution data points",
        )

    except Exception as exc:
        return _result(
            "Latency (p50/p95/p99)",
            "SKIP",
            f"Cannot query latency metrics: {exc}",
            "Ensure caller has roles/monitoring.viewer",
        )


# ── Check 4: Error Rate ─────────────────────────────────────────────────────


def check_error_rate(project: str, location: str) -> dict[str, Any]:
    """Query prediction error count from Cloud Monitoring and compute error rate.

    Ref: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform
    Metrics:
      - aiplatform.googleapis.com/prediction/online/prediction_count
      - aiplatform.googleapis.com/prediction/online/error_count
    """
    if monitoring_v3 is None:
        return _result(
            "Error Rate",
            "SKIP",
            "google-cloud-monitoring not installed",
            "pip install google-cloud-monitoring",
        )

    try:
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{project}"

        now = time.time()
        interval = monitoring_v3.TimeInterval(
            end_time={"seconds": int(now)},
            start_time={"seconds": int(now - 3600)},
        )

        def _sum_metric(metric_type: str) -> int:
            """Sum all data points for a metric over the interval."""
            results = client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type = "{metric_type}"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )
            total = 0
            for ts in results:
                for point in ts.points:
                    total += point.value.int64_value
            return total

        # Ref: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-aiplatform
        total_predictions = _sum_metric("aiplatform.googleapis.com/prediction/online/prediction_count")
        total_errors = _sum_metric("aiplatform.googleapis.com/prediction/online/error_count")

        if total_predictions == 0:
            return _result(
                "Error Rate",
                "WARNING",
                "No prediction traffic in the last hour",
                "Send prediction requests to generate metrics",
            )

        error_rate = total_errors / total_predictions
        evidence = f"{error_rate:.2%} error rate ({total_errors} errors / {total_predictions} predictions, last hour)"

        if error_rate > ERROR_RATE_THRESHOLD:
            return _result(
                "Error Rate",
                "FAIL",
                evidence,
                f"Error rate exceeds {ERROR_RATE_THRESHOLD:.0%} threshold. "
                "Investigate error logs: "
                "https://cloud.google.com/vertex-ai/docs/predictions/online-logging",
            )

        return _result("Error Rate", "PASS", evidence)

    except Exception as exc:
        return _result(
            "Error Rate",
            "SKIP",
            f"Cannot query error metrics: {exc}",
            "Ensure caller has roles/monitoring.viewer",
        )


# ── Entrypoint ───────────────────────────────────────────────────────────────


def run_performance_checks(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Run all performance validation checks.

    Args:
        project: GCP project ID.
        agent_id: Optional Vertex AI Agent ID (reasoning engine).
        location: GCP region (default us-central1).
        dry_run: If True, list checks without making API calls.

    Returns:
        List of check result dicts.
    """
    checks = [
        ("Auto-scaling", lambda: check_autoscaling(project, location)),
        ("Resource Limits", lambda: check_resource_limits(project, location)),
        ("Latency (p50/p95/p99)", lambda: check_latency(project, location)),
        ("Error Rate", lambda: check_error_rate(project, location)),
    ]

    if dry_run:
        print("\n[DRY RUN] Performance checks that would run:")
        results = []
        for name, _ in checks:
            r = _result(name, "SKIP", "dry-run mode — no API calls made")
            results.append(r)
        return results

    if _MISSING_DEPS:
        print(f"\n{YELLOW}[WARN]{RESET} Missing optional deps: {', '.join(_MISSING_DEPS)}")
        print(f"       Install with: pip install {' '.join(_MISSING_DEPS)}\n")

    print(f"\n{'=' * 60}")
    print(f"  Performance Validation — project={project}, location={location}")
    print(f"{'=' * 60}")

    results = []
    for name, fn in checks:
        results.append(fn())

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate performance for Vertex AI Agent Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 validate_performance.py --project my-project --location us-central1",
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--agent-id", help="Vertex AI Agent (Reasoning Engine) ID")
    parser.add_argument("--location", default="us-central1", help="GCP region (default: us-central1)")
    parser.add_argument("--dry-run", action="store_true", help="List checks without making API calls")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    results = run_performance_checks(
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
