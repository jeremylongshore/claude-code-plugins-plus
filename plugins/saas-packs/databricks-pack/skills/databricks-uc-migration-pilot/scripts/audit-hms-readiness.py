#!/usr/bin/env python3
"""audit-hms-readiness.py — classify every Hive Metastore (HMS) table by its
Unity Catalog (UC) migratability, deterministically.

The migration-pilot skill runs the enumeration SQL (SHOW TABLES / DESCRIBE
DETAIL against `hive_metastore`, plus `system.information_schema`) and hands the
raw rows to this script; the script does the CLASSIFICATION — the LLM never
eyeballs a storage URI. Output is a readiness CSV the `migration-planner`
subagent consumes to order the migration.

The classification rule is the whole point and is deterministic:

  storage URI scheme        verdict     why
  ------------------------  ----------  --------------------------------------
  s3:// abfss:// gs://       READY       cloud-native URI UC can govern via an
                                         external location + storage credential
  wasbs:// adl://            BLOCKED     Azure legacy schemes UC cannot govern
                                         (external locations require abfss://)
  dbfs:/user/hive/... , dbfs:/  BLOCKED  DBFS-root managed data, no cloud URI
  (missing / unreadable)     ORPHAN      HMS entry points at deleted/absent
                                         storage — a dangling catalog row, NOT a
                                         migration blocker (surface, don't block)

A table on a LEGACY_TABLE_ACL cluster is additionally flagged: even a
cloud-native table inherits the DENY-based ACL model UC (allow-only) cannot
auto-map, so its grants must be re-authored.

Input: JSON array of rows on stdin or --input FILE. Each row:
  {"table_name": "hive_metastore.sales.orders",
   "storage_uri": "s3://bucket/warehouse/orders",   # may be null/"" -> orphan
   "table_type":  "EXTERNAL" | "MANAGED",            # optional
   "table_format":"DELTA" | "PARQUET" | ...,         # optional
   "acl_mode":    "LEGACY_TABLE_ACL" | "..." }        # optional

Output: CSV to stdout (or --out FILE) with columns
  table_name, storage_uri, scheme, migration_blocker, suggested_action

Live mode (--live) enumerates HMS itself through the Databricks CLI Statement
Execution API (needs DATABRICKS_WAREHOUSE_ID + an authenticated CLI); default
mode is pure classification so the logic is unit-testable with no workspace.

Exit codes: 0 ok (even when blockers exist — blockers are data, not failure) ·
            2 bad usage/input · 3 databricks CLI missing (live mode only).
"""

import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys

# Cloud-native schemes UC can govern via an external location + storage credential.
READY_SCHEMES = ("s3", "s3a", "s3n", "abfss", "gs")
# Legacy Azure schemes UC external locations do not accept (must move to abfss://).
AZURE_LEGACY_SCHEMES = ("wasb", "wasbs", "adl")
SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):")

READY = "READY"
BLOCKED = "BLOCKED"
ORPHAN = "ORPHAN"


def uri_scheme(uri):
    """Return the lowercased URI scheme (`s3`, `abfss`, `dbfs`, …) or '' if the
    string carries no scheme. `dbfs:/x` and `dbfs:///x` both yield `dbfs`."""
    if not uri:
        return ""
    m = SCHEME_RE.match(uri.strip())
    return m.group(1).lower() if m else ""


def classify(row):
    """Classify one HMS table row → (scheme, blocker, suggested_action).

    `blocker` is '' when the table is migration-ready. Pure: no I/O, no network,
    so the whole readiness contract is unit-testable."""
    uri = (row.get("storage_uri") or "").strip()
    scheme = uri_scheme(uri)
    table_format = (row.get("table_format") or "").upper()
    table_type = (row.get("table_type") or "").upper()
    acl = (row.get("acl_mode") or "").upper()

    # ORPHAN first: an HMS entry with no resolvable storage is a dangling catalog
    # row (deleted path, or a MANAGED table whose data was dropped) — surface it
    # for cleanup, never as a migration blocker (WATCH per bead q9d7).
    if not uri:
        return (
            "",
            ORPHAN,
            "Dangling HMS entry (no storage location) — verify the data exists; DROP the stale table or repoint it before migrating.",
        )

    verdict = READY
    reasons = []
    actions = []

    if scheme in AZURE_LEGACY_SCHEMES:
        verdict = BLOCKED
        reasons.append(f"{scheme}:// is a legacy Azure scheme UC cannot govern")
        actions.append(
            "Relocate the data to an abfss:// (ADLS Gen2) path via DEEP CLONE, then register an external location + CREATE TABLE at the new path"
        )
    elif scheme == "dbfs":
        verdict = BLOCKED
        # dbfs:/user/hive/warehouse is the classic managed-root case; any dbfs:/ is un-governable by UC.
        reasons.append("DBFS-root storage has no cloud-native URI UC can govern")
        actions.append(
            "Rewrite to a cloud path: DEEP CLONE (Delta) or CREATE TABLE AS SELECT (non-Delta) into s3://|abfss://|gs://, then migrate the copy"
        )
    elif scheme not in READY_SCHEMES:
        # Unknown/other scheme (e.g. file:/, hdfs:) — not something UC governs.
        verdict = BLOCKED
        reasons.append(f"'{scheme or 'no'}' scheme is not a UC-governable cloud location")
        actions.append("Move the data to a supported cloud object store (s3://, abfss://, gs://) before migrating")

    # A non-Delta EXTERNAL table on a ready path still migrates differently — SYNC
    # handles Delta; Parquet/ORC/CSV/JSON externals must be re-registered.
    if verdict == READY and table_type == "EXTERNAL" and table_format and table_format != "DELTA":
        actions.append(
            f"Non-Delta ({table_format}) external: re-CREATE as an external table under UC at the same path (SYNC covers Delta only)"
        )

    # LEGACY_TABLE_ACL: even a ready table's DENY-based grants cannot auto-map to
    # UC's allow-only model — flag so the planner re-authors permissions.
    if acl == "LEGACY_TABLE_ACL":
        if verdict == READY:
            actions.append(
                "Cluster uses LEGACY_TABLE_ACL (DENY-based) — re-author grants for UC's allow-only model; table data itself is ready"
            )
        else:
            reasons.append("also on a LEGACY_TABLE_ACL cluster — grants must be re-authored, not auto-mapped")

    blocker = "; ".join(reasons)
    suggested = (
        " | ".join(actions) if actions else "SYNC the table into a UC catalog (Delta, cloud-native path — ready as-is)"
    )
    return scheme, blocker, suggested


