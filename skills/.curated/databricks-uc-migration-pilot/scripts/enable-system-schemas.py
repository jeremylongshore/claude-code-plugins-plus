#!/usr/bin/env python3
"""enable-system-schemas.py — enable Unity Catalog system schemas and grant a
group read access, idempotently (bead 8jj0 / doc 004-RL-RSRC D10).

The migration pilot reads `system.information_schema` (readiness audit) and
`system.access` / `system.billing` (permission tracing). Those schemas are each
individually gated behind an account-level enable flag AND a metastore-admin
grant chain — the #1 reason the pilot stalls with a bare `PERMISSION_DENIED`.
This script does both halves in one idempotent pass so an account admin can run
it once and hand the pilot a workspace that can actually see the tables.

Two-layer model (why this needs two roles):
  1. ENABLE (account admin): turn the system schema on via the metastore's UC
     SystemSchemas surface — `databricks system-schemas enable <metastore_id>
     <schema>` (equivalently PUT /api/2.1/unity-catalog/metastores/<id>/
     systemschemas/<schema>). The CALLER must be an account admin, so the script
     prechecks account-level access (a plain workspace PAT for a non-account-admin
     is rejected up front) and fails with a typed error BEFORE any call, so you
     never get a half-enabled metastore.
  2. GRANT (metastore admin): grant the group USE CATALOG system + USE SCHEMA
     system.<schema> + SELECT on the schema's tables, run through a SQL warehouse.

Idempotent by construction: an already-enabled schema and an already-present
grant are treated as success, not error, so re-running is safe (WATCH per 8jj0).
Every action is recorded in an audit-log JSON written to --audit-out.

Usage:
  enable-system-schemas.py --account-id <A> --metastore-id <M> \
      --grant-to data-governance \
      [--schemas billing,access,compute,lineage,query,storage] \
      [--audit-out ./system-schemas-audit.json] [--dry-run]

Requires the Databricks CLI authenticated at ACCOUNT level (a profile with
account_id, or `databricks auth login --account-id`), a running SQL warehouse in
DATABRICKS_WAREHOUSE_ID for the grants, and jq is not needed (pure-python JSON).

Exit codes: 0 ok · 2 bad usage · 3 databricks CLI missing ·
            4 not account-level auth (typed precheck failure) · 5 an API/SQL call failed.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# The system schemas that carry their own per-schema enable flag. information_schema
# is always on and is intentionally NOT here (enabling it errors). Kept as the
# validation allowlist so a typo becomes a clear error, not a silent API 400.
KNOWN_SYSTEM_SCHEMAS = (
    "access",
    "billing",
    "compute",
    "lineage",
    "query",
    "storage",
    "serving",
    "marketplace",
)
DEFAULT_SCHEMAS = ("billing", "access", "compute", "lineage", "query", "storage")

# Enable-state values the Account API reports; ENABLE_COMPLETED / ENABLE_INITIALIZED
# both mean "on" for our idempotency purposes (a re-run must treat them as success).
ENABLED_STATES = ("ENABLE_COMPLETED", "ENABLE_INITIALIZED", "ENABLED")


def validate_schemas(requested):
    """Split requested schemas into (valid, unknown). Pure — the caller decides
    whether an unknown name is fatal (default) or skipped."""
    valid, unknown = [], []
    for s in requested:
        s = s.strip().lower()
        if not s:
            continue
        (valid if s in KNOWN_SYSTEM_SCHEMAS else unknown).append(s)
    return valid, unknown


def is_already_enabled(schema_state):
    """True if an Account-API systemschemas GET/PUT state means the schema is
    already on — so a re-run is a no-op, not an error (idempotency contract)."""
    return str(schema_state or "").upper() in ENABLED_STATES


def grant_statements(schema, group):
    """The idempotent grant chain for one system schema. UC GRANTs are additive
    and re-applying an existing grant is a no-op, so these are safe to re-run.
    SELECT ON SCHEMA covers all current + future tables in the schema. Pure."""
    g = group.replace("`", "")  # never let a backtick break out of the identifier
    return [
        "GRANT USE CATALOG ON CATALOG system TO `%s`" % g,
        "GRANT USE SCHEMA ON SCHEMA system.%s TO `%s`" % (schema, g),
        "GRANT SELECT ON SCHEMA system.%s TO `%s`" % (schema, g),
    ]


def build_audit_record(account_id, metastore_id, group, results, dry_run):
    """The audit JSON the org keeps: what was enabled/granted and to whom. Pure
    (timestamp is injected by the caller so this stays deterministic/testable)."""
    return {
        "action": "enable-system-schemas",
        "dry_run": bool(dry_run),
        "account_id": account_id,
        "metastore_id": metastore_id,
        "granted_to": group,
        "schemas": results,
        "summary": {
            "enabled": sum(1 for r in results if r.get("enable") == "enabled"),
            "already_enabled": sum(1 for r in results if r.get("enable") == "already-enabled"),
            "granted": sum(1 for r in results if r.get("grant") == "applied"),
            "failed": sum(1 for r in results if r.get("error")),
        },
    }


# --------------------------------------------------------------------------
# Orchestration (the account-level + SQL calls). Kept out of the pure core.
# --------------------------------------------------------------------------
def _account_auth_ok():
    """Precheck: is the CLI authenticated at ACCOUNT level? A workspace PAT can't
    hit the account API. `databricks account metastores list` succeeds only with
    account-level auth; use it as the probe."""
    if not shutil.which("databricks"):
        sys.exit(3)
    probe = subprocess.run(
        ["databricks", "account", "metastores", "list", "--output", "json"],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0, (probe.stderr or "").strip()


def _enable_schema(metastore_id, schema, dry_run):
    # Real enablement is the metastore's UC SystemSchemas surface, exposed as the
    # `databricks system-schemas enable <metastore_id> <schema>` CLI command — NOT
    # an account-scoped API path. The caller must be an account admin (verified by
    # the precheck above).
    if dry_run:
        return "would-enable", None
    proc = subprocess.run(
        ["databricks", "system-schemas", "enable", metastore_id, schema],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return "enabled", None
    err = (proc.stderr or proc.stdout or "").strip()
    # Idempotency: an "already enabled" style error is success, not failure.
    if any(k in err.upper() for k in ("ALREADY", "ENABLE_COMPLETED", "EXISTS")):
        return "already-enabled", None
    return None, err[:300]


def _run_sql(statement, dry_run):
    if dry_run:
        return True, None
    wh = os.environ.get("DATABRICKS_WAREHOUSE_ID")
    if not wh:
        return False, "DATABRICKS_WAREHOUSE_ID unset (needed to run the grants)"
    payload = {"warehouse_id": wh, "statement": statement, "wait_timeout": "30s"}
    proc = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--json", json.dumps(payload)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, (proc.stderr or "").strip()[:300]
    state = json.loads(proc.stdout or "{}").get("status", {}).get("state")
    return state == "SUCCEEDED", None if state == "SUCCEEDED" else f"statement state {state}"


def main():
    ap = argparse.ArgumentParser(description="Enable UC system schemas + grant a group, idempotently")
    ap.add_argument("--account-id", required=True)
    ap.add_argument("--metastore-id", required=True)
    ap.add_argument(
        "--grant-to",
        required=True,
        metavar="GROUP",
        help="account group to grant USE CATALOG/SCHEMA + SELECT on each schema",
    )
    ap.add_argument(
        "--schemas", default=",".join(DEFAULT_SCHEMAS), help="comma-separated system schemas (default: %(default)s)"
    )
    ap.add_argument("--audit-out", default="./system-schemas-audit.json")
    ap.add_argument(
        "--allow-unknown", action="store_true", help="skip (rather than fail on) schema names not in the known set"
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    valid, unknown = validate_schemas(args.schemas.split(","))
    if unknown and not args.allow_unknown:
        sys.exit(
            f"error: unknown system schema(s): {', '.join(unknown)}. "
            f"Known: {', '.join(KNOWN_SYSTEM_SCHEMAS)}. Use --allow-unknown to skip them."
        )
    if not valid:
        sys.exit("error: no valid system schemas to enable")

    # Typed auth-scope precheck BEFORE any mutation (WATCH per 8jj0).
    if not args.dry_run:
        ok, err = _account_auth_ok()
        if not ok:
            sys.stderr.write(
                "error: not authenticated at ACCOUNT level — a workspace PAT cannot enable "
                "system schemas. Use an account profile (`databricks auth login --account-id "
                f"{args.account_id}`). Probe said: {err[:200]}\n"
            )
            return 4

    results = []
    for schema in valid:
        rec = {"schema": schema}
        enable_state, enable_err = _enable_schema(args.metastore_id, schema, args.dry_run)
        rec["enable"] = enable_state
        if enable_err:
            rec["error"] = f"enable: {enable_err}"
            results.append(rec)
            continue
        # Grants (idempotent). Stop this schema's grants on first failure, record it.
        applied = True
        for stmt in grant_statements(schema, args.grant_to):
            ok, gerr = _run_sql(stmt, args.dry_run)
            if not ok:
                rec["error"] = f"grant: {gerr}"
                applied = False
                break
        rec["grant"] = "applied" if applied else "failed"
        results.append(rec)

    audit = build_audit_record(args.account_id, args.metastore_id, args.grant_to, results, args.dry_run)
    with open(args.audit_out, "w") as fh:
        json.dump(audit, fh, indent=2)
    print(json.dumps(audit["summary"], indent=2))
    print(f"audit log: {args.audit_out}", file=sys.stderr)
    return 5 if audit["summary"]["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
