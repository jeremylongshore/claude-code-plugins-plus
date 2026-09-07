#!/usr/bin/env python3
"""Validate and classify normalized Snowflake query evidence without mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    """Raised when query evidence is malformed or unsafe to interpret."""


EXPECTED_COLLECTOR_SOURCES = [
    "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
]
HASH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
QUERY_ID_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
ACCOUNT_USAGE_HISTORY_SOURCE = "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY"
INFORMATION_SCHEMA_HISTORY_SOURCE = "INFORMATION_SCHEMA.QUERY_HISTORY"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TERMINAL_QUERY_STATUSES_BY_SOURCE = {
    ACCOUNT_USAGE_HISTORY_SOURCE: {"success", "fail", "incident"},
    INFORMATION_SCHEMA_HISTORY_SOURCE: {"success", "failed_with_error", "failed_with_incident"},
}
NONTERMINAL_QUERY_STATUSES_BY_SOURCE = {
    ACCOUNT_USAGE_HISTORY_SOURCE: set(),
    INFORMATION_SCHEMA_HISTORY_SOURCE: {"resuming_warehouse", "running", "queued", "blocked"},
}
EXPECTED_FRESHNESS_SEMANTICS = "dataset observation only; the analyzer derives freshness from the anchor query row"
SAFE_LABEL_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,256}$")
OWNER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+ -]{0,127}$")
OPERATOR_ID_RE = re.compile(r"^[0-9]{1,20}$")
OPERATOR_TYPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _./:-]{0,127}$")
INSIGHT_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
SQL_HASH_PREFIXES = {
    "SELECT",
    "WITH",
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "CALL",
}


def validate_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be an opaque query hash, not SQL or free-form text")
    if value.split(".", 1)[0].upper() in SQL_HASH_PREFIXES:
        raise EvidenceError(f"{field} must be an opaque query hash, not SQL or free-form text")
    return value


def validate_query_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not QUERY_ID_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be a Snowflake UUID query ID")
    return value


def status_is_terminal(history_source: str, status: str) -> bool:
    return status in TERMINAL_QUERY_STATUSES_BY_SOURCE.get(history_source, set())


def status_is_known(history_source: str, status: str) -> bool:
    return status_is_terminal(history_source, status) or status in NONTERMINAL_QUERY_STATUSES_BY_SOURCE.get(
        history_source, set()
    )


def bind_rows_to_query(
    rows: list[dict[str, Any]], label: str, query_id: str, warnings: list[str]
) -> tuple[list[dict[str, Any]], bool]:
    bound: list[dict[str, Any]] = []
    complete = True
    for index, row in enumerate(rows):
        supplied_query_id = row.get("query_id")
        if supplied_query_id is None:
            warnings.append(f"{label}[{index}]: query_id absent; row excluded from query-bound analysis")
            complete = False
            continue
        if validate_query_id(supplied_query_id, f"{label}[{index}].query_id") != query_id:
            raise EvidenceError(f"{label}[{index}].query_id must match metadata.query_id")
        bound.append(row)
    return bound, complete


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def input_sha256(data: dict[str, Any]) -> str:
    """Return the canonical digest used as an out-of-band local trust anchor."""
    return f"sha256:{hashlib.sha256(_canonical_json(data)).hexdigest()}"


def assess_input_trust(data: dict[str, Any], trusted_input_sha256: str | None, warnings: list[str]) -> dict[str, Any]:
    actual = input_sha256(data)
    non_claim = (
        "A matching out-of-band digest proves only that this canonical normalized bundle matches the bundle "
        "approved at a trusted local boundary; it is not a signature and does not identify who collected the evidence."
    )
    if trusted_input_sha256 is None:
        warnings.append(
            "evidence provenance is untrusted; no out-of-band digest from a trusted local collection boundary was supplied"
        )
        return {
            "status": "UNTRUSTED",
            "trusted": False,
            "input_sha256": actual,
            "non_claim": non_claim,
        }
    if not isinstance(trusted_input_sha256, str) or not DIGEST_RE.fullmatch(trusted_input_sha256):
        warnings.append("trusted input digest is malformed; evidence provenance remains untrusted")
        return {
            "status": "INVALID_TRUST_ANCHOR",
            "trusted": False,
            "input_sha256": actual,
            "non_claim": non_claim,
        }
    if trusted_input_sha256 != actual:
        warnings.append("trusted input digest does not match the normalized evidence bundle")
        return {
            "status": "DIGEST_MISMATCH",
            "trusted": False,
            "input_sha256": actual,
            "non_claim": non_claim,
        }
    return {
        "status": "TRUSTED_LOCAL_DIGEST",
        "trusted": True,
        "input_sha256": actual,
        "non_claim": non_claim,
    }


def _rows_match(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
        return False
    return sorted(_canonical_json(row) for row in left) == sorted(_canonical_json(row) for row in right)


def _rows_contain(container: Any, required: Any) -> bool:
    if not isinstance(container, list) or not isinstance(required, list):
        return False
    available = [_canonical_json(row) for row in container]
    for row in required:
        encoded = _canonical_json(row)
        if encoded not in available:
            return False
        available.remove(encoded)
    return True


def validate_collector_receipt(
    data: dict[str, Any],
    warnings: list[str],
    evaluation_time: datetime,
    source_max_time: datetime,
    source_max_age_seconds: int,
    query_id: str,
    history_source: str,
    metadata_role: str,
    input_trusted: bool,
) -> dict[str, Any]:
    receipt = data.get("collector_receipt")
    if receipt is None:
        issue = "collector receipt not supplied; provenance and completeness are not verified"
        warnings.append(issue)
        return {
            "status": "not_supplied",
            "integrity_status": "NOT_CHECKED",
            "provenance_status": "UNTRUSTED",
            "complete": False,
            "issues": [issue],
        }
    issues: list[str] = []
    if not isinstance(receipt, dict):
        issues.append("collector_receipt is not an object")
        receipt = {}
    if receipt.get("schema_version") != "2":
        issues.append("schema_version is not 2")
    if receipt.get("surface") != "query":
        issues.append("surface is not query")
    if receipt.get("status") != "collected":
        issues.append(f"status is {receipt.get('status')!r}")
    if receipt.get("errors"):
        issues.append("collector reported an error")
    if not isinstance(receipt.get("connection_profile"), str) or not receipt["connection_profile"].strip():
        issues.append("connection_profile is missing")
    receipt_time = None
    try:
        receipt_time = parse_time(receipt.get("collected_at"), "collector_receipt.collected_at")
        if receipt_time > evaluation_time or receipt_time > datetime.now(timezone.utc):
            issues.append("collected_at is after the report evaluation time or in the future")
        elif receipt_time != evaluation_time:
            issues.append("collected_at does not match metadata.collected_at")
    except EvidenceError:
        issues.append("collected_at is invalid")
    if receipt.get("source_views") != EXPECTED_COLLECTOR_SOURCES:
        issues.append("source_views do not match the reviewed query SQL")
    receipt_query_sources = [
        source
        for source in receipt.get("source_views", [])
        if isinstance(source, str) and source.endswith(".QUERY_HISTORY")
    ]
    if history_source not in receipt_query_sources:
        issues.append("metadata.history_source does not match the receipted query-history source")
    sql_path = Path(__file__).resolve().parent / "sql" / "query.sql"
    expected_sql_hash = None
    expected_row_limit = None
    if sql_path.is_file():
        sql_bytes = sql_path.read_bytes()
        expected_sql_hash = f"sha256:{hashlib.sha256(sql_bytes).hexdigest()}"
        limits = re.findall(r"\bLIMIT\s+(\d+)\b", sql_bytes.decode("utf-8"), flags=re.IGNORECASE)
        expected_row_limit = int(limits[-1]) if limits else None
    if receipt.get("sql_sha256") != expected_sql_hash:
        issues.append("sql_sha256 does not match the reviewed query SQL")
    supplied_receipt_hash = receipt.get("receipt_sha256")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    expected_receipt_hash = f"sha256:{hashlib.sha256(_canonical_json(body)).hexdigest()}"
    if supplied_receipt_hash != expected_receipt_hash:
        issues.append("receipt_sha256 is missing or invalid")
    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        issues.append("datasets is not an object")
        datasets = {}
    row_count = receipt.get("row_count")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
        issues.append("row_count is invalid")
    elif row_count != sum(len(value) for value in datasets.values() if isinstance(value, list)):
        issues.append("row_count does not match receipt datasets")
    row_limit = receipt.get("row_limit")
    if expected_row_limit is None:
        issues.append("reviewed query SQL has no enforceable row cap")
    elif row_limit != expected_row_limit:
        issues.append("row_limit does not match the reviewed query SQL cap")
    if isinstance(row_count, int) and not isinstance(row_count, bool) and expected_row_limit is not None:
        expected_truncation = row_count >= expected_row_limit
        if receipt.get("truncation_possible") is not expected_truncation:
            issues.append("truncation_possible does not match row_count and the reviewed SQL cap")
        if expected_truncation:
            issues.append("row_count is at or above the reviewed SQL cap")
    elif receipt.get("truncation_possible") is not False:
        issues.append("truncation_possible is invalid")
    freshness = receipt.get("freshness")
    receipt_dataset_max_time = None
    if not isinstance(freshness, dict):
        issues.append("freshness binding is missing")
    else:
        if freshness.get("dataset") != "query_history":
            issues.append("freshness dataset is not query_history")
        try:
            receipt_dataset_max_time = parse_time(
                freshness.get("dataset_max_time"), "collector_receipt.freshness.dataset_max_time"
            )
        except EvidenceError:
            issues.append("freshness dataset_max_time is invalid")
        receipt_max_age = freshness.get("source_max_age_seconds")
        if not isinstance(receipt_max_age, int) or isinstance(receipt_max_age, bool) or receipt_max_age <= 0:
            issues.append("freshness source_max_age_seconds is invalid")
        elif receipt_max_age != source_max_age_seconds:
            issues.append("freshness source_max_age_seconds does not match metadata.source_max_age_seconds")
        if freshness.get("semantics") != EXPECTED_FRESHNESS_SEMANTICS:
            issues.append("freshness semantics do not match the reviewed anchor-specific contract")
    dataset_source_times: list[datetime] = []
    anchor_source_times: list[datetime] = []
    anchor_roles: list[Any] = []
    anchor_row_count = 0
    receipt_history_rows = datasets.get("query_history", [])
    if not isinstance(receipt_history_rows, list):
        issues.append("query_history receipt dataset is not an array")
    else:
        try:
            for index, row in enumerate(receipt_history_rows):
                if not isinstance(row, dict):
                    raise EvidenceError(f"collector_receipt.datasets.query_history[{index}] must be an object")
                row_query_id = validate_query_id(
                    row.get("query_id"), f"collector_receipt.datasets.query_history[{index}].query_id"
                )
                if row_query_id == query_id:
                    anchor_row_count += 1
                    anchor_roles.append(row.get("role_name"))
                for field in ("end_time", "start_time"):
                    if row.get(field) is not None:
                        parsed = parse_time(
                            row[field],
                            f"collector_receipt.datasets.query_history[{index}].{field}",
                        )
                        dataset_source_times.append(parsed)
                        if row_query_id == query_id:
                            anchor_source_times.append(parsed)
        except EvidenceError:
            issues.append("query_history receipt identity or timestamps are invalid")
    if not dataset_source_times:
        issues.append("query_history receipt has no source timestamp")
    elif receipt_dataset_max_time != max(dataset_source_times):
        issues.append("freshness dataset_max_time is not derived from all query_history receipt rows")
    if anchor_row_count != 1:
        issues.append("query_history receipt must contain exactly one row for metadata.query_id")
    if len(anchor_roles) == 1:
        anchor_role = anchor_roles[0]
        if not isinstance(anchor_role, str) or not anchor_role.strip():
            issues.append("anchor query-history receipt row has no role_name for metadata binding")
        elif anchor_role != metadata_role:
            issues.append("metadata.role does not match the receipted anchor role_name")
    if not anchor_source_times:
        issues.append("query_history receipt has no timestamp for metadata.query_id")
    elif source_max_time != max(anchor_source_times):
        issues.append("metadata.history_source_max_time is not derived from the anchor query receipt row")
    for name in ("query_history", "warehouse_load"):
        supplied = data.get(name, [])
        supplied_rows = [supplied] if name == "query_history" and isinstance(supplied, dict) else supplied
        receipt_rows = datasets.get(name, [])
        rows_match = (
            _rows_contain(receipt_rows, supplied_rows)
            if name == "query_history"
            else _rows_match(supplied_rows, receipt_rows)
        )
        if not rows_match:
            issues.append(f"{name} rows do not match collector receipt")
    for issue in issues:
        warnings.append(f"collector receipt unverifiable: {issue}")
    integrity_status = "CONSISTENT" if not issues else "INVALID"
    if issues:
        status = "invalid"
    elif input_trusted:
        status = "trusted_local_boundary"
    else:
        status = "self_consistent_untrusted"
        warnings.append(
            "collector receipt self-checksum is internally consistent but has no trusted provenance boundary"
        )
    return {
        "status": status,
        "integrity_status": integrity_status,
        "provenance_status": "TRUSTED_LOCAL_DIGEST" if input_trusted else "UNTRUSTED",
        "complete": not issues and input_trusted,
        "issues": sorted(set(issues)),
        "surface": receipt.get("surface"),
        "row_count": receipt.get("row_count"),
        "row_limit": receipt.get("row_limit"),
        "truncation_possible": receipt.get("truncation_possible"),
    }


SENSITIVE_KEYS = {
    "accesstoken",
    "apikey",
    "authorization",
    "authorizationheader",
    "clientsecret",
    "credential",
    "credentials",
    "idtoken",
    "jwt",
    "oauthcode",
    "oauthtoken",
    "passphrase",
    "password",
    "privatekey",
    "secret",
    "secretaccesskey",
    "sessiontoken",
    "token",
}
SAFE_SENSITIVE_METADATA_KEYS = {"haspassword", "haspat", "hasrsapublickey", "hasworkloadidentity"}
SENSITIVE_KEY_FRAGMENTS = (
    "apikey",
    "authorization",
    "credential",
    "jwt",
    "password",
    "passphrase",
    "privatekey",
    "secret",
    "token",
)
AUTH_FOLDED_VALUE_PATTERN = r"[^\r\n]*(?:\r?\n[ \t]+[^\r\n]*)*"
AUTH_SCHEME_TOKEN_PATTERN = r"[A-Za-z][A-Za-z0-9!#$%&'*+.^_`|~-]{0,63}"
AUTH_PARAM_NAME_PATTERN = r"[A-Za-z0-9!#$%&'*+.^_`|~-]+"
AUTH_PARAM_VALUE_PATTERN = r"""(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,]+)"""
AUTH_PARAM_LIST_PATTERN = (
    rf"{AUTH_PARAM_NAME_PATTERN}\s*=\s*{AUTH_PARAM_VALUE_PATTERN}"
    rf"(?:\s*,\s*{AUTH_PARAM_NAME_PATTERN}\s*=\s*{AUTH_PARAM_VALUE_PATTERN})*"
)
AUTHORIZATION_HEADER_RE = re.compile(
    rf"""\b(?:proxy[-_ ]*)?authorization(?:[-_ ]*header)?\s*[:=]\s*{AUTH_FOLDED_VALUE_PATTERN}""",
    re.IGNORECASE,
)
AUTH_PARAMETER_CANDIDATE_RE = re.compile(
    rf"(?<![\w.-])(?P<scheme>{AUTH_SCHEME_TOKEN_PATTERN})[ \t]+(?P<payload>{AUTH_PARAM_LIST_PATTERN})",
    re.IGNORECASE,
)
BARE_AUTH_SCHEME_PATTERN = (
    r"(?:ApiKey|Basic|Bearer|Digest|DPoP|Hawk|HOBA|MAC|Mutual|Negotiate|NTLM|OAuth|PoP|"
    r"SCRAM-SHA-(?:1|256)|Signature|VAPID|[A-Za-z][A-Za-z0-9!#$%&'*+.^_`|~-]*"
    r"(?:Auth|Credential|Proof|Signature)[A-Za-z0-9!#$%&'*+.^_`|~-]*)"
)
AUTH_BARE_TOKEN_RE = re.compile(
    rf"(?<![\w.-])(?P<scheme>{BARE_AUTH_SCHEME_PATTERN})[ \t]+(?P<payload>[A-Za-z0-9._~+/-]+=*)(?![A-Za-z0-9._~+/=-])",
    re.IGNORECASE,
)
BARE_AUTH_SCHEMES = {
    "apikey",
    "basic",
    "bearer",
    "digest",
    "dpop",
    "hawk",
    "hoba",
    "mac",
    "mutual",
    "negotiate",
    "ntlm",
    "oauth",
    "pop",
    "scramsha1",
    "scramsha256",
    "signature",
    "vapid",
}
TOKEN68_AUTH_SCHEMES = {
    "apikey",
    "basic",
    "bearer",
    "dpop",
    "mutual",
    "negotiate",
    "ntlm",
    "pop",
    "scramsha1",
    "scramsha256",
}
AUTH_PROSE_TOKEN68_WORDS = {
    "authentication",
    "available",
    "configured",
    "disabled",
    "enabled",
    "required",
    "reviewed",
    "support",
    "supported",
}
AUTH_SCHEME_SIGNALS = ("credential", "proof", "signature")
AUTH_SCHEME_PARAMETER_NAMES = {
    "aws4hmacsha256": {"credential", "signature", "signedheaders"},
    "digest": {"cnonce", "nonce", "opaque", "qop", "response", "username"},
    "hawk": {"app", "dlg", "ext", "hash", "id", "mac", "nonce", "ts"},
    "hoba": {"result"},
    "mac": {"ext", "hash", "id", "mac", "nonce", "ts"},
    "oauth": {"signature", "token"},
    "scramsha1": {"data"},
    "scramsha256": {"data"},
    "signature": {"keyid", "nonce", "signature"},
    "vapid": {"k", "t"},
}
AUTH_CREDENTIAL_PARAMETER_SIGNALS = ("credential", "keyid", "nonce", "proof", "response", "signature", "token")
STATIC_REDACTIONS = (
    (
        re.compile(
            rf"(?<!\w)[\"']?(?:[\w-]*(?:password|passphrase|token|secret|credential|private[_-]?key|jwt|api[_-]?key|authorization)[\w-]*|has[_-]?pat|has[_-]?rsa[_-]?public[_-]?key|has[_-]?workload[_-]?identity)[\"']?\s*[=:]\s*{AUTH_FOLDED_VALUE_PATTERN}",
            re.IGNORECASE,
        ),
        "[REDACTED_CREDENTIAL]",
    ),
    (re.compile(r"https?://\S+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
)
AUTH_PARAM_PAIR_RE = re.compile(
    rf"(?P<name>{AUTH_PARAM_NAME_PATTERN})\s*=\s*(?P<value>{AUTH_PARAM_VALUE_PATTERN})",
    re.IGNORECASE,
)
SQL_TOKEN_RE = re.compile(
    r"""(?:'(?:''|[^'])*'|"(?:""|[^"])*"|file://[^\s,;()]+|->>|=>|::|\|\||<>|!=|<=|>=|[-+*/%=<>,:();]|@[A-Za-z0-9_$./~-]+|\$[A-Za-z0-9_$]+|[A-Za-z_][A-Za-z0-9_$]*|\d+(?:\.\d+)?|\S)""",
    re.IGNORECASE,
)
SQL_SELECT_PREFIXES = {"ALL", "CASE", "DISTINCT", "FALSE", "NOT", "NULL", "TOP", "TRUE"}
SQL_SELECT_CLAUSES = {
    "AS",
    "FROM",
    "GROUP",
    "HAVING",
    "LIMIT",
    "ORDER",
    "OVER",
    "QUALIFY",
    "WHERE",
    "WINDOW",
}
SQL_OPERATORS = {"(", ")", "+", "-", "*", "/", "%", "=", "<", ">", "<=", ">=", "<>", "!=", "::", "||"}
SQL_SHOW_LEADS = {
    "API",
    "APPLICATIONS",
    "AUTHENTICATION",
    "COLUMNS",
    "CONNECTIONS",
    "DATABASES",
    "DYNAMIC",
    "EXTERNAL",
    "FAILOVER",
    "FILE",
    "FUNCTIONS",
    "FUTURE",
    "GRANTS",
    "HYBRID",
    "ICEBERG",
    "IMPORTED",
    "INTEGRATIONS",
    "LOCKS",
    "MANAGED",
    "MASKING",
    "MATERIALIZED",
    "NETWORK",
    "OBJECTS",
    "PACKAGES",
    "PARAMETERS",
    "PASSWORD",
    "PIPES",
    "PRIMARY",
    "PROCEDURES",
    "REFERENTIAL",
    "REPLICATION",
    "RESOURCE",
    "ROLES",
    "SCHEMAS",
    "SECRETS",
    "SECURITY",
    "SESSION",
    "SHARES",
    "STAGES",
    "STREAMS",
    "TABLES",
    "TAGS",
    "TASKS",
    "TERSE",
    "TRANSACTIONS",
    "UNIQUE",
    "USERS",
    "VARIABLES",
    "VIEWS",
    "WAREHOUSES",
}
SQL_OBJECT_LEADS = {
    "ACCOUNT",
    "API",
    "AUTHENTICATION",
    "CONNECTION",
    "DATABASE",
    "DYNAMIC",
    "EVENT",
    "EXTERNAL",
    "FAILOVER",
    "FILE",
    "FUNCTION",
    "HYBRID",
    "ICEBERG",
    "INTEGRATION",
    "MASKING",
    "MATERIALIZED",
    "NETWORK",
    "PASSWORD",
    "PIPE",
    "PROCEDURE",
    "REPLICATION",
    "RESOURCE",
    "ROLE",
    "ROW",
    "SCHEMA",
    "SECURITY",
    "SECRET",
    "SEQUENCE",
    "SESSION",
    "SHARE",
    "STAGE",
    "STREAM",
    "TABLE",
    "TAG",
    "TASK",
    "USER",
    "VIEW",
    "WAREHOUSE",
}
SQL_SCRIPT_STATEMENT_LEADS = {
    "ALTER",
    "CALL",
    "COMMENT",
    "COPY",
    "CREATE",
    "DELETE",
    "DESC",
    "DESCRIBE",
    "DROP",
    "EXECUTE",
    "GET",
    "GRANT",
    "INSERT",
    "LIST",
    "LS",
    "MERGE",
    "PUT",
    "REMOVE",
    "REVOKE",
    "SELECT",
    "SET",
    "SHOW",
    "TRUNCATE",
    "UNDROP",
    "UNSET",
    "UPDATE",
    "USE",
    "VALUES",
    "WITH",
}

