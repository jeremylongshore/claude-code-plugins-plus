#!/usr/bin/env python3
"""Classify read-only Snowflake deployment evidence.

This is a connector-neutral gate for Terraform, schemachange, Snowflake CLI/
drivers, and behavior-change review. It does not invoke any of those tools or
apply a plan. Feed it redacted JSON collected by an operator or CI preview.

Exit codes: 0 for valid input (findings are data), 2 for bad usage/input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any


SENSITIVE_VALUE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passwd|pwd|passphrase|secret|token|api[_ -]?key|authorization|credential|private[_ -]?key)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
)


def _finding(code: str, severity: str, evidence: str, action: str, rank: int) -> dict[str, Any]:
    return {"code": code, "severity": severity, "evidence": evidence, "read_only_action": action, "recovery_rank": rank}


def _major(version: Any) -> int | None:
    match = re.fullmatch(
        r"\s*v?(\d+)(?:\.\d+){1,2}(?:[-+][0-9A-Za-z.-]+)?\s*",
        str(version or ""),
    )
    return int(match.group(1)) if match else None


def _bool(value: Any) -> bool:
    return value is True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _exact_version(value: Any) -> bool:
    return bool(
        re.fullmatch(
            r"\s*v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?\s*",
            str(value or ""),
        )
    )


def _safe_backend(value: Any) -> str | None:
    if not _nonempty(value):
        return None
    text = str(value).strip()
    lowered = text.casefold()
    if re.search(r"://[^/\s:@]+:[^@\s/]+@", text):
        return None
    if re.search(r"[?&](?:[^=&]*(?:token|secret|password|credential|key)[^=&]*)=", lowered):
        return None
    return text


def _reject_secret_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if any(
                fragment in normalized
                for fragment in (
                    "password",
                    "passphrase",
                    "secret",
                    "privatekey",
                    "credential",
                    "token",
                    "apikey",
                    "authorization",
                    "jwt",
                )
            ):
                raise ValueError(f"credential-bearing field is not accepted: {path}.{key}")
            _reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_fields(child, f"{path}[{index}]")
    elif (
        isinstance(value, str)
        and not path.endswith(".backend")
        and any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS)
    ):
        raise ValueError(f"credential-shaped value is not accepted: {path}")


def _timestamp(value: Any, field: str) -> datetime | None:
    if not _nonempty(value):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _sha256(value: Any) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(value or "")))


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _canonical_receipt_valid(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    supplied = value.get("receipt_sha256")
    if not isinstance(supplied, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", supplied):
        return False
    body = dict(value)
    body.pop("receipt_sha256", None)
    expected = f"sha256:{hashlib.sha256(_canonical_json(body)).hexdigest()}"
    return supplied == expected


def _object_label(row: dict[str, Any]) -> str:
    return str(row.get("object") or row.get("address") or row.get("name") or "").strip()


def _inventory_rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
    return value


def validate_input(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("evidence must be a JSON object")
    for field in ("metadata", "terraform", "tools", "bcr", "rollback"):
        if field in data and not isinstance(data[field], dict):
            raise ValueError(f"{field} must be an object")
    tf = data.get("terraform", {})
    for field in ("state", "plan"):
        if field in tf and not isinstance(tf[field], dict):
            raise ValueError(f"terraform.{field} must be an object")
    for field in ("resources", "preview_features", "affected_objects"):
        if field in tf and not isinstance(tf[field], list):
            raise ValueError(f"terraform.{field} must be an array")
    for index, row in enumerate(tf.get("resources", [])):
        if not isinstance(row, dict):
            raise ValueError(f"terraform.resources[{index}] must be an object")
    if "affected_objects" in data:
        _inventory_rows(data["affected_objects"], "affected_objects")
    if "preflight" in data and not isinstance(data["preflight"], dict):
        raise ValueError("preflight must be an object")
    if "state_backup" in data and not isinstance(data["state_backup"], dict):
        raise ValueError("state_backup must be an object")
    if "bcr" in data and isinstance(data["bcr"], dict) and "inventory" in data["bcr"]:
        _inventory_rows(data["bcr"]["inventory"], "bcr.inventory")
    if "bcr_inventory" in data:
        _inventory_rows(data["bcr_inventory"], "bcr_inventory")
    if "zero_change_receipt" in data and not isinstance(data["zero_change_receipt"], dict):
        raise ValueError("zero_change_receipt must be an object")
    if "migrations" in data and not isinstance(data["migrations"], list):
        raise ValueError("migrations must be an array")
    for index, row in enumerate(data.get("migrations", [])):
        if not isinstance(row, dict):
            raise ValueError(f"migrations[{index}] must be an object")
    for field in ("provider_migrations", "dbt_projects", "post_change_invariants"):
        if field in data:
            _inventory_rows(data[field], field)
    return data


def analyze(data: Any) -> dict[str, Any]:
    data = validate_input(data)
    _reject_secret_fields(data)
    findings: list[dict[str, Any]] = []
    metadata = data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {}
    tf = data.get("terraform", {}) if isinstance(data.get("terraform", {}), dict) else {}
    state = tf.get("state", {}) if isinstance(tf.get("state", {}), dict) else {}
    plan = tf.get("plan", {}) if isinstance(tf.get("plan", {}), dict) else {}
    provider_version = _major(tf.get("version"))
    provider_source = str(tf.get("provider_source", ""))
    backend = _safe_backend(tf.get("backend"))

    missing_provenance: list[str] = []
    for field in ("account", "role", "repo_sha", "collected_at", "window_start", "window_end"):
        if not _nonempty(metadata.get(field)):
            missing_provenance.append(f"metadata.{field}")
    collected_at = _timestamp(metadata.get("collected_at"), "metadata.collected_at")
    window_start = _timestamp(metadata.get("window_start"), "metadata.window_start")
    window_end = _timestamp(metadata.get("window_end"), "metadata.window_end")
    if collected_at is None:
        missing_provenance.append("metadata.collected_at(valid timezone timestamp)")
    elif collected_at > datetime.now(timezone.utc):
        missing_provenance.append("metadata.collected_at(not in future)")
    if window_start is None:
        missing_provenance.append("metadata.window_start(valid timezone timestamp)")
    if window_end is None:
        missing_provenance.append("metadata.window_end(valid timezone timestamp)")
    if window_start is not None and window_end is not None and window_start > window_end:
        missing_provenance.append("metadata.observation_window(ordered)")
    if window_end is not None and collected_at is not None and window_end > collected_at:
        missing_provenance.append("metadata.window_end(no later than collection)")
    if _nonempty(metadata.get("repo_sha")) and not re.fullmatch(
        r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", metadata["repo_sha"]
    ):
        missing_provenance.append("metadata.repo_sha(valid Git SHA)")
    for field in ("backend", "workspace"):
        if not _nonempty(tf.get(field)):
            missing_provenance.append(f"terraform.{field}")
    if backend is None:
        missing_provenance.append("terraform.backend(redacted identifier without credentials)")
    if provider_source.lower() != "snowflakedb/snowflake":
        missing_provenance.append("terraform.provider_source(snowflakedb/snowflake)")
    if not _exact_version(tf.get("version")):
        missing_provenance.append("terraform.version(exact semantic version)")
    for field in ("saved_plan_sha256", "generated_at"):
        if not _nonempty(plan.get(field)):
            missing_provenance.append(f"terraform.plan.{field}")
    plan_generated_at = _timestamp(plan.get("generated_at"), "terraform.plan.generated_at")
    if plan_generated_at is None:
        missing_provenance.append("terraform.plan.generated_at(valid timezone timestamp)")
    elif collected_at is not None and plan_generated_at > collected_at:
        missing_provenance.append("terraform.plan.generated_at(no later than collection)")
    if _nonempty(plan.get("saved_plan_sha256")) and not re.fullmatch(r"[0-9a-fA-F]{64}", plan["saved_plan_sha256"]):
        missing_provenance.append("terraform.plan.saved_plan_sha256(valid SHA-256)")
    if not _canonical_receipt_valid(plan):
        findings.append(
            _finding(
                "PLAN_RECEIPT_UNVERIFIABLE",
                "critical",
                "saved plan metadata lacks a matching canonical receipt hash",
                "Recreate the plan receipt from the exact detailed-exitcode result and saved-plan hash; do not approve an altered or partial plan envelope.",
                6,
            )
        )

    if provider_version is not None and provider_version < 2:
        findings.append(
            _finding(
                "PROVIDER_PRE_2",
                "critical",
                f"provider version {tf.get('version')!s}",
                "Verify the current snowflakedb/snowflake provider support matrix and migrate before trusting a production plan.",
                10,
            )
        )
    if provider_source and provider_source.lower() != "snowflakedb/snowflake":
        findings.append(
            _finding(
                "PROVIDER_SOURCE_UNEXPECTED",
                "high",
                provider_source,
                "Confirm the provider source and lock file; do not assume a similarly named fork has the same grant/state semantics.",
                11,
            )
        )
    state_valid = state.get("valid", True)
    if not state or state.get("parseable") is not True or state_valid is not True:
        findings.append(
            _finding(
                "TERRAFORM_STATE_UNREADABLE",
                "critical",
                "state is missing or marked unparseable",
                "Stop before plan/apply; preserve the state backend receipt and recover a known-good state through the backend's documented recovery path.",
                12,
            )
        )

    preview = tf.get("preview_features", [])
    if preview:
        findings.append(
            _finding(
                "PROVIDER_PREVIEW_FEATURE",
                "high",
                ", ".join(map(str, preview)),
                "Verify the live provider preview contract, upgrade notes, and rollback path; preview resources are not treated as stable by default.",
                13,
            )
        )

    provider_migrations = data.get("provider_migrations", [])
    if data.get("provider_migrations_verified") is not True:
        findings.append(
            _finding(
                "PROVIDER_MIGRATION_INVENTORY_MISSING",
                "critical",
                "provider migration segments are not verified",
                "Enumerate every migration-guide segment between the locked source and target provider versions, including state moves, import changes, and preview schema changes.",
                14,
            )
        )
    for index, segment in enumerate(provider_migrations):
        required = ("from_version", "to_version", "source", "status")
        if any(not _nonempty(segment.get(field)) for field in required) or not _canonical_receipt_valid(segment):
            findings.append(
                _finding(
                    f"PROVIDER_MIGRATION_SEGMENT_UNVERIFIABLE-{index}",
                    "critical",
                    f"provider migration segment {index} is incomplete or hash-invalid",
                    "Bind the exact migration-guide segment, source/target versions, affected addresses, state-move boundary, and disposition to a canonical receipt hash.",
                    15,
                )
            )
            continue
        status = str(segment.get("status", "")).upper()
        if status not in {"VERIFIED", "NOT_APPLICABLE"}:
            findings.append(
                _finding(
                    f"PROVIDER_MIGRATION_SEGMENT_OPEN-{index}",
                    "critical",
                    f"{segment['from_version']} -> {segment['to_version']} status={status}",
                    "Resolve the migration segment in an isolated state copy and require a reviewed zero-change or explicitly approved change plan before production.",
                    16,
                )
            )

    resources = tf.get("resources", [])
    for resource in resources:
        address = str(resource.get("address", "unknown"))
        resource_type = str(resource.get("type", address.split(".")[0]))
        existing = _bool(resource.get("existing"))
        action = str(resource.get("action", "")).lower()
        import_id = resource.get("import_id") or resource.get("imported_id")
        is_grant = "grant" in resource_type
        if is_grant and existing and action in {"create", "replace", ""} and not import_id:
            findings.append(
                _finding(
                    "GRANT_IMPORT_REQUIRED",
                    "critical",
                    f"{address}: existing grant resource has no import identity",
                    "Declare the intended grant resource, obtain its documented import identity, and preview adoption; never hand-edit terraform.tfstate or destroy a grant graph to force adoption.",
                    20,
                )
            )
        if action in {"replace", "destroy", "delete"} or _bool(resource.get("destroy")):
            findings.append(
                _finding(
                    "DESTRUCTIVE_PLAN_CHANGE",
                    "critical",
                    f"{address}: planned action {action or 'destroy'}",
                    "Require an explicit impact review, backup/rollback evidence, and an approved maintenance window before any apply.",
                    40,
                )
            )

    exit_code = plan.get("exit_code")
    changes = plan.get("changes")
    plan_numbers_valid = type(exit_code) is int and type(changes) is int and changes >= 0
    if not plan_numbers_valid:
        findings.append(
            _finding(
                "PLAN_NOT_VERIFIED",
                "high",
                "plan exit_code/change count is missing or not typed as non-boolean integers",
                "Run a current, saved read-only Terraform plan with detailed exit status and inspect it; do not proceed from configuration alone.",
                30,
            )
        )
    elif exit_code not in (0, 2):
        findings.append(
            _finding(
                "PLAN_FAILED",
                "critical",
                f"terraform plan exit_code={exit_code}",
                "Fix the plan error and preserve its output; exit code 2 means changes, while another non-zero code is not a valid preview.",
                31,
            )
        )
    elif changes == 0 and exit_code == 0:
        # This is a positive receipt, not a finding. It is copied into the report.
        pass
    elif changes > 0:
        findings.append(
            _finding(
                "PLAN_HAS_CHANGES",
                "review",
                f"{changes} planned change(s), exit_code={exit_code}",
                "Review every create/update/replace/destroy action, grant ordering, ownership, and state address before approval.",
                32,
            )
        )

    migrations = data.get("migrations", [])
    versions: Counter[str] = Counter()
    for migration in migrations:
        path = str(migration.get("path", "unknown"))
        mtype = str(migration.get("type", "")).upper()
        version = str(migration.get("version", ""))
        if mtype == "V" and version:
            versions[version] += 1
            if migration.get("applied_checksum") and migration.get("checksum") != migration.get("applied_checksum"):
                findings.append(
                    _finding(
                        "VERSIONED_CHECKSUM_DRIFT",
                        "critical",
                        f"{path}: current checksum differs from applied checksum",
                        "Do not edit an applied versioned script in place; compare the stored change-history row, restore the original or create a new versioned migration, and record the decision.",
                        20,
                    )
                )
        if (
            mtype == "R"
            and migration.get("applied_checksum")
            and migration.get("checksum") != migration.get("applied_checksum")
        ):
            findings.append(
                _finding(
                    "REPEATABLE_CHANGE_DETECTED",
                    "review",
                    f"{path}: repeatable checksum changed",
                    "Confirm the change-history/checksum behavior and idempotence, then preview the intentional rerun; do not treat a repeatable rerun as a versioned migration.",
                    25,
                )
            )
    for version, count in sorted(versions.items()):
        if count > 1:
            findings.append(
                _finding(
                    "VERSION_COLLISION",
                    "critical",
                    f"version {version} appears {count} times",
                    "Resolve the migration naming collision before deployment; do not rely on filesystem ordering or an out-of-order flag to choose between two scripts.",
                    21,
                )
            )

    dbt_projects = data.get("dbt_projects", [])
    if data.get("dbt_projects_verified") is not True:
        findings.append(
            _finding(
                "DBT_PROJECT_DENOMINATOR_UNVERIFIED",
                "critical",
                "affected dbt Project object inventory is not verified",
                "Inventory every affected dbt Project object and bind its current/live-version model, code hashes, supported dbt version, BCR disposition, and rollback boundary.",
                22,
            )
        )
    for index, project in enumerate(dbt_projects):
        name = str(project.get("name") or f"dbt-project-{index}")
        if not _canonical_receipt_valid(project):
            findings.append(
                _finding(
                    f"DBT_PROJECT_RECEIPT_UNVERIFIABLE-{index}",
                    "critical",
                    f"{name}: receipt hash missing or invalid",
                    "Recollect the dbt Project preflight from the exact deployed object and staged artifact without embedding project source or credentials.",
                    23,
                )
            )
            continue
        current_model = str(project.get("current_model", "")).upper()
        target_model = str(project.get("target_model", "")).upper()
        disposition = str(project.get("bcr_disposition", "")).upper()
        if current_model not in {"VERSIONED", "LIVE"} or target_model not in {"VERSIONED", "LIVE"}:
            findings.append(
                _finding(
                    f"DBT_PROJECT_MODEL_UNVERIFIED-{index}",
                    "critical",
                    f"{name}: current/target deployment model is invalid",
                    "Recollect the deployed object and target BCR state; use only the observed VERSIONED or LIVE model.",
                    24,
                )
            )
        if current_model != target_model and disposition not in {"VERIFIED", "MITIGATED", "NOT_APPLICABLE"}:
            findings.append(
                _finding(
                    f"DBT_PROJECT_BCR_UNRESOLVED-{index}",
                    "critical",
                    f"{name}: {current_model or 'unknown'} -> {target_model or 'unknown'}",
                    "Resolve the dbt Project live-version behavior-change disposition before deployment; do not assume immutable-version rollback still exists.",
                    24,
                )
            )
        if project.get("target_version_supported") is not True:
            findings.append(
                _finding(
                    f"DBT_PROJECT_VERSION_UNSUPPORTED-{index}",
                    "critical",
                    f"{name}: target dbt runtime support is not verified",
                    "Check the current Snowflake-supported dbt version table and pin a supported runtime before deploying the project object.",
                    25,
                )
            )
        deployed_hash = project.get("deployed_code_sha256")
        staged_hash = project.get("staged_code_sha256")
        if not _sha256(deployed_hash) or not _sha256(staged_hash):
            findings.append(
                _finding(
                    f"DBT_PROJECT_ARTIFACT_UNVERIFIED-{index}",
                    "critical",
                    f"{name}: deployed/staged code SHA-256 is missing or invalid",
                    "Hash the exact deployed and staged dbt Project artifacts without exporting source code or credentials.",
                    25,
                )
            )
        rollback_hash = project.get("rollback_artifact_sha256")
        if _nonempty(rollback_hash) and not _sha256(rollback_hash):
            findings.append(
                _finding(
                    f"DBT_PROJECT_ROLLBACK_UNVERIFIABLE-{index}",
                    "critical",
                    f"{name}: rollback artifact SHA-256 is malformed",
                    "Preserve and hash the exact previous project artifact before approving a mutable live-version replacement.",
                    26,
                )
            )
        code_changed = deployed_hash != staged_hash
        if code_changed and not _nonempty(project.get("rollback_artifact_sha256")):
            findings.append(
                _finding(
                    f"DBT_PROJECT_ROLLBACK_UNBOUNDED-{index}",
                    "critical",
                    f"{name}: staged code differs without a rollback artifact hash",
                    "Preserve the exact previous project artifact and define the operator restore trigger before replacing the mutable live version.",
                    26,
                )
            )

    tools = data.get("tools", {}) if isinstance(data.get("tools", {}), dict) else {}
    missing_tools = [name for name in ("snowflake_cli", "python_connector") if not isinstance(tools.get(name), dict)]
    if missing_tools:
        findings.append(
            _finding(
                "TOOLCHAIN_UNVERIFIED",
                "high",
                "missing evidence: " + ", ".join(missing_tools),
                "Verify the current Snowflake CLI, connector/driver, Python/runtime, and lockfile compatibility from live release notes before deploy.",
                35,
            )
        )
    for name in ("snowflake_cli", "python_connector"):
        evidence = tools.get(name)
        if isinstance(evidence, dict):
            version = evidence.get("version")
            if not _exact_version(version):
                missing_provenance.append(f"tools.{name}.version(exact)")
    bcr = data.get("bcr", {}) if isinstance(data.get("bcr", {}), dict) else {}
    if bcr.get("checked") is not True:
        findings.append(
            _finding(
                "BCR_NOT_CHECKED",
                "high",
                "behavior-change review is absent or not marked complete",
                "Check the current Snowflake behavior-change release notes for the account release window, CLI/driver versions, SQL semantics, and deprecations.",
                36,
            )
        )
    for field in ("id", "source", "checked_at"):
        if not _nonempty(bcr.get(field)):
            missing_provenance.append(f"bcr.{field}")
    bcr_checked_at = _timestamp(bcr.get("checked_at"), "bcr.checked_at")
    if bcr_checked_at is None:
        missing_provenance.append("bcr.checked_at(valid timezone timestamp)")
    elif collected_at is not None and bcr_checked_at > collected_at:
        missing_provenance.append("bcr.checked_at(no later than collection)")

    # A checked BCR is an inventory of account-release behavior changes, not a
    # single checkbox.  Every item needs a disposition so an affected change
    # cannot disappear behind a generic "reviewed" label.
    bcr_inventory = bcr.get("inventory", data.get("bcr_inventory", []))
    if bcr.get("checked") is True and not bcr_inventory:
        findings.append(
            _finding(
                "BCR_INVENTORY_MISSING",
                "critical",
                "BCR checked without an itemized behavior-change inventory",
                "Recollect the account-release BCR inventory with item IDs, affected surfaces, disposition, and owner before approving the deploy.",
                37,
            )
        )
    for index, item in enumerate(bcr_inventory if isinstance(bcr_inventory, list) else []):
        if not _nonempty(item.get("id")):
            missing_provenance.append(f"bcr.inventory[{index}].id")
        if not _nonempty(item.get("source")):
            missing_provenance.append(f"bcr.inventory[{index}].source")
        affected = item.get("affected") is True or str(item.get("status", "")).upper() in {"OPEN", "IMPACTED", "REVIEW"}
        disposition = str(item.get("disposition", "")).upper()
        if affected and disposition not in {"VERIFIED", "MITIGATED", "ACCEPTED", "NOT_APPLICABLE"}:
            findings.append(
                _finding(
                    f"BCR_AFFECTED_UNRESOLVED-{index}",
                    "critical",
                    f"{item.get('id') or 'unnamed BCR'} is marked affected without an approved disposition",
                    "Review the BCR against the affected objects and toolchain, record an owner and mitigation, or block the release.",
                    38,
                )
            )

    # Preflight is deliberately a separate gate from the Terraform plan: a
    # valid plan can still target the wrong account, stale backend, or unknown
    # object set.  Check records are metadata only and must be explicit.
    preflight = data.get("preflight", {}) if isinstance(data.get("preflight", {}), dict) else {}
    check_rows = preflight.get("checks", [])
    if (
        preflight.get("completed") is not True
        or not _nonempty(preflight.get("operator"))
        or _timestamp(preflight.get("checked_at"), "preflight.checked_at") is None
        or not isinstance(check_rows, list)
        or not check_rows
    ):
        findings.append(
            _finding(
                "PREFLIGHT_INCOMPLETE",
                "critical",
                "deployment preflight is absent or incomplete",
                "Capture account/backend/workspace identity, state lock/backup, affected-object inventory, plan, BCR, and rollback checks with an operator and UTC timestamp.",
                6,
            )
        )
    else:
        preflight_checked_at = _timestamp(preflight.get("checked_at"), "preflight.checked_at")
        if collected_at is not None and preflight_checked_at is not None and preflight_checked_at > collected_at:
            missing_provenance.append("preflight.checked_at(no later than collection)")
        failed_checks = []
        for index, check in enumerate(check_rows):
            if isinstance(check, dict):
                if not _nonempty(check.get("name")) or str(check.get("status", "")).upper() != "PASS":
                    failed_checks.append(str(check.get("name") or f"check-{index}"))
            elif not (isinstance(check, str) and check.strip()):
                failed_checks.append(f"check-{index}")
        if failed_checks:
            findings.append(
                _finding(
                    "PREFLIGHT_CHECK_FAILED",
                    "critical",
                    ", ".join(failed_checks),
                    "Resolve each failed preflight check and recollect the packet; do not infer readiness from a green Terraform plan.",
                    7,
                )
            )

    state_backup = data.get("state_backup") or data.get("state_backup_receipt") or tf.get("state_backup")
    if (
        not isinstance(state_backup, dict)
        or state_backup.get("created") is not True
        or state_backup.get("verified") is not True
    ):
        findings.append(
            _finding(
                "STATE_BACKUP_MISSING",
                "critical",
                "verified state backup receipt is missing",
                "Preserve a point-in-time backend snapshot/version and verify its identity, timestamp, location, and checksum before any state refresh or apply.",
                8,
            )
        )
    else:
        for field in ("location", "captured_at", "state_sha256"):
            if not _nonempty(state_backup.get(field)):
                missing_provenance.append(f"state_backup.{field}")
        if _safe_backend(state_backup.get("location")) is None:
            missing_provenance.append("state_backup.location(redacted identifier without credentials)")
        if not _sha256(state_backup.get("state_sha256")):
            missing_provenance.append("state_backup.state_sha256(valid SHA-256)")
        state_backup_at = _timestamp(state_backup.get("captured_at"), "state_backup.captured_at")
        if state_backup_at is None:
            missing_provenance.append("state_backup.captured_at(valid timezone timestamp)")
        elif collected_at is not None and state_backup_at > collected_at:
            missing_provenance.append("state_backup.captured_at(no later than collection)")
        if not _canonical_receipt_valid(state_backup):
            findings.append(
                _finding(
                    "STATE_BACKUP_RECEIPT_UNVERIFIABLE",
                    "critical",
                    "state backup metadata lacks a matching canonical receipt hash",
                    "Recreate and verify the state-backup receipt from the exact backend version, capture time, and state SHA-256 before any refresh or apply.",
                    8,
                )
            )

    affected_objects = data.get("affected_objects", data.get("affected_object_inventory", tf.get("affected_objects")))
    if isinstance(affected_objects, dict):
        affected_verified = affected_objects.get("verified")
        affected_objects = affected_objects.get("objects", [])
    else:
        affected_verified = data.get("affected_objects_verified", tf.get("affected_objects_verified"))
    if not isinstance(affected_objects, list) or affected_verified is not True:
        findings.append(
            _finding(
                "AFFECTED_OBJECTS_UNVERIFIED",
                "critical",
                "affected-object inventory is absent or not verified",
                "Reconcile plan addresses to database/schema/table/view/grant identities and record the exact reviewed object set before approval.",
                9,
            )
        )
    else:
        blank_objects = [str(index) for index, row in enumerate(affected_objects) if not _object_label(row)]
        if blank_objects:
            findings.append(
                _finding(
                    "AFFECTED_OBJECTS_INCOMPLETE",
                    "high",
                    "blank object identity at rows " + ", ".join(blank_objects),
                    "Complete the object inventory with stable Terraform addresses or fully qualified Snowflake object names.",
                    10,
                )
            )

    rollback = data.get("rollback", {}) if isinstance(data.get("rollback", {}), dict) else {}
    if rollback.get("tested") is not True:
        findings.append(
            _finding(
                "ROLLBACK_UNTESTED",
                "critical",
                str(rollback.get("strategy") or "no tested rollback receipt"),
                "Define and test a bounded rollback or forward-fix strategy against the exact plan/migration set; do not call backup existence a rollback test.",
                50,
            )
        )
    for field in ("strategy", "owner", "stop_condition", "tested_at", "plan_sha256"):
        if not _nonempty(rollback.get(field)):
            missing_provenance.append(f"rollback.{field}")
    rollback_tested_at = _timestamp(rollback.get("tested_at"), "rollback.tested_at")
    if rollback_tested_at is None:
        missing_provenance.append("rollback.tested_at(valid timezone timestamp)")
    elif collected_at is not None and rollback_tested_at > collected_at:
        missing_provenance.append("rollback.tested_at(no later than collection)")
    if (
        _nonempty(rollback.get("plan_sha256"))
        and _nonempty(plan.get("saved_plan_sha256"))
        and rollback["plan_sha256"] != plan["saved_plan_sha256"]
    ):
        missing_provenance.append("rollback.plan_sha256(matches saved plan)")

    post_change_invariants = data.get("post_change_invariants", [])
    if data.get("post_change_invariants_verified") is not True or (
        plan_numbers_valid and changes > 0 and not post_change_invariants
    ):
        findings.append(
            _finding(
                "POST_CHANGE_INVARIANTS_MISSING",
                "critical",
                "post-change invariant denominator is absent or not verified",
                "Declare the exact account/object invariants, owners, expected values, read-only verification, and rollback triggers before approving a non-zero plan.",
                51,
            )
        )
    for index, invariant in enumerate(post_change_invariants):
        required = ("name", "owner", "expected", "verification", "rollback_trigger")
        if any(not _nonempty(invariant.get(field)) for field in required) or not _canonical_receipt_valid(invariant):
            findings.append(
                _finding(
                    f"POST_CHANGE_INVARIANT_UNVERIFIABLE-{index}",
                    "critical",
                    f"post-change invariant {index} is incomplete or hash-invalid",
                    "Bind each invariant to a canonical receipt and a read-only check; do not use deploy exit status as post-change proof.",
                    52,
                )
            )

    if missing_provenance:
        findings.append(
            _finding(
                "EVIDENCE_PROVENANCE_INCOMPLETE",
                "critical",
                ", ".join(sorted(set(missing_provenance))),
                "Stop: recollect the deployment packet with typed account, role, repository, backend/workspace, saved-plan, tool-version, behavior-change, and rollback receipts.",
                5,
            )
        )

    zero_change = plan_numbers_valid and exit_code == 0 and changes == 0
    zero_receipt = data.get("zero_change_receipt", {}) if isinstance(data.get("zero_change_receipt", {}), dict) else {}
    if zero_change:
        receipt_plan_hash = zero_receipt.get("plan_sha256") or zero_receipt.get("saved_plan_sha256")
        receipt_object_count = zero_receipt.get("affected_objects", zero_receipt.get("affected_object_count"))
        receipt_issued_at = _timestamp(zero_receipt.get("issued_at"), "zero_change_receipt.issued_at")
        receipt_matches = (
            zero_receipt.get("issued") is True
            and _sha256(receipt_plan_hash)
            and receipt_plan_hash == plan.get("saved_plan_sha256")
            and receipt_object_count == 0
            and receipt_issued_at is not None
            and (collected_at is None or receipt_issued_at <= collected_at)
        )
        if not receipt_matches:
            findings.append(
                _finding(
                    "ZERO_CHANGE_RECEIPT_MISSING",
                    "critical",
                    "exit_code=0 and changes=0 without a matching zero-change receipt",
                    "Issue a signed/hashed zero-change receipt tied to the saved plan, verified object count, and UTC issuance time; do not treat plan output alone as adoption proof.",
                    11,
                )
            )
    findings.sort(key=lambda item: (item["recovery_rank"], item["code"]))
    recovery: list[dict[str, Any]] = []
    seen: set[str] = set()
    for finding in findings:
        action = finding["read_only_action"]
        if action not in seen:
            seen.add(action)
            recovery.append({"order": len(recovery) + 1, "for": finding["code"], "action": action})
    release_gate = "pass" if zero_change and not findings else "blocked"
    safe_state_backup = dict(state_backup) if isinstance(state_backup, dict) else {}
    if safe_state_backup and _safe_backend(safe_state_backup.get("location")) is None:
        safe_state_backup["location"] = None
    return {
        "schema_version": "1",
        "zero_change_plan": zero_change,
        "release_gate": release_gate,
        "provenance": {
            "account": metadata.get("account"),
            "role": metadata.get("role"),
            "repo_sha": metadata.get("repo_sha"),
            "collected_at": metadata.get("collected_at"),
            "observation_window": {
                "start": metadata.get("window_start"),
                "end": metadata.get("window_end"),
            },
            "backend": backend,
            "workspace": tf.get("workspace"),
            "saved_plan_sha256": plan.get("saved_plan_sha256"),
            "plan_generated_at": plan.get("generated_at"),
        },
        "provider": {
            "source": provider_source or None,
            "version": tf.get("version"),
            "major": provider_version,
        },
        "toolchain": {
            name: {"version": tools.get(name, {}).get("version")}
            for name in ("snowflake_cli", "python_connector")
            if isinstance(tools.get(name), dict)
        },
        "behavior_change_review": {
            "checked": bcr.get("checked"),
            "id": bcr.get("id"),
            "source": bcr.get("source"),
            "checked_at": bcr.get("checked_at"),
            "inventory": bcr_inventory,
        },
        "preflight": {
            "completed": preflight.get("completed"),
            "operator": preflight.get("operator"),
            "checked_at": preflight.get("checked_at"),
            "checks": check_rows,
        },
        "affected_object_inventory": {
            "verified": affected_verified,
            "objects": affected_objects if isinstance(affected_objects, list) else [],
        },
        "state_backup_receipt": safe_state_backup,
        "zero_change_receipt": zero_receipt,
        "migration_evidence": [
            {
                "path": migration.get("path"),
                "type": migration.get("type"),
                "version": migration.get("version"),
                "checksum_status": (
                    "match"
                    if migration.get("applied_checksum")
                    and migration.get("checksum") == migration.get("applied_checksum")
                    else "drift"
                    if migration.get("applied_checksum")
                    else "not_observed"
                ),
            }
            for migration in migrations
        ],
        "provider_migration_segments": provider_migrations,
        "dbt_project_preflight": dbt_projects,
        "post_change_invariant_receipts": post_change_invariants,
        "rollback_receipt": {
            "tested": rollback.get("tested"),
            "strategy": rollback.get("strategy"),
            "owner": rollback.get("owner"),
            "stop_condition": rollback.get("stop_condition"),
            "tested_at": rollback.get("tested_at"),
            "plan_sha256": rollback.get("plan_sha256"),
        },
        "findings": findings,
        "ordered_recovery": recovery,
        "post_deploy_invariants": [
            "The saved Terraform plan is zero-change after adoption, or every remaining change has an approved owner and impact receipt.",
            "Grant resources resolve to the intended role/object and state imports are reproducible without hand-edited state.",
            "Versioned migration checksums match change history; repeatable reruns are intentional and idempotent.",
            "Snowflake CLI, connector/driver, runtime, and behavior-change review are current for this account release window.",
            "Rollback or forward-fix was tested against the exact plan/migration set and its stop condition is recorded.",
            "Preflight, BCR inventory, affected-object inventory, and state-backup receipts reconcile to the same account and plan.",
            "A zero-change receipt is issued only for exit code 0, zero changes, and a matching saved-plan hash.",
        ],
        "limitations": [
            "This report classifies supplied evidence; it does not invoke Terraform, schemachange, Snowflake CLI, a driver, or Snowflake SQL.",
            "Provider/tool versions and behavior changes must be verified against current primary release notes at execution time.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify read-only Snowflake deployment evidence")
    parser.add_argument("--input", "-i", help="JSON input path; default is stdin")
    args = parser.parse_args()
    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        report = analyze(json.loads(raw))
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
