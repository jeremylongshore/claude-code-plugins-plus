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
from datetime import datetime, timedelta, timezone
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
    "auth": ("auth.sql", ["SNOWFLAKE.ACCOUNT_USAGE.USERS"]),
    "auth-login-history": (
        "auth-login-history.sql",
        ["SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY"],
    ),
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
        ["SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS"],
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
    "replication": ("replication.sql", ["INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_HISTORY_ALL"]),
    "replication-progress": (
        "replication-progress.sql",
        ["INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL"],
    ),
}
SUBSURFACES = {
    "access-database-role-current": (
        "access-database-role-current.sql",
        ["SHOW GRANTS TO DATABASE ROLE"],
        "database_role",
    ),
    "access-future-database": (
        "access-future-database.sql",
        ["SHOW FUTURE GRANTS IN DATABASE"],
        "database",
    ),
    "access-future-schema": (
        "access-future-schema.sql",
        ["SHOW FUTURE GRANTS IN SCHEMA"],
        "schema",
    ),
    "access-role-current": ("access-role-current.sql", ["SHOW GRANTS TO ROLE"], "role"),
    "access-role-parents": ("access-role-parents.sql", ["SHOW GRANTS OF ROLE"], "role"),
    "access-session": ("access-session.sql", ["Snowflake current-session context functions"], None),
    "access-user-current": ("access-user-current.sql", ["SHOW GRANTS TO USER"], "user"),
    "auth-current": ("auth-current.sql", ["SHOW USERS"], None),
    "cost-adaptive": ("cost-adaptive.sql", ["SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY"], None),
    "cost-ai-functions": ("cost-ai-functions.sql", ["SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY"], None),
    "cost-budgets": ("cost-budgets.sql", ["SHOW SNOWFLAKE.CORE.BUDGET"], None),
    "cost-internal-transfer": (
        "cost-internal-transfer.sql",
        ["SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY"],
        None,
    ),
    "cost-resource-monitors": ("cost-resource-monitors.sql", ["SHOW RESOURCE MONITORS"], None),
    "cost-storage": ("cost-storage.sql", ["SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE"], None),
    "cost-transfer": ("cost-transfer.sql", ["SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY"], None),
    "data-quality-associations-current": (
        "data-quality-associations-current.sql",
        ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES"],
        "data_quality_object",
    ),
    "data-quality-expectations-current": (
        "data-quality-expectations-current.sql",
        ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_EXPECTATIONS"],
        "data_quality_object",
    ),
    "data-quality-notification-current": (
        "data-quality-notification-current.sql",
        ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES"],
        "data_quality_object",
    ),
    "governance-classification-current": (
        "governance-classification-current.sql",
        ["SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST"],
        "governance_database",
    ),
    "governance-policies-current": (
        "governance-policies-current.sql",
        ["INFORMATION_SCHEMA.POLICY_REFERENCES"],
        "governance_object",
    ),
    "governance-tags-current": (
        "governance-tags-current.sql",
        ["INFORMATION_SCHEMA.TAG_REFERENCES", "INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS"],
        "governance_object",
    ),
    "pipeline-dynamic-table-current": (
        "pipeline-dynamic-table-current.sql",
        ["SHOW DYNAMIC TABLES IN ACCOUNT"],
        None,
    ),
    "pipeline-pipe-current": ("pipeline-pipe-current.sql", ["SHOW PIPES IN ACCOUNT"], None),
    "pipeline-pipe-status": (
        "pipeline-pipe-status.sql",
        ["SYSTEM$PIPE_STATUS"],
        "pipe",
    ),
    "pipeline-stream-current": ("pipeline-stream-current.sql", ["SHOW STREAMS IN ACCOUNT"], None),
    "pipeline-task-current": ("pipeline-task-current.sql", ["SHOW TASKS IN ACCOUNT"], None),
    "replication-current": ("replication-current.sql", ["SHOW FAILOVER GROUPS"], None),
    "replication-dangling": (
        "replication-dangling.sql",
        ["INFORMATION_SCHEMA.REPLICATION_GROUP_DANGLING_REFERENCES"],
        "replication_group",
    ),
    "native-app-versions-current": (
        "native-app-versions-current.sql",
        ["SHOW VERSIONS IN APPLICATION PACKAGE"],
        "application_package",
    ),
    "native-app-release-directives-current": (
        "native-app-release-directives-current.sql",
        ["SHOW RELEASE DIRECTIVES IN APPLICATION PACKAGE"],
        "application_package",
    ),
    "native-app-upgrade-cohorts-current": (
        "native-app-upgrade-cohorts-current.sql",
        ["SNOWFLAKE.DATA_SHARING_USAGE.APPLICATION_STATE"],
        "application_package",
    ),
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
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}$")
QUALIFIED_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}$")
THREE_PART_IDENTIFIER_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}$"
)
SELECTOR_MARKERS = {
    "database": "__DATABASE_IDENTIFIER__",
    "database_role": "__DATABASE_ROLE_IDENTIFIER__",
    "role": "__ROLE_IDENTIFIER__",
    "schema": "__SCHEMA_IDENTIFIER__",
    "user": "__USER_IDENTIFIER__",
    "pipe": "__PIPE_IDENTIFIER__",
    "data_quality_object": "__DATA_QUALITY_OBJECT_IDENTIFIER__",
    "data_quality_domain": "__DATA_QUALITY_DOMAIN__",
    "governance_database": "__GOVERNANCE_DATABASE_IDENTIFIER__",
    "governance_object": "__GOVERNANCE_OBJECT_IDENTIFIER__",
    "governance_domain": "__GOVERNANCE_DOMAIN__",
    "replication_group": "__REPLICATION_GROUP_IDENTIFIER__",
    "application_package": "__APPLICATION_PACKAGE_IDENTIFIER__",
}
WINDOW_SELECTOR_MARKERS = {
    "window_start": "__WINDOW_START_UTC__",
    "window_end": "__WINDOW_END_UTC__",
}
DATA_QUALITY_DATABASE_MARKER = "__DATA_QUALITY_DATABASE_IDENTIFIER__"
DATA_QUALITY_SELECTOR_SURFACES = frozenset(
    {
        "data-quality-associations-current",
        "data-quality-expectations-current",
        "data-quality-notification-current",
    }
)
NATIVE_APP_SELECTOR_SURFACES = frozenset(
    {
        "native-app-versions-current",
        "native-app-release-directives-current",
        "native-app-upgrade-cohorts-current",
    }
)
GOVERNANCE_DATABASE_MARKER = "__GOVERNANCE_OBJECT_DATABASE_IDENTIFIER__"
GOVERNANCE_OBJECT_SELECTOR_SURFACES = frozenset({"governance-policies-current", "governance-tags-current"})
GOVERNANCE_DATABASE_SELECTOR_SURFACES = frozenset({"governance-classification-current"})
COST_WINDOW_SURFACES = {
    "cost",
    "cost-adaptive",
    "cost-ai-functions",
    "cost-internal-transfer",
    "cost-storage",
    "cost-transfer",
}
PIPELINE_WINDOW_SURFACES = {"pipeline"}
DATA_QUALITY_WINDOW_SURFACES = {"data-quality"}
REPLICATION_WINDOW_SURFACES = {"replication", "replication-progress"}
WINDOW_SURFACES = (
    COST_WINDOW_SURFACES | PIPELINE_WINDOW_SURFACES | DATA_QUALITY_WINDOW_SURFACES | REPLICATION_WINDOW_SURFACES
)
INTRINSIC_ROW_LIMITS = {
    "cost-resource-monitors": 10000,
    "pipeline-dynamic-table-current": 10000,
    "pipeline-pipe-current": 10000,
    "pipeline-pipe-status": 1,
    "pipeline-stream-current": 10000,
    "pipeline-task-current": 10000,
    "governance-classification-current": 5000,
    "governance-policies-current": 5000,
    "governance-tags-current": 5000,
}
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
RECEIPT_EXPECTED_DATASETS = {
    "access": ("grants_to_roles", "grants_to_users", "roles"),
    "access-database-role-current": ("execution_context", "rows"),
    "access-future-database": ("execution_context", "rows"),
    "access-future-schema": ("execution_context", "rows"),
    "access-role-current": ("execution_context", "rows"),
    "access-role-parents": ("execution_context", "rows"),
    "access-session": ("session_context",),
    "access-user-current": ("execution_context", "rows"),
    "auth": ("execution_context", "historical_users"),
    "auth-current": ("current_users", "execution_context"),
    "auth-login-history": ("execution_context", "login_history"),
    "cost": (
        "execution_context",
        "warehouse_metering",
        "query_attribution",
        "warehouse_load",
        "serverless_usage",
    ),
    "cost-adaptive": ("adaptive_usage", "execution_context"),
    "cost-ai-functions": ("ai_usage", "execution_context"),
    "cost-budgets": ("budgets", "execution_context"),
    "cost-internal-transfer": ("execution_context", "internal_transfer_usage"),
    "cost-resource-monitors": ("execution_context", "resource_monitors"),
    "cost-storage": ("execution_context", "storage_usage"),
    "cost-transfer": ("data_transfer_usage", "execution_context"),
    "data-quality": ("execution_context", "expectation_history"),
    "data-quality-associations-current": ("current_associations", "execution_context"),
    "data-quality-expectations-current": ("current_expectations", "execution_context"),
    "data-quality-notification-current": ("execution_context", "notification_associations"),
    "governance-classification-current": ("classification_latest", "execution_context"),
    "governance-policies-current": ("execution_context", "policy_references"),
    "governance-tags-current": ("execution_context", "tag_references"),
    "pipeline": ("copy_history", "dynamic_table_refresh_history", "execution_context", "task_history"),
    "pipeline-dynamic-table-current": ("current_dynamic_tables", "execution_context"),
    "pipeline-pipe-current": ("current_pipes", "execution_context"),
    "pipeline-pipe-status": ("execution_context", "pipe_status"),
    "pipeline-stream-current": ("current_streams", "execution_context"),
    "pipeline-task-current": ("current_tasks", "execution_context"),
    "replication": ("execution_context", "replication_refresh_history"),
    "replication-current": ("current_groups", "execution_context"),
    "replication-dangling": ("dangling_references", "execution_context"),
    "replication-progress": ("execution_context", "replication_progress"),
    "native-app-versions-current": ("execution_context", "versions"),
    "native-app-release-directives-current": ("execution_context", "release_directives"),
    "native-app-upgrade-cohorts-current": ("execution_context", "upgrade_cohorts"),
}
CAP_DATASET_BY_SURFACE = {
    "auth": "historical_users",
    "auth-current": "current_users",
    "auth-login-history": "login_history",
    **{surface: "rows" for surface in SUBSURFACES if surface.startswith("access-") and surface != "access-session"},
    **{
        surface: datasets[0] if datasets[0] != "execution_context" else datasets[1]
        for surface, datasets in RECEIPT_EXPECTED_DATASETS.items()
        if surface.startswith("cost-")
    },
    "pipeline-dynamic-table-current": "current_dynamic_tables",
    "pipeline-pipe-current": "current_pipes",
    "pipeline-stream-current": "current_streams",
    "pipeline-task-current": "current_tasks",
    "governance-classification-current": "classification_latest",
    "governance-policies-current": "policy_references",
    "governance-tags-current": "tag_references",
    "replication-current": "current_groups",
    "replication-dangling": "dangling_references",
    "native-app-versions-current": "versions",
    "native-app-release-directives-current": "release_directives",
    "native-app-upgrade-cohorts-current": "upgrade_cohorts",
}
CAP_DATASETS_BY_SURFACE = {
    "cost": ("warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage"),
    "data-quality": ("expectation_history",),
    "data-quality-associations-current": ("current_associations",),
    "data-quality-expectations-current": ("current_expectations",),
    "data-quality-notification-current": ("notification_associations",),
    "pipeline": ("task_history", "dynamic_table_refresh_history", "copy_history"),
    "governance-classification-current": ("classification_latest",),
    "governance-policies-current": ("policy_references",),
    "governance-tags-current": ("tag_references",),
    "replication": ("replication_refresh_history",),
    "replication-current": ("current_groups",),
    "replication-dangling": ("dangling_references",),
    "replication-progress": ("replication_progress",),
    "native-app-versions-current": ("versions",),
    "native-app-release-directives-current": ("release_directives",),
    "native-app-upgrade-cohorts-current": ("upgrade_cohorts",),
}
RECEIPT_NON_CLAIMS = (
    "No Snowflake mutation was executed by the reviewed collector SQL.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
    "The embedded receipt SHA-256 is a self-checksum, not proof of origin or authenticity.",
    "The collector does not attest to operations performed elsewhere in the surrounding session or workflow.",
)
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
    "password",
    "passphrase",
    "pii",
    "privatekey",
    "querytext",
    "rawrows",
    "refreshtoken",
    "secret",
    "secretaccesskey",
    "sessiontoken",
    "sqltext",
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
    (re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s/]+@\S+", re.IGNORECASE), "[REDACTED_CONNECTION_URL]"),
    (re.compile(r"https?://\S+[?&](?:X-Amz-|X-Goog-|sig=|signature=)\S*", re.IGNORECASE), "[REDACTED_PRESIGNED_URL]"),
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
    "RELEASE",
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
    "VERSIONS",
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