SQL_DIAGNOSTIC_PREFIX_RE = re.compile(
    r"(?i)^(?:\[(?:SNOWFLAKE\s+)?(?:DIAGNOSTIC|ERROR|FAILED|FAILURE|MESSAGE|WARNING)\]"
    r"(?:\s*[-:]\s*)*|"
    r"(?:SNOWFLAKE\s+)?(?:DIAGNOSTIC|ERROR|FAILED|FAILURE|MESSAGE|WARNING)"
    r"(?:\s*[-:]\s*)+)\s*"
)
SQL_STATEMENT_LABEL_RE = re.compile(
    r"(?i)^(?:[A-Za-z][A-Za-z0-9_-]*(?:\s+[A-Za-z][A-Za-z0-9_-]*){0,5}\s+)?"
    r"\[?(?:SQL|QUERY|STATEMENT)\]?\s*:\s*"
)
SQL_SHOW_CLAUSES = {"IN", "LIKE", "LIMIT", "ON", "STARTS", "TO"}
SQL_SHOW_SCOPES = {"ACCOUNT", "APPLICATION", "DATABASE", "SCHEMA", "TABLE", "VIEW"}
SQL_INTEGRATION_TYPES = {"API", "CATALOG", "NOTIFICATION", "SECURITY", "STORAGE"}
SQL_SHOW_MODIFIERS = {
    "DYNAMIC",
    "EVENT",
    "EXTERNAL",
    "FUTURE",
    "HYBRID",
    "ICEBERG",
    "IMPORTED",
    "MANAGED",
    "MASKING",
    "MATERIALIZED",
    "NETWORK",
    "PASSWORD",
    "REFERENTIAL",
    "RESOURCE",
    "ROW",
    "SECURITY",
    "SEMANTIC",
    "STORAGE",
    "TERSE",
}
SQL_FROM_CLAUSES = SQL_SELECT_CLAUSES.union({"FETCH", "OFFSET", "SAMPLE"})
SQL_JOIN_PREFIXES = {"CROSS", "FULL", "INNER", "LEFT", "NATURAL", "RIGHT"}
SQL_STATEMENT_STARTS = SQL_SCRIPT_STATEMENT_LEADS.union(
    {"BEGIN", "COMMIT", "DECLARE", "DESC", "DESCRIBE", "EXPLAIN", "LIST", "LS", "ROLLBACK", "SHOW", "VALUES"}
)
MAX_SQL_SCAN_CHARS = 16_384
MAX_SQL_TOKENS = 2_048
MAX_SQL_WRAPPER_PASSES = 16
MAX_SANITIZE_TREE_DEPTH = 32
MAX_SANITIZE_TREE_NODES = 100_000


