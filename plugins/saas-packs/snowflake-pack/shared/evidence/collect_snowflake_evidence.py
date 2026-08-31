#!/usr/bin/env python3
"""Collect bounded read-only Snowflake evidence through an existing CLI profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
SURFACES = {
    "access": (
        "access.sql",
        [
            "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES",
            "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS",
            "SNOWFLAKE.ACCOUNT_USAGE.ROLES",
        ],
    ),
    "auth": ("auth.sql", ["SNOWFLAKE.ACCOUNT_USAGE.USERS", "SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY"]),
    "cost": (
        "cost.sql",
        [
            "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY",
        ],
    ),
    "data-quality": (
        "data-quality.sql",
        [
            "SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS",
            "SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY",
        ],
    ),
    "pipeline": (
        "pipeline.sql",
        [
            "SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.DYNAMIC_TABLE_REFRESH_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY",
        ],
    ),
    "query": (
        "query.sql",
        [
            "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
        ],
    ),
    "replication": ("replication.sql", ["SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_GROUP_REFRESH_HISTORY"]),
}
SUBSURFACES = {
    "access-current": ("access-current.sql", ["SHOW GRANTS ON ACCOUNT"], None),
    "access-future": ("access-future.sql", ["SHOW FUTURE GRANTS"], "database"),
    "auth-current": ("auth-current.sql", ["SHOW USERS"], None),
    "cost-adaptive": ("cost-adaptive.sql", ["SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY"], None),
    "cost-ai-functions": ("cost-ai-functions.sql", ["SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY"], None),
    "cost-budgets": ("cost-budgets.sql", ["SHOW SNOWFLAKE.CORE.BUDGET"], None),
    "cost-internal-transfer": ("cost-internal-transfer.sql", ["SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY"], None),
    "cost-resource-monitors": ("cost-resource-monitors.sql", ["SHOW RESOURCE MONITORS"], None),
    "cost-storage": ("cost-storage.sql", ["SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE"], None),
    "cost-transfer": ("cost-transfer.sql", ["SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY"], None),
    "data-quality-current": ("data-quality-current.sql", ["SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES"], None),
    "pipeline-current": ("pipeline-current.sql", ["SHOW TASKS", "SHOW STREAMS", "SHOW DYNAMIC TABLES", "SHOW PIPES"], None),
    "query-operator-stats": ("query-operator-stats.sql", ["GET_QUERY_OPERATOR_STATS"], "query_id"),
    "query-insights": ("query-insights.sql", ["SNOWFLAKE.ACCOUNT_USAGE.QUERY_INSIGHTS"], "query_id"),
    "replication-current": ("replication-current.sql", ["SHOW REPLICATION GROUPS", "INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL"], None),
}
FORBIDDEN_SQL = {
    "ALTER",
    "CALL",
    "COPY",
    "CREATE",
    "DELETE",
    "DROP",
    "EXECUTE",
    "GET",
    "GRANT",
    "INSERT",
    "MERGE",
    "PUT",
    "REMOVE",
    "REPLACE",
    "REVOKE",
    "TRUNCATE",
    "UNDROP",
    "UPDATE",
    "USE",
}
SAFE_START = {"DESCRIBE", "SELECT", "SHOW", "WITH"}
PROFILE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
QUERY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}$")
SELECTOR_MARKERS = {"query_id": "__QUERY_ID__", "database": "__DATABASE_IDENTIFIER__"}
SENSITIVE_KEYS = {
    "account_endpoint",
    "account_endpoints",
    "account_identifier",
    "account_locator",
    "account_name",
    "account_url",
    "allowed_accounts",
    "api_key",
    "authorization",
    "credential",
    "credentials",
    "detail",
    "details",
    "endpoint",
    "host",
    "hostname",
    "jwt",
    "oauth_token",
    "password",
    "passphrase",
    "pii",
    "private_key",
    "query_text",
    "raw_rows",
    "secret",
    "session_token",
    "sql_text",
    "token",
}
FORBIDDEN_RAW_METADATA_KEYS = {
    "endpoint",
    "endpoints",
    "filter",
    "filter_value",
    "filter_values",
    "group_by_values",
    "group_values",
    "raw_filter",
    "raw_group_values",
    "within_group",
}
REDACTIONS = (
    (re.compile(r"(?i)\bBearer\s+\S+"), "[REDACTED_BEARER]"),
    (re.compile(r"(?i)\b(password|token|secret|private[_-]?key|authorization)\s*[=:]\s*\S+"), "[REDACTED_CREDENTIAL]"),
    (re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s/]+@\S+", re.IGNORECASE), "[REDACTED_CONNECTION_URL]"),
    (re.compile(r"https?://\S+[?&](?:X-Amz-|X-Goog-|sig=|signature=)\S*", re.IGNORECASE), "[REDACTED_PRESIGNED_URL]"),
)


class CollectionError(ValueError):
    """Raised when evidence collection would be unsafe or malformed."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sanitize_text(value: Any) -> str:
    text = str(value)
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    return text[:2000]


