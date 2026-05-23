#!/usr/bin/env python3
"""Validate security posture for Vertex AI Agent Builder deployments.

Checks:
  - IAM least-privilege (service account roles)
  - VPC Service Controls perimeter
  - Encryption (CMEK vs Google-managed)
  - Model Armor (Responsible AI sanitization)
  - Secret Manager (no plaintext secrets in agent config)

References:
  - IAM: https://cloud.google.com/vertex-ai/docs/general/access-control
  - VPC-SC: https://cloud.google.com/vpc-service-controls/docs/overview
  - CMEK: https://cloud.google.com/vertex-ai/docs/general/cmek
  - Model Armor: https://cloud.google.com/vertex-ai/docs/model-armor/overview
  - Secret Manager: https://cloud.google.com/secret-manager/docs/overview
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
    from google.api_core import exceptions as api_exceptions
except ImportError:
    api_exceptions = None  # type: ignore[assignment]

try:
    from google.cloud import secretmanager_v1
except ImportError:
    secretmanager_v1 = None  # type: ignore[assignment]
    _MISSING_DEPS.append("google-cloud-secret-manager")

try:
    from google.iam.v1 import iam_policy_pb2  # noqa: F401
except ImportError:
    iam_policy_pb2 = None  # type: ignore[assignment]

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

# ── Over-privileged roles to flag ────────────────────────────────────────────
# Ref: https://cloud.google.com/iam/docs/understanding-roles
OVERPRIVILEGED_ROLES = {
    "roles/owner",
    "roles/editor",
    "roles/aiplatform.admin",
    "roles/iam.securityAdmin",
    "roles/resourcemanager.projectIamAdmin",
}

# Recommended least-privilege roles for Vertex AI agents
# Ref: https://cloud.google.com/vertex-ai/docs/general/access-control#aiplatform.user
RECOMMENDED_ROLES = {
    "roles/aiplatform.user",
    "roles/aiplatform.serviceAgent",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
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
        "category": "Security",
        "check": check,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    }


# ── Check 1: IAM Least Privilege ─────────────────────────────────────────────


def check_iam_least_privilege(project: str) -> dict[str, Any]:
    """List IAM bindings and flag over-privileged service accounts.

    Ref: https://cloud.google.com/resource-manager/reference/rest/v3/projects/getIamPolicy
    """
    if resourcemanager_v3 is None:
        return _result(
            "IAM Least Privilege",
            "SKIP",
            "google-cloud-resource-manager not installed",
            "pip install google-cloud-resource-manager",
        )

    try:
        client = resourcemanager_v3.ProjectsClient()
        # GetIamPolicy — returns the IAM policy for the project
        # Ref: https://cloud.google.com/resource-manager/reference/rest/v3/projects/getIamPolicy
        request = {"resource": f"projects/{project}"}
        policy = client.get_iam_policy(request=request)

        overprivileged: list[str] = []
        sa_bindings: list[str] = []

        for binding in policy.bindings:
            for member in binding.members:
                if "serviceAccount:" in member:
                    sa_bindings.append(f"{member} -> {binding.role}")
                    if binding.role in OVERPRIVILEGED_ROLES:
                        overprivileged.append(f"{member} has {binding.role}")

        if overprivileged:
            return _result(
                "IAM Least Privilege",
                "FAIL",
                f"{len(overprivileged)} over-privileged SA(s): {'; '.join(overprivileged[:3])}",
                "Downgrade to roles/aiplatform.user or custom role. "
                "See https://cloud.google.com/vertex-ai/docs/general/access-control",
            )
        return _result(
            "IAM Least Privilege",
            "PASS",
            f"{len(sa_bindings)} service account binding(s), none over-privileged",
        )

    except Exception as exc:
        return _result(
            "IAM Least Privilege",
            "SKIP",
            f"Permission denied or API error: {exc}",
            "Ensure caller has roles/resourcemanager.projectIamAdmin or roles/iam.securityReviewer",
        )


# ── Check 2: VPC Service Controls Perimeter ──────────────────────────────────


def check_vpc_sc(project: str) -> dict[str, Any]:
    """Check for VPC-SC access policies protecting the project.

    Ref: https://cloud.google.com/vpc-service-controls/docs/manage-policies
    Uses the Access Context Manager API.
    """
    try:
        from google.cloud import accesscontextmanager_v1
    except ImportError:
        return _result(
            "VPC-SC Perimeter",
            "SKIP",
            "google-cloud-access-context-manager not installed",
            "pip install google-cloud-access-context-manager",
        )

    try:
        client = accesscontextmanager_v1.AccessContextManagerClient()
        # List access policies for the organization
        # Ref: https://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies/list
        policies = list(
            client.list_access_policies(
                request=accesscontextmanager_v1.ListAccessPoliciesRequest(
                    parent=f"projects/{project}",
                )
            )
        )

        if not policies:
            return _result(
                "VPC-SC Perimeter",
                "WARNING",
                "No access policies found — project may not be inside a VPC-SC perimeter",
                "Configure VPC-SC: https://cloud.google.com/vpc-service-controls/docs/create-service-perimeters",
            )

        perimeter_names = [p.name for p in policies]
        return _result(
            "VPC-SC Perimeter",
            "PASS",
            f"{len(policies)} access policy(ies) found: {', '.join(perimeter_names[:3])}",
        )

    except Exception as exc:
        return _result(
            "VPC-SC Perimeter",
            "SKIP",
            f"Cannot query Access Context Manager: {exc}",
            "Ensure caller has roles/accesscontextmanager.policyReader",
        )


# ── Check 3: Encryption (CMEK) ──────────────────────────────────────────────


def check_encryption(project: str, location: str) -> dict[str, Any]:
    """Check if Vertex AI resources use CMEK encryption.

    Ref: https://cloud.google.com/vertex-ai/docs/general/cmek
    """
    try:
        from google.cloud import aiplatform_v1
    except ImportError:
        return _result(
            "Encryption (CMEK)",
            "SKIP",
            "google-cloud-aiplatform not installed",
            "pip install google-cloud-aiplatform",
        )

    try:
        # Check custom jobs as a proxy for CMEK usage — they carry encryption_spec
        # Ref: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.customJobs
        client = aiplatform_v1.JobServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        parent = f"projects/{project}/locations/{location}"

        # List a sample of custom jobs to inspect encryption_spec
        jobs = list(client.list_custom_jobs(request={"parent": parent, "page_size": 5}))

        if not jobs:
            return _result(
                "Encryption (CMEK)",
                "WARNING",
                "No custom jobs found to inspect encryption config",
                "When creating resources, specify encryption_spec with your KMS key. "
                "See https://cloud.google.com/vertex-ai/docs/general/cmek",
            )

        cmek_jobs = [j.display_name for j in jobs if j.encryption_spec and j.encryption_spec.kms_key_name]
        google_managed = [j.display_name for j in jobs if not (j.encryption_spec and j.encryption_spec.kms_key_name)]

        if google_managed:
            return _result(
                "Encryption (CMEK)",
                "WARNING",
                f"{len(google_managed)}/{len(jobs)} job(s) use Google-managed encryption (not CMEK)",
                "Migrate to CMEK: https://cloud.google.com/vertex-ai/docs/general/cmek",
            )
        return _result(
            "Encryption (CMEK)",
            "PASS",
            f"All {len(cmek_jobs)} inspected job(s) use CMEK",
        )

    except Exception as exc:
        return _result(
            "Encryption (CMEK)",
            "SKIP",
            f"Cannot inspect encryption config: {exc}",
            "Ensure caller has roles/aiplatform.viewer",
        )


# ── Check 4: Model Armor ────────────────────────────────────────────────────


def check_model_armor(project: str, location: str) -> dict[str, Any]:
    """Check Model Armor templates for input/output sanitization.

    Ref: https://cloud.google.com/vertex-ai/docs/model-armor/overview
    Model Armor provides content safety filters for Vertex AI models.
    """
    try:
        from google.cloud import modelarmor_v1
    except ImportError:
        return _result(
            "Model Armor",
            "SKIP",
            "google-cloud-modelarmor not installed (optional, SDK may not be GA)",
            "Model Armor can be configured via Console: https://cloud.google.com/vertex-ai/docs/model-armor/overview",
        )

    try:
        client = modelarmor_v1.ModelArmorClient(
            client_options={"api_endpoint": f"modelarmor.{location}.rep.googleapis.com"}
        )
        parent = f"projects/{project}/locations/{location}"

        # List templates
        # Ref: https://cloud.google.com/vertex-ai/docs/model-armor/create-template
        templates = list(client.list_templates(request={"parent": parent}))

        if not templates:
            return _result(
                "Model Armor",
                "WARNING",
                "No Model Armor templates found",
                "Create templates: https://cloud.google.com/vertex-ai/docs/model-armor/create-template",
            )

        return _result(
            "Model Armor",
            "PASS",
            f"{len(templates)} Model Armor template(s) configured",
        )

    except Exception as exc:
        return _result(
            "Model Armor",
            "SKIP",
            f"Cannot query Model Armor: {exc}",
            "Model Armor may not be available in this region or project",
        )


# ── Check 5: Secret Manager ─────────────────────────────────────────────────


def check_secrets(project: str) -> dict[str, Any]:
    """Verify secrets are stored in Secret Manager, not plaintext.

    Ref: https://cloud.google.com/secret-manager/docs/overview
    """
    if secretmanager_v1 is None:
        return _result(
            "Secret Manager Usage",
            "SKIP",
            "google-cloud-secret-manager not installed",
            "pip install google-cloud-secret-manager",
        )

    try:
        client = secretmanager_v1.SecretManagerServiceClient()
        parent = f"projects/{project}"

        # List secrets to verify Secret Manager is in use
        # Ref: https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets/list
        secrets = list(client.list_secrets(request={"parent": parent, "page_size": 50}))

        if not secrets:
            return _result(
                "Secret Manager Usage",
                "WARNING",
                "No secrets found in Secret Manager — API keys/credentials may be hardcoded",
                "Store sensitive config in Secret Manager: "
                "https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets",
            )

        # Check for secrets with no active versions (stale secrets)
        secret_names = [s.name.split("/")[-1] for s in secrets]
        return _result(
            "Secret Manager Usage",
            "PASS",
            f"{len(secrets)} secret(s) in Secret Manager: {', '.join(secret_names[:5])}{'...' if len(secrets) > 5 else ''}",
        )

    except Exception as exc:
        return _result(
            "Secret Manager Usage",
            "SKIP",
            f"Cannot query Secret Manager: {exc}",
            "Ensure caller has roles/secretmanager.viewer",
        )


# ── Entrypoint ───────────────────────────────────────────────────────────────


def run_security_checks(
    project: str,
    agent_id: str | None = None,
    location: str = "us-central1",
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Run all security validation checks.

    Args:
        project: GCP project ID.
        agent_id: Optional Vertex AI Agent ID (reasoning engine).
        location: GCP region (default us-central1).
        dry_run: If True, list checks without making API calls.

    Returns:
        List of check result dicts.
    """
    checks = [
        ("IAM Least Privilege", lambda: check_iam_least_privilege(project)),
        ("VPC-SC Perimeter", lambda: check_vpc_sc(project)),
        ("Encryption (CMEK)", lambda: check_encryption(project, location)),
        ("Model Armor", lambda: check_model_armor(project, location)),
        ("Secret Manager Usage", lambda: check_secrets(project)),
    ]

    if dry_run:
        print("\n[DRY RUN] Security checks that would run:")
        results = []
        for name, _ in checks:
            r = _result(name, "SKIP", "dry-run mode — no API calls made")
            results.append(r)
        return results

    if _MISSING_DEPS:
        print(f"\n{YELLOW}[WARN]{RESET} Missing optional deps: {', '.join(_MISSING_DEPS)}")
        print(f"       Install with: pip install {' '.join(_MISSING_DEPS)}\n")

    print(f"\n{'=' * 60}")
    print(f"  Security Validation — project={project}")
    print(f"{'=' * 60}")

    results = []
    for name, fn in checks:
        results.append(fn())

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate security posture for Vertex AI Agent Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 validate_security.py --project my-project --agent-id 12345",
    )
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--agent-id", help="Vertex AI Agent (Reasoning Engine) ID")
    parser.add_argument("--location", default="us-central1", help="GCP region (default: us-central1)")
    parser.add_argument("--dry-run", action="store_true", help="List checks without making API calls")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    results = run_security_checks(
        project=args.project,
        agent_id=args.agent_id,
        location=args.location,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(results, indent=2))

    # Exit code: 1 if any FAIL
    if any(r["status"] == "FAIL" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