def normalized_auth_scheme(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def is_auth_like_scheme(value: str) -> bool:
    normalized = normalized_auth_scheme(value)
    return normalized in BARE_AUTH_SCHEMES or any(signal in normalized for signal in AUTH_SCHEME_SIGNALS)


def redact_authorization_values(value: str) -> str:
    text = AUTHORIZATION_HEADER_RE.sub("[REDACTED_AUTHORIZATION]", value)

    def redact_parameters(match: re.Match[str]) -> str:
        scheme = match.group("scheme")
        payload = match.group("payload")
        pairs = list(AUTH_PARAM_PAIR_RE.finditer(payload))
        normalized_scheme = normalized_auth_scheme(scheme)
        names = {normalized_auth_scheme(pair.group("name")) for pair in pairs}
        expected_names = AUTH_SCHEME_PARAMETER_NAMES.get(normalized_scheme, set())
        if expected_names.intersection(names) or (
            normalized_scheme == "oauth" and any(name.startswith("oauth") for name in names)
        ):
            return "[REDACTED_AUTHORIZATION]"
        credential_name_present = any(
            any(signal in name for signal in AUTH_CREDENTIAL_PARAMETER_SIGNALS) for name in names
        )
        if any(signal in normalized_scheme for signal in AUTH_SCHEME_SIGNALS) and (
            len(pairs) > 1 or credential_name_present
        ):
            return "[REDACTED_AUTHORIZATION]"
        if normalized_scheme in BARE_AUTH_SCHEMES and credential_name_present:
            return "[REDACTED_AUTHORIZATION]"
        return match.group(0)

    text = AUTH_PARAMETER_CANDIDATE_RE.sub(redact_parameters, text)

    def redact_bare_token(match: re.Match[str]) -> str:
        payload = match.group("payload")
        if (
            normalized_auth_scheme(match.group("scheme")) in TOKEN68_AUTH_SCHEMES
            and payload.casefold() not in AUTH_PROSE_TOKEN68_WORDS
        ):
            return "[REDACTED_AUTHORIZATION]"
        return match.group(0)

    return AUTH_BARE_TOKEN_RE.sub(redact_bare_token, text)


def strip_sql_comments(value: str) -> str:
    """Remove SQL comments without treating comment markers inside quoted values as comments."""
    result: list[str] = []
    index = 0
    quote: str | None = None
    while index < len(value):
        char = value[index]
        if quote is not None:
            result.append(char)
            if char == quote:
                if index + 1 < len(value) and value[index + 1] == quote:
                    result.append(value[index + 1])
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(char)
            index += 1
            continue
        if value.startswith("--", index):
            newline = value.find("\n", index + 2)
            if newline < 0:
                break
            result.append("\n")
            index = newline + 1
            continue
        if value.startswith("/*", index):
            end = value.find("*/", index + 2)
            result.append(" ")
            index = len(value) if end < 0 else end + 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def matching_parenthesis(tokens: list[str], start: int = 0) -> int:
    if start >= len(tokens) or tokens[start] != "(":
        return -1
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index] == "(":
            depth += 1
        elif tokens[index] == ")":
            depth -= 1
            if depth == 0:
                return index
            if depth < 0:
                return -1
    return -1


def is_bare_metric_row(tokens: list[str]) -> bool:
    return (
        bool(tokens)
        and len(tokens) % 2 == 1
        and all(
            (index % 2 == 0 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token)) or (index % 2 == 1 and token == ",")
            for index, token in enumerate(tokens)
        )
    )


def looks_like_values_rows(tokens: list[str], preserve_bare_labels: bool = False) -> bool:
    if not tokens or tokens[0] != "(":
        return False
    position = 0
    saw_row = False
    all_bare_labels = True
    while position < len(tokens):
        if tokens[position] == ";":
            return saw_row and position == len(tokens) - 1
        if tokens[position] != "(":
            return False
        close = matching_parenthesis(tokens, position)
        if close < 0:
            return True
        all_bare_labels = all_bare_labels and is_bare_metric_row(tokens[position + 1 : close])
        saw_row = True
        position = close + 1
        if position == len(tokens):
            return not (preserve_bare_labels and all_bare_labels)
        if tokens[position] == ";":
            return position == len(tokens) - 1
        if tokens[position] != ",":
            return False
        position += 1
    return saw_row