def rows_to_csv(rows, out):
    w = csv.writer(out)
    w.writerow(["table_name", "storage_uri", "scheme", "migration_blocker", "suggested_action"])
    counts = {READY: 0, BLOCKED: 0, ORPHAN: 0}
    for row in rows:
        scheme, blocker, suggested = classify(row)
        verdict = ORPHAN if not (row.get("storage_uri") or "").strip() else (BLOCKED if blocker else READY)
        counts[verdict] += 1
        w.writerow(
            [
                row.get("table_name", ""),
                row.get("storage_uri", "") or "",
                scheme,
                blocker,
                suggested,
            ]
        )
    return counts


# --------------------------------------------------------------------------
# Live enumeration (opt-in) — enumerate HMS through the CLI Statement Exec API.
# --------------------------------------------------------------------------
def _sql(statement):
    wh = os.environ.get("DATABRICKS_WAREHOUSE_ID")
    if not wh:
        sys.exit("error: --live needs DATABRICKS_WAREHOUSE_ID (a running SQL warehouse)")
    payload = {"warehouse_id": wh, "statement": statement, "wait_timeout": "50s"}
    proc = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/sql/statements", "--json", json.dumps(payload)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"error: databricks statement failed: {proc.stderr.strip()[:400]}")
    doc = json.loads(proc.stdout or "{}")
    if doc.get("status", {}).get("state") != "SUCCEEDED":
        sys.exit(f"error: statement not SUCCEEDED: {json.dumps(doc.get('status', {}))[:400]}")
    return [r for r in doc.get("result", {}).get("data_array", [])]


def enumerate_live(schema):
    """Enumerate hive_metastore.<schema> tables + their storage locations.

    Uses system.information_schema.tables for the table list, then DESCRIBE
    DETAIL per table for the physical `location` (HMS tables expose it there).
    Real path; kept separate from classify() so the classifier stays pure."""
    if not shutil.which("databricks"):
        sys.exit(3)
    tables = _sql(
        "SELECT table_name, table_type FROM system.information_schema.tables "
        f"WHERE table_catalog = 'hive_metastore' AND table_schema = '{schema}'"
    )
    rows = []
    for name, ttype in tables:
        fq = f"hive_metastore.{schema}.{name}"
        try:
            detail = _sql(f"DESCRIBE DETAIL {fq}")
            # DESCRIBE DETAIL returns a row incl. a `location` and `format` column.
            loc = detail[0][_col_index("location")] if detail else None
            fmt = detail[0][_col_index("format")] if detail else None
        except SystemExit:
            loc, fmt = None, None  # orphan / unreadable → surfaced as ORPHAN
        rows.append({"table_name": fq, "storage_uri": loc, "table_type": ttype, "table_format": fmt})
    return rows


# DESCRIBE DETAIL column order is stable in Databricks; index defensively.
_DETAIL_COLS = ["format", "id", "name", "description", "location"]


def _col_index(col):
    return _DETAIL_COLS.index(col) if col in _DETAIL_COLS else 4


def main():
    ap = argparse.ArgumentParser(description="Classify HMS tables by UC migratability")
    ap.add_argument("--input", help="JSON array of table rows (default: stdin)")
    ap.add_argument("--out", help="write CSV here (default: stdout)")
    ap.add_argument("--live", metavar="SCHEMA", help="enumerate hive_metastore.<SCHEMA> live via the Databricks CLI")
    ap.add_argument("--summary", action="store_true", help="print a READY/BLOCKED/ORPHAN tally to stderr")
    args = ap.parse_args()

    if args.live:
        rows = enumerate_live(args.live)
    else:
        raw = open(args.input).read() if args.input else sys.stdin.read()
        if not raw.strip():
            sys.exit("error: no input (pass --input FILE, pipe JSON on stdin, or use --live SCHEMA)")
        try:
            rows = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.exit(f"error: input is not valid JSON: {e}")
        if not isinstance(rows, list):
            sys.exit("error: input must be a JSON array of table rows")

    buf = io.StringIO()
    counts = rows_to_csv(rows, buf)
    out_text = buf.getvalue()
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out_text)
    else:
        sys.stdout.write(out_text)
    if args.summary:
        print(
            f"readiness: {counts[READY]} READY, {counts[BLOCKED]} BLOCKED, "
            f"{counts[ORPHAN]} ORPHAN ({sum(counts.values())} tables)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
