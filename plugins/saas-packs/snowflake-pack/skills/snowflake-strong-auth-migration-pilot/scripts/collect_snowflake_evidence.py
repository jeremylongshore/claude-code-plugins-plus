#!/usr/bin/env python3
"""Collect bounded read-only Snowflake evidence through an existing CLI profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
SURFACES = {
    "access": ("access.sql", ["SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES", "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS"]),
    "auth": ("auth.sql", ["SNOWFLAKE.ACCOUNT_USAGE.USERS"]),
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
SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "credential",
    "credentials",
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
                raise CollectionError(f"credential-bearing field is not accepted: {path}.{key}")
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


def load_surface(surface: str) -> tuple[Path, str, list[str]]:
    try:
        filename, sources = SURFACES[surface]
    except KeyError as exc:
        raise CollectionError(f"unsupported surface: {surface}") from exc
    path = SQL_DIR / filename
    if not path.is_file():
        raise CollectionError(f"surface is not bundled in this installed skill: {surface}")
    sql = path.read_text(encoding="utf-8")
    if "\x00" in sql:
        raise CollectionError(f"NUL byte in SQL file: {path}")
    validate_read_only_sql(sql)
    return path, sql, sources


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
) -> dict[str, Any]:
    datasets: dict[str, list[dict[str, Any]]] = {}
    row_count = 0
    if raw is not None:
        datasets, row_count = normalize_cli_json(raw)
    limits = re.findall(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
    row_limit = int(limits[-1]) if limits else None
    truncation_possible = row_limit is not None and row_count >= row_limit
    receipt = {
        "schema_version": "1",
        "surface": surface,
        "status": "error" if error else "collected",
        "collected_at": collected_at or utc_now(),
        "connection_profile": connection,
        "sql_sha256": f"sha256:{hashlib.sha256(sql.encode('utf-8')).hexdigest()}",
        "source_views": sources,
        "row_count": row_count,
        "row_limit": row_limit,
        "truncation_possible": truncation_possible,
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
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[dict[str, Any], int]:
    if not PROFILE_RE.fullmatch(connection):
        raise CollectionError("connection profile must use only letters, digits, dot, underscore, or hyphen")
    path, sql, sources = load_surface(surface)
    command = [
        "snow",
        "sql",
        "--filename",
        str(path),
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
        return build_receipt(surface, connection, sql, sources, error=error), 2
    except subprocess.TimeoutExpired:
        error = {"code": "SNOW_CLI_TIMEOUT", "message": "Snowflake CLI collection exceeded 120 seconds"}
        return build_receipt(surface, connection, sql, sources, error=error), 5
    if completed.returncode != 0:
        error = {
            "code": "SNOW_CLI_FAILED",
            "exit_code": completed.returncode,
            "message": sanitize_text(completed.stderr or completed.stdout or "Snowflake CLI failed"),
        }
        return build_receipt(surface, connection, sql, sources, error=error), completed.returncode
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CollectionError("Snowflake CLI did not return valid JSON_EXT output") from exc
    return build_receipt(surface, connection, sql, sources, raw=raw), 0


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
    bundled_surfaces = sorted(surface for surface, (filename, _) in SURFACES.items() if (SQL_DIR / filename).is_file())
    parser.add_argument("--surface", choices=bundled_surfaces, required=True)
    parser.add_argument("--connection", help="Existing Snowflake CLI profile name")
    parser.add_argument("--output", type=Path, help="JSON receipt path; stdout when omitted")
    parser.add_argument("--input-json", type=Path, help="Normalize saved Snowflake CLI JSON_EXT instead of connecting")
    parser.add_argument("--validate-only", action="store_true", help="Validate the reviewed SQL and exit")
    args = parser.parse_args(argv)
    try:
        _, sql, sources = load_surface(args.surface)
        if args.validate_only:
            return 0
        if args.input_json:
            raw = json.loads(args.input_json.read_text(encoding="utf-8"))
            receipt = build_receipt(args.surface, "offline-input", sql, sources, raw=raw)
            code = 0
        else:
            if not args.connection:
                parser.error("--connection is required unless --input-json or --validate-only is used")
            receipt, code = execute_surface(args.surface, args.connection)
        write_receipt(receipt, args.output)
        return code
    except (CollectionError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {sanitize_text(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
