#!/usr/bin/env python3
"""Validate compliance posture for Vertex AI Agent Builder deployments.

Checks:
  - Audit logging (ADMIN_READ, DATA_READ, DATA_WRITE for aiplatform)
  - Data residency (region in approved list)
  - Backup/DR configuration

References:
  - Audit Logging: https://cloud.google.com/logging/docs/audit/configure-data-access
  - Data Residency: https://cloud.google.com/vertex-ai/docs/general/locations
  - Cloud Audit Logs: https://cloud.google.com/logging/docs/audit
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# ── Graceful dependency handling ─────────────────────────────────────────────

_MISSING_DEPS: list[str] = []

try:
    from google.cloud import resourcemanager_v3
except ImportError:
    resourcemanager_v3 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-resource-manager")

try:
    from google.cloud import logging as cloud_logging
except ImportError:
    cloud_logging = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-logging")

try:
    from google.cloud import aiplatform_v1
except ImportError:
    aiplatform_v1 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-aiplatform")

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

# ── Approved Regions ─────────────────────────────────────────────────────────
# Ref: https://cloud.google.com/vertex-ai/docs/general/locations
# Modify this set to match your organization's data residency requirements.
APPROVED_REGIONS_US = {
    "us-central1",
    "us-east1",
    "us-east4",
    "us-south1",
    "us-west1",
    "us-west2",
    "us-west3",
    "us-west4",
}

APPROVED_REGIONS_EU = {
    "europe-west1",
    "europe-west2",
    "europe-west3",
    "europe-west4",
    "europe-west6",
    "europe-west9",
}

APPROVED_REGIONS_APAC = {
    "asia-east1",
    "asia-east2",
    "asia-northeast1",
    "asia-northeast3",
    "asia-south1",
    "asia-southeast1",
    "asia-southeast2",
    "australia-southeast1",
}

# Default: all GA Vertex AI regions considered approved
ALL_APPROVED_REGIONS = APPROVED_REGIONS_US | APPROVED_REGIONS_EU | APPROVED_REGIONS_APAC

# Required audit log types for aiplatform.googleapis.com
# Ref: https://cloud.google.com/logging/docs/audit/configure-data-access
REQUIRED_AUDIT_LOG_TYPES = {"ADMIN_READ", "DATA_READ", "DATA_WRITE"}


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
        "category": "Compliance",
        "check": check,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    }


# ── Check 1: Audit Logging ──────────────────────────────────────────────────


def check_audit_logging(project: str) -> dict[str, Any]:
    """Verify audit logging is enabled for aiplatform.googleapis.com.

    Checks that ADMIN_READ, DATA_READ, and DATA_WRITE audit log types are
    enabled in the project's IAM policy audit configs.

    Ref: https://cloud.google.com/logging/docs/audit/configure-data-access
    The audit config is part of the IAM policy (getIamPolicy response).
    """
    if resourcemanager_v3 is None:
        return _result(
            "Audit Logging",
            "SKIP",
            "google-cloud-resource-manager not installed",
            "pip install google-cloud-resource-manager",
        )

    try:
        client = resourcemanager_v3.ProjectsClient()
        # GetIamPolicy includes audit configs
        # Ref: https://cloud.google.com/resource-manager/reference/rest/v3/projects/getIamPolicy
        request = {"resource": f"projects/{project}"}
        policy = client.get_iam_policy(request=request)

        # Check audit configs for aiplatform.googleapis.com
        # Ref: https://cloud.google.com/iam/docs/reference/rest/v1/Policy#AuditConfig
        aiplatform_audit = None
        for audit_config in policy.audit_configs:
            if audit_config.service in ("aiplatform.googleapis.com", "allServices"):
                aiplatform_audit = audit_config
                break

        if aiplatform_audit is None:
            return _result(
                "Audit Logging",
                "FAIL",
                "No audit logging configured for aiplatform.googleapis.com",
                "Enable audit logs: https://cloud.google.com/logging/docs/audit/configure-data-access#config-console",
            )

        # Extract enabled log types
        enabled_types = set()
        for log_config in aiplatform_audit.audit_log_configs:
            # log_type is an enum: 1=ADMIN_READ, 2=DATA_WRITE, 3=DATA_READ
            log_type_map = {1: "ADMIN_READ", 2: "DATA_WRITE", 3: "DATA_READ"}
            log_type_name = log_type_map.get(log_config.log_type, f"UNKNOWN({log_config.log_type})")
            enabled_types.add(log_type_name)

        missing = REQUIRED_AUDIT_LOG_TYPES - enabled_types

        if missing:
            return _result(
                "Audit Logging",
                "FAIL",
                f"Missing audit log types for aiplatform: {', '.join(sorted(missing))}. "
                f"Enabled: {', '.join(sorted(enabled_types))}",
                "Enable all three log types: https://cloud.google.com/logging/docs/audit/configure-data-access",
            )

        return _result(
            "Audit Logging",
            "PASS",
            f"All required audit log types enabled for "
            f"{'aiplatform.googleapis.com' if aiplatform_audit.service != 'allServices' else 'allServices'}: "
            f"{', '.join(sorted(enabled_types))}",
        )

    except Exception as exc:
        return _result(
            "Audit Logging",
            "SKIP",
            f"Cannot read IAM policy: {exc}",
            "Ensure caller has roles/iam.securityReviewer",
        )


# ── Check 2: Data Residency ─────────────────────────────────────────────────


def check_data_residency(project: str, location: str) -> dict[str, Any]:
    """Verify the deployment region is in the approved list.

    Ref: https://cloud.google.com/vertex-ai/docs/general/locations
    """
    if location in ALL_APPROVED_REGIONS:
        # Determine which geo the region belongs to
        geo = "US" if location in APPROVED_REGIONS_US else ("EU" if location in APPROVED_REGIONS_EU else "APAC")
        return _result(
            "Data Residency",
            "PASS",
            f"Region '{location}' is in approved {geo} region list",
        )

    return _result(
        "Data Residency",
        "FAIL",
        f"Region '{location}' is NOT in the approved region list",
        f"Approved regions: {', '.join(sorted(ALL_APPROVED_REGIONS))}. "
        "Update ALL_APPROVED_REGIONS in this script if your org approves additional regions.",
    )


# ── Check 3: Backup / DR Configuration ──────────────────────────────────────


def check_backup_dr(project: str, location: str) -> dict[str, Any]:
    """Check for backup and disaster recovery indicators.

    This checks for:
      1. Model artifacts in multiple regions (multi-region redundancy)
      2. Endpoint deployments across regions

    Ref: https://cloud.google.com/vertex-ai/docs/general/locations
    Note: Vertex AI does not have a built-in "backup" API — this check looks
    for multi-region deployment patterns as a proxy.
    """
    if aiplatform_v1 is None:
        return _result(
            "Backup / DR",
            "SKIP",
            "google-cloud-aiplatform not installed",
            "pip install google-cloud-aiplatform",
        )

    try:
        # Check if models exist in the primary region
        client = aiplatform_v1.ModelServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        parent = f"projects/{project}/locations/{location}"

        models = list(client.list_models(request={"parent": parent, "page_size": 20}))

        if not models:
            return _result(
                "Backup / DR",
                "WARNING",
                f"No models found in {location} — cannot assess DR posture",
                "Ensure critical models are deployed in multiple regions",
            )

        # Check model metadata for artifact URIs pointing to multi-region buckets
        multi_region_artifacts = 0
        for model in models:
            artifact_uri = model.artifact_uri or ""
            # Multi-region GCS buckets use prefixes like gs://us-*, gs://eu-*
            if any(prefix in artifact_uri for prefix in ["gs://us-", "gs://eu-", "gs://asia-"]):
                multi_region_artifacts += 1

        if multi_region_artifacts > 0:
            return _result(
                "Backup / DR",
                "PASS",
                f"{multi_region_artifacts}/{len(models)} model(s) use multi-region GCS buckets",
            )

        return _result(
            "Backup / DR",
            "WARNING",
            f"{len(models)} model(s) found but none appear to use multi-region storage. "
            "Single-region deployments have limited DR options",
            "Store artifacts in multi-region or dual-region GCS buckets. "
            "Consider deploying to multiple regions. "
            "See https://cloud.google.com/storage/docs/locations",
        )

    except Exception as exc:
        return _result(
            "Backup / DR",
            "SKIP",
            f"Cannot assess backup/DR: {exc}",
            "Ensure caller has roles/aiplatform.viewer",
        )


# ── Entrypoint ───────────────────────────────────────────────────────────────


def run_compliance_checks(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Run all compliance validation checks.

    Args:
        project: GCP project ID.
        agent_id: Optional Vertex AI Agent ID (reasoning engine).
        location: GCP region (default us-central1).
        dry_run: If True, list checks without making API calls.

    Returns:
        List of check result dicts.
    """
    checks = [
        ("Audit Logging", lambda: check_audit_logging(project)),
        ("Data Residency", lambda: check_data_residency(project, location)),
        ("Backup / DR", lambda: check_backup_dr(project, location)),
    ]

    if dry_run:
        print("\n[DRY RUN] Compliance checks that would run:")
        results = []
        for name, _ in checks:
            r = _result(name, "SKIP", "dry-run mode — no API calls made")
            results.append(r)
        return results

    if _MISSING_DEPS:
        print(f"\n{YELLOW}[WARN]{RESET} Missing optional deps: {', '.join(_MISSING_DEPS)}")
        print(f"       Install with: pip install {' '.join(_MISSING_DEPS)}\n")

    print(f"\n{'=' * 60}")
    print(f"  Compliance Validation — project={project}, location={location}")
    print(f"{'=' * 60}")

    results = []
    for name, fn in checks:
        results.append(fn())

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate compliance for Vertex AI Agent Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 validate_compliance.py --project my-project --location us-central1",
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--agent-id", help="Vertex AI Agent (Reasoning Engine) ID")
    parser.add_argument("--location", default="us-central1", help="GCP region (default: us-central1)")
    parser.add_argument("--dry-run", action="store_true", help="List checks without making API calls")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    results = run_compliance_checks(
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