def reject_secret_fields(value: Any, path: str = "result") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
            # Boolean metadata such as HAS_PASSWORD is safe; password material is not.
            if normalized in {"query_tag", "user_name"}:
                raise CollectionError(
                    f"raw identity/tag field is not accepted: {path}.{key}; use a Snowflake-side hash"
                )
            if normalized in SENSITIVE_KEYS or normalized.endswith(("_token", "_secret", "_private_key")):
                category = (
                    "credential-bearing field; raw filter/group/endpoint field"
                    if normalized in FORBIDDEN_RAW_METADATA_KEYS
                    else "credential-bearing field"
                )
                raise CollectionError(f"{category} is not accepted: {path}.{key}")
            if normalized in FORBIDDEN_RAW_METADATA_KEYS:
                raise CollectionError(
                    f"raw filter/group/endpoint field is not accepted: {path}.{key}"
                )
            reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_fields(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern, _ in REDACTIONS):
            raise CollectionError(f"credential-like value is not accepted: {path}")


def strip_sql_comments_and_strings(sql: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    without_lines = re.sub(r"--[^\n]*", " ", without_blocks)
    return re.sub(r"'(?:''|[^'])*'", "''", without_lines)


def validate_read_only_sql(sql: str) -> None:
    cleaned = strip_sql_comments_and_strings(sql)
    words = set(re.findall(r"\b[A-Za-z_]+\b", cleaned.upper()))
    blocked = sorted(words & FORBIDDEN_SQL)
    if blocked:
        raise CollectionError(f"SQL contains forbidden mutation/session tokens: {', '.join(blocked)}")
    statements = [part.strip() for part in cleaned.split(";") if part.strip()]
    if not statements:
        raise CollectionError("SQL file is empty")
    for statement in statements:
        first = re.match(r"[A-Za-z_]+", statement)
        if first is None or first.group(0).upper() not in SAFE_START:
            raise CollectionError("every SQL statement must start with SELECT, WITH, SHOW, or DESCRIBE")


def _surface_spec(surface: str) -> tuple[str, list[str], str | None]:
    if surface in SURFACES:
        filename, sources = SURFACES[surface]
        return filename, sources, None
    if surface in SUBSURFACES:
        return SUBSURFACES[surface]
    raise CollectionError(f"unsupported surface: {surface}")


def load_surface(surface: str) -> tuple[Path, str, list[str]]:
    filename, sources, _ = _surface_spec(surface)
    path = SQL_DIR / filename
    if not path.is_file():
        raise CollectionError(f"surface is not bundled in this installed skill: {surface}")
    sql = path.read_text(encoding="utf-8")
    if "\x00" in sql:
        raise CollectionError(f"NUL byte in SQL file: {path}")
    validate_read_only_sql(sql)
    return path, sql, sources


def render_surface(
    surface: str,
    *,
    query_id: str | None = None,
    database: str | None = None,
) -> tuple[Path, str, str, list[str], dict[str, str]]:
    """Render a reviewed template using only validated opaque selectors."""

    path, template_sql, sources = load_surface(surface)
    _, _, selector_name = _surface_spec(surface)
    selector: dict[str, str] = {}
    if selector_name == "query_id":
        if query_id is None or not QUERY_ID_RE.fullmatch(query_id):
            raise CollectionError("query_id must be an opaque identifier, not SQL or a free-form fragment")
        selector["query_id"] = query_id
    elif selector_name == "database":
        if database is None or not IDENTIFIER_RE.fullmatch(database):
            raise CollectionError("database must be one unquoted Snowflake identifier, not SQL or a fragment")
        selector["database"] = database
    elif query_id is not None or database is not None:
        raise CollectionError(f"surface {surface} does not accept a selector")
    rendered_sql = template_sql
    for name, marker in SELECTOR_MARKERS.items():
        if name in selector:
            rendered_sql = rendered_sql.replace(marker, selector[name])
        elif marker in rendered_sql:
            raise CollectionError(f"surface {surface} requires selector: {name}")
    validate_read_only_sql(rendered_sql)
    return path, template_sql, rendered_sql, sources, selector


def normalize_cli_json(raw: Any) -> tuple[dict[str, list[dict[str, Any]]], int]:
    if isinstance(raw, dict):
        rows = [raw]
    elif isinstance(raw, list):
        rows = raw
    else:
        raise CollectionError("Snowflake CLI JSON must be an object or array")
    datasets: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise CollectionError(f"row {index} must be an object")
        payload: Any = row.get("EVIDENCE", row.get("evidence", row))
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise CollectionError(f"row {index} EVIDENCE is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise CollectionError(f"row {index} evidence payload must be an object")
        reject_secret_fields(payload, f"rows[{index}]")
        payload = dict(payload)
        dataset = str(payload.pop("_dataset", "rows"))
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", dataset):
            raise CollectionError(f"row {index} has invalid dataset name")
        datasets.setdefault(dataset, []).append(payload)
    for name in datasets:
        datasets[name].sort(key=lambda item: canonical_json(item))
    return dict(sorted(datasets.items())), len(rows)


def build_receipt(
    surface: str,
    connection: str,
    sql: str,
    sources: list[str],
    *,
    raw: Any | None = None,
    collected_at: str | None = None,
    error: dict[str, Any] | None = None,
    template_sql: str | None = None,
    template_path: Path | None = None,
    selector: dict[str, str] | None = None,
) -> dict[str, Any]:
    datasets: dict[str, list[dict[str, Any]]] = {}
    row_count = 0
    if raw is not None:
        datasets, row_count = normalize_cli_json(raw)
        # Preserve the reviewed dataset identity even when Snowflake returns no
        # association rows. Consumers can distinguish a complete empty result
        # from a receipt whose expected dataset was removed.
        if surface == "data-quality-current":
            datasets.setdefault("data_quality_current", [])
    limits = re.findall(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
    row_limit = int(limits[-1]) if limits else None
    dataset_truncation = {
        name: row_limit is not None and len(rows) >= row_limit for name, rows in datasets.items()
    }
    truncation_possible = any(dataset_truncation.values())
    canonical_template = template_sql if template_sql is not None else sql
    template_hash = f"sha256:{hashlib.sha256(canonical_template.encode('utf-8')).hexdigest()}"
    rendered_hash = f"sha256:{hashlib.sha256(sql.encode('utf-8')).hexdigest()}"
    selector_fingerprint = None
    if selector:
        selector_fingerprint = f"sha256:{hashlib.sha256(canonical_json(selector)).hexdigest()}"
    selector_metadata = {name: True for name in (selector or {})}
    receipt = {
        "schema_version": "1",
        "surface": surface,
        "status": "error" if error else "collected",
        "collected_at": collected_at or utc_now(),
        "connection_profile": connection,
        # Keep sql_sha256 as the reviewed template hash for v1 consumers. The
        # rendered hash and selector identity are additive for dynamic paths.
        "sql_sha256": template_hash,
        "template_sha256": template_hash,
        "rendered_sql_sha256": rendered_hash,
        "selector_fingerprint": selector_fingerprint,
        "source_metadata": {
            "template": template_path.name if template_path is not None else None,
            "source_views": list(sources),
            # Selector values may identify customer objects or query activity;
            # expose only presence and bind the opaque value via its digest.
            "selector": selector_metadata,
        },
        "source_views": sources,
        "row_count": row_count,
        "row_limit": row_limit,
        "truncation_possible": truncation_possible,
        "dataset_row_limits": {name: row_limit for name in datasets} if row_limit is not None else {},
        "dataset_truncation_possible": dataset_truncation,
        "datasets": datasets,
        "errors": [error] if error else [],
        "non_claims": [
            "No Snowflake mutation was executed.",
            "Missing rows or permission-blocked views do not prove health.",
            "Account Usage evidence can lag and must not be treated as real-time state.",
            "The selected domain skill must evaluate freshness and completeness.",
            "A row count at the reviewed SQL limit may indicate truncated evidence.",
        ],
    }
    receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(canonical_json(receipt)).hexdigest()}"
    return receipt


def execute_surface(
    surface: str,
    connection: str,
    *,
    query_id: str | None = None,
    database: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[dict[str, Any], int]:
    if not PROFILE_RE.fullmatch(connection):
        raise CollectionError("connection profile must use only letters, digits, dot, underscore, or hyphen")
    path, template_sql, sql, sources, selector = render_surface(
        surface,
        query_id=query_id,
        database=database,
    )
    temporary_path: Path | None = None
    def cleanup() -> None:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    try:
        command_path = path
        if sql != template_sql:
            # Dynamic SQL belongs in the OS temp directory. Installed skill trees
            # may be read-only and must remain byte/entry-identical after a run.
            descriptor, temporary_name = tempfile.mkstemp(prefix=f"snowflake-{path.stem}-", suffix=".sql")
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(sql)
            command_path = temporary_path

        command = [
            "snow",
            "sql",
            "--filename",
            str(command_path),
            "--connection",
            connection,
            "--format",
            "JSON_EXT",
            "--silent",
            "--enhanced-exit-codes",
            "--local-only",
        ]
        try:
            completed = runner(command, capture_output=True, text=True, timeout=120, check=False)
        except FileNotFoundError:
            error = {"code": "SNOW_CLI_NOT_FOUND", "message": "Snowflake CLI executable 'snow' was not found"}
            return (
                build_receipt(
                    surface, connection, sql, sources, error=error,
                    template_sql=template_sql, template_path=path, selector=selector,
                ),
                2,
            )
        except subprocess.TimeoutExpired:
            error = {"code": "SNOW_CLI_TIMEOUT", "message": "Snowflake CLI collection exceeded 120 seconds"}
            return (
                build_receipt(
                    surface, connection, sql, sources, error=error,
                    template_sql=template_sql, template_path=path, selector=selector,
                ),
                5,
            )
        if completed.returncode != 0:
            error = {
                "code": "SNOW_CLI_FAILED",
                "exit_code": completed.returncode,
                "message": sanitize_text(completed.stderr or completed.stdout or "Snowflake CLI failed"),
            }
            return (
                build_receipt(
                    surface, connection, sql, sources, error=error,
                    template_sql=template_sql, template_path=path, selector=selector,
                ),
                completed.returncode,
            )
        try:
            raw = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise CollectionError("Snowflake CLI did not return valid JSON_EXT output") from exc
        return (
            build_receipt(
                surface, connection, sql, sources, raw=raw,
                template_sql=template_sql, template_path=path, selector=selector,
            ),
            0,
        )
    finally:
        # One outer guarantee covers runner OSError/exception and even failures
        # while creating or writing the rendered selector file.
        cleanup()


def write_receipt(receipt: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    bundled_surfaces = sorted(
        surface
        for surface in {**SURFACES, **SUBSURFACES}
        if _surface_spec(surface)[0] and (SQL_DIR / _surface_spec(surface)[0]).is_file()
    )
    parser.add_argument("--surface", choices=bundled_surfaces, required=True)
    parser.add_argument("--connection", help="Existing Snowflake CLI profile name")
    parser.add_argument("--output", type=Path, help="JSON receipt path; stdout when omitted")
    parser.add_argument("--input-json", type=Path, help="Normalize saved Snowflake CLI JSON_EXT instead of connecting")
    parser.add_argument("--query-id", help="Opaque completed query ID for query operator/insight sub-surfaces")
    parser.add_argument("--database", help="One unquoted database identifier for the access-future sub-surface")
    parser.add_argument("--validate-only", action="store_true", help="Validate the reviewed SQL and exit")
    args = parser.parse_args(argv)
    try:
        path, template_sql, sql, sources, selector = render_surface(
            args.surface,
            query_id=args.query_id,
            database=args.database,
        )
        if args.validate_only:
            return 0
        if args.input_json:
            raw = json.loads(args.input_json.read_text(encoding="utf-8"))
            receipt = build_receipt(
                args.surface,
                "offline-input",
                sql,
                sources,
                raw=raw,
                template_sql=template_sql,
                template_path=path,
                selector=selector,
            )
            code = 0
        else:
            if not args.connection:
                parser.error("--connection is required unless --input-json or --validate-only is used")
            receipt, code = execute_surface(
                args.surface,
                args.connection,
                query_id=args.query_id,
                database=args.database,
            )
        write_receipt(receipt, args.output)
        return code
    except (CollectionError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {sanitize_text(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