SOURCE_TIME_FIELDS = {
    "query_history": ("end_time", "start_time"),
}


class CollectionError(ValueError):
    """Raised when evidence collection would be unsafe or malformed."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_source_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CollectionError(f"{field} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise CollectionError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise CollectionError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def derive_source_max_time(datasets: dict[str, list[dict[str, Any]]], dataset: str) -> str | None:
    maximum: datetime | None = None
    for index, row in enumerate(datasets.get(dataset, [])):
        for field in SOURCE_TIME_FIELDS.get(dataset, ()):
            value = row.get(field)
            if value is None:
                continue
            parsed = parse_source_time(value, f"datasets.{dataset}[{index}].{field}")
            if maximum is None or parsed > maximum:
                maximum = parsed
    if maximum is None:
        return None
    return maximum.isoformat().replace("+00:00", "Z")


def sanitize_text(value: Any) -> str:
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
    return normalize_sensitive_key(key) in SAFE_SENSITIVE_METADATA_KEYS and (isinstance(value, bool) or value is None)


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
        return sanitize_text(value)
    return value


def sanitize_output_tree(value: Any) -> Any:
    """Sanitize every emitted scalar without allowing malformed input to escape."""
    try:
        return _sanitize_output_tree(value, 0, [MAX_SANITIZE_TREE_NODES])
    except Exception:
        return "[REDACTED_CREDENTIAL]"


def redact_selector_values(value: Any, selector: dict[str, str] | None) -> Any:
    """Remove customer identifiers from arbitrary CLI error structures."""
    if not selector:
        return value
    raw_values = sorted(set(selector.values()), key=len, reverse=True)
    if isinstance(value, dict):
        return {key: redact_selector_values(child, selector) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_selector_values(child, selector) for child in value]
    if isinstance(value, str):
        for raw in raw_values:
            value = re.sub(re.escape(raw), "[REDACTED_SELECTOR]", value, flags=re.IGNORECASE)
        return value
    return value


def reject_secret_fields(value: Any, path: str = "result", depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [MAX_SANITIZE_TREE_NODES]
    if depth >= MAX_SANITIZE_TREE_DEPTH or budget[0] <= 0:
        raise CollectionError(f"input nesting exceeds the supported limit: {path}")
    budget[0] -= 1
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = normalize_sensitive_key(key)
            # Boolean/null posture metadata such as HAS_PASSWORD is safe; password material is not.
            if normalized in {"querytag", "username"}:
                raise CollectionError(
                    f"raw identity/tag field is not accepted: {path}.{key}; use a Snowflake-side hash"
                )
            if is_safe_sensitive_metadata(key, child):
                continue
            if is_sensitive_key(key):
                raise CollectionError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_secret_fields(child, f"{path}.{key}", depth + 1, budget)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_fields(child, f"{path}[{index}]", depth + 1, budget)
    elif isinstance(value, str):
        if len(value) > MAX_SQL_SCAN_CHARS:
            raise CollectionError(f"input string exceeds the supported limit: {path}")
        if (
            redact_authorization_values(value) != value
            or any(pattern.search(value) for pattern, _ in STATIC_REDACTIONS)
            or looks_like_raw_sql(value)
        ):
            raise CollectionError(f"credential-like or raw-SQL-like value is not accepted: {path}")


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
    system_functions = set(re.findall(r"\bSYSTEM\s*\$\s*([A-Z][A-Z0-9_]*)", cleaned.upper()))
    unsupported_system_functions = sorted(system_functions - {"PIPE_STATUS"})
    if unsupported_system_functions:
        raise CollectionError("SQL contains an unreviewed SYSTEM$ function: " + ", ".join(unsupported_system_functions))
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
    database: str | None = None,
    database_role: str | None = None,
    role: str | None = None,
    schema: str | None = None,
    user: str | None = None,
    pipe: str | None = None,
    data_quality_object: str | None = None,
    data_quality_domain: str | None = None,
    governance_database: str | None = None,
    governance_object: str | None = None,
    governance_domain: str | None = None,
    replication_group: str | None = None,
    application_package: str | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
) -> tuple[Path, str, str, list[str], dict[str, str]]:
    """Render a reviewed SQL template with a strictly validated selector."""

    path, template_sql, sources = load_surface(surface)
    _, _, selector_name = _surface_spec(surface)
    supplied = {
        name: value
        for name, value in {
            "database": database,
            "database_role": database_role,
            "role": role,
            "schema": schema,
            "user": user,
            "pipe": pipe,
            "data_quality_object": data_quality_object,
            "data_quality_domain": data_quality_domain,
            "governance_database": governance_database,
            "governance_object": governance_object,
            "governance_domain": governance_domain,
            "replication_group": replication_group,
            "application_package": application_package,
        }.items()
        if value is not None
    }
    selector: dict[str, str] = {}
    if selector_name == "data_quality_object":
        if set(supplied) != {"data_quality_object", "data_quality_domain"}:
            raise CollectionError(
                f"surface {surface} requires only the data_quality_object and data_quality_domain selectors"
            )
        if not THREE_PART_IDENTIFIER_RE.fullmatch(supplied["data_quality_object"]):
            raise CollectionError(
                "data_quality_object must be one validated three-part unquoted Snowflake identifier, not SQL or a fragment"
            )
        if supplied["data_quality_domain"] not in {"TABLE", "VIEW"}:
            raise CollectionError("data_quality_domain must be TABLE or VIEW")
        selector.update(
            {
                "data_quality_object": supplied["data_quality_object"].upper(),
                "data_quality_domain": supplied["data_quality_domain"],
            }
        )
    elif selector_name == "governance_object":
        if set(supplied) != {"governance_object", "governance_domain"}:
            raise CollectionError(
                f"surface {surface} requires only the governance_object and governance_domain selectors"
            )
        if not THREE_PART_IDENTIFIER_RE.fullmatch(supplied["governance_object"]):
            raise CollectionError(
                "governance_object must be one validated three-part unquoted Snowflake identifier, not SQL or a fragment"
            )
        if supplied["governance_domain"] not in {"TABLE", "VIEW"}:
            raise CollectionError("governance_domain must be TABLE or VIEW")
        selector.update(
            {
                "governance_object": supplied["governance_object"].upper(),
                "governance_domain": supplied["governance_domain"],
            }
        )
    elif selector_name is None:
        if supplied:
            raise CollectionError(f"surface {surface} does not accept a selector")
    else:
        if set(supplied) != {selector_name}:
            raise CollectionError(f"surface {surface} requires only the {selector_name} selector")
        value = supplied[selector_name]
        if selector_name == "pipe":
            pattern = THREE_PART_IDENTIFIER_RE
        elif selector_name in {"database_role", "schema"}:
            pattern = QUALIFIED_IDENTIFIER_RE
        else:
            pattern = IDENTIFIER_RE
        if not pattern.fullmatch(value):
            qualification = (
                "three-part"
                if pattern is THREE_PART_IDENTIFIER_RE
                else "two-part"
                if pattern is QUALIFIED_IDENTIFIER_RE
                else "one-part"
            )
            raise CollectionError(
                f"{selector_name} must be one validated {qualification} unquoted Snowflake identifier, not SQL or a fragment"
            )
        selector[selector_name] = (
            value.upper()
            if selector_name in {"governance_database", "replication_group", "application_package"}
            else value
        )

    if surface in WINDOW_SURFACES:
        if window_start is None or window_end is None:
            raise CollectionError(f"surface {surface} requires both window_start and window_end")
        for name, value in (("window_start", window_start), ("window_end", window_end)):
            if not UTC_TIMESTAMP_RE.fullmatch(value):
                raise CollectionError(f"{name} must be a canonical ISO-8601 UTC timestamp ending in Z")
            try:
                parsed = datetime.fromisoformat(value[:-1] + "+00:00")
            except ValueError as exc:
                raise CollectionError(f"{name} must be a valid ISO-8601 UTC timestamp") from exc
            selector[name] = value
            selector[f"_{name}_parsed"] = parsed.isoformat()
        start_parsed = datetime.fromisoformat(selector.pop("_window_start_parsed"))
        end_parsed = datetime.fromisoformat(selector.pop("_window_end_parsed"))
        if start_parsed >= end_parsed:
            raise CollectionError("window_start must be before window_end")
        if end_parsed - start_parsed > timedelta(days=7):
            domain = (
                "pipeline"
                if surface in PIPELINE_WINDOW_SURFACES
                else "data-quality"
                if surface in DATA_QUALITY_WINDOW_SURFACES
                else "replication"
                if surface in REPLICATION_WINDOW_SURFACES
                else "cost"
            )
            raise CollectionError(f"{domain} collection windows cannot exceed seven days; partition longer audits")
    elif window_start is not None or window_end is not None:
        raise CollectionError(f"surface {surface} does not accept a time window")

    rendered_sql = template_sql
    if DATA_QUALITY_DATABASE_MARKER in rendered_sql:
        selected_object = selector.get("data_quality_object")
        if selected_object is None:
            raise CollectionError(f"surface {surface} requires selector: data_quality_object")
        rendered_sql = rendered_sql.replace(DATA_QUALITY_DATABASE_MARKER, selected_object.split(".", 1)[0])
    if GOVERNANCE_DATABASE_MARKER in rendered_sql:
        selected_object = selector.get("governance_object")
        if selected_object is None:
            raise CollectionError(f"surface {surface} requires selector: governance_object")
        rendered_sql = rendered_sql.replace(GOVERNANCE_DATABASE_MARKER, selected_object.split(".", 1)[0])
    for name, marker in SELECTOR_MARKERS.items():
        if name in selector:
            rendered_sql = rendered_sql.replace(marker, selector[name])
        elif marker in rendered_sql:
            raise CollectionError(f"surface {surface} requires selector: {name}")
    for name, marker in WINDOW_SELECTOR_MARKERS.items():
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
    source_max_age_seconds: int | None = None,
    error: dict[str, Any] | None = None,
    template_sql: str | None = None,
    template_path: Path | None = None,
    selector: dict[str, str] | None = None,
    collection_mode: str = "offline-normalized",
    collection_started_at: str | None = None,
    collection_completed_at: str | None = None,
) -> dict[str, Any]:
    # A live collection's observation timestamp is the instant collection
    # completed.  Derive it from the supplied completion time before sampling a
    # new clock value so collector-produced receipts cannot claim that they were
    # collected after their own collection interval.
    effective_collected_at = collected_at or collection_completed_at or utc_now()
    effective_started_at = collection_started_at or effective_collected_at
    effective_completed_at = collection_completed_at or effective_collected_at
    datasets: dict[str, list[dict[str, Any]]] = {}
    row_count = 0
    if raw is not None:
        datasets, row_count = normalize_cli_json(raw)
    expected_datasets = list(RECEIPT_EXPECTED_DATASETS.get(surface, ()))
    for dataset in expected_datasets:
        datasets.setdefault(dataset, [])
    datasets = dict(sorted(datasets.items()))
    limits = re.findall(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
    row_limit = int(limits[-1]) if limits else INTRINSIC_ROW_LIMITS.get(surface)
    cap_dataset = CAP_DATASET_BY_SURFACE.get(surface)
    capped_row_count = len(datasets.get(cap_dataset, [])) if cap_dataset else row_count
    cap_datasets = CAP_DATASETS_BY_SURFACE.get(surface)
    if cap_datasets:
        truncation_possible = row_limit is not None and any(
            len(datasets.get(dataset, [])) >= row_limit for dataset in cap_datasets
        )
    else:
        truncation_possible = row_limit is not None and capped_row_count >= row_limit
    if surface == "pipeline-pipe-status":
        # SYSTEM$PIPE_STATUS is invoked for exactly one validated named pipe;
        # its one status row plus the context row are not a pageable result.
        truncation_possible = False
    if surface == "query" and (
        not isinstance(source_max_age_seconds, int)
        or isinstance(source_max_age_seconds, bool)
        or source_max_age_seconds <= 0
    ):
        raise CollectionError("query collection requires a positive source_max_age_seconds")
    sanitized_error = sanitize_output_tree(redact_selector_values(error, selector)) if error else None
    canonical_template = template_sql if template_sql is not None else sql
    template_hash = f"sha256:{hashlib.sha256(canonical_template.encode('utf-8')).hexdigest()}"
    selector_binding: dict[str, str] | None = None
    if surface == "pipeline-pipe-status":
        status_rows = datasets.get("pipe_status", [])
        object_key = status_rows[0].get("object_key_sha256") if len(status_rows) == 1 else None
        if isinstance(object_key, str):
            selector_binding = {"pipe_object_key_sha256": object_key}
    if surface in DATA_QUALITY_SELECTOR_SURFACES and not error:
        if len(context_rows := datasets.get("execution_context", [])) == 1:
            object_key = context_rows[0].get("selected_object_key_sha256")
            object_domain = context_rows[0].get("selected_object_domain")
            if (
                isinstance(object_key, str)
                and re.fullmatch(r"[0-9a-f]{64}", object_key)
                and object_domain in {"TABLE", "VIEW"}
            ):
                selector_binding = {
                    "selected_object_key_sha256": object_key,
                    "selected_object_domain": object_domain,
                }
    if surface in GOVERNANCE_OBJECT_SELECTOR_SURFACES and not error:
        if len(context_rows := datasets.get("execution_context", [])) == 1:
            object_key = context_rows[0].get("selected_object_key_sha256")
            object_domain = context_rows[0].get("selected_object_domain")
            if (
                isinstance(object_key, str)
                and re.fullmatch(r"[0-9a-f]{64}", object_key)
                and object_domain in {"TABLE", "VIEW"}
            ):
                selector_binding = {
                    "selected_object_key_sha256": object_key,
                    "selected_object_domain": object_domain,
                }
    if surface in GOVERNANCE_DATABASE_SELECTOR_SURFACES and not error:
        if len(context_rows := datasets.get("execution_context", [])) == 1:
            database_key = context_rows[0].get("selected_database_key_sha256")
            if isinstance(database_key, str) and re.fullmatch(r"[0-9a-f]{64}", database_key):
                selector_binding = {"selected_database_key_sha256": database_key}
    if surface == "replication-dangling" and not error:
        dangling_context = datasets.get("execution_context", [])
        if len(dangling_context) == 1:
            group_key = dangling_context[0].get("selected_group_key_sha256")
            if isinstance(group_key, str) and re.fullmatch(r"[0-9a-f]{64}", group_key):
                selector_binding = {"selected_group_key_sha256": group_key}
    if surface in NATIVE_APP_SELECTOR_SURFACES and not error:
        native_context = datasets.get("execution_context", [])
        if len(native_context) == 1:
            package_key = native_context[0].get("selected_package_key_sha256")
            if isinstance(package_key, str) and re.fullmatch(r"[0-9a-f]{64}", package_key):
                selector_binding = {"selected_package_key_sha256": package_key}
    receipt_rendered_sql = sql
    fingerprint_value: dict[str, str] | None = selector_binding or selector
    if surface == "pipeline-pipe-status":
        if selector_binding is not None:
            receipt_rendered_sql = canonical_template.replace(
                "__PIPE_IDENTIFIER__",
                f"__PIPE_OBJECT_KEY_SHA256_{selector_binding['pipe_object_key_sha256']}__",
            )
            fingerprint_value = selector_binding
        else:
            # An error response has no Snowflake-produced scoped object hash.
            # Hashing either the rendered SQL or the raw selector would make a
            # private pipe name dictionary-testable, so retain only the public
            # reviewed template proof and no selector fingerprint.
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    if surface in DATA_QUALITY_SELECTOR_SURFACES:
        if selector_binding is not None:
            receipt_rendered_sql = (
                canonical_template.replace(
                    "__DATA_QUALITY_OBJECT_IDENTIFIER__",
                    f"__DATA_QUALITY_OBJECT_KEY_SHA256_{selector_binding['selected_object_key_sha256']}__",
                )
                .replace(
                    "__DATA_QUALITY_DOMAIN__",
                    f"__DATA_QUALITY_DOMAIN_{selector_binding['selected_object_domain']}__",
                )
                .replace(
                    DATA_QUALITY_DATABASE_MARKER,
                    f"__DATA_QUALITY_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{selector_binding['selected_object_key_sha256']}__",
                )
            )
            fingerprint_value = selector_binding
        else:
            # Without Snowflake-produced execution context, retain only public
            # template proof so the raw object selector is not dictionary-testable.
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    if surface in GOVERNANCE_OBJECT_SELECTOR_SURFACES:
        if selector_binding is not None:
            selected = selector_binding["selected_object_key_sha256"]
            domain = selector_binding["selected_object_domain"]
            receipt_rendered_sql = (
                canonical_template.replace(
                    "__GOVERNANCE_OBJECT_IDENTIFIER__",
                    f"__GOVERNANCE_OBJECT_KEY_SHA256_{selected}__",
                )
                .replace("__GOVERNANCE_DOMAIN__", f"__GOVERNANCE_DOMAIN_{domain}__")
                .replace(
                    GOVERNANCE_DATABASE_MARKER,
                    f"__GOVERNANCE_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{selected}__",
                )
            )
            fingerprint_value = selector_binding
        else:
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    if surface in GOVERNANCE_DATABASE_SELECTOR_SURFACES:
        if selector_binding is not None:
            selected = selector_binding["selected_database_key_sha256"]
            receipt_rendered_sql = canonical_template.replace(
                "__GOVERNANCE_DATABASE_IDENTIFIER__",
                f"__GOVERNANCE_DATABASE_KEY_SHA256_{selected}__",
            )
            fingerprint_value = selector_binding
        else:
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    if surface == "replication-dangling":
        if selector_binding is not None:
            receipt_rendered_sql = canonical_template.replace(
                "__REPLICATION_GROUP_IDENTIFIER__",
                f"__REPLICATION_GROUP_KEY_SHA256_{selector_binding['selected_group_key_sha256']}__",
            )
            fingerprint_value = selector_binding
        else:
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    if surface in NATIVE_APP_SELECTOR_SURFACES:
        if selector_binding is not None:
            receipt_rendered_sql = canonical_template.replace(
                "__APPLICATION_PACKAGE_IDENTIFIER__",
                f"__APPLICATION_PACKAGE_KEY_SHA256_{selector_binding['selected_package_key_sha256']}__",
            )
            fingerprint_value = selector_binding
        else:
            # An error response cannot bind a private package selector to a
            # Snowflake-produced scoped hash. Keep public template proof only.
            receipt_rendered_sql = canonical_template
            fingerprint_value = None
    rendered_hash = f"sha256:{hashlib.sha256(receipt_rendered_sql.encode('utf-8')).hexdigest()}"
    selector_fingerprint = (
        f"sha256:{hashlib.sha256(canonical_json(fingerprint_value)).hexdigest()}" if fingerprint_value else None
    )
    context_rows = datasets.get("execution_context", [])
    account_scope = (
        context_rows[0].get("account_identifier_sha256")
        if len(context_rows) == 1 and isinstance(context_rows[0], dict)
        else None
    )
    receipt = {
        "schema_version": "2"
        if surface == "query"
        or surface.startswith(
            ("access", "auth", "cost", "data-quality", "governance", "pipeline", "replication", "native-app")
        )
        else "1",
        "surface": surface,
        "status": "error" if error else "collected",
        "collected_at": effective_collected_at,
        "sql_sha256": template_hash,
        "template_sha256": template_hash,
        "rendered_sql_sha256": rendered_hash,
        "selector_fingerprint": selector_fingerprint,
        "source_metadata": {
            "template": template_path.name if template_path is not None else None,
            "source_views": list(sources),
            "selector": {name: True for name in (selector or {})},
        },
        "source_views": sources,
        "row_count": row_count,
        "row_limit": row_limit,
        "truncation_possible": truncation_possible,
        "dataset_row_counts": {name: len(rows) for name, rows in datasets.items()},
        "expected_datasets": expected_datasets,
        "datasets": datasets,
        "errors": [sanitized_error] if sanitized_error else [],
        "non_claims": list(RECEIPT_NON_CLAIMS),
    }
    if surface == "pipeline" and selector:
        receipt["source_metadata"]["selector_values"] = dict(selector)
    if surface == "data-quality" and selector:
        receipt["source_metadata"]["selector_values"] = dict(selector)
    if surface in REPLICATION_WINDOW_SURFACES and selector:
        receipt["source_metadata"]["selector_values"] = dict(selector)
    if surface == "pipeline-pipe-status" and selector_binding:
        receipt["source_metadata"]["selector_binding"] = selector_binding
        receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
    if surface in DATA_QUALITY_SELECTOR_SURFACES and selector_binding:
        receipt["source_metadata"]["selector_binding"] = selector_binding
        receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
    if surface in GOVERNANCE_OBJECT_SELECTOR_SURFACES | GOVERNANCE_DATABASE_SELECTOR_SURFACES and selector_binding:
        receipt["source_metadata"]["selector_binding"] = selector_binding
        receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
    if surface == "replication-dangling" and selector_binding:
        receipt["source_metadata"]["selector_binding"] = selector_binding
        receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
    if surface in NATIVE_APP_SELECTOR_SURFACES and selector_binding:
        receipt["source_metadata"]["selector_binding"] = selector_binding
        receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
    if surface.startswith(("cost", "data-quality", "governance", "pipeline", "replication", "native-app")):
        receipt["cap_scope"] = "per_dataset" if cap_datasets else "single_dataset_or_result"
        receipt["result_sha256"] = f"sha256:{hashlib.sha256(canonical_json(datasets)).hexdigest()}"
        receipt["connection_profile_sha256"] = (
            f"sha256:{hashlib.sha256(canonical_json([account_scope, connection])).hexdigest()}"
        )
        receipt["snowflake_query_id"] = None
        receipt["snowflake_query_id_status"] = "not_exposed_by_snow_cli_json_ext"
    else:
        receipt["connection_profile"] = connection
    if surface.startswith(
        ("access", "auth", "cost", "data-quality", "governance", "pipeline", "replication", "native-app")
    ):
        receipt["collection_mode"] = collection_mode
        receipt["collection_started_at"] = effective_started_at
        receipt["collection_completed_at"] = effective_completed_at
    if surface == "query":
        receipt["freshness"] = {
            "dataset": "query_history",
            "dataset_max_time": derive_source_max_time(datasets, "query_history"),
            "source_max_age_seconds": source_max_age_seconds,
            "semantics": "dataset observation only; the analyzer derives freshness from the anchor query row",
        }
    receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(canonical_json(receipt)).hexdigest()}"
    return receipt


def execute_surface(
    surface: str,
    connection: str,
    *,
    source_max_age_seconds: int | None = None,
    database: str | None = None,
    database_role: str | None = None,
    role: str | None = None,
    schema: str | None = None,
    user: str | None = None,
    pipe: str | None = None,
    data_quality_object: str | None = None,
    data_quality_domain: str | None = None,
    governance_database: str | None = None,
    governance_object: str | None = None,
    governance_domain: str | None = None,
    replication_group: str | None = None,
    application_package: str | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[dict[str, Any], int]:
    if not PROFILE_RE.fullmatch(connection):
        raise CollectionError("connection profile must use only letters, digits, dot, underscore, or hyphen")
    path, template_sql, sql, sources, selector = render_surface(
        surface,
        database=database,
        database_role=database_role,
        role=role,
        schema=schema,
        user=user,
        pipe=pipe,
        data_quality_object=data_quality_object,
        data_quality_domain=data_quality_domain,
        governance_database=governance_database,
        governance_object=governance_object,
        governance_domain=governance_domain,
        replication_group=replication_group,
        application_package=application_package,
        window_start=window_start,
        window_end=window_end,
    )
    temporary_path: Path | None = None
    collection_started_at = utc_now()
    try:
        command_path = path
        if sql != template_sql:
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
                    surface,
                    connection,
                    sql,
                    sources,
                    source_max_age_seconds=source_max_age_seconds,
                    error=error,
                    template_sql=template_sql,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                    collection_started_at=collection_started_at,
                    collection_completed_at=utc_now(),
                ),
                2,
            )
        except subprocess.TimeoutExpired:
            error = {"code": "SNOW_CLI_TIMEOUT", "message": "Snowflake CLI collection exceeded 120 seconds"}
            return (
                build_receipt(
                    surface,
                    connection,
                    sql,
                    sources,
                    source_max_age_seconds=source_max_age_seconds,
                    error=error,
                    template_sql=template_sql,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                    collection_started_at=collection_started_at,
                    collection_completed_at=utc_now(),
                ),
                5,
            )
        if completed.returncode != 0:
            error = {
                "code": "SNOW_CLI_FAILED",
                "exit_code": completed.returncode,
                "message": "Snowflake CLI collection failed; inspect local CLI diagnostics outside the receipt",
            }
            return (
                build_receipt(
                    surface,
                    connection,
                    sql,
                    sources,
                    source_max_age_seconds=source_max_age_seconds,
                    error=error,
                    template_sql=template_sql,
                    template_path=path,
                    selector=selector,
                    collection_mode="live-cli",
                    collection_started_at=collection_started_at,
                    collection_completed_at=utc_now(),
                ),
                completed.returncode,
            )
        try:
            raw = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise CollectionError("Snowflake CLI did not return valid JSON_EXT output") from exc
        return (
            build_receipt(
                surface,
                connection,
                sql,
                sources,
                raw=raw,
                source_max_age_seconds=source_max_age_seconds,
                template_sql=template_sql,
                template_path=path,
                selector=selector,
                collection_mode="live-cli",
                collection_started_at=collection_started_at,
                collection_completed_at=utc_now(),
            ),
            0,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


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
        surface for surface in {**SURFACES, **SUBSURFACES} if (SQL_DIR / _surface_spec(surface)[0]).is_file()
    )
    parser.add_argument("--surface", choices=bundled_surfaces, required=True)
    parser.add_argument("--connection", help="Existing Snowflake CLI profile name")
    parser.add_argument("--output", type=Path, help="JSON receipt path; stdout when omitted")
    parser.add_argument("--input-json", type=Path, help="Normalize saved Snowflake CLI JSON_EXT instead of connecting")
    parser.add_argument(
        "--source-max-age-seconds",
        type=int,
        help="Positive incident freshness bound; required for the query surface",
    )
    parser.add_argument(
        "--database",
        help="One unquoted database identifier for access-future-database",
    )
    parser.add_argument(
        "--database-role",
        help="Two-part unquoted database-role identifier for access-database-role-current",
    )
    parser.add_argument("--role", help="One unquoted account-role identifier for role sub-surfaces")
    parser.add_argument("--schema", help="Two-part unquoted schema identifier for access-future-schema")
    parser.add_argument("--user", help="One unquoted user identifier for access-user-current")
    parser.add_argument("--pipe", help="Three-part unquoted pipe identifier for pipeline-pipe-status")
    parser.add_argument(
        "--data-quality-object",
        help="Three-part unquoted object identifier for selector-scoped data-quality current surfaces",
    )
    parser.add_argument(
        "--data-quality-domain",
        choices=("TABLE", "VIEW"),
        help="Object domain for selector-scoped data-quality current surfaces",
    )
    parser.add_argument(
        "--governance-database",
        help="One unquoted database identifier for governance classification evidence",
    )
    parser.add_argument(
        "--governance-object",
        help="Three-part unquoted object identifier for selector-scoped governance current surfaces",
    )
    parser.add_argument(
        "--governance-domain",
        choices=("TABLE", "VIEW"),
        help="Object domain for selector-scoped governance current surfaces",
    )
    parser.add_argument(
        "--replication-group",
        help="One unquoted local replication/failover-group identifier for selector-scoped evidence",
    )
    parser.add_argument(
        "--application-package",
        help="One unquoted application-package identifier for Native App provider evidence",
    )
    parser.add_argument("--window-start", help="Canonical UTC lower bound for bounded history surfaces")
    parser.add_argument("--window-end", help="Canonical UTC exclusive upper bound for bounded history surfaces")
    parser.add_argument("--validate-only", action="store_true", help="Validate the reviewed SQL and exit")
    args = parser.parse_args(argv)
    try:
        path, template_sql, sql, sources, selector = render_surface(
            args.surface,
            database=args.database,
            database_role=args.database_role,
            role=args.role,
            schema=args.schema,
            user=args.user,
            pipe=args.pipe,
            data_quality_object=args.data_quality_object,
            data_quality_domain=args.data_quality_domain,
            governance_database=args.governance_database,
            governance_object=args.governance_object,
            governance_domain=args.governance_domain,
            replication_group=args.replication_group,
            application_package=args.application_package,
            window_start=args.window_start,
            window_end=args.window_end,
        )
        if args.validate_only:
            return 0
        if args.surface == "query" and (args.source_max_age_seconds is None or args.source_max_age_seconds <= 0):
            raise CollectionError("--source-max-age-seconds must be positive for the query surface")
        if args.input_json:
            if args.surface.startswith(
                ("access", "auth", "cost", "data-quality", "governance", "pipeline", "replication", "native-app")
            ):
                raise CollectionError(
                    "offline normalization is diagnostic-only and is not accepted for governed evidence; collect live so Snowflake execution context is bound to the result"
                )
            raw = json.loads(args.input_json.read_text(encoding="utf-8"))
            receipt = build_receipt(
                args.surface,
                "offline-input",
                sql,
                sources,
                raw=raw,
                source_max_age_seconds=args.source_max_age_seconds,
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
                source_max_age_seconds=args.source_max_age_seconds,
                database=args.database,
                database_role=args.database_role,
                role=args.role,
                schema=args.schema,
                user=args.user,
                pipe=args.pipe,
                data_quality_object=args.data_quality_object,
                data_quality_domain=args.data_quality_domain,
                governance_database=args.governance_database,
                governance_object=args.governance_object,
                governance_domain=args.governance_domain,
                replication_group=args.replication_group,
                application_package=args.application_package,
                window_start=args.window_start,
                window_end=args.window_end,
            )
        write_receipt(receipt, args.output)
        return code
    except (CollectionError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {sanitize_text(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
