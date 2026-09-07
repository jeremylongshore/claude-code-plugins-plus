#!/usr/bin/env python3
"""Deterministically classify privacy-reviewed Snowflake deploy evidence.

This module is pure: it reads JSON and emits a redacted report. It never invokes
Terraform, schemachange, Snowflake clients, a shell, or a network API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
MAX_DEPTH = 64
MAX_NODES = 100_000
PACKET_MAX_AGE = timedelta(minutes=15)
BCR_MAX_AGE = timedelta(hours=24)
BACKUP_MAX_AGE = timedelta(hours=24)
ROLLBACK_MAX_AGE = timedelta(hours=24)
WINDOW_TAIL_MAX = timedelta(seconds=60)

SHA_RE = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
VERSION_RE = re.compile(r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?")
SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")
OFFICIAL_SOURCE_RE = re.compile(
    r"https://(?:docs\.snowflake\.com/|github\.com/(?:snowflakedb|Snowflake-Labs)/|"
    r"registry\.terraform\.io/providers/snowflakedb/snowflake/|developer\.hashicorp\.com/)[^\s?#]+"
)
ACTION_VALUES = {"no-op", "create", "read", "update", "delete", "delete-create", "create-delete"}
ACTION_SEQUENCES = {
    ("no-op",),
    ("create",),
    ("read",),
    ("update",),
    ("delete",),
    ("delete", "create"),
    ("create", "delete"),
}
DISPOSITIONS = {"VERIFIED", "MITIGATED", "ACCEPTED", "NOT_APPLICABLE"}
BCR_BUNDLE_ITEMS = {
    "2026_06": frozenset(
        {
            "BCR-2261",
            "BCR-2342",
            "BCR-2343",
            "BCR-2352",
            "BCR-2359",
            "BCR-2360",
            "BCR-2362",
            "BCR-2363",
            "BCR-2364",
            "BCR-2368",
            "BCR-2371",
            "BCR-2373",
            "BCR-2376",
            "BCR-2377",
            "BCR-2379",
            "BCR-2380",
            "BCR-2381",
            "BCR-2382",
            "BCR-2384",
        }
    )
}
REQUIRED_PREFLIGHT = {
    "identity",
    "backend-lock",
    "state-backup",
    "affected-objects",
    "plan",
    "provider-migrations",
    "preview",
    "schemachange",
    "bcr",
    "dbt-projects",
    "rollback",
    "post-change-invariants",
}
SENSITIVE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passwd|pwd|passphrase|secret|token|api[_ -]?key|authorization|credential|private[_ -]?key)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def bundle_digest(value: Any) -> str:
    """Digest expected through an independent CI/artifact channel."""
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def _version(value: Any) -> bool:
    return isinstance(value, str) and bool(VERSION_RE.fullmatch(value))


def _version_tuple(value: Any) -> tuple[int, int, int] | None:
    if not _version(value):
        return None
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?", value)
    return tuple(int(part) for part in match.groups()) if match else None


def _migration_version_tuple(value: Any) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9]\d*)(?:[._](?:0|[1-9]\d*))*", value):
        return None
    return tuple(int(part) for part in re.split(r"[._]", value))


def _natural_script_key(value: str) -> tuple[tuple[int, str | int], ...]:
    return tuple((1, int(part)) if part.isdigit() else (0, part) for part in re.split(r"(\d+)", value.casefold()))


def _canonical_script_name(value: str) -> str:
    return re.sub(r"(?i)\.jinja$", "", value).casefold()


def _migration_script_key(row: dict[str, Any]) -> tuple[int, Any] | None:
    script_type = row.get("script_type")
    script_name = row.get("script_name")
    version = row.get("version")
    if not isinstance(script_name, str) or not 1 <= len(script_name) <= 200:
        return None
    if any(character in script_name for character in ("/", "\\", "\n", "\r", "\x00")):
        return None
    suffix = r"(?:\.sql(?:\.jinja)?|\.cli\.yml(?:\.jinja)?)"
    if script_type == "V":
        match = re.fullmatch(
            rf"V(?P<version>(?:0|[1-9]\d*)(?:[._](?:0|[1-9]\d*))*)__(?!.*__)[^\r\n]+{suffix}",
            script_name,
            re.IGNORECASE,
        )
        version_tuple = _migration_version_tuple(version)
        if match is None or version_tuple is None or match.group("version") != version:
            return None
        return (0, _natural_script_key(_canonical_script_name(script_name)))
    if script_type in {"R", "A"}:
        if (
            version is not None
            or re.fullmatch(rf"{script_type}__(?!.*__)[^\r\n]+{suffix}", script_name, re.IGNORECASE) is None
        ):
            return None
        return ({"R": 1, "A": 2}[script_type], _natural_script_key(_canonical_script_name(script_name)))
    return None


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SAFE_ID_RE.fullmatch(value))


def _official_source(value: Any) -> bool:
    return isinstance(value, str) and bool(OFFICIAL_SOURCE_RE.fullmatch(value))


def _source_for(value: Any, surface: str) -> bool:
    if not _official_source(value):
        return False
    patterns = {
        "preview": r"https://(?:registry\.terraform\.io/providers/snowflakedb/snowflake/|github\.com/snowflakedb/terraform-provider-snowflake/).+",
        "provider_migration": r"https://github\.com/snowflakedb/terraform-provider-snowflake/blob/[0-9a-f]{40}/MIGRATION_GUIDE\.md",
        "bcr": r"https://docs\.snowflake\.com/(?:en/)?release-notes/bcr-bundles/.+",
        "snowflake_cli": r"https://docs\.snowflake\.com/(?:en/)?developer-guide/snowflake-cli/.+",
        "python_connector": r"https://(?:docs\.snowflake\.com/(?:en/)?developer-guide/python-connector(?:/.+)?|github\.com/snowflakedb/snowflake-connector-python/.+)",
        "schemachange": r"https://github\.com/Snowflake-Labs/schemachange/.+",
    }
    return bool(re.fullmatch(patterns[surface], value))


def _integer(value: Any, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if len(value) > MAX_ROWS:
        raise ValueError(f"{field} exceeds the row limit")
    if any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{field} contains a non-object row")
    return value


def _reject_secrets(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise ValueError("input nesting or node count exceeds the safety limit")
        if isinstance(current, dict):
            for key, child in current.items():
                normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
                if any(
                    part in normalized
                    for part in (
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
                    raise ValueError("credential-bearing field is not accepted")
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
        elif isinstance(current, str) and any(pattern.search(current) for pattern in SENSITIVE_PATTERNS):
            raise ValueError("credential-shaped value is not accepted")


def _receipt(value: Any, fields: set[str]) -> bool:
    if not isinstance(value, dict) or set(value) != fields:
        return False
    supplied = value.get("receipt_sha256")
    if not isinstance(supplied, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", supplied):
        return False
    body = dict(value)
    body.pop("receipt_sha256")
    return supplied == "sha256:" + hashlib.sha256(_canonical(body)).hexdigest()


def _finding(code: str, rank: int, evidence: str, action: str, severity: str = "critical") -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "evidence": evidence,
        "read_only_action": action,
        "recovery_rank": rank,
    }


def _add(
    findings: list[dict[str, Any]],
    condition: bool,
    code: str,
    rank: int,
    evidence: str,
    action: str,
    severity: str = "critical",
) -> None:
    if condition:
        findings.append(_finding(code, rank, evidence, action, severity))


def _strict_json(raw: str) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON object key is not accepted")
            result[key] = value
        return result

    def constant(_: str) -> None:
        raise ValueError("non-finite JSON number is not accepted")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def _shape(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("evidence must be a JSON object")
    allowed = {
        "schema_version",
        "metadata",
        "terraform",
        "preflight",
        "affected_objects_verified",
        "affected_objects_expected_count",
        "affected_objects",
        "state_backup",
        "migrations_verified",
        "migrations_expected_count",
        "migrations_observed_at",
        "migration_repository_sha256",
        "change_history_expected_count",
        "change_history_sha256",
        "change_history_projection_sha256",
        "migrations",
        "provider_migrations_verified",
        "provider_migrations_expected_count",
        "provider_migrations",
        "dbt_projects_verified",
        "dbt_projects_expected_count",
        "dbt_projects",
        "post_change_invariants_verified",
        "post_change_invariants_expected_count",
        "post_change_invariants",
        "tools",
        "bcr",
        "rollback",
        "zero_change_receipt",
    }
    if set(value) - allowed:
        raise ValueError("unexpected top-level field is not accepted")
    for field in (
        "metadata",
        "terraform",
        "preflight",
        "state_backup",
        "tools",
        "bcr",
        "rollback",
        "zero_change_receipt",
    ):
        if not isinstance(value.get(field), dict):
            raise ValueError(f"{field} must be an object")
    tf = value["terraform"]
    for field in ("state", "plan", "preview_inventory"):
        if not isinstance(tf.get(field), dict):
            raise ValueError(f"terraform.{field} must be an object")
    for field in (
        "affected_objects",
        "migrations",
        "provider_migrations",
        "dbt_projects",
        "post_change_invariants",
    ):
        _rows(value.get(field), field)
    _rows(tf.get("resources"), "terraform.resources")
    _rows(value["bcr"].get("inventory"), "bcr.inventory")
    _rows(value["preflight"].get("checks"), "preflight.checks")
    _reject_secrets(value)
    _canonical(value)
    return value


def analyze(
    value: Any,
    *,
    analysis_as_of: str | datetime | None = None,
    trusted_bundle_sha256: str | None = None,
) -> dict[str, Any]:
    data = _shape(value)
    if isinstance(analysis_as_of, datetime):
        as_of = analysis_as_of.astimezone(timezone.utc) if analysis_as_of.tzinfo is not None else None
    else:
        as_of = _timestamp(analysis_as_of)
    if as_of is None:
        raise ValueError("analysis_as_of must be a timezone-aware timestamp")
    findings: list[dict[str, Any]] = []
    actual_digest = bundle_digest(data)
    trusted = trusted_bundle_sha256 == actual_digest and bool(
        re.fullmatch(r"sha256:[0-9a-f]{64}", trusted_bundle_sha256 or "")
    )
    _add(
        findings,
        not trusted,
        "TRUSTED_BUNDLE_DIGEST_MISSING_OR_MISMATCHED",
        1,
        "the out-of-band bundle digest is absent or mismatched",
        "Obtain the canonical packet digest from the trusted CI/artifact channel; nested self-hashes do not prove origin.",
    )

    metadata = data["metadata"]
    tf = data["terraform"]
    state = tf["state"]
    plan = tf["plan"]
    resources = tf["resources"]
    collected_at = _timestamp(metadata.get("collected_at"))
    window_start = _timestamp(metadata.get("window_start"))
    window_end = _timestamp(metadata.get("window_end"))
    metadata_fields = {"account_ref", "role_ref", "repo_sha", "collected_at", "window_start", "window_end"}
    metadata_ok = (
        data.get("schema_version") == "2"
        and set(metadata) == metadata_fields
        and all(_sha(metadata.get(field)) for field in ("account_ref", "role_ref"))
        and bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(metadata.get("repo_sha", ""))))
        and collected_at is not None
        and window_start is not None
        and window_end is not None
        and window_start < window_end <= collected_at <= as_of
        and collected_at - window_end <= WINDOW_TAIL_MAX
        and as_of - collected_at <= PACKET_MAX_AGE
    )
    _add(
        findings,
        not metadata_ok,
        "EVIDENCE_CONTEXT_INVALID_OR_STALE",
        2,
        "packet identity, observation window, or freshness is invalid",
        "Recollect from the exact account/role/repository and analyze within 15 minutes; require a nonzero observation window.",
    )

    def in_window(timestamp: datetime | None) -> bool:
        return (
            timestamp is not None
            and window_start is not None
            and window_end is not None
            and window_start <= timestamp <= window_end
        )

    tf_fields = {
        "runtime_version",
        "platform",
        "provider_source",
        "previous_provider_version",
        "provider_version",
        "selected_provider_version",
        "lockfile_sha256",
        "backend_ref",
        "workspace_ref",
        "state",
        "plan",
        "resources",
        "preview_features_enabled",
        "preview_inventory",
    }
    tf_ok = (
        set(tf) == tf_fields
        and _version(tf.get("runtime_version"))
        and _safe_id(tf.get("platform"))
        and tf.get("provider_source") == "snowflakedb/snowflake"
        and all(
            _version(tf.get(field))
            for field in ("previous_provider_version", "provider_version", "selected_provider_version")
        )
        and (_version_tuple(tf.get("provider_version")) or (0, 0, 0))[0] == 2
        and tf.get("provider_version") == tf.get("selected_provider_version")
        and all(_sha(tf.get(field)) for field in ("lockfile_sha256", "backend_ref", "workspace_ref"))
    )
    _add(
        findings,
        not tf_ok,
        "TERRAFORM_TOOLCHAIN_OR_CONTEXT_UNVERIFIED",
        3,
        "runtime, selected provider, lock file, backend, or workspace is unverified",
        "Reproject terraform version -json, the lock file, backend/workspace refs, and the selected official provider.",
    )

    # Canonical Terraform JSON projection. Every decision is derived from these
    # bounded rows; the caller's count and detailed exit code must reconcile.
    resource_fields = {"resource_ref", "type", "actions", "preview", "existing", "import_ref"}
    resource_ok = True
    resource_refs: list[str] = []
    changed_refs: list[str] = []
    preview_refs: list[str] = []
    dbt_refs: list[str] = []
    action_counts: Counter[str] = Counter()
    actions_by_ref: dict[str, tuple[str, ...]] = {}
    for index, row in enumerate(resources):
        actions = row.get("actions")
        row_ok = (
            set(row) == resource_fields
            and _sha(row.get("resource_ref"))
            and _safe_id(row.get("type"))
            and isinstance(actions, list)
            and bool(actions)
            and tuple(actions) in ACTION_SEQUENCES
            and type(row.get("preview")) is bool
            and type(row.get("existing")) is bool
            and (row.get("import_ref") is None or _sha(row.get("import_ref")))
            and (
                (tuple(actions) == ("create",) and row.get("existing") is False)
                or (tuple(actions) != ("create",) and row.get("existing") is True)
            )
        )
        resource_ok = bool(resource_ok and row_ok)
        if not row_ok:
            continue
        ref = row["resource_ref"]
        resource_refs.append(ref)
        action_sequence = tuple(actions)
        action_label = "-".join(action_sequence)
        action_counts.update([action_label])
        actions_by_ref[ref] = action_sequence
        if actions != ["no-op"]:
            changed_refs.append(ref)
        if row["preview"]:
            preview_refs.append(ref)
        if "dbt_project" in row["type"].casefold():
            dbt_refs.append(ref)
        if (
            row["existing"]
            and "grant" in row["type"].casefold()
            and actions != ["no-op"]
            and not _sha(row.get("import_ref"))
        ):
            findings.append(
                _finding(
                    f"GRANT_IMPORT_REQUIRED-{index}",
                    20,
                    "an existing grant change lacks a privacy-safe import reference",
                    "Use the documented provider import identity, refresh, and require a reconciled plan; never hand-edit state.",
                )
            )
        if "delete" in actions:
            findings.append(
                _finding(
                    f"DESTRUCTIVE_PLAN_CHANGE-{index}",
                    40,
                    "a managed resource has a destructive action",
                    "Require impact ownership, a bound backup, tested rollback, and an approved window before operator apply.",
                )
            )
    _add(
        findings,
        not resource_ok or len(resource_refs) != len(set(resource_refs)),
        "PLAN_RESOURCE_INVENTORY_INVALID",
        4,
        "resource rows are malformed or duplicate",
        "Reproject the complete terraform show -json resource_changes into unique redacted refs and canonical action arrays.",
    )

    resources_digest = bundle_digest(resources)
    normalized_counts = {key: action_counts[key] for key in sorted(ACTION_VALUES)}
    plan_fields = {
        "format_version",
        "terraform_version",
        "complete",
        "errored",
        "refresh_enabled",
        "action_inventory_complete",
        "exit_code",
        "changes",
        "resource_change_count",
        "action_counts",
        "resources_sha256",
        "saved_plan_sha256",
        "prior_state_lineage_ref",
        "prior_state_serial",
        "generated_at",
        "receipt_sha256",
    }
    plan_at = _timestamp(plan.get("generated_at"))
    plan_ok = (
        _receipt(plan, plan_fields)
        and _version(plan.get("terraform_version"))
        and plan.get("terraform_version") == tf.get("runtime_version")
        and bool(re.fullmatch(r"1\.\d+", str(plan.get("format_version", ""))))
        and plan.get("complete") is True
        and plan.get("errored") is False
        and plan.get("refresh_enabled") is True
        and plan.get("action_inventory_complete") is True
        and _integer(plan.get("resource_change_count"))
        and plan.get("resource_change_count") == len(resources)
        and isinstance(plan.get("action_counts"), dict)
        and set(plan.get("action_counts", {})) == ACTION_VALUES
        and all(_integer(count) for count in plan.get("action_counts", {}).values())
        and plan.get("action_counts") == normalized_counts
        and plan.get("resources_sha256") == resources_digest
        and _sha(plan.get("saved_plan_sha256"))
        and _sha(plan.get("prior_state_lineage_ref"))
        and _integer(plan.get("prior_state_serial"))
        and plan_at is not None
        and collected_at is not None
        and collected_at - PACKET_MAX_AGE <= plan_at <= collected_at
        and in_window(plan_at)
    )
    _add(
        findings,
        not plan_ok,
        "PLAN_RECEIPT_UNVERIFIABLE",
        5,
        "the sanitized plan projection is incomplete, stale, contradictory, or hash-invalid",
        "Regenerate a complete terraform show -json projection and bind its actions, prior state, timestamps, and saved-plan hash.",
    )

    derived_changes = len(changed_refs)
    exit_code = plan.get("exit_code")
    declared_changes = plan.get("changes")
    exit_ok = (
        _integer(exit_code)
        and _integer(declared_changes)
        and (
            (exit_code == 0 and declared_changes == derived_changes == 0)
            or (exit_code == 2 and declared_changes == derived_changes and derived_changes > 0)
        )
    )
    _add(
        findings,
        not exit_ok,
        "PLAN_EXIT_ACTION_CONTRADICTION",
        6,
        "detailed exit status, change count, and canonical actions disagree",
        "Rerun plan -detailed-exitcode and derive the count from the complete action inventory.",
    )
    zero_change = bool(exit_ok and exit_code == 0)
    if exit_ok and not zero_change:
        findings.append(
            _finding(
                "PLAN_HAS_CHANGES",
                32,
                f"the trusted projection contains {derived_changes} changed resource(s)",
                "Keep release blocked until an authorized operator executes and independently verifies the approved plan.",
                "review",
            )
        )

    state_fields = {
        "parseable",
        "valid",
        "lineage_ref",
        "serial",
        "resource_count",
        "resource_refs",
        "resources_sha256",
        "lock_capability",
        "lock_status",
        "state_sha256",
    }
    state_ok = (
        set(state) == state_fields
        and state.get("parseable") is True
        and state.get("valid") is True
        and _sha(state.get("lineage_ref"))
        and _integer(state.get("serial"))
        and _integer(state.get("resource_count"))
        and isinstance(state.get("resource_refs"), list)
        and len(state.get("resource_refs", [])) == len(set(state.get("resource_refs", [])))
        and all(_sha(ref) for ref in state.get("resource_refs", []))
        and state.get("resource_count") == len(state.get("resource_refs", []))
        and state.get("resources_sha256") == bundle_digest(state.get("resource_refs", []))
        and all(
            not row.get("existing") or row.get("resource_ref") in state.get("resource_refs", [])
            for row in resources
            if isinstance(row, dict)
        )
        and (state.get("lock_capability"), state.get("lock_status"))
        in {("SUPPORTED", "ACQUIRED"), ("UNSUPPORTED", "NOT_APPLICABLE")}
        and _sha(state.get("state_sha256"))
        and plan.get("prior_state_lineage_ref") == state.get("lineage_ref")
        and plan.get("prior_state_serial") == state.get("serial")
    )
    _add(
        findings,
        not state_ok,
        "TERRAFORM_STATE_UNREADABLE_OR_UNBOUND",
        7,
        "state lineage, serial, lock, denominator, or plan binding is invalid",
        "Stop before apply; recover and verify the exact backend state, lock semantics, lineage, serial, and plan binding.",
    )

    backup = data["state_backup"]
    backup_fields = {
        "created",
        "verified",
        "account_ref",
        "backend_ref",
        "workspace_ref",
        "lineage_ref",
        "serial",
        "state_sha256",
        "captured_at",
        "receipt_sha256",
    }
    backup_at = _timestamp(backup.get("captured_at"))
    backup_ok = (
        _receipt(backup, backup_fields)
        and backup.get("created") is True
        and backup.get("verified") is True
        and backup.get("account_ref") == metadata.get("account_ref")
        and backup.get("backend_ref") == tf.get("backend_ref")
        and backup.get("workspace_ref") == tf.get("workspace_ref")
        and backup.get("lineage_ref") == state.get("lineage_ref")
        and backup.get("serial") == state.get("serial")
        and backup.get("state_sha256") == state.get("state_sha256")
        and backup_at is not None
        and plan_at is not None
        and collected_at is not None
        and collected_at - BACKUP_MAX_AGE <= backup_at <= plan_at
        and in_window(backup_at)
    )
    _add(
        findings,
        not backup_ok,
        "STATE_BACKUP_RECEIPT_UNVERIFIABLE",
        8,
        "backup is not bound to account/backend/workspace/state or was captured after plan generation",
        "Capture a verified backend version before plan generation and bind lineage, serial, and state digest.",
    )

    affected = data["affected_objects"]
    affected_expected = data.get("affected_objects_expected_count")
    affected_ok = data.get("affected_objects_verified") is True and _integer(affected_expected)
    affected_plan_refs: list[str] = []
    for row in affected:
        row_ok = (
            set(row) == {"object_ref", "plan_resource_ref"}
            and _sha(row.get("object_ref"))
            and _sha(row.get("plan_resource_ref"))
        )
        affected_ok = bool(affected_ok and row_ok)
        if row_ok:
            affected_plan_refs.append(row["plan_resource_ref"])
    affected_ok = bool(
        affected_ok
        and affected_expected == len(affected)
        and len(affected_plan_refs) == len(set(affected_plan_refs))
        and set(affected_plan_refs) == set(changed_refs)
    )
    _add(
        findings,
        not affected_ok,
        "AFFECTED_OBJECT_DENOMINATOR_UNVERIFIED",
        9,
        "affected objects do not exactly reconcile to changed plan resources",
        "Map each changed Terraform resource to one privacy-safe Snowflake object ref and record the exact count.",
    )

    preview = tf["preview_inventory"]
    preview_fields = {
        "verified",
        "provider_version",
        "expected_count",
        "detected_count",
        "resource_refs_sha256",
        "source_url",
        "observed_at",
        "receipt_sha256",
    }
    preview_at = _timestamp(preview.get("observed_at"))
    preview_features = tf.get("preview_features_enabled")
    preview_ok = (
        isinstance(preview_features, list)
        and len(preview_features) == len(set(preview_features))
        and all(_safe_id(item) for item in preview_features)
        and _receipt(preview, preview_fields)
        and preview.get("verified") is True
        and preview.get("provider_version") == tf.get("provider_version")
        and _integer(preview.get("expected_count"))
        and _integer(preview.get("detected_count"))
        and preview.get("expected_count") == len(preview_refs)
        and preview.get("detected_count") == len(preview_refs)
        and preview.get("resource_refs_sha256") == bundle_digest(sorted(preview_refs))
        and _source_for(preview.get("source_url"), "preview")
        and preview_at is not None
        and collected_at is not None
        and collected_at - PACKET_MAX_AGE <= preview_at <= collected_at
        and in_window(preview_at)
    )
    _add(
        findings,
        not preview_ok,
        "PROVIDER_PREVIEW_DENOMINATOR_UNVERIFIED",
        10,
        "preview detection is incomplete, stale, or not selected-provider bound",
        "Reconcile enabled experiments and detected preview resources against the selected version and official contract.",
    )
    _add(
        findings,
        bool(preview_refs or preview_features),
        "PROVIDER_PREVIEW_FEATURE",
        13,
        "the trusted plan or configuration contains preview functionality",
        "Verify the live preview contract, isolated-state behavior, and rollback; preview remains blocking by default.",
        "high",
    )

    provider_segments = data["provider_migrations"]
    provider_expected = data.get("provider_migrations_expected_count")
    provider_ok = data.get("provider_migrations_verified") is True and _integer(provider_expected)
    segment_projection: list[dict[str, Any]] = []
    provider_observation_times: list[datetime] = []
    segment_fields = {
        "from_version",
        "to_version",
        "source_url",
        "affected_count",
        "affected_address_refs",
        "affected_addresses_sha256",
        "source_snapshot_sha256",
        "observed_at",
        "state_move_required",
        "state_move_completed",
        "isolated_state_tested",
        "status",
        "receipt_sha256",
    }
    previous_to: str | None = None
    seen_provider_versions: set[str] = set()
    for index, row in enumerate(provider_segments):
        from_tuple = _version_tuple(row.get("from_version"))
        to_tuple = _version_tuple(row.get("to_version"))
        affected_addresses = row.get("affected_address_refs")
        observed_at = _timestamp(row.get("observed_at"))
        row_ok = (
            _receipt(row, segment_fields)
            and _version(row.get("from_version"))
            and _version(row.get("to_version"))
            and _source_for(row.get("source_url"), "provider_migration")
            and _integer(row.get("affected_count"))
            and isinstance(affected_addresses, list)
            and len(affected_addresses) == len(set(affected_addresses))
            and all(_sha(ref) for ref in affected_addresses)
            and row.get("affected_count") == len(affected_addresses)
            and row.get("affected_addresses_sha256") == bundle_digest(affected_addresses)
            and all(ref in state.get("resource_refs", []) for ref in affected_addresses)
            and all(ref in resource_refs for ref in affected_addresses)
            and _sha(row.get("source_snapshot_sha256"))
            and observed_at is not None
            and collected_at is not None
            and collected_at - PACKET_MAX_AGE <= observed_at <= collected_at
            and in_window(observed_at)
            and type(row.get("state_move_required")) is bool
            and type(row.get("state_move_completed")) is bool
            and row.get("state_move_completed") is row.get("state_move_required")
            and (row.get("state_move_required") is False or row.get("affected_count") > 0)
            and row.get("isolated_state_tested") is True
            and row.get("status") in {"VERIFIED", "NOT_APPLICABLE"}
            and from_tuple is not None
            and to_tuple is not None
            and from_tuple < to_tuple
            and (
                (from_tuple[0] == to_tuple[0] and to_tuple[1] - from_tuple[1] <= 1)
                or (to_tuple[0] == from_tuple[0] + 1 and to_tuple[1] == 0)
            )
            and (previous_to is None or row.get("from_version") == previous_to)
            and (index != 0 or row.get("from_version") == tf.get("previous_provider_version"))
            and row.get("to_version") not in seen_provider_versions
            and (
                row.get("status") != "NOT_APPLICABLE"
                or (row.get("affected_count") == 0 and row.get("state_move_required") is False)
            )
        )
        provider_ok = bool(provider_ok and row_ok)
        if row_ok:
            provider_observation_times.append(observed_at)
            if index == 0:
                seen_provider_versions.add(row["from_version"])
            seen_provider_versions.add(row["to_version"])
        previous_to = row.get("to_version") if isinstance(row.get("to_version"), str) else None
        if row_ok:
            segment_projection.append(
                {
                    "from_version": row["from_version"],
                    "to_version": row["to_version"],
                    "status": row["status"],
                    "affected_count": row["affected_count"],
                    "state_move_required": row["state_move_required"],
                    "state_move_completed": row["state_move_completed"],
                    "isolated_state_tested": row["isolated_state_tested"],
                }
            )
    upgrade = tf.get("previous_provider_version") != tf.get("provider_version")
    provider_ok = bool(
        provider_ok
        and provider_expected == len(provider_segments)
        and ((not upgrade and provider_expected == 0) or (upgrade and provider_expected > 0))
        and (not provider_segments or previous_to == tf.get("provider_version"))
    )
    _add(
        findings,
        not provider_ok,
        "PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED",
        14,
        "provider migration segments are missing, unordered, discontinuous, open, or unbound",
        "Inventory every official guide segment from locked prior provider to selected target and test state/import boundaries.",
    )

    migrations = data["migrations"]
    migrations_expected = data.get("migrations_expected_count")
    change_history_expected = data.get("change_history_expected_count")
    migrations_observed_at = _timestamp(data.get("migrations_observed_at"))
    migrations_ok = (
        data.get("migrations_verified") is True
        and _integer(migrations_expected)
        and migrations_expected > 0
        and _integer(change_history_expected)
        and change_history_expected > 0
        and in_window(migrations_observed_at)
        and collected_at is not None
        and collected_at - PACKET_MAX_AGE <= migrations_observed_at <= collected_at
    )
    migration_refs: list[str] = []
    migration_names: list[str] = []
    versions: Counter[tuple[int, ...]] = Counter()
    migration_order: list[tuple[int, Any]] = []
    migration_projection: list[dict[str, Any]] = []
    migration_fields = {
        "migration_ref",
        "script_type",
        "script_name",
        "version",
        "checksum_sha256",
        "applied_checksum_sha256",
        "status",
        "installed_at",
        "pending",
        "out_of_order",
        "dry_run_verified",
        "rendered_sql_redacted",
        "always_run_reviewed",
        "idempotence_verified",
        "receipt_sha256",
    }
    for index, row in enumerate(migrations):
        script_type = row.get("script_type")
        installed_at = _timestamp(row.get("installed_at")) if row.get("installed_at") is not None else None
        version_value = row.get("version")
        version_tuple = _migration_version_tuple(version_value)
        script_key = _migration_script_key(row)
        row_ok = (
            _receipt(row, migration_fields)
            and _sha(row.get("migration_ref"))
            and script_type in {"V", "R", "A"}
            and script_key is not None
            and _sha(row.get("checksum_sha256"))
            and (row.get("applied_checksum_sha256") is None or _sha(row.get("applied_checksum_sha256")))
            and row.get("status") in {"SUCCESS", "PENDING", "FAILED"}
            and type(row.get("pending")) is bool
            and type(row.get("out_of_order")) is bool
            and type(row.get("dry_run_verified")) is bool
            and row.get("dry_run_verified") is True
            and row.get("rendered_sql_redacted") is True
            and type(row.get("always_run_reviewed")) is bool
            and type(row.get("idempotence_verified")) is bool
            and installed_at is not None
            and migrations_observed_at is not None
            and installed_at <= migrations_observed_at
            and collected_at is not None
            and installed_at <= collected_at
        )
        migrations_ok = bool(migrations_ok and row_ok)
        if not row_ok:
            continue
        migration_refs.append(row["migration_ref"])
        migration_names.append(_canonical_script_name(row["script_name"]))
        if script_type == "V" and version_tuple is not None:
            versions[version_tuple] += 1
        migration_order.append(script_key)
        if row["status"] != "SUCCESS" or row["pending"]:
            findings.append(
                _finding(
                    f"MIGRATION_PENDING_OR_FAILED-{index}",
                    22,
                    "a migration is not a settled successful history row",
                    "Review dry-run order and CHANGE_HISTORY; do not deploy or mark failed/pending scripts complete.",
                )
            )
        if row["out_of_order"]:
            findings.append(
                _finding(
                    f"MIGRATION_OUT_OF_ORDER-{index}",
                    23,
                    "a migration depends on out-of-order execution",
                    "Resolve ordering and explicitly review the current schemachange out-of-order policy.",
                    "high",
                )
            )
        applied = row.get("applied_checksum_sha256")
        current = row.get("checksum_sha256")
        if script_type == "V" and (applied is None or current != applied):
            findings.append(
                _finding(
                    f"VERSIONED_CHECKSUM_DRIFT-{index}",
                    20,
                    "an applied versioned migration lacks a matching checksum",
                    "Restore the applied script or create a new versioned migration; never edit CHANGE_HISTORY.",
                )
            )
        if script_type == "R" and applied is None:
            findings.append(
                _finding(
                    f"REPEATABLE_HISTORY_MISSING-{index}",
                    20,
                    "a successful repeatable migration lacks its installed checksum",
                    "Reconcile the exact successful CHANGE_HISTORY row before evaluating a repeatable rerun.",
                )
            )
        if script_type == "R" and applied is not None and current != applied:
            findings.append(
                _finding(
                    f"REPEATABLE_CHANGE_DETECTED-{index}",
                    25,
                    "a repeatable migration checksum changed",
                    "Verify intended rerun scope and idempotence after versioned scripts before deployment.",
                    "review",
                )
            )
        if script_type == "A" and not (row.get("always_run_reviewed") and row.get("idempotence_verified")):
            findings.append(
                _finding(
                    f"ALWAYS_MIGRATION_UNREVIEWED-{index}",
                    24,
                    "an always-run migration lacks scope and idempotence proof",
                    "Review the always script that runs every invocation and last; prove bounded idempotence.",
                )
            )
        if script_type == "A" and (applied is None or current != applied):
            findings.append(
                _finding(
                    f"ALWAYS_HISTORY_MISMATCH-{index}",
                    24,
                    "a successful always-run migration lacks a matching installed checksum",
                    "Reconcile the last successful always-run history row and review its next execution separately.",
                )
            )
        migration_projection.append(
            {
                "migration_ref": row.get("migration_ref"),
                "script_type": script_type,
                "status": row.get("status"),
                "checksum_status": "match" if applied == current else "changed" if applied else "not_observed",
            }
        )
    migrations_ok = bool(
        migrations_ok
        and migrations_expected == len(migrations)
        and change_history_expected >= len(migrations)
        and data.get("migration_repository_sha256") == bundle_digest(migrations)
        and _sha(data.get("change_history_sha256"))
        and data.get("change_history_projection_sha256") == bundle_digest(migrations)
        and len(migration_refs) == len(set(migration_refs))
        and len(migration_names) == len(set(migration_names))
        and all(count == 1 for count in versions.values())
        and migration_order == sorted(migration_order)
    )
    _add(
        findings,
        not migrations_ok,
        "MIGRATION_DENOMINATOR_UNVERIFIED",
        19,
        "repository/history denominator is incomplete, duplicated, malformed, or hash-invalid",
        "Reconcile every V/R/A script to CHANGE_HISTORY and repository with status, time, checksum, order, and redacted dry-run proof.",
    )

    bcr = data["bcr"]
    bcr_inventory = bcr["inventory"]
    bcr_fields = {
        "bundle",
        "status",
        "source_url",
        "source_snapshot_sha256",
        "observed_at",
        "expected_count",
        "complete",
        "inventory_sha256",
        "inventory",
        "receipt_sha256",
    }
    bcr_item_fields = {
        "item_id",
        "affected",
        "affected_refs",
        "owner_ref",
        "disposition",
        "receipt_sha256",
    }
    bcr_at = _timestamp(bcr.get("observed_at"))
    bcr_ok = (
        _receipt(bcr, bcr_fields)
        and bool(re.fullmatch(r"\d{4}_\d{2}", str(bcr.get("bundle", ""))))
        and bcr.get("status") in {"ENABLED", "DISABLED", "RELEASED"}
        and _source_for(bcr.get("source_url"), "bcr")
        and bcr.get("source_url")
        == f"https://docs.snowflake.com/en/release-notes/bcr-bundles/{bcr.get('bundle')}_bundle"
        and _sha(bcr.get("source_snapshot_sha256"))
        and bcr_at is not None
        and collected_at is not None
        and collected_at - BCR_MAX_AGE <= bcr_at <= collected_at
        and in_window(bcr_at)
        and _integer(bcr.get("expected_count"))
        and bcr.get("expected_count") == len(bcr_inventory)
        and bcr.get("expected_count") > 0
        and bcr.get("complete") is True
        and bcr.get("inventory_sha256") == bundle_digest(bcr_inventory)
    )
    bcr_ids: list[str] = []
    bcr_projection: list[dict[str, Any]] = []
    for index, row in enumerate(bcr_inventory):
        refs = row.get("affected_refs")
        affected_flag = row.get("affected")
        row_ok = (
            _receipt(row, bcr_item_fields)
            and bool(re.fullmatch(r"BCR-\d{4}", str(row.get("item_id", ""))))
            and type(affected_flag) is bool
            and isinstance(refs, list)
            and len(refs) == len(set(refs))
            and all(_sha(ref) for ref in refs)
            and _sha(row.get("owner_ref"))
            and row.get("disposition") in DISPOSITIONS
            and ((affected_flag and bool(refs)) or (not affected_flag and not refs))
            and (not affected_flag or row.get("disposition") in {"VERIFIED", "MITIGATED", "ACCEPTED"})
            and (affected_flag or row.get("disposition") == "NOT_APPLICABLE")
        )
        bcr_ok = bool(bcr_ok and row_ok)
        if not row_ok:
            continue
        bcr_ids.append(row["item_id"])
        if affected_flag:
            findings.append(
                _finding(
                    f"BCR_IMPACT_REQUIRES_REVIEW-{index}",
                    16,
                    "a current behavior-change item affects the bounded deployment",
                    "Review the official item, affected object refs, owner, disposition, and rollback before operator apply.",
                    "review",
                )
            )
        bcr_projection.append(
            {
                "item_id": row["item_id"],
                "affected": affected_flag,
                "disposition": row["disposition"],
                "affected_count": len(refs),
            }
        )
    expected_bcr_ids = BCR_BUNDLE_ITEMS.get(str(bcr.get("bundle")))
    bcr_ok = bool(
        bcr_ok
        and len(bcr_ids) == len(set(bcr_ids))
        and expected_bcr_ids is not None
        and set(bcr_ids) == expected_bcr_ids
        and bcr.get("source_snapshot_sha256") == bundle_digest(sorted(expected_bcr_ids))
    )
    bcr_by_id = {
        row["item_id"]: row
        for row in bcr_inventory
        if isinstance(row.get("item_id"), str) and row.get("item_id") in bcr_ids
    }
    _add(
        findings,
        not bcr_ok,
        "BCR_INVENTORY_UNVERIFIED",
        15,
        "behavior-change bundle status or item denominator is malformed, stale, duplicated, or hash-invalid",
        "Requery SYSTEM$BEHAVIOR_CHANGE_BUNDLE_STATUS and reconcile every official bundle item to redacted affected refs.",
    )

    dbt_projects = data["dbt_projects"]
    dbt_expected = data.get("dbt_projects_expected_count")
    dbt_ok = data.get("dbt_projects_verified") is True and _integer(dbt_expected)
    dbt_fields = {
        "project_ref",
        "plan_resource_ref",
        "current_model",
        "target_model",
        "bundle_status",
        "bcr_item_id",
        "bcr_disposition",
        "target_version_supported",
        "deployed_code_sha256",
        "staged_code_sha256",
        "rollback_artifact_sha256",
        "profile_verified",
        "dependencies_verified",
        "compile_verified",
        "build_verified",
        "tests_verified",
        "force_replace",
        "ownership_verified",
        "early_opt_in_verified",
        "early_opt_in_ref",
        "demigration_available",
        "observed_at",
        "receipt_sha256",
    }
    dbt_plan_refs: list[str] = []
    dbt_projection: list[dict[str, Any]] = []
    dbt_observation_times: list[datetime] = []
    for index, row in enumerate(dbt_projects):
        observed_at = _timestamp(row.get("observed_at"))
        bound_bcr = bcr_by_id.get("BCR-2362")
        row_ok = (
            _receipt(row, dbt_fields)
            and _sha(row.get("project_ref"))
            and _sha(row.get("plan_resource_ref"))
            and row.get("current_model") in {"VERSIONED", "LIVE"}
            and row.get("target_model") in {"VERSIONED", "LIVE"}
            and row.get("bundle_status") == bcr.get("status")
            and row.get("bcr_item_id") == "BCR-2362"
            and row.get("bcr_disposition") in DISPOSITIONS
            and bound_bcr is not None
            and bound_bcr.get("affected") is True
            and row.get("project_ref") in bound_bcr.get("affected_refs", [])
            and row.get("bcr_disposition") == bound_bcr.get("disposition")
            and all(
                type(row.get(field)) is bool
                for field in (
                    "target_version_supported",
                    "profile_verified",
                    "dependencies_verified",
                    "compile_verified",
                    "build_verified",
                    "tests_verified",
                    "force_replace",
                    "ownership_verified",
                    "early_opt_in_verified",
                    "demigration_available",
                )
            )
            and (
                (row.get("early_opt_in_verified") is True and _sha(row.get("early_opt_in_ref")))
                or (row.get("early_opt_in_verified") is False and row.get("early_opt_in_ref") is None)
            )
            and (row.get("early_opt_in_verified") is False or bcr.get("status") == "DISABLED")
            and all(
                _sha(row.get(field))
                for field in (
                    "deployed_code_sha256",
                    "staged_code_sha256",
                    "rollback_artifact_sha256",
                )
            )
            and observed_at is not None
            and collected_at is not None
            and collected_at - PACKET_MAX_AGE <= observed_at <= collected_at
            and in_window(observed_at)
        )
        dbt_ok = bool(dbt_ok and row_ok)
        if not row_ok:
            continue
        dbt_plan_refs.append(row["plan_resource_ref"])
        dbt_observation_times.append(observed_at)
        safe = all(
            row[field] is True
            for field in (
                "target_version_supported",
                "profile_verified",
                "dependencies_verified",
                "compile_verified",
                "build_verified",
                "tests_verified",
                "ownership_verified",
            )
        )
        artifact_changed_without_plan = row["deployed_code_sha256"] != row["staged_code_sha256"] and actions_by_ref.get(
            row["plan_resource_ref"]
        ) == ("no-op",)
        preflight_safe = safe and not row["force_replace"] and not artifact_changed_without_plan
        if not preflight_safe:
            findings.append(
                _finding(
                    f"DBT_PROJECT_PREFLIGHT_INCOMPLETE-{index}",
                    17,
                    "a dbt Project object lacks supported-version, build/test, ownership, or non-destructive proof",
                    "Stage the exact artifact, verify profile/dependencies/compile/build/tests and ownership, and prohibit unreviewed FORCE replacement.",
                )
            )
        early_opted_in = row["early_opt_in_verified"]
        model_transition_ok = (
            (bcr.get("status") == "RELEASED" and row["current_model"] == row["target_model"] == "LIVE")
            or bcr.get("status") == "ENABLED"
            or (
                bcr.get("status") == "DISABLED"
                and ((row["current_model"] == row["target_model"] == "VERSIONED") or early_opted_in)
            )
        )
        if bcr.get("status") == "RELEASED" and (row["current_model"] != "LIVE" or row["target_model"] != "LIVE"):
            findings.append(
                _finding(
                    f"DBT_PROJECT_LIVE_VERSION_REQUIRED-{index}",
                    18,
                    "the released behavior change requires the live version model",
                    "Migrate the bounded dbt Project object to LIVE with a tested rollback artifact and BCR-2362 disposition.",
                )
            )
        if bcr.get("status") == "DISABLED" and not model_transition_ok:
            findings.append(
                _finding(
                    f"DBT_PROJECT_BCR_NOT_ACTIVE-{index}",
                    18,
                    "the requested dbt Project version-model transition is not active for the target account",
                    "Keep the current model until the exact account bundle is enabled, then recollect and re-evaluate.",
                )
            )
        demigration_ok = (
            (
                bcr.get("status") == "DISABLED"
                and row["demigration_available"]
                is (early_opted_in and (row["current_model"] == "LIVE" or row["target_model"] == "LIVE"))
            )
            or (
                bcr.get("status") == "ENABLED"
                and row["demigration_available"] is (row["current_model"] == "LIVE" or row["target_model"] == "LIVE")
            )
            or (bcr.get("status") == "RELEASED" and row["demigration_available"] is False)
        )
        if not demigration_ok:
            findings.append(
                _finding(
                    f"DBT_PROJECT_DEMIGRATION_BOUNDARY_INVALID-{index}",
                    18,
                    "the claimed dbt Project rollback capability contradicts the target account bundle state",
                    "Verify the live SYSTEM$MIGRATE/SYSTEM$DEMIGRATE boundary and bind rollback to the current account status.",
                )
            )
        projected_safe = preflight_safe and model_transition_ok and demigration_ok and bcr_ok
        dbt_projection.append(
            {
                "project_ref": row["project_ref"],
                "current_model": row["current_model"],
                "target_model": row["target_model"],
                "early_opt_in_verified": row["early_opt_in_verified"],
                "safe": projected_safe,
            }
        )
    dbt_ok = bool(
        dbt_ok
        and dbt_expected == len(dbt_projects) == len(dbt_refs)
        and len(dbt_plan_refs) == len(set(dbt_plan_refs))
        and set(dbt_plan_refs) == set(dbt_refs)
        and (not dbt_refs or (bcr.get("bundle") == "2026_06" and "BCR-2362" in bcr_ids))
    )
    _add(
        findings,
        not dbt_ok,
        "DBT_PROJECT_DENOMINATOR_UNVERIFIED",
        17,
        "dbt Project objects do not exactly reconcile to the plan and current behavior-change evidence",
        "Inventory every planned dbt Project object and bind BCR-2362, runtime, artifacts, tests, ownership, and rollback evidence.",
    )

    tools = data["tools"]
    tool_fields = {"version", "source_url", "observed_at"}
    required_tools = {"snowflake_cli", "python_connector", "schemachange"}
    tools_ok = set(tools) == required_tools
    tool_projection: dict[str, str] = {}
    tool_observation_times: list[datetime] = []
    for name in sorted(required_tools):
        row = tools.get(name)
        observed_at = _timestamp(row.get("observed_at")) if isinstance(row, dict) else None
        row_ok = (
            isinstance(row, dict)
            and set(row) == tool_fields
            and _version(row.get("version"))
            and _source_for(row.get("source_url"), name)
            and observed_at is not None
            and collected_at is not None
            and collected_at - PACKET_MAX_AGE <= observed_at <= collected_at
            and in_window(observed_at)
        )
        tools_ok = bool(tools_ok and row_ok)
        if row_ok:
            tool_projection[name] = row["version"]
            tool_observation_times.append(observed_at)
    _add(
        findings,
        not tools_ok,
        "DEPLOY_TOOLCHAIN_UNVERIFIED",
        11,
        "the required deployment tool versions are incomplete, stale, or unofficial",
        "Capture current Snowflake CLI, connector, and schemachange versions from official distributions.",
    )

    rollback = data["rollback"]
    rollback_at = _timestamp(rollback.get("tested_at"))

    preflight = data["preflight"]
    preflight_fields = {"completed", "operator_ref", "checked_at", "checks", "receipt_sha256"}
    checked_at = _timestamp(preflight.get("checked_at"))
    check_names: list[str] = []
    checks_ok = True
    for row in preflight["checks"]:
        row_ok = (
            set(row) == {"name", "status"} and row.get("name") in REQUIRED_PREFLIGHT and row.get("status") == "PASS"
        )
        checks_ok = bool(checks_ok and row_ok)
        if row_ok:
            check_names.append(row["name"])
    preflight_ok = (
        _receipt(preflight, preflight_fields)
        and preflight.get("completed") is True
        and _sha(preflight.get("operator_ref"))
        and checked_at is not None
        and collected_at is not None
        and collected_at - PACKET_MAX_AGE <= checked_at <= collected_at
        and plan_at is not None
        and checked_at
        >= max(
            timestamp
            for timestamp in (
                plan_at,
                backup_at,
                preview_at,
                bcr_at,
                migrations_observed_at,
                rollback_at,
                *provider_observation_times,
                *tool_observation_times,
                *dbt_observation_times,
            )
            if timestamp is not None
        )
        and in_window(checked_at)
        and checks_ok
        and len(check_names) == len(set(check_names))
        and set(check_names) == REQUIRED_PREFLIGHT
    )
    _add(
        findings,
        not preflight_ok,
        "PREFLIGHT_DENOMINATOR_UNVERIFIED",
        12,
        "the exact preflight checklist is incomplete, duplicated, stale, or hash-invalid",
        "Run and receipt every required identity, state, plan, migration, BCR, rollback, and invariant check.",
    )

    rollback_fields = {
        "tested",
        "strategy",
        "owner_ref",
        "stop_condition_ref",
        "tested_at",
        "plan_sha256",
        "migration_inventory_sha256",
        "receipt_sha256",
    }
    rollback_ok = (
        _receipt(rollback, rollback_fields)
        and rollback.get("tested") is True
        and rollback.get("strategy") in {"STATE_RESTORE", "FORWARD_FIX", "ARTIFACT_ROLLBACK"}
        and _sha(rollback.get("owner_ref"))
        and _sha(rollback.get("stop_condition_ref"))
        and rollback_at is not None
        and collected_at is not None
        and collected_at - ROLLBACK_MAX_AGE <= rollback_at <= collected_at
        and plan_at is not None
        and rollback_at >= plan_at
        and in_window(rollback_at)
        and rollback.get("plan_sha256") == plan.get("saved_plan_sha256")
        and rollback.get("migration_inventory_sha256") == bundle_digest(migrations)
    )
    _add(
        findings,
        not rollback_ok,
        "ROLLBACK_RECEIPT_UNVERIFIABLE",
        27,
        "rollback proof is stale, hash-invalid, or unbound to the plan and migration inventory",
        "Test a bounded rollback strategy and bind its owner, stop condition, saved plan, and migration inventory.",
    )

    invariants = data["post_change_invariants"]
    invariant_expected = data.get("post_change_invariants_expected_count")
    invariant_ok = data.get("post_change_invariants_verified") is True and _integer(invariant_expected)
    invariant_fields = {
        "invariant_ref",
        "plan_resource_ref",
        "account_ref",
        "plan_sha256",
        "owner_ref",
        "expected_digest",
        "verification_kind",
        "rollback_trigger_ref",
        "status",
        "receipt_sha256",
    }
    invariant_refs: list[str] = []
    invariant_plan_refs: list[str] = []
    for row in invariants:
        row_ok = (
            _receipt(row, invariant_fields)
            and all(
                _sha(row.get(field))
                for field in (
                    "invariant_ref",
                    "plan_resource_ref",
                    "account_ref",
                    "plan_sha256",
                    "owner_ref",
                    "expected_digest",
                    "rollback_trigger_ref",
                )
            )
            and row.get("account_ref") == metadata.get("account_ref")
            and row.get("plan_resource_ref") in changed_refs
            and row.get("plan_sha256") == plan.get("saved_plan_sha256")
            and row.get("verification_kind") in {"READ_ONLY_SQL", "STATE_READ", "METADATA_READ", "ARTIFACT_HASH"}
            and row.get("status") == "PLANNED"
        )
        invariant_ok = bool(invariant_ok and row_ok)
        if row_ok:
            invariant_refs.append(row["invariant_ref"])
            invariant_plan_refs.append(row["plan_resource_ref"])
    invariant_ok = bool(
        invariant_ok
        and invariant_expected == len(invariants)
        and len(invariant_refs) == len(set(invariant_refs))
        and len(invariant_plan_refs) == len(set(invariant_plan_refs))
        and set(invariant_plan_refs) == set(changed_refs)
    )
    _add(
        findings,
        not invariant_ok,
        "POST_CHANGE_INVARIANTS_UNVERIFIED",
        28,
        "post-change verification plans are incomplete, duplicate, malformed, or unbound",
        "Define account/plan-bound read-only invariants, expected digests, owners, and rollback triggers for every changed plan.",
    )

    zero_receipt = data["zero_change_receipt"]
    zero_fields = {
        "issued",
        "plan_sha256",
        "affected_objects",
        "resources_sha256",
        "issued_at",
        "receipt_sha256",
    }
    zero_at = _timestamp(zero_receipt.get("issued_at"))
    zero_ok = (
        _receipt(zero_receipt, zero_fields)
        and zero_receipt.get("issued") is zero_change
        and zero_receipt.get("plan_sha256") == plan.get("saved_plan_sha256")
        and type(zero_receipt.get("affected_objects")) is int
        and zero_receipt.get("affected_objects") == len(affected)
        and zero_receipt.get("resources_sha256") == resources_digest
        and zero_at is not None
        and plan_at is not None
        and collected_at is not None
        and plan_at <= zero_at <= collected_at
    )
    _add(
        findings,
        not zero_ok,
        "ZERO_CHANGE_RECEIPT_UNVERIFIABLE",
        29,
        "zero/change classification receipt is contradictory, stale, or unbound",
        "Issue the receipt only from the reconciled detailed exit code, resource actions, affected denominator, and plan digest.",
    )

    findings.sort(key=lambda item: (item["recovery_rank"], item["code"]))
    recovery: list[str] = []
    for item in findings:
        if item["read_only_action"] not in recovery:
            recovery.append(item["read_only_action"])
    if findings:
        for project in dbt_projection:
            project["safe"] = False
    status = "PASS_AS_OF" if zero_change and not findings else "BLOCKED"
    return {
        "schema_version": "2",
        "status": status,
        "safe_to_apply": False,
        "trusted_bundle_sha256": actual_digest if trusted else None,
        "analysis_as_of_utc": _iso(as_of),
        "temporal_qualification": {
            "kind": "point_in_time_only",
            "valid_until_utc": _iso(as_of),
            "reason": "Snowflake account, bundle, provider, state, and repository facts can change after analysis.",
        },
        "summary": {
            "plan_change_count": derived_changes,
            "resource_count": len(resources),
            "affected_object_count": len(affected),
            "provider_migration_segment_count": len(provider_segments),
            "migration_count": len(migrations),
            "dbt_project_count": len(dbt_projects),
            "post_change_invariant_count": len(invariants),
            "bcr_item_count": len(bcr_inventory),
            "preview_resource_count": len(preview_refs),
        },
        "tool_versions": tool_projection,
        "provider_migrations": segment_projection,
        "migrations": migration_projection,
        "bcr_items": bcr_projection,
        "dbt_projects": dbt_projection,
        "findings": findings,
        "recovery_sequence": recovery,
        "operator_boundary": "This report never applies changes. Recollect and reanalyze immediately before an authorized operator action.",
    }


def _read_input(argument: str | None) -> str:
    if argument is None or argument == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        path = Path(argument)
        if path.is_absolute() or ".." in path.parts or path.is_symlink():
            raise ValueError("input path must be a nonsymlink relative file below the current directory")
        resolved = path.resolve()
        current = Path.cwd().resolve()
        if current != resolved.parent and current not in resolved.parents:
            raise ValueError("input path must remain below the current directory")
        if not resolved.is_file():
            raise ValueError("input must be a regular file")
        if resolved.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("input exceeds the byte limit")
        raw = resolved.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds the byte limit")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("input must be UTF-8 JSON") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="relative JSON evidence file; omit or use - for stdin")
    parser.add_argument("--as-of", required=True, help="explicit UTC analysis timestamp")
    parser.add_argument("--trusted-bundle-sha256", required=True, help="trusted digest for the exact JSON packet")
    args = parser.parse_args()
    try:
        report = analyze(
            _strict_json(_read_input(args.input)),
            analysis_as_of=args.as_of,
            trusted_bundle_sha256=args.trusted_bundle_sha256,
        )
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else "unable to read or analyze input"
        print(f"error: {message}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