def is_sql_identifier(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", token) or (len(token) >= 2 and token[0] == token[-1] == '"'))


def consume_qualified_identifier(tokens: list[str], position: int) -> int:
    if position >= len(tokens) or not is_sql_identifier(tokens[position]):
        return -1
    position += 1
    while position + 1 < len(tokens) and tokens[position] == "." and is_sql_identifier(tokens[position + 1]):
        position += 2
    return position


def consume_relation_base(tokens: list[str], position: int) -> int:
    if position >= len(tokens):
        return -1
    token = tokens[position]
    lateral = token.upper() == "LATERAL"
    if lateral:
        position += 1
        if position >= len(tokens):
            return -1
        token = tokens[position]
    if token.startswith("@"):
        position += 1
        if position < len(tokens) and tokens[position] == "(":
            close = matching_parenthesis(tokens, position)
            if close < 0 or close == position + 1 or "=>" not in tokens[position + 1 : close]:
                return -1
            position = close + 1
        return position
    if token.startswith("$"):
        return position + 1
    if token.upper() == "DIRECTORY" and position + 1 < len(tokens) and tokens[position + 1] == "(":
        close = matching_parenthesis(tokens, position + 1)
        if close < 0 or close != position + 3 or not tokens[position + 2].startswith("@"):
            return -1
        return close + 1
    if token.upper() == "SEMANTIC_VIEW" and position + 1 < len(tokens) and tokens[position + 1] == "(":
        close = matching_parenthesis(tokens, position + 1)
        if (
            close < 0
            or close == position + 2
            or not {item.upper() for item in tokens[position + 2 : close]}.intersection(
                {"DIMENSIONS", "FACTS", "METRICS"}
            )
        ):
            return -1
        return close + 1
    if token == "(":
        close = matching_parenthesis(tokens, position)
        if close < 0 or position + 1 >= close or tokens[position + 1].upper() not in {"SELECT", "WITH"}:
            return -1
        return close + 1
    if token.upper() == "TABLE" and position + 1 < len(tokens) and tokens[position + 1] == "(":
        close = matching_parenthesis(tokens, position + 1)
        if close < 0 or close == position + 2:
            return -1
        return close + 1
    identifier_end = consume_qualified_identifier(tokens, position)
    if lateral:
        if identifier_end < 0 or identifier_end >= len(tokens) or tokens[identifier_end] != "(":
            return -1
        close = matching_parenthesis(tokens, identifier_end)
        if close < 0 or close == identifier_end + 1:
            return -1
        return close + 1
    return identifier_end


def consume_relation(tokens: list[str], position: int) -> int:
    start = position
    position = consume_relation_base(tokens, position)
    if position < 0:
        return -1
    upper = [token.upper() for token in tokens]
    if position < len(tokens) and upper[position] == "CHANGES":
        if position + 1 >= len(tokens) or tokens[position + 1] != "(":
            return -1
        close = matching_parenthesis(tokens, position + 1)
        if close < 0 or close == position + 2 or "=>" not in tokens[position + 2 : close]:
            return -1
        position = close + 1
    for _ in range(2):
        if position >= len(tokens) or upper[position] not in {"AT", "BEFORE", "END"}:
            break
        if position + 1 >= len(tokens) or tokens[position + 1] != "(":
            return -1
        close = matching_parenthesis(tokens, position + 1)
        if close < 0 or close == position + 2 or "=>" not in tokens[position + 2 : close]:
            return -1
        position = close + 1
    for _ in range(2):
        if position >= len(tokens):
            break
        if upper[position] == "UNPIVOT":
            position += 1
            if position < len(tokens) and upper[position] in {"EXCLUDE", "INCLUDE"}:
                position += 1
                if position >= len(tokens) or upper[position] != "NULLS":
                    return -1
                position += 1
            if position >= len(tokens) or tokens[position] != "(":
                return -1
            close = matching_parenthesis(tokens, position)
            if close < 0 or close == position + 1:
                return -1
            position = close + 1
            continue
        if upper[position] == "PIVOT":
            if position + 1 >= len(tokens) or tokens[position + 1] != "(":
                return -1
            close = matching_parenthesis(tokens, position + 1)
            if close < 0 or close == position + 2:
                return -1
            position = close + 1
            continue
        if upper[position] in {"SAMPLE", "TABLESAMPLE"}:
            position += 1
            if position < len(tokens) and upper[position] in {"BERNOULLI", "BLOCK", "ROW", "SYSTEM"}:
                position += 1
            if position >= len(tokens) or tokens[position] != "(":
                return -1
            close = matching_parenthesis(tokens, position)
            if close < 0 or close == position + 1:
                return -1
            position = close + 1
            if position < len(tokens) and upper[position] in {"REPEATABLE", "SEED"}:
                if position + 1 >= len(tokens) or tokens[position + 1] != "(":
                    return -1
                close = matching_parenthesis(tokens, position + 1)
                if close < 0 or close == position + 2:
                    return -1
                position = close + 1
            continue
        break
    if position < len(tokens) and upper[position] == "AS":
        return consume_qualified_identifier(tokens, position + 1)
    alias_reserved = SQL_FROM_CLAUSES.union(SQL_JOIN_PREFIXES).union({",", ";", "JOIN", "ON", "USING"})
    if position < len(tokens) and is_sql_identifier(tokens[position]) and upper[position] not in alias_reserved:
        if upper[start] == "THE" and start + 2 == len(tokens):
            return -1
        position += 1
    return position


def looks_like_from_tail(tokens: list[str]) -> bool:
    if not tokens:
        return False
    upper = [token.upper() for token in tokens]
    position = consume_relation(tokens, 0)
    if position < 0:
        return False
    while position < len(tokens):
        token = upper[position]
        if token == ";":
            return position == len(tokens) - 1
        if token in SQL_FROM_CLAUSES:
            return True
        if token == ",":
            position = consume_relation(tokens, position + 1)
            if position < 0:
                return False
            continue
        join_position = position
        if token in SQL_JOIN_PREFIXES:
            join_position += 1
            if join_position < len(tokens) and upper[join_position] == "OUTER":
                join_position += 1
        if join_position < len(tokens) and upper[join_position] == "JOIN":
            position = consume_relation(tokens, join_position + 1)
            if position < 0:
                return False
            if position < len(tokens) and upper[position] in {"ON", "USING"}:
                return position + 1 < len(tokens)
            continue
        return False
    return True


def top_level_keyword(tokens: list[str], keyword: str, start: int = 0) -> int:
    depth = 0
    for index in range(start, len(tokens)):
        token = tokens[index]
        if token == "(":
            depth += 1
        elif token == ")":
            depth -= 1
            if depth < 0:
                return -1
        elif depth == 0 and token.upper() == keyword:
            return index
    return -1


def looks_like_select_branch(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    from_index = top_level_keyword(tokens, "FROM", 1)
    if from_index >= 0:
        return from_index > 1 and looks_like_from_tail(tokens[from_index + 1 :])
    tail = tokens[1:]
    if tail[-1:] == [";"]:
        tail = tail[:-1]
    if not tail:
        return False
    upper_tail = [token.upper() for token in tail]
    if len(tail) == 1:
        token = tail[0]
        return bool(
            upper_tail[0] in SQL_SELECT_PREFIXES
            or upper_tail[0].startswith("CURRENT_")
            or token.startswith(("'", '"', "$"))
            or token == "?"
            or re.fullmatch(r"\d+(?:\.\d+)?", token)
        )
    if len(tail) == 2 and tail[0] == ":" and is_sql_identifier(tail[1]):
        return True
    if tail[0] == "(":
        close = matching_parenthesis(tail)
        if close < 0:
            return True
        if close == len(tail) - 1:
            return True
        return tail[close + 1] in SQL_OPERATORS.difference({"(", ")"}) or upper_tail[close + 1] in SQL_SELECT_CLAUSES
    if (
        is_sql_identifier(tail[0])
        and len(tail) > 1
        and tail[1] == "("
        and matching_parenthesis(tail, 1) == len(tail) - 1
    ):
        return True
    return bool(SQL_OPERATORS.intersection(tail) or SQL_SELECT_CLAUSES.intersection(upper_tail))


def consume_cte_prefix(tokens: list[str]) -> int:
    upper = [token.upper() for token in tokens]
    position = 1
    if position < len(tokens) and upper[position] == "RECURSIVE":
        position += 1
    definitions = 0
    while position < len(tokens) and definitions < MAX_SQL_TOKENS:
        position = consume_qualified_identifier(tokens, position)
        if position < 0:
            return -1
        if position < len(tokens) and tokens[position] == "(":
            close = matching_parenthesis(tokens, position)
            if close < 0 or close == position + 1:
                return -1
            position = close + 1
        if position >= len(tokens) or upper[position] != "AS":
            return -1
        position += 1
        if position >= len(tokens) or tokens[position] != "(":
            return -1
        close = matching_parenthesis(tokens, position)
        if close < 0 or close == position + 1:
            return -1
        inner_position = position + 1
        for _ in range(MAX_SQL_WRAPPER_PASSES):
            if inner_position < close and tokens[inner_position] == "(":
                inner_position += 1
                continue
            break
        if inner_position >= close or (
            tokens[inner_position] != "(" and upper[inner_position] not in {"SELECT", "VALUES", "WITH"}
        ):
            return -1
        position = close + 1
        definitions += 1
        if position < len(tokens) and tokens[position] == ",":
            position += 1
            continue
        break
    return position if definitions and position < len(tokens) else -1


def looks_like_select(tokens: list[str]) -> bool:
    pending = [tokens]
    processed = 0
    while pending:
        candidate = pending.pop()
        processed += 1
        if processed > MAX_SQL_TOKENS:
            return True
        if candidate[-1:] == [";"]:
            candidate = candidate[:-1]
        for _ in range(MAX_SQL_WRAPPER_PASSES):
            if candidate and candidate[0] == "(" and matching_parenthesis(candidate) == len(candidate) - 1:
                candidate = candidate[1:-1]
                continue
            break
        if not candidate:
            return False
        if candidate[0] == "(" and matching_parenthesis(candidate) == len(candidate) - 1:
            return True
        if candidate[0].upper() == "WITH":
            select_position = consume_cte_prefix(candidate)
            if select_position < 0:
                return False
            pending.append(candidate[select_position:])
            continue
        branches: list[list[str]] = []
        start = 0
        depth = 0
        position = 0
        while position < len(candidate):
            token = candidate[position]
            if token == "(":
                depth += 1
            elif token == ")":
                depth -= 1
                if depth < 0:
                    return False
            elif depth == 0 and token.upper() in {"EXCEPT", "INTERSECT", "MINUS", "UNION"}:
                if position == start:
                    return False
                branches.append(candidate[start:position])
                position += 1
                if (
                    token.upper() == "UNION"
                    and position < len(candidate)
                    and candidate[position].upper()
                    in {
                        "ALL",
                        "DISTINCT",
                    }
                ):
                    position += 1
                if token.upper() == "UNION" and position < len(candidate) and candidate[position].upper() == "BY":
                    if position + 1 >= len(candidate) or candidate[position + 1].upper() != "NAME":
                        return False
                    position += 2
                start = position
                continue
            position += 1
        if depth != 0 or start >= len(candidate):
            return False
        if branches:
            branches.append(candidate[start:])
            pending.extend(branches)
            continue
        if candidate[0].upper() != "SELECT" or not looks_like_select_branch(candidate):
            return False
    return True


def looks_like_show(tokens: list[str]) -> bool:
    upper = [token.upper() for token in tokens]
    end = len(tokens) - 1 if tokens[-1:] == [";"] else len(tokens)
    external_access_family = end > 3 and upper[1:4] == ["EXTERNAL", "ACCESS", "INTEGRATIONS"]
    semantic_metadata_family = (
        end > 2
        and upper[1] == "SEMANTIC"
        and upper[2]
        in {
            "DIMENSIONS",
            "FACTS",
            "METRICS",
        }
    )
    compound_family = end > 2 and (
        (upper[1] in SQL_SHOW_MODIFIERS and upper[2] in SQL_SHOW_LEADS)
        or (upper[1] in SQL_INTEGRATION_TYPES and upper[2] == "INTEGRATIONS")
        or semantic_metadata_family
    )
    if end < 2 or (
        upper[1] not in SQL_SHOW_LEADS
        and not compound_family
        and not (end > 2 and upper[2] == "INTEGRATIONS")
        and not external_access_family
    ):
        return False
    family_position = 3 if external_access_family else 2 if compound_family else 1
    family = upper[family_position]
    position = family_position + 1
    integration_family = family == "INTEGRATIONS"
    grant_family = family == "GRANTS"
    if not integration_family and not grant_family and position < end and upper[position] == "HISTORY":
        position += 1
    if position == end:
        return True
    if integration_family:
        allowed_clauses = {"LIKE"}
    elif grant_family:
        allowed_clauses = {"IN", "OF", "ON", "TO"}
    else:
        allowed_clauses = {"IN", "LIKE", "LIMIT", "STARTS"}
        if semantic_metadata_family and family == "DIMENSIONS":
            allowed_clauses.add("FOR")
    while position < end:
        clause = upper[position]
        position += 1
        if clause not in allowed_clauses:
            return False
        if clause == "FOR":
            if position >= end or upper[position] != "METRIC":
                return False
            position += 1
            if position >= end:
                return False
            position = consume_qualified_identifier(tokens[:end], position)
            if position < 0:
                return False
            continue
        if grant_family:
            if position >= end:
                return False
            if upper[position] == "ACCOUNT":
                position += 1
                continue
            if upper[position] in SQL_OBJECT_LEADS.union({"APPLICATION", "ROLE", "SHARE", "USER"}):
                position += 1
                if position < end and upper[position - 1] == "DATABASE" and upper[position] == "ROLE":
                    position += 1
            if position >= end:
                return False
            position = consume_qualified_identifier(tokens[:end], position)
            continue
        if clause == "STARTS":
            if position >= end or upper[position] != "WITH":
                return False
            position += 1
        elif clause == "LIMIT":
            if position >= end or not re.fullmatch(r"\d+", tokens[position]):
                return False
            position += 1
            if position < end and upper[position] == "FROM":
                position += 1
                if position >= end:
                    return False
                if tokens[position].startswith(("'", '"')):
                    position += 1
                else:
                    position = consume_qualified_identifier(tokens[:end], position)
            continue
        elif clause == "IN":
            if position >= end:
                return False
            if upper[position] in SQL_SHOW_SCOPES:
                position += 1
                if position == end:
                    continue
            position = consume_qualified_identifier(tokens[:end], position)
            continue
        elif clause != "LIKE":
            return False
        if position >= end or not (
            is_sql_identifier(tokens[position]) or tokens[position].startswith(("'", '"', "@", "$"))
        ):
            return False
        position += 1
    return position == end


def looks_like_describe(tokens: list[str]) -> bool:
    upper = [token.upper() for token in tokens]
    end = len(tokens) - 1 if tokens[-1:] == [";"] else len(tokens)
    if end < 3:
        return False
    position = 2
    family = upper[1]
    if upper[1] == "ROW" and end > 3 and upper[2:4] == ["ACCESS", "POLICY"]:
        family = "POLICY"
        position = 4
    elif end > 2 and (
        (upper[1] in {"DYNAMIC", "EVENT", "EXTERNAL", "HYBRID", "ICEBERG"} and upper[2] == "TABLE")
        or (upper[1] == "MATERIALIZED" and upper[2] == "VIEW")
        or (upper[1] == "SEMANTIC" and upper[2] == "VIEW")
        or (upper[1] == "FILE" and upper[2] == "FORMAT")
        or upper[2] in {"INTEGRATION", "POLICY"}
    ):
        family = upper[2]
        position = 3
    elif family not in SQL_OBJECT_LEADS.union({"QUERY", "RESULT"}):
        return False

    if family == "RESULT":
        if position >= end:
            return False
        if tokens[position].startswith(("'", '"')):
            return position + 1 == end
        function_end = consume_qualified_identifier(tokens[:end], position)
        if function_end < 0 or function_end >= end or tokens[function_end] != "(":
            return False
        close = matching_parenthesis(tokens[:end], function_end)
        return close == end - 1

    position = consume_qualified_identifier(tokens[:end], position)
    if position < 0:
        return False
    if family in {"FUNCTION", "PROCEDURE"} and position < end and tokens[position] == "(":
        close = matching_parenthesis(tokens[:end], position)
        return close == end - 1
    if family == "TABLE" and position + 2 < end and upper[position : position + 2] == ["TYPE", "="]:
        return position + 3 == end and upper[position + 2] in {"COLUMNS", "STAGE"}
    return position == end


def strip_leading_sql_comments(value: str) -> str:
    stripped = value.lstrip()
    while stripped:
        if stripped.startswith("/*"):
            end = stripped.find("*/", 2)
            if end < 0:
                return ""
            stripped = stripped[end + 2 :].lstrip()
            continue
        if stripped.startswith("--"):
            newline = stripped.find("\n", 2)
            if newline < 0:
                return ""
            stripped = stripped[newline + 1 :].lstrip()
            continue
        break
    return stripped


def peel_sql_wrappers(value: str) -> str:
    unwrapped = value.strip()
    for _ in range(MAX_SQL_WRAPPER_PASSES):
        if not unwrapped:
            break
        previous = unwrapped
        unwrapped = SQL_DIAGNOSTIC_PREFIX_RE.sub("", unwrapped, count=1).strip()
        unwrapped = strip_leading_sql_comments(unwrapped)
        unwrapped = SQL_STATEMENT_LABEL_RE.sub("", unwrapped, count=1).strip()
        if unwrapped == previous:
            break
    else:
        stripped = unwrapped.lstrip()
        if (
            SQL_DIAGNOSTIC_PREFIX_RE.match(stripped)
            or SQL_STATEMENT_LABEL_RE.match(stripped)
            or stripped.startswith(("/*", "--"))
        ):
            return "VALUES (0)"
    return unwrapped


def has_suspicious_sql_prefix(value: str) -> bool:
    sample = value[:512]
    if SQL_DIAGNOSTIC_PREFIX_RE.match(sample) or SQL_STATEMENT_LABEL_RE.match(sample):
        return True
    candidate = strip_sql_comments(peel_sql_wrappers(sample)).lstrip(" ;\t\r\n")
    first = re.match(r"[A-Za-z_]+", candidate)
    return bool(first and first.group(0).upper() in SQL_STATEMENT_STARTS)


def looks_like_raw_sql(value: str) -> bool:
    if len(value) > MAX_SQL_SCAN_CHARS:
        return has_suspicious_sql_prefix(value)
    cleaned = strip_sql_comments(peel_sql_wrappers(value)).strip()
    cleaned = re.sub(r"^(?:\s*;\s*)+", "", cleaned)
    if not cleaned:
        return False
    tokens = SQL_TOKEN_RE.findall(cleaned)
    if not tokens:
        return False
    if len(tokens) > MAX_SQL_TOKENS:
        position = 0
        while position < len(tokens) and tokens[position] == "(":
            position += 1
        return position < len(tokens) and tokens[position].upper() in SQL_STATEMENT_STARTS
    upper = [token.upper() for token in tokens]
    first = upper[0]
    tail = tokens[1:]
    upper_tail = upper[1:]

    pipe_index = top_level_keyword(tokens, "->>")
    if pipe_index > 0:
        left = tokens[:pipe_index]
        right = tokens[pipe_index + 1 :]
        left_first = left[0].upper()
        if right and right[0].upper() == "SELECT" and looks_like_select(right):
            if left_first == "SHOW" and looks_like_show(left):
                return True
            if left_first in {"DESC", "DESCRIBE"} and looks_like_describe(left):
                return True

    if first == "SELECT":
        return looks_like_select(tokens)
    if first == "(":
        return looks_like_select(tokens)
    if first == "WITH":
        return "AS" in upper_tail and "(" in tail
    if first == "VALUES":
        return looks_like_values_rows(tail, tokens[0] == "Values")
    if first == "SHOW":
        return looks_like_show(tokens)
    if first in {"DESCRIBE", "DESC"}:
        return looks_like_describe(tokens)
    if first in {"LIST", "LS"}:
        return bool(tail and tail[0].startswith("@"))
    if first == "USE":
        return bool(upper_tail and upper_tail[0] in {"DATABASE", "ROLE", "SCHEMA", "SECONDARY", "WAREHOUSE"})
    if first == "TRUNCATE":
        return bool(tail and (upper_tail[0] == "TABLE" or re.match(r'[A-Za-z_$"]', tail[0])))
    if first == "INSERT":
        return bool(upper_tail and upper_tail[0] == "INTO")
    if first == "UPDATE":
        return "SET" in upper_tail
    if first == "DELETE":
        return bool(upper_tail and upper_tail[0] == "FROM")
    if first == "MERGE":
        return bool(upper_tail and upper_tail[0] == "INTO")
    if first in {"CREATE", "ALTER", "DROP"}:
        modifiers = {
            "EXISTS",
            "IF",
            "NOT",
            "OR",
            "ALTER",
            "REPLACE",
            "SECURE",
            "TEMP",
            "TEMPORARY",
            "TRANSIENT",
            "VOLATILE",
        }
        object_tokens = [token for token in upper_tail if token not in modifiers]
        return bool(
            object_tokens
            and (object_tokens[0] in SQL_OBJECT_LEADS or (len(object_tokens) > 1 and object_tokens[1] == "INTEGRATION"))
        )
    if first == "COPY":
        return bool(
            upper_tail
            and (
                upper_tail[0] == "INTO"
                or (len(upper_tail) > 1 and upper_tail[0] == "FILES" and upper_tail[1] == "INTO")
            )
        )
    if first == "BEGIN":
        return bool(
            upper_tail
            and (
                upper_tail[0] in {"TRANSACTION", "WORK"}
                or (
                    "END" in upper_tail
                    and ";" in tail
                    and SQL_SCRIPT_STATEMENT_LEADS.union(
                        {"DECLARE", "FOR", "IF", "LET", "LOOP", "RETURN", "WHILE"}
                    ).intersection(upper_tail)
                )
            )
        )
    if first == "DECLARE":
        return bool("BEGIN" in upper_tail and "END" in upper_tail and ";" in tail)
    if first == "GRANT":
        return "TO" in upper_tail
    if first == "REVOKE":
        return "FROM" in upper_tail
    if first == "CALL":
        return "(" in tail
    if first == "EXECUTE":
        return bool(upper_tail and upper_tail[0] in {"IMMEDIATE", "TASK"})
    if first in {"GET", "REMOVE"}:
        return bool(tail and tail[0].startswith("@"))
    if first == "PUT":
        if not tail:
            return False
        source = tail[0][1:-1] if tail[0][:1] in {"'", '"'} and tail[0][-1:] == tail[0][:1] else tail[0]
        return bool(tail and (source.casefold().startswith("file://") or source.startswith("@")))
    if first == "COMMENT":
        return "ON" in upper_tail
    if first == "UNDROP":
        return bool(upper_tail and upper_tail[0] in {"DATABASE", "SCHEMA", "TABLE"})
    if first == "EXPLAIN":
        return bool({"DELETE", "INSERT", "MERGE", "SELECT", "UPDATE", "WITH"}.intersection(upper_tail))
    if first in {"COMMIT", "ROLLBACK"}:
        return not upper_tail or upper_tail[0] == "WORK"
    if first == "SET":
        return "=" in tail
    if first == "UNSET":
        return bool(tail)
    return False


def normalize_sensitive_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def is_sensitive_key(value: Any) -> bool:
    normalized = normalize_sensitive_key(value)
    return (
        normalized in SENSITIVE_KEYS
        or normalized in SAFE_SENSITIVE_METADATA_KEYS
        or any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)
    )


def is_safe_sensitive_metadata(key: Any, value: Any) -> bool:
    return normalize_sensitive_key(key) in SAFE_SENSITIVE_METADATA_KEYS and isinstance(value, bool)


def reject_secret_fields(value: Any, path: str = "input", depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [MAX_SANITIZE_TREE_NODES]
    if depth >= MAX_SANITIZE_TREE_DEPTH or budget[0] <= 0:
        raise EvidenceError(f"input nesting exceeds the supported limit: {path}")
    budget[0] -= 1
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = normalize_sensitive_key(key)
            if normalized in {"querytag", "username"}:
                raise EvidenceError(f"raw identity/tag field is not accepted: {path}.{key}; use a Snowflake-side hash")
            if is_safe_sensitive_metadata(key, child):
                continue
            if is_sensitive_key(key):
                raise EvidenceError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_secret_fields(child, f"{path}.{key}", depth + 1, budget)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_fields(child, f"{path}[{index}]", depth + 1, budget)


def safe_text(value: Any) -> str:
    try:
        raw = str(value)
    except Exception:
        return "[REDACTED_CREDENTIAL]"
    oversized = len(raw) > MAX_SQL_SCAN_CHARS
    text = raw[:MAX_SQL_SCAN_CHARS]
    try:
        text = redact_authorization_values(text)
        for pattern, replacement in STATIC_REDACTIONS:
            text = pattern.sub(replacement, text)
        if (oversized and has_suspicious_sql_prefix(text)) or looks_like_raw_sql(text):
            return "[REDACTED_SQL]"
        return text[:2000]
    except Exception:
        return "[REDACTED_SQL]"


def _sanitize_output_tree(value: Any, depth: int, budget: list[int]) -> Any:
    if depth >= MAX_SANITIZE_TREE_DEPTH or budget[0] <= 0:
        return "[REDACTED_CREDENTIAL]"
    budget[0] -= 1
    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, child in value.items():
            if budget[0] <= 0:
                sanitized["_sanitizer_truncated"] = "[REDACTED_CREDENTIAL]"
                break
            if is_safe_sensitive_metadata(key, child):
                sanitized[key] = child
            elif is_sensitive_key(key):
                sanitized[key] = "[REDACTED_CREDENTIAL]"
            else:
                sanitized[key] = _sanitize_output_tree(child, depth + 1, budget)
        return sanitized
    if isinstance(value, (list, tuple)):
        sanitized_list = []
        for child in value:
            if budget[0] <= 0:
                sanitized_list.append("[REDACTED_CREDENTIAL]")
                break
            sanitized_list.append(_sanitize_output_tree(child, depth + 1, budget))
        return sanitized_list
    if isinstance(value, str):
        return safe_text(value)
    return value


def sanitize_output_tree(value: Any) -> Any:
    """Redact output without allowing malformed input to escape artifact APIs."""
    try:
        return _sanitize_output_tree(value, 0, [MAX_SANITIZE_TREE_NODES])
    except Exception:
        return "[REDACTED_CREDENTIAL]"


def validate_safe_label(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SAFE_LABEL_RE.fullmatch(value) or value != value.strip():
        raise EvidenceError(f"{field} must be a bounded printable label")
    sanitized = safe_text(value)
    if sanitized != value:
        raise EvidenceError(f"{field} contains credential-bearing, identifying, URL, or raw-SQL-like text")
    return value


def validate_owner(value: Any, field: str) -> str:
    owner = validate_safe_label(value, field)
    if not OWNER_RE.fullmatch(owner):
        raise EvidenceError(f"{field} must use the reviewed owner identifier grammar")
    return owner


def validate_operator_id(value: Any, field: str) -> str:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        rendered = str(value)
    elif isinstance(value, str):
        rendered = validate_safe_label(value, field)
    else:
        raise EvidenceError(f"{field} must be a non-negative decimal identifier")
    if not OPERATOR_ID_RE.fullmatch(rendered):
        raise EvidenceError(f"{field} must be a non-negative decimal identifier")
    return rendered


def validate_operator_type(value: Any, field: str) -> str:
    rendered = validate_safe_label(value, field)
    if not OPERATOR_TYPE_RE.fullmatch(rendered):
        raise EvidenceError(f"{field} must use the reviewed operator-type identifier grammar")
    return rendered


def validate_insight_type(value: Any, field: str) -> str:
    rendered = validate_safe_label(value, field)
    if not INSIGHT_TYPE_RE.fullmatch(rendered):
        raise EvidenceError(f"{field} must use the reviewed Query Insights type identifier grammar")
    return rendered


def decimal_value(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise EvidenceError(f"{field} must be a finite non-negative number") from exc
    if not number.is_finite() or number < 0:
        raise EvidenceError(f"{field} must be a finite non-negative number")
    return number


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def as_text(number: Decimal) -> str:
    return format(number.quantize(Decimal("0.000001")).normalize(), "f")


def nested_number(container: dict[str, Any], path: tuple[str, ...], field: str) -> Decimal:
    current: Any = container
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return Decimal("0")
        current = current[key]
    return decimal_value(current, field)


def load_summary(
    rows: Any,
    warnings: list[str],
    query_start: datetime,
    query_end: datetime,
    query_warehouse: str,
) -> list[dict[str, str]]:
    if rows is None:
        return []
    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
        raise EvidenceError("warehouse_load must be an array of objects")
    grouped: dict[str, dict[str, Decimal]] = {}
    excluded = 0
    for index, row in enumerate(rows):
        prefix = f"warehouse_load[{index}]"
        if row.get("start_time") is None or row.get("end_time") is None:
            raise EvidenceError(f"{prefix}.start_time and end_time are required for query alignment")
        row_start = parse_time(row["start_time"], f"{prefix}.start_time")
        row_end = parse_time(row["end_time"], f"{prefix}.end_time")
        if row_start >= row_end:
            raise EvidenceError(f"{prefix}.start_time must be before end_time")
        name = str(row.get("warehouse_name") or "<unknown>")
        if name != query_warehouse or row_end <= query_start or row_start >= query_end:
            excluded += 1
            continue
        item = grouped.setdefault(
            name,
            {
                "running": Decimal("0"),
                "queued": Decimal("0"),
                "provisioning": Decimal("0"),
                "blocked": Decimal("0"),
                "rows": Decimal("0"),
            },
        )
        for source, target in (
            ("avg_running", "running"),
            ("avg_queued_load", "queued"),
            ("avg_queued_provisioning", "provisioning"),
            ("avg_blocked", "blocked"),
        ):
            if row.get(source) is not None:
                item[target] += decimal_value(row[source], f"warehouse_load[{index}].{source}")
        item["rows"] += 1
    if excluded:
        warnings.append(f"warehouse_load: excluded {excluded} row(s) outside the query interval or warehouse")
    result = []
    for name, values in grouped.items():
        result.append(
            {
                "warehouse_name": name,
                "interval_count": as_text(values["rows"]),
                "avg_running_load_sum": as_text(values["running"]),
                "avg_queued_load_sum": as_text(values["queued"]),
                "avg_queued_provisioning_sum": as_text(values["provisioning"]),
                "avg_blocked_sum": as_text(values["blocked"]),
                "classification": "confirmed",
            }
        )
        if values["queued"] > 0 or values["provisioning"] > 0:
            warnings.append(
                f"{name}: warehouse load shows queue/provisioning pressure; align it with this query's wait timeline"
            )
    return sorted(result, key=lambda item: item["warehouse_name"])


def hash_comparison(data: dict[str, Any], warnings: list[str]) -> list[dict[str, Any]]:
    supplied = data.get("query_runs")
    if supplied is None:
        supplied = [data["query_history"]]
    if not isinstance(supplied, list) or not all(isinstance(item, dict) for item in supplied):
        raise EvidenceError("query_runs must be an array of objects")
    if len(supplied) > 1:
        alignment = data.get("comparison_alignment")
        required = ("warehouse_name", "data_scope", "parameters", "cache_state", "session_parameters")
        if not isinstance(alignment, dict) or alignment.get("status") != "aligned":
            warnings.append("query hash comparison unavailable: explicit aligned comparison receipt is missing")
            return []
        missing = [field for field in required if field not in alignment or alignment[field] is None]
        if missing:
            warnings.append(
                "query hash comparison unavailable: aligned comparison receipt is missing " + ", ".join(missing)
            )
            return []
        if any(not isinstance(alignment[field], (str, dict, list, bool, int, float)) for field in required):
            warnings.append("query hash comparison unavailable: aligned comparison receipt contains invalid fields")
            return []
    else:
        alignment = None
    groups: dict[str, list[tuple[Decimal, str | None]]] = {}
    invalid = False
    for index, row in enumerate(supplied):
        fingerprint = row.get("query_parameterized_hash") or row.get("query_hash")
        elapsed = row.get("total_elapsed_time_ms")
        if fingerprint is None or elapsed is None or not row.get("query_id"):
            warnings.append(f"query_runs[{index}]: fingerprint, elapsed time, and query_id are required for comparison")
            invalid = True
            continue
        fingerprint = validate_hash(fingerprint, f"query_runs[{index}].query_fingerprint")
        if alignment is not None and row.get("warehouse_name") != alignment.get("warehouse_name"):
            warnings.append(f"query_runs[{index}]: warehouse does not match aligned comparison receipt")
            invalid = True
            continue
        value = decimal_value(elapsed, f"query_runs[{index}].total_elapsed_time_ms")
        group_key = str(fingerprint)
        run_id = validate_query_id(row.get("query_id"), f"query_runs[{index}].query_id")
        groups.setdefault(group_key, []).append((value, run_id))
    if invalid:
        return []
    if not groups:
        warnings.append("query hash comparison unavailable: no fingerprinted runs with elapsed time")
    result = []
    for fingerprint, runs in groups.items():
        values = [value for value, _ in runs]
        result.append(
            {
                "fingerprint": safe_text(fingerprint),
                "sample_count": len(values),
                "average_elapsed_time_ms": as_text(sum(values, Decimal("0")) / len(values)),
                "min_elapsed_time_ms": as_text(min(values)),
                "max_elapsed_time_ms": as_text(max(values)),
                "query_ids": [safe_text(str(query_id)) for _, query_id in runs if query_id is not None],
                "classification": "derived",
            }
        )
    return sorted(result, key=lambda item: str(item["fingerprint"]))


def search_optimization_roi(data: dict[str, Any], warnings: list[str]) -> list[dict[str, str]]:
    supplied = data.get("search_optimization")
    if supplied is None:
        return []
    if isinstance(supplied, dict):
        supplied = [supplied]
    if not isinstance(supplied, list) or not all(isinstance(item, dict) for item in supplied):
        raise EvidenceError("search_optimization must be an object or array of objects")
    result: list[dict[str, str]] = []
    for index, row in enumerate(supplied):
        for field in (
            "credits_used",
            "query_count",
            "latency_before_ms",
            "latency_after_ms",
            "bytes_scanned_before",
            "bytes_scanned_after",
        ):
            if field in row and row[field] is not None:
                decimal_value(row[field], f"search_optimization[{index}].{field}")
        credits = decimal_value(row.get("credits_used", 0), f"search_optimization[{index}].credits_used")
        before_latency = row.get("latency_before_ms")
        after_latency = row.get("latency_after_ms")
        before_bytes = row.get("bytes_scanned_before")
        after_bytes = row.get("bytes_scanned_after")
        item: dict[str, str] = {"classification": "derived", "credits_used": as_text(credits)}
        if before_latency is not None and after_latency is not None:
            latency_delta = decimal_value(
                before_latency, f"search_optimization[{index}].latency_before_ms"
            ) - decimal_value(after_latency, f"search_optimization[{index}].latency_after_ms")
            item["latency_reduction_ms"] = as_text(latency_delta)
        if before_bytes is not None and after_bytes is not None:
            bytes_delta = decimal_value(
                before_bytes, f"search_optimization[{index}].bytes_scanned_before"
            ) - decimal_value(after_bytes, f"search_optimization[{index}].bytes_scanned_after")
            item["bytes_scanned_reduction"] = as_text(bytes_delta)
        if credits > 0 and "latency_reduction_ms" not in item and "bytes_scanned_reduction" not in item:
            warnings.append(
                "search optimization credits supplied without a measured latency or scan baseline; ROI is unknown"
            )
        item["decision"] = "review measured benefit against maintenance credits; no SOS change proposed"
        result.append(item)
    return result


def analyze(data: dict[str, Any], *, trusted_input_sha256: str | None = None) -> dict[str, Any]:
    reject_secret_fields(data)
    if data.get("schema_version") != "2.0":
        raise EvidenceError("schema_version must be 2.0; recollect or migrate legacy query evidence")
    metadata = data.get("metadata")
    history = data.get("query_history")
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    if not isinstance(history, dict):
        raise EvidenceError("query_history must be an object")
    query_id = validate_query_id(metadata.get("query_id"), "metadata.query_id")
    history_query_id = validate_query_id(history.get("query_id"), "query_history.query_id")
    if history_query_id != query_id:
        raise EvidenceError("metadata.query_id must match query_history.query_id")
    for field in ("query_hash", "query_parameterized_hash"):
        if history.get(field) is not None:
            validate_hash(history[field], f"query_history.{field}")
    account = validate_safe_label(metadata.get("account"), "metadata.account")
    metadata_role = validate_safe_label(metadata.get("role"), "metadata.role")
    history_source = validate_safe_label(metadata.get("history_source"), "metadata.history_source")
    if history_source not in TERMINAL_QUERY_STATUSES_BY_SOURCE:
        raise EvidenceError("metadata.history_source is not a supported reviewed query-history surface")
    experiment_owner = validate_owner(metadata.get("experiment_owner"), "metadata.experiment_owner")
    warehouse_name = validate_safe_label(history.get("warehouse_name"), "query_history.warehouse_name")
    collected_at = parse_time(metadata.get("collected_at"), "metadata.collected_at")
    source_max_time = parse_time(metadata.get("history_source_max_time"), "metadata.history_source_max_time")
    if source_max_time > collected_at:
        raise EvidenceError("metadata.history_source_max_time cannot be later than metadata.collected_at")
    if collected_at > datetime.now(timezone.utc):
        raise EvidenceError("metadata.collected_at cannot be in the future")
    observed_age = Decimal(str((collected_at - source_max_time).total_seconds()))
    source_max_age_seconds = metadata.get("source_max_age_seconds")
    if (
        not isinstance(source_max_age_seconds, int)
        or isinstance(source_max_age_seconds, bool)
        or source_max_age_seconds <= 0
    ):
        raise EvidenceError("metadata.source_max_age_seconds must be a positive integer")
    calculated_source_freshness_ok = observed_age <= source_max_age_seconds

    operators = data.get("operators", [])
    insights = data.get("query_insights", [])
    if not isinstance(operators, list) or not all(isinstance(item, dict) for item in operators):
        raise EvidenceError("operators must be an array of objects")
    if not isinstance(insights, list) or not all(isinstance(item, dict) for item in insights):
        raise EvidenceError("query_insights must be an array of objects")

    confirmed: list[dict[str, str]] = []
    derived: list[dict[str, str]] = []
    hypotheses: list[dict[str, str]] = []
    warnings: list[str] = []
    evidence_trust = assess_input_trust(data, trusted_input_sha256, warnings)
    collector_receipt = validate_collector_receipt(
        data,
        warnings,
        collected_at,
        source_max_time,
        source_max_age_seconds,
        query_id,
        history_source,
        metadata_role,
        evidence_trust["trusted"],
    )
    source_freshness_verified = collector_receipt["complete"]
    source_freshness_ok = source_freshness_verified and calculated_source_freshness_ok
    if not calculated_source_freshness_ok:
        warnings.append("query history source exceeds the declared freshness bound")
    if not source_freshness_verified:
        warnings.append("query history freshness is unverified because its receipt binding failed")
    query_start = query_end = None
    if data.get("warehouse_load"):
        query_start = parse_time(history.get("start_time"), "query_history.start_time")
        query_end = parse_time(history.get("end_time"), "query_history.end_time")
        if query_start >= query_end:
            raise EvidenceError("query_history.start_time must be before end_time")
    operators_supplied = bool(operators)
    insights_supplied = bool(insights)
    operators, operators_bound = bind_rows_to_query(operators, "operators", query_id, warnings)
    insights, insights_bound = bind_rows_to_query(insights, "query_insights", query_id, warnings)
    evidence_binding_complete = operators_bound and insights_bound

    status = validate_safe_label(
        str(history.get("execution_status") or "unknown").lower(), "query_history.execution_status"
    )
    operator_evidence_eligible = status_is_terminal(history_source, status)
    if not status_is_known(history_source, status):
        warnings.append(f"execution status is not valid for {history_source}; evidence claims were withheld")
    if not collector_receipt["complete"]:
        if operators_supplied or insights_supplied:
            warnings.append(
                "operator and Query Insights claims were withheld because the evidence trust boundary is incomplete"
            )
        evidence_binding_complete = False
    if not operator_evidence_eligible:
        if operators_supplied or insights_supplied:
            warnings.append(
                "operator or Query Insights rows were supplied for a nonterminal query; rows excluded and binding marked incomplete"
            )
        evidence_binding_complete = False
    if not operators:
        warnings.append(
            "required operator statistics are absent; this is a partial packet and completeness remains blocked"
        )
        evidence_binding_complete = False
    claim_boundary_complete = collector_receipt["complete"] and operator_evidence_eligible and evidence_binding_complete
    if not claim_boundary_complete:
        operators = []
        insights = []

    if claim_boundary_complete:
        warehouse_load = load_summary(
            data.get("warehouse_load", []),
            warnings,
            query_start or datetime.min.replace(tzinfo=timezone.utc),
            query_end or datetime.max.replace(tzinfo=timezone.utc),
            warehouse_name,
        )
        hash_comparison_rows = hash_comparison(data, warnings)
        sos_roi = search_optimization_roi(data, warnings)
    else:
        warehouse_load = []
        hash_comparison_rows = []
        sos_roi = []
        if data.get("warehouse_load") or data.get("query_runs") or data.get("search_optimization"):
            warnings.append(
                "derived comparison and warehouse claims were withheld because the complete evidence boundary was not met"
            )
    timing_fields = (
        ("compilation_time_ms", "compilation"),
        ("execution_time_ms", "execution"),
        ("queued_overload_time_ms", "warehouse queue overload"),
        ("queued_provisioning_time_ms", "warehouse provisioning wait"),
        ("queued_repair_time_ms", "warehouse repair wait"),
        ("transaction_blocked_time_ms", "transaction blocked wait"),
    )
    timeline: dict[str, str | None] = {}
    supplied_component_total = Decimal("0")
    for field, label in timing_fields:
        if field not in history or history[field] is None:
            timeline[field] = None
            continue
        value = decimal_value(history[field], f"query_history.{field}")
        timeline[field] = as_text(value)
        supplied_component_total += value
        if value > 0 and claim_boundary_complete:
            confirmed.append(
                {
                    "kind": "timing",
                    "metric": field,
                    "value": as_text(value),
                    "unit": "milliseconds",
                    "classification": "confirmed",
                    "observation": label,
                }
            )
            if field == "queued_overload_time_ms":
                hypotheses.append(
                    {
                        "hypothesis": "concurrency or workload-placement pressure",
                        "classification": "at-risk",
                        "evidence": f"{as_text(value)} ms queued for overload",
                        "competing_explanation": "temporary burst or intentionally bounded capacity",
                        "next_read_only_check": "correlate warehouse load over the same interval",
                    }
                )
            if field == "transaction_blocked_time_ms":
                hypotheses.append(
                    {
                        "hypothesis": "transaction lock contention",
                        "classification": "at-risk",
                        "evidence": f"{as_text(value)} ms transaction-blocked time",
                        "competing_explanation": "expected serialization for the workload",
                        "next_read_only_check": "identify blocker and waiter transactions without terminating either",
                    }
                )

    if history.get("total_elapsed_time_ms") is not None:
        total_elapsed = decimal_value(history["total_elapsed_time_ms"], "query_history.total_elapsed_time_ms")
        timeline["total_elapsed_time_ms"] = as_text(total_elapsed)
        difference = total_elapsed - supplied_component_total
        if difference >= 0:
            timeline["other_or_unexplained_time_ms"] = as_text(difference)
        else:
            timeline["other_or_unexplained_time_ms"] = None
            warnings.append("supplied timing components exceed total elapsed time; verify source semantics and overlap")
    else:
        timeline["total_elapsed_time_ms"] = None
        timeline["other_or_unexplained_time_ms"] = None
        warnings.append("total elapsed time absent; supplied timing fields cannot be reconciled")

    for field, unit in (
        ("bytes_scanned", "bytes"),
        ("partitions_scanned", "partitions"),
        ("partitions_total", "partitions"),
        ("bytes_spilled_to_local_storage", "bytes"),
        ("bytes_spilled_to_remote_storage", "bytes"),
    ):
        if history.get(field) is None:
            continue
        value = decimal_value(history[field], f"query_history.{field}")
        if claim_boundary_complete:
            confirmed.append(
                {
                    "kind": "query_history",
                    "metric": field,
                    "value": as_text(value),
                    "unit": unit,
                    "classification": "confirmed",
                    "observation": "QUERY_HISTORY counter supplied",
                }
            )
    top_operators: list[dict[str, str]] = []
    for index, operator in enumerate(operators):
        operator_id = validate_operator_id(operator.get("operator_id"), f"operators[{index}].operator_id")
        operator_type = validate_operator_type(operator.get("operator_type"), f"operators[{index}].operator_type")
        statistics = operator.get("operator_statistics") or {}
        breakdown = operator.get("execution_time_breakdown") or {}
        if not isinstance(statistics, dict) or not isinstance(breakdown, dict):
            raise EvidenceError(f"operators[{index}] statistics and breakdown must be objects")

        overall = decimal_value(
            breakdown.get("overall_percentage", 0),
            f"operators[{index}].execution_time_breakdown.overall_percentage",
        )
        if overall > 100:
            raise EvidenceError(f"operators[{index}].execution_time_breakdown.overall_percentage cannot exceed 100")
        top_operators.append(
            {
                "operator_id": operator_id,
                "operator_type": operator_type,
                "overall_percentage": as_text(overall),
            }
        )

        remote_spill = nested_number(
            statistics,
            ("spilling", "bytes_spilled_remote_storage"),
            f"operators[{index}].operator_statistics.spilling.bytes_spilled_remote_storage",
        )
        local_spill = nested_number(
            statistics,
            ("spilling", "bytes_spilled_local_storage"),
            f"operators[{index}].operator_statistics.spilling.bytes_spilled_local_storage",
        )
        for metric, value in (
            ("bytes_spilled_remote_storage", remote_spill),
            ("bytes_spilled_local_storage", local_spill),
        ):
            if value > 0:
                confirmed.append(
                    {
                        "kind": "operator",
                        "metric": metric,
                        "value": as_text(value),
                        "unit": "bytes",
                        "operator_id": operator_id,
                        "operator_type": operator_type,
                        "classification": "confirmed",
                        "observation": "spill recorded by operator statistics",
                    }
                )
        if remote_spill > 0:
            hypotheses.append(
                {
                    "hypothesis": "query shape or warehouse capacity contributed to remote spill",
                    "classification": "at-risk",
                    "evidence": f"operator {operator_id} recorded {as_text(remote_spill)} remote-spill bytes",
                    "competing_explanation": "data-volume change or intentional batch shape",
                    "next_read_only_check": "compare the same parameterized hash and aligned data volume",
                }
            )

        input_rows = statistics.get("input_rows")
        output_rows = statistics.get("output_rows")
        if input_rows is not None and output_rows is not None:
            input_value = decimal_value(input_rows, f"operators[{index}].operator_statistics.input_rows")
            output_value = decimal_value(output_rows, f"operators[{index}].operator_statistics.output_rows")
            if input_value > 0:
                multiple = output_value / input_value
                derived.append(
                    {
                        "metric": "output_to_input_row_multiple",
                        "value": as_text(multiple),
                        "operator_id": operator_id,
                        "operator_type": operator_type,
                        "classification": "estimated",
                        "basis": "output_rows / input_rows",
                    }
                )
                if operator_type.lower() in {"join", "cartesianjoin"} and multiple > 1:
                    hypotheses.append(
                        {
                            "hypothesis": "join expansion requires semantic review",
                            "classification": "at-risk",
                            "evidence": f"operator {operator_id} output/input multiple {as_text(multiple)}",
                            "competing_explanation": "valid many-to-many join semantics",
                            "next_read_only_check": "review approved redacted join predicates and baseline cardinality",
                        }
                    )

        scanned = nested_number(
            statistics,
            ("pruning", "partitions_scanned"),
            f"operators[{index}].operator_statistics.pruning.partitions_scanned",
        )
        total = nested_number(
            statistics,
            ("pruning", "partitions_total"),
            f"operators[{index}].operator_statistics.pruning.partitions_total",
        )
        if total > 0:
            if scanned > total:
                raise EvidenceError(f"operators[{index}] partitions_scanned cannot exceed partitions_total")
            ratio = scanned / total
            derived.append(
                {
                    "metric": "partitions_scanned_fraction",
                    "value": as_text(ratio),
                    "operator_id": operator_id,
                    "operator_type": operator_type,
                    "classification": "estimated",
                    "basis": "partitions_scanned / partitions_total",
                }
            )
            if scanned == total:
                hypotheses.append(
                    {
                        "hypothesis": "no partition pruning observed for this scan",
                        "classification": "at-risk",
                        "evidence": f"operator {operator_id} scanned {as_text(scanned)} of {as_text(total)} partitions",
                        "competing_explanation": "the query may intentionally require the full table",
                        "next_read_only_check": "compare predicates and data layout for the same query hash",
                    }
                )

    top_operators.sort(key=lambda item: Decimal(item["overall_percentage"]), reverse=True)

    for index, insight in enumerate(insights):
        type_id = validate_insight_type(insight.get("type_id"), f"query_insights[{index}].type_id")
        confirmed.append(
            {
                "kind": "query_insight",
                "metric": type_id,
                "value": safe_text(insight.get("message") or "platform insight returned"),
                "unit": "message",
                "classification": "confirmed",
                "observation": "Snowflake Query Insight supplied",
            }
        )

    if not operator_evidence_eligible:
        warnings.append(f"execution status is {status}; operator statistics may be unavailable until completion")
    if not operators:
        warnings.append("operator statistics absent; operator-level conditions are unknown, not zero")
    insight_status = data.get("query_insights_status")
    if insight_status is not None:
        if not isinstance(insight_status, dict):
            raise EvidenceError("query_insights_status must be an object")
        status_value = str(insight_status.get("status") or "unknown")
        if status_value not in {"available", "unavailable", "excluded", "unknown"}:
            raise EvidenceError("query_insights_status.status must be available, unavailable, excluded, or unknown")
        insight_coverage = {"status": status_value, "reason": safe_text(insight_status.get("reason") or "not supplied")}
    else:
        insight_coverage = {
            "status": "available" if insights else "unknown",
            "reason": "rows supplied"
            if insights
            else "no row supplied; exclusion, latency, or no signal are all possible",
        }
    if not insights:
        warnings.append(f"no Query Insights supplied; absence is not proof; {insight_coverage['reason']}")

    for hypothesis in hypotheses:
        hypothesis["falsification_evidence"] = (
            "an aligned repeat with the same parameterized hash and fixed inputs does not reproduce the condition"
        )
        hypothesis["experiment_owner"] = experiment_owner

    result = {
        "schema_version": "2.0",
        "query": {
            "query_id": query_id,
            "execution_status": status,
            "account": account,
            "role": metadata_role,
            "warehouse_name": warehouse_name,
            "query_hash": history.get("query_hash"),
            "query_parameterized_hash": history.get("query_parameterized_hash"),
        },
        "history_source": history_source,
        "history_source_max_time": source_max_time.isoformat(),
        "collected_at": collected_at.isoformat(),
        "observed_history_age_seconds": as_text(observed_age),
        "source_freshness": {
            "status": (
                "UNVERIFIED"
                if not source_freshness_verified
                else "FRESH"
                if calculated_source_freshness_ok
                else "STALE"
            ),
            "calculated_status": (
                "UNVERIFIED"
                if not source_freshness_verified
                else "FRESH"
                if calculated_source_freshness_ok
                else "STALE"
            ),
            "observed_age_seconds": as_text(observed_age),
            "declared_max_age_seconds": source_max_age_seconds,
        },
        "timeline_ms": timeline,
        "confirmed_observations": confirmed,
        "estimated_or_derived_metrics": derived,
        "at_risk_hypotheses": hypotheses,
        "top_operators_by_observed_percentage": top_operators,
        "warehouse_load_summary": warehouse_load,
        "query_hash_comparison": hash_comparison_rows,
        "evidence_trust": evidence_trust,
        "collector_receipt_assessment": collector_receipt,
        "evidence_binding": {
            "status": "BOUND" if evidence_binding_complete else "INCOMPLETE",
            "anchor_query_id": query_id,
            "required_minimum": "trusted receipted anchor, source-compatible terminal status, and at least one bound operator row",
        },
        "completeness_claim_blocked": (not claim_boundary_complete or not source_freshness_ok),
        "search_optimization_roi": sos_roi,
        "query_insights_coverage": insight_coverage,
        "one_variable_experiment": {
            "status": "not_proposed",
            "owner": experiment_owner,
            "baseline": "use this packet only after timing/source reconciliation",
            "change": None,
            "fixed_inputs": "same parameterized hash, aligned data window, role, warehouse, and session context",
            "measurement_window": None,
            "success_criteria": None,
            "impact": "unknown until an operator supplies one proposed variable",
            "approval": "explicit workload owner and Snowflake change approver required",
            "rollback": "define reversal for the single selected variable before execution",
        },
        "warnings": sorted(set(warnings)),
        "non_claims": [
            "No single metric was treated as a proven root cause.",
            "No universal performance threshold or SLA was applied.",
            "No SQL, warehouse, clustering, session, or query state was mutated.",
            "Raw query text was not required by this evidence contract.",
        ],
    }
    return sanitize_output_tree(result)


def render_markdown(result: dict[str, Any]) -> str:
    result = sanitize_output_tree(result)
    query = result["query"]
    lines = [
        "# Snowflake query forensics packet",
        "",
        f"Query: `{query['query_id']}` · Status: `{query['execution_status']}`",
        f"Account: `{query.get('account') or 'not supplied'}` · Role: `{query.get('role') or 'not supplied'}`",
        f"History source: `{result.get('history_source') or 'not supplied'}`; observed age {result['observed_history_age_seconds']} seconds",
        f"Source freshness: `{result['source_freshness']['status']}` against declared maximum {result['source_freshness']['declared_max_age_seconds']} seconds",
        f"Evidence trust: `{result['evidence_trust']['status']}`; {result['evidence_trust']['non_claim']}",
        f"Evidence binding: `{result['evidence_binding']['status']}` to `{result['evidence_binding']['anchor_query_id']}`",
        f"Collector receipt: `{result['collector_receipt_assessment']['status']}`; completeness claim blocked: `{result['completeness_claim_blocked']}`",
        "",
        "## Timeline (milliseconds)",
        "",
        "| Field | Supplied/reconciled value |",
        "|---|---:|",
    ]
    for field, value in result["timeline_ms"].items():
        lines.append(f"| {field} | {value if value is not None else 'not supplied'} |")
    lines.extend(
        [
            "",
            "## Confirmed observations",
            "",
        ]
    )
    if result["confirmed_observations"]:
        lines.extend(["| Evidence | Value | Context |", "|---|---:|---|"])
        for item in result["confirmed_observations"]:
            lines.append(f"| {item['metric']} | {item['value']} {item['unit']} | {item['observation']} |")
    else:
        lines.append("No positive confirmed condition was present in the supplied fields.")
    lines.extend(["", "## Estimated or derived metrics", ""])
    if result["estimated_or_derived_metrics"]:
        lines.extend(["| Metric | Value | Basis |", "|---|---:|---|"])
        for item in result["estimated_or_derived_metrics"]:
            lines.append(f"| {item['metric']} | {item['value']} | {item['basis']} |")
    else:
        lines.append("No derived metric was computable from the supplied evidence.")
    lines.extend(["", "## At-risk hypotheses — corroboration required", ""])
    if result["at_risk_hypotheses"]:
        for item in result["at_risk_hypotheses"]:
            lines.extend(
                [
                    f"### {item['hypothesis']}",
                    "",
                    f"- Evidence: {item['evidence']}",
                    f"- Competing explanation: {item['competing_explanation']}",
                    f"- Next read-only check: {item['next_read_only_check']}",
                    f"- Falsification evidence: {item['falsification_evidence']}",
                    f"- Experiment owner: {item['experiment_owner']}",
                    "",
                ]
            )
    else:
        lines.append("No hypothesis was generated from the supplied evidence.")
    lines.extend(["", "## Warehouse load correlation", ""])
    lines.append(
        f"Query Insights coverage: `{result['query_insights_coverage']['status']}` — {result['query_insights_coverage']['reason']}"
    )
    if result["warehouse_load_summary"]:
        lines.extend(
            [
                "",
                "| Warehouse | Intervals | Running load | Queued load | Provisioning load | Blocked load |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for item in result["warehouse_load_summary"]:
            lines.append(
                f"| {item['warehouse_name']} | {item['interval_count']} | {item['avg_running_load_sum']} | {item['avg_queued_load_sum']} | {item['avg_queued_provisioning_sum']} | {item['avg_blocked_sum']} |"
            )
    else:
        lines.append("No warehouse load rows supplied; queue cause remains unknown.")
    lines.extend(["", "## Query-hash comparison", ""])
    for item in result["query_hash_comparison"]:
        lines.append(
            f"- `{item['fingerprint']}` — {item['sample_count']} run(s), average {item['average_elapsed_time_ms']} ms, range {item['min_elapsed_time_ms']}–{item['max_elapsed_time_ms']} ms."
        )
    if not result["query_hash_comparison"]:
        lines.append("No comparable query fingerprint was supplied.")
    lines.extend(["", "## Search Optimization Service ROI", ""])
    if result["search_optimization_roi"]:
        for item in result["search_optimization_roi"]:
            lines.append(
                f"- Credits used: {item['credits_used']}; latency reduction: {item.get('latency_reduction_ms', 'unknown')} ms; bytes reduction: {item.get('bytes_scanned_reduction', 'unknown')}; {item['decision']}."
            )
    else:
        lines.append("No Search Optimization Service ROI evidence supplied; benefit and maintenance cost are unknown.")
    experiment = result["one_variable_experiment"]
    lines.extend(
        [
            "## One-variable experiment boundary",
            "",
            f"- Status: {experiment['status']}",
            f"- Owner: {experiment['owner']}",
            f"- Fixed inputs: {experiment['fixed_inputs']}",
            f"- Approval: {experiment['approval']}",
            f"- Rollback: {experiment['rollback']}",
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend(f"- {warning}" for warning in result["warnings"])
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {item}" for item in result["non_claims"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument(
        "--trusted-input-sha256",
        help="Out-of-band sha256:<hex> recorded from this canonical bundle at a trusted local boundary",
    )
    parser.add_argument(
        "--print-input-sha256",
        action="store_true",
        help="Print the canonical digest for separate trusted-boundary recording, then exit; this alone creates no trust",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise EvidenceError("input root must be an object")
        reject_secret_fields(data)
        if args.print_input_sha256:
            sys.stdout.write(input_sha256(data) + "\n")
            return 0
        result = analyze(data, trusted_input_sha256=args.trusted_input_sha256)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"evidence error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    if args.markdown_out:
        args.markdown_out.write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
