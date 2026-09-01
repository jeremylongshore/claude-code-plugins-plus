#!/usr/bin/env python3
"""Collect one bounded, privacy-safe Snowflake governance evidence surface."""

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
from typing import Any


HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}$")
OBJECT_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}(?:\.[A-Za-z_][A-Za-z0-9_$]{0,254}){1,2}$")
PROFILE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
OPAQUE = re.compile(r"^(?:asset|policy|tag)_[a-z0-9][a-z0-9_-]{0,126}$")
SURFACES = {
    "denominator": ("governance-denominator.sql", "SNOWFLAKE.ACCOUNT_USAGE.TABLES+COLUMNS"),
    "tag_references": ("governance-tag-references.sql", "SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES"),
    "policy_references": ("governance-policy-references.sql", "SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES"),
    "classification_latest": (
        "governance-classification-latest.sql",
        "SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST+TABLES",
    ),
}


class CollectionError(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def render_surface(surface: str, database: str, row_limit: int) -> tuple[Path, str, str, str, dict]:
    if surface not in SURFACES:
        raise CollectionError("unsupported surface")
    if not IDENTIFIER.fullmatch(database):
        raise CollectionError("database must be one unquoted Snowflake identifier")
    if isinstance(row_limit, bool) or not 1 <= row_limit <= 10_000:
        raise CollectionError("row-limit must be between 1 and 10000")
    template_name, source = SURFACES[surface]
    path = SQL_DIR / template_name
    template = path.read_text(encoding="utf-8")
    rendered = template.replace("__DATABASE_LITERAL__", database).replace("__ROW_LIMIT_PLUS_ONE__", str(row_limit + 1))
    if "__" in rendered:
        raise CollectionError("unresolved SQL substitution token")
    statements = [part.strip() for part in rendered.split(";") if part.strip()]
    if len(statements) != 1 or not re.match(r"^(?:--[^\n]*\n\s*)*(?:SELECT|WITH)\b", statements[0], re.IGNORECASE):
        raise CollectionError("template must contain exactly one read-only SELECT/CTE statement")
    if re.search(r"\b(?:ALTER|CALL|COPY|CREATE|DELETE|DROP|GRANT|INSERT|MERGE|PUT|REMOVE|REVOKE|TRUNCATE|UPDATE)\b", rendered, re.IGNORECASE):
        raise CollectionError("template contains a mutation token")
    selector = {"database": database}
    return path, template, rendered, source, selector


def load_object_manifest(path: Path | None, database: str) -> list[dict]:
    if path is None:
        raise CollectionError("current policy collection requires --object-manifest")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CollectionError(f"cannot read object manifest: {error}") from error
    if not isinstance(raw, list) or not raw or len(raw) > 1_000:
        raise CollectionError("object manifest must contain 1 to 1000 rows")
    result = []
    seen = set()
    for index, row in enumerate(raw):
        if not isinstance(row, dict) or set(row) != {"asset_key", "object_name", "domain"}:
            raise CollectionError(f"object_manifest[{index}] must contain only asset_key, object_name, and domain")
        asset_key = _key(row.get("asset_key"), "asset", f"object_manifest[{index}].asset_key")
        object_name = str(row.get("object_name") or "")
        if not OBJECT_IDENTIFIER.fullmatch(object_name):
            raise CollectionError(f"object_manifest[{index}].object_name must be a 2- or 3-part unquoted identifier")
        if len(object_name.split(".")) == 3 and object_name.split(".")[0].upper() != database.upper():
            raise CollectionError(f"object_manifest[{index}] is outside the selected database")
        domain = str(row.get("domain") or "").upper()
        if domain not in {"TABLE", "VIEW"}:
            raise CollectionError(f"object_manifest[{index}].domain must be TABLE or VIEW")
        if asset_key in seen:
            raise CollectionError(f"duplicate object manifest asset: {asset_key}")
        seen.add(asset_key)
        result.append({"asset_key": asset_key, "object_name": object_name, "domain": domain})
    return sorted(result, key=lambda item: item["asset_key"])


def render_current_policy(database: str, row_limit: int, objects: list[dict]) -> tuple[str, str, str, dict]:
    if isinstance(row_limit, bool) or not 1 <= row_limit <= 10_000:
        raise CollectionError("row-limit must be between 1 and 10000")
    path = SQL_DIR / "governance-policy-references-current.sql"
    template = path.read_text(encoding="utf-8")
    rendered_queries = []
    for item in objects:
        rendered = (
            template.replace("__DATABASE_IDENTIFIER__", database)
            .replace("__OBJECT_LITERAL__", item["object_name"])
            .replace("__DOMAIN_LITERAL__", item["domain"])
            .replace("__ASSET_KEY_LITERAL__", item["asset_key"])
            .replace("__ROW_LIMIT_PLUS_ONE__", str(row_limit + 1))
        )
        if "__" in rendered:
            raise CollectionError("unresolved current-policy SQL substitution token")
        statements = [part.strip() for part in rendered.split(";") if part.strip()]
        if len(statements) != 1 or not re.match(r"^(?:--[^\n]*\n\s*)*SELECT\b", statements[0], re.IGNORECASE):
            raise CollectionError("current-policy template must contain exactly one read-only SELECT")
        if re.search(r"\b(?:ALTER|CALL|COPY|CREATE|DELETE|DROP|GRANT|INSERT|MERGE|PUT|REMOVE|REVOKE|TRUNCATE|UPDATE)\b", rendered, re.IGNORECASE):
            raise CollectionError("current-policy template contains a mutation token")
        rendered_queries.append(rendered)
    selector = {"database": database, "objects": objects}
    return template, "\n".join(rendered_queries), "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES", selector


def _rows(raw: Any) -> list[dict]:
    if isinstance(raw, dict) and isinstance(raw.get("data"), list):
        raw = raw["data"]
    elif isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise CollectionError("Snowflake CLI JSON_EXT must be an object or array")
    rows = []
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            raise CollectionError(f"Snowflake row {index} is not an object")
        rows.append({str(key).casefold(): value for key, value in row.items()})
    return rows


def _key(value: object, prefix: str, path: str) -> str:
    result = str(value or "").strip().lower()
    if not result.startswith(prefix + "_") or not OPAQUE.fullmatch(result):
        raise CollectionError(f"{path} is not a valid privacy-safe {prefix} key")
    return result


def load_requirements(path: Path | None) -> dict[str, dict]:
    if path is None:
        raise CollectionError("denominator collection requires --requirements")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CollectionError(f"cannot read requirements: {error}") from error
    if not isinstance(raw, list) or not raw or len(raw) > 10_000:
        raise CollectionError("requirements must contain 1 to 10000 rows")
    result = {}
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            raise CollectionError(f"requirements[{index}] must be an object")
        allowed = {"asset_key", "domain", "require_tag", "require_classification", "required_controls"}
        if set(row) - allowed:
            raise CollectionError(f"requirements[{index}] contains raw or unsupported fields")
        key = _key(row.get("asset_key"), "asset", f"requirements[{index}].asset_key")
        if key in result:
            raise CollectionError(f"duplicate requirement: {key}")
        if row.get("domain") not in {"COLUMN", "TABLE", "VIEW"}:
            raise CollectionError(f"requirements[{index}].domain is invalid")
        if not isinstance(row.get("require_tag"), bool) or not isinstance(row.get("require_classification"), bool):
            raise CollectionError(f"requirements[{index}] booleans are invalid")
        if not isinstance(row.get("required_controls"), list) or any(not isinstance(item, str) for item in row["required_controls"]):
            raise CollectionError(f"requirements[{index}].required_controls is invalid")
        result[key] = row
    return result


def normalize(surface: str, raw: Any, requirements: dict[str, dict] | None = None) -> tuple[list[dict], int]:
    rows = _rows(raw)
    allowed_columns = {
        "denominator": {"asset_key", "domain", "data_type"},
        "tag_references": {"asset_key", "tag_key", "apply_method"},
        "policy_references": {
            "asset_key", "policy_key", "policy_kind", "assignment", "policy_status", "entity_key_hash"
        },
        "classification_latest": {
            "asset_key", "status", "last_classified_on", "last_attempt_on", "error_present"
        },
    }[surface]
    for index, row in enumerate(rows):
        unexpected = set(row) - allowed_columns
        if unexpected:
            raise CollectionError(f"{surface} row {index} contains unexpected fields: {sorted(unexpected)}")
    dataset: list[dict] = []
    if surface == "denominator":
        discovered = {_key(row.get("asset_key"), "asset", "denominator.asset_key") for row in rows}
        expected = set(requirements or {})
        missing = expected - discovered
        if missing:
            raise CollectionError(f"{len(missing)} denominator requirements were not visible to the collector role")
        dataset = [dict((requirements or {})[key]) for key in sorted(expected)]
    elif surface == "tag_references":
        for row in rows:
            dataset.append(
                {
                    "asset_key": _key(row.get("asset_key"), "asset", "tags.asset_key"),
                    "tag_key": _key(row.get("tag_key"), "tag", "tags.tag_key"),
                    "apply_method": str(row.get("apply_method") or "LEGACY").upper(),
                }
            )
    elif surface == "policy_references":
        for row in rows:
            entity_hash = row.get("entity_key_hash")
            dataset.append(
                {
                    "asset_key": _key(row.get("asset_key"), "asset", "policies.asset_key"),
                    "policy_key": _key(row.get("policy_key"), "policy", "policies.policy_key"),
                    "policy_kind": str(row.get("policy_kind") or "").upper(),
                    "assignment": str(row.get("assignment") or "").upper(),
                    "policy_status": str(row.get("policy_status") or "").upper(),
                    "entity_key_hashes": [str(entity_hash)] if entity_hash else [],
                }
            )
    elif surface == "classification_latest":
        for row in rows:
            if not isinstance(row.get("error_present"), bool):
                raise CollectionError("classifications.error_present must be boolean")
            dataset.append(
                {
                    "asset_key": _key(row.get("asset_key"), "asset", "classifications.asset_key"),
                    "status": str(row.get("status") or "").upper(),
                    "last_classified_on": row.get("last_classified_on"),
                    "last_attempt_on": row.get("last_attempt_on"),
                    "error_present": row["error_present"],
                }
            )
    dataset.sort(key=lambda item: canonical(item))
    return dataset, len(rows)


def build_envelope(
    surface: str,
    template: str,
    rendered: str,
    source: str,
    selector: dict,
    dataset: list[dict],
    raw_count: int,
    row_limit: int,
    privilege_scope: str,
    collected_at: str,
    truncated: bool,
) -> dict:
    selector_metadata = {"database": True}
    if isinstance(selector.get("objects"), list):
        selector_metadata["objects"] = len(selector["objects"])
    receipt = {
        "schema_version": "1",
        "surface": surface,
        "status": "COLLECTED",
        "collected_at": collected_at,
        "row_count": len(dataset),
        "raw_row_count": raw_count,
        "row_limit": row_limit,
        "truncated": truncated,
        "privilege_scope": privilege_scope,
        "source": source,
        "query_sha256": sha(rendered.encode()),
        "template_sha256": sha(template.encode()),
        "rendered_sql_sha256": sha(rendered.encode()),
        "dataset_sha256": sha(canonical(dataset)),
        "source_metadata": {"selector": selector_metadata},
        "selector_fingerprint": sha(canonical(selector)),
    }
    receipt["receipt_sha256"] = sha(canonical(receipt))
    return {"schema_version": "1", "surface": surface, "dataset": dataset, "receipt": receipt}


def execute(connection: str, rendered: str, runner=subprocess.run) -> Any:
    if not PROFILE.fullmatch(connection):
        raise CollectionError("connection profile contains unsupported characters")
    descriptor, temporary_name = tempfile.mkstemp(prefix="snowflake-governance-", suffix=".sql")
    path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        command = [
            "snow", "sql", "--filename", str(path), "--connection", connection,
            "--format", "JSON_EXT", "--silent", "--enhanced-exit-codes", "--local-only",
        ]
        completed = runner(command, capture_output=True, text=True, timeout=120, check=False)
        if completed.returncode != 0:
            raise CollectionError(f"Snowflake CLI failed with exit code {completed.returncode}")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise CollectionError("Snowflake CLI did not return valid JSON_EXT") from error
    finally:
        path.unlink(missing_ok=True)


def write_json(value: dict, output: Path | None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise CollectionError("refusing to replace a symlink output")
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", choices=sorted(SURFACES), required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--row-limit", type=int, default=1000)
    parser.add_argument("--connection")
    parser.add_argument("--input-json", type=Path, help="normalize saved Snowflake CLI JSON_EXT instead of connecting")
    parser.add_argument("--requirements", type=Path, help="sanitized denominator requirements JSON")
    parser.add_argument("--object-manifest", type=Path, help="restricted object manifest for current POLICY_REFERENCES collection")
    parser.add_argument("--privilege-scope", choices=("COMPLETE", "PARTIAL", "UNKNOWN"), default="UNKNOWN")
    parser.add_argument("--collected-at", default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()
    try:
        current_objects = None
        if args.surface == "policy_references" and args.object_manifest:
            if not IDENTIFIER.fullmatch(args.database):
                raise CollectionError("database must be one unquoted Snowflake identifier")
            current_objects = load_object_manifest(args.object_manifest, args.database)
            template, rendered, source, selector = render_current_policy(args.database, args.row_limit, current_objects)
        else:
            _, template, rendered, source, selector = render_surface(args.surface, args.database, args.row_limit)
        if args.render_only:
            sys.stdout.write(rendered)
            return 0
        if args.input_json:
            raw = json.loads(args.input_json.read_text(encoding="utf-8"))
        elif args.connection:
            if current_objects:
                raw = []
                for item in current_objects:
                    _, one_rendered, _, _ = render_current_policy(args.database, args.row_limit, [item])
                    raw.extend(_rows(execute(args.connection, one_rendered)))
            else:
                raw = execute(args.connection, rendered)
        else:
            raise CollectionError("provide --connection or --input-json")
        requirements = load_requirements(args.requirements) if args.surface == "denominator" else None
        dataset, raw_count = normalize(args.surface, raw, requirements)
        raw_rows = _rows(raw)
        if current_objects:
            counts: dict[str, int] = {}
            for row in raw_rows:
                key = str(row.get("asset_key") or "").lower()
                counts[key] = counts.get(key, 0) + 1
            truncated = any(count > args.row_limit for count in counts.values())
        else:
            truncated = raw_count > args.row_limit
        envelope = build_envelope(
            args.surface, template, rendered, source, selector, dataset, raw_count,
            args.row_limit, args.privilege_scope, args.collected_at or utc_now(), truncated,
        )
        write_json(envelope, args.output)
    except (CollectionError, FileNotFoundError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(f"governance evidence collection failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
