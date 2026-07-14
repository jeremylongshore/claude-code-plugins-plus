#!/usr/bin/env python3
"""
dolt-sync.py — one-way exporter: freshie/inventory.sqlite → Dolt → DoltHub.

Freshie's runtime format stays SQLite (zero consumer rewrites); the Dolt repo
at freshie/dolt/freshie/ is the versioned system of record, pushed to the
public DoltHub database <org>/freshie-inventory. This script is the ONLY
writer of the Dolt repo — never hand-edit it, never merge DoltHub PRs or
web-edit the public database (local is the sole writer).

Protocol per inventory cycle:
    python3 freshie/scripts/rebuild-inventory.py
    python3 scripts/validate-skills-schema.py --marketplace --populate-db freshie/inventory.sqlite
    python3 freshie/scripts/dolt-sync.py

What one sync does:
  1. Takes an flock (freshie/dolt/.sync.lock); refuses to start if a Dolt
     sql-server holds the repo open. Clears any dead prior run with
     `dolt reset --hard` + `dolt clean` (reset alone leaves never-committed
     tables behind).
  2. Snapshots the SQLite DB (VACUUM INTO a tmpfs copy) so every table export
     reads one consistent point in time.
  3. Filters tables through the explicit EXPORT_ALLOWLIST — only the intended
     CMDB tables are published. Known j-rig runtime contaminants
     (JRIG_RUNTIME_TABLES) are excluded with a log line; any OTHER unknown
     table is a hard failure (the BLOB philosophy: never publish what was
     not deliberately reviewed). Then translates the schema (see translate
     rules below) and creates any table missing from the Dolt repo. Existing
     Dolt schemas are left alone — a schema-mismatch abort from
     `dolt table import -r` is a free parity gate; pass --recreate-tables to
     drop + recreate on legitimate schema change.
  4. Pumps every allowlisted table: `sqlite3 -header -csv` → `dolt table import -r`.
     NULL vs '' needs no sentinel — the sqlite3 emitter writes NULL as an
     unquoted empty field and '' as a quoted "" pair, which is exactly the
     dialect Dolt's CSV reader distinguishes (verified against dolt 2.1.10;
     the (NULL,'') canary re-proves it on every run). If the canary ever
     fails, tables containing empty strings are routed through batched
     multi-row INSERTs instead (never `dolt sql -b`, a documented no-op).
     No --pk on import: it is silently ignored with -r; PKs live in the DDL.
  5. Gates before committing: per-table COUNT(*) parity (hard fail),
     float-tolerant aggregate checksums on every REAL column, and per-row
     MD5 byte checksums on the JSON-bearing TEXT columns.
  6. Writes the tracked compact export: freshie/grades.csv (one row per
     skill IN THE LATEST GRADED RUN, deterministic sort) +
     freshie/grade-histogram.json (labeled with that run's id). Scoped to
     one run so a skill deleted from the repo drops out of the export
     instead of ghosting forever. Their git diff is the "skill X went B→A"
     story — the append-only run_id model means `dolt diff run-7 run-8`
     shows added rows, not cell changes; history queries against Dolt are
     `WHERE run_id = N` / `AS OF 'run-N'`.
  7. Commits (`--skip-empty`), tags run-<N> (N = MAX(discovery_runs.id))
     only when the tag would sit on a commit that actually carries run N,
     then pushes main AND the tag (tags do not ride along on a branch push)
     AND any older local run-* tag missing from the remote (heals a tag
     stranded by a prior failed push). Push failure with valid creds exits
     non-zero and loud — a silently unpushed Dolt repo is single-copy
     history on an OOM-prone box.
  8. Runs `dolt gc` under the same flock every GC_EVERY_N_SYNCS syncs or
     when the repo directory doubles since the last gc (no auto-GC runs on
     the import path in this Dolt build).

Schema translation rules (SQLite → Dolt/MySQL dialect):
  - every identifier backtick-quoted
  - AUTOINCREMENT stripped entirely (ids always come from the data; kills
    the explicit-id-0 rewrite class in the INSERT fallback path)
  - INTEGER → BIGINT, REAL → DOUBLE, TIMESTAMP → DATETIME(6) (stored values
    are ISO-8601 with microseconds), TEXT → LONGTEXT
  - EXCEPT: a TEXT column that is part of the PRIMARY KEY → VARCHAR(255),
    guarded by a MAX(LENGTH(col)) <= 255 assert (npm package names are
    spec-capped at 214)
  - UNIQUE constraints keep their LONGTEXT columns (Dolt indexes TEXT
    natively — laxer than MySQL); non-unique indexes over TEXT columns get
    a (255) prefix
  - DEFAULT CURRENT_TIMESTAMP on a DATETIME(6) column becomes
    DEFAULT CURRENT_TIMESTAMP(6) (MySQL requires matching precision)
  - any BLOB column is a hard failure; ENUM is never emitted;
    sqlite_sequence is skipped

Restore path (DoltHub → local SQLite):
    dolt clone jeremylongshore/freshie-inventory && cd freshie-inventory
    dolt sql -r csv -q "SELECT * FROM skill_compliance" > skill_compliance.csv
    sqlite3 new.sqlite ".import --csv skill_compliance.csv skill_compliance"

Vocabulary: the DoltHub push is what makes the data durable and visible;
it is not "backup" (borg on the VPS is backup). CI runners need a commit
identity (`dolt config --global --add user.name ...` / user.email) and can
authenticate the push without `dolt login` by setting BOTH
DOLT_REMOTE_USER=<name> and DOLT_REMOTE_PASSWORD=<api token> — push() then
runs `dolt push --user <name>` (dolt reads the password from the env var)
and skips the interactive `dolt creds check`.

Usage:
    python3 freshie/scripts/dolt-sync.py [--db PATH] [--no-push] [--dry-run]
        [--recreate-tables] [--gc] [--org ORG] [--repo NAME]

Exit codes: 0 ok · 1 gate/translation failure · 2 lock contention ·
            3 push failure (loud, actionable).
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import io
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Derive the repo root from this file's location (freshie/scripts/dolt-sync.py)
# so the script works from any cwd, including git worktrees.
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DEFAULT = REPO_ROOT / "freshie" / "inventory.sqlite"
DOLT_PARENT = REPO_ROOT / "freshie" / "dolt"
DOLT_DB_NAME = "freshie"  # directory name == Dolt SQL database name
GRADES_CSV = REPO_ROOT / "freshie" / "grades.csv"
GRADE_HISTOGRAM = REPO_ROOT / "freshie" / "grade-histogram.json"

DEFAULT_ORG = os.environ.get("DOLTHUB_ORG", "jeremylongshore")
DEFAULT_REPO = "freshie-inventory"
CREDS_ENDPOINT = "doltremoteapi.dolthub.com:443"

SKIP_TABLES = frozenset({"sqlite_sequence"})

# Explicit export ALLOWLIST — the intended CMDB tables ONLY, enumerated from
# the schema-creation code (rebuild-inventory.py RUN_ID_TABLES + NPM_TABLES,
# validate-skills-schema.py --populate-db compliance tables + forge_proofs,
# plus the discovery_runs registry). 51 tables, matching freshie/README.md.
# inventory.sqlite is a shared local runtime file that other tools can drop
# stray tables into; only tables named here may reach the public DoltHub
# record. An unknown table is a HARD FAILURE (mirrors the BLOB hard-fail
# philosophy) — extend this list deliberately when a legitimate CMDB table
# is added.
EXPORT_ALLOWLIST = frozenset({
    # run registry + eval proofs
    "discovery_runs",
    "forge_proofs",
    # validator --populate-db compliance tables
    "skill_compliance",
    "agent_compliance",
    "plugin_compliance",
    # rebuild-inventory.py RUN_ID_TABLES
    "packs",
    "plugins",
    "skills",
    "plugin_companions",
    "pack_metadata",
    "frontmatter_fields",
    "frontmatter_values",
    "frontmatter_shapes",
    "plugin_fields",
    "plugin_values",
    "plugin_shapes",
    "skill_files",
    "skill_structure_shapes",
    "unique_filenames",
    "unique_subdirs",
    "unique_extensions",
    "content_signals",
    "pack_aggregates",
    "command_files",
    "agent_files",
    "duplicate_files",
    "cross_references",
    "anomalies",
    "restructure_observations",
    "field_registry",
    "root_files",
    "scripts",
    "validators",
    "validator_checks",
    "docs",
    "ci_workflows",
    "marketplace_catalog",
    "planned_skills",
    "root_skills_files",
    "skill_database_vendors",
    "plugin_templates",
    # rebuild-inventory.py NPM_TABLES
    "npm_discovery_runs",
    "npm_dist_tags",
    "npm_download_stats",
    "npm_fetch_log",
    "npm_package_dependencies",
    "npm_packages",
    "npm_publish_history_summary",
    "npm_version_comparisons",
    "npm_versions",
    "repo_package_sources",
})

# j-rig runtime tables — KNOWN contaminants of the local inventory.sqlite.
# j-rig creates its own run tables inside whatever --db it is given (the
# blessed eval path, scripts/run-jrig-eval.sh, uses a /dev/shm scratch DB
# precisely to avoid this), but the tables leaked into the tracked inventory
# DB before the allowlist existed. Excluded from export GOING FORWARD only:
# DoltHub history for runs <= 9.1 already carries these tables, and Dolt
# history is never rewritten, so they linger there as inert cruft. This set
# is the full table list of @intentsolutions/jrig-cli's recorder schema.
JRIG_RUNTIME_TABLES = frozenset({
    "runs",
    "run_summaries",
    "skill_versions",
    "criterion_results",
    "artifacts",
    "skill_usage_events",
    "skill_human_reviews",
})

TYPE_MAP = {
    "INTEGER": "BIGINT",
    "REAL": "DOUBLE",
    "TIMESTAMP": "DATETIME(6)",
    "TEXT": "LONGTEXT",
}
VARCHAR_PK_MAX = 255
TEXT_INDEX_PREFIX = 255

# JSON-bearing TEXT columns that get per-row MD5 byte verification.
# PK column names are discovered from introspection at runtime.
JSON_CHECKSUM_COLUMNS = [
    ("marketplace_catalog", "raw_json"),
    ("ci_workflows", "jobs_json"),
    ("validators", "checks_json"),
]

GC_EVERY_N_SYNCS = 5
GC_SIZE_FACTOR = 2.0
INSERT_BATCH_SIZE = 500
FLOAT_REL_TOL = 1e-9

CANARY_TABLE = "_sync_canary"


class SyncError(Exception):
    """Fatal sync failure (translation, gate, or environment)."""


class PushError(Exception):
    """Push failed after local commit succeeded — history is single-copy."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    print(f"[dolt-sync] {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True,
        input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, check=check,
        input=input_text, capture_output=True, text=True,
    )


def dolt(args: list[str], repo: Path, check: bool = True,
         input_text: str | None = None) -> subprocess.CompletedProcess:
    return run(["dolt", *args], cwd=repo, check=check, input_text=input_text)


def dolt_csv_query(repo: Path, sql: str) -> list[list[str]]:
    """Run a query in the Dolt repo, return parsed CSV rows (minus header).

    Parses the raw stdout stream (not splitlines) so quoted multi-line
    fields survive intact.
    """
    proc = dolt(["sql", "-r", "csv", "-q", sql], repo)
    rows = list(csv.reader(io.StringIO(proc.stdout)))
    return rows[1:] if rows else []


# ---------------------------------------------------------------------------
# Schema introspection + translation (pure — unit-tested)
# ---------------------------------------------------------------------------


def introspect_schema(conn: sqlite3.Connection) -> dict[str, dict]:
    """Read tables, columns, PKs, and indexes from a SQLite connection.

    Returns {table: {"columns": [(name, type, notnull, dflt, pk_ordinal)],
                     "indexes": [{"name", "unique", "origin", "cols"}]}}
    """
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        if r[0] not in SKIP_TABLES
    ]
    schema: dict[str, dict] = {}
    for t in tables:
        cols = [
            (r[1], r[2], bool(r[3]), r[4], r[5])
            for r in conn.execute(f'PRAGMA table_info("{t}")')
        ]
        indexes = []
        for idx_row in conn.execute(f'PRAGMA index_list("{t}")'):
            name, unique, origin = idx_row[1], bool(idx_row[2]), idx_row[3]
            icols = [r[2] for r in conn.execute(f'PRAGMA index_info("{name}")')]
            indexes.append(
                {"name": name, "unique": unique, "origin": origin, "cols": icols}
            )
        schema[t] = {"columns": cols, "indexes": indexes}
    return schema


def filter_export_tables(tables: list[str]) -> tuple[list[str], list[str]]:
    """Split introspected table names into (allowed, excluded_contaminants).

    Allowed = the explicit EXPORT_ALLOWLIST (the intended CMDB tables).
    Excluded = JRIG_RUNTIME_TABLES, the known j-rig contamination — logged
    and skipped so it never reaches the public record again (runs <= 9.1 on
    DoltHub already carry it; going-forward exclusion only, no history
    rewrite). ANY other table is a hard failure, mirroring the BLOB
    hard-fail philosophy: an unreviewed table must never be published.
    """
    allowed: list[str] = []
    contaminants: list[str] = []
    unknown: list[str] = []
    for t in tables:
        if t in EXPORT_ALLOWLIST:
            allowed.append(t)
        elif t in JRIG_RUNTIME_TABLES:
            contaminants.append(t)
        else:
            unknown.append(t)
    if unknown:
        raise SyncError(
            f"unknown table(s) in the source DB: {', '.join(sorted(unknown))} — "
            f"not in EXPORT_ALLOWLIST. dolt-sync publishes to the PUBLIC DoltHub "
            f"record, so only explicitly allowlisted CMDB tables are exported. "
            f"If this is a legitimate new CMDB table, add it to EXPORT_ALLOWLIST "
            f"in freshie/scripts/dolt-sync.py deliberately; if a tool dropped a "
            f"runtime table into inventory.sqlite, remove it (or extend "
            f"JRIG_RUNTIME_TABLES for j-rig schema changes)."
        )
    return allowed, contaminants


def translate_column_type(table: str, col: str, sqlite_type: str, is_pk: bool) -> str:
    """Map one SQLite column type to the Dolt/MySQL dialect."""
    declared = (sqlite_type or "").strip().upper()
    if "BLOB" in declared:
        raise SyncError(f"{table}.{col}: BLOB columns are not supported — hard fail")
    if declared not in TYPE_MAP:
        raise SyncError(
            f"{table}.{col}: unmapped SQLite type {sqlite_type!r} — extend TYPE_MAP deliberately"
        )
    if declared == "TEXT" and is_pk:
        return f"VARCHAR({VARCHAR_PK_MAX})"
    return TYPE_MAP[declared]


def translate_default(dflt: str, mysql_type: str) -> str:
    """Carry a SQLite DEFAULT into MySQL dialect (precision-matched CURRENT_TIMESTAMP)."""
    if dflt.upper() == "CURRENT_TIMESTAMP" and mysql_type == "DATETIME(6)":
        return "CURRENT_TIMESTAMP(6)"
    return dflt


def scan_type_violations(conn: sqlite3.Connection,
                         schema: dict[str, dict]) -> dict[tuple[str, str], int]:
    """Find columns whose stored data violates their declared type.

    SQLite typing is advisory — a declared-INTEGER column can hold TEXT
    (e.g. YAML-comment cruft captured by the scanner). Dolt's typed columns
    reject such rows, and the system of record must hold what SQLite
    actually holds, so violating non-PK columns are widened to LONGTEXT.
    Returns {(table, column): violating_row_count}. A violation on a PK
    column is a hard failure (widening a key would change identity).
    """
    checks = {
        "INTEGER": "typeof(\"{c}\") NOT IN ('integer', 'null')",
        "REAL": "typeof(\"{c}\") NOT IN ('real', 'integer', 'null')",
        # Stored timestamps are ISO-8601 text; anything not shaped like a
        # datetime cannot enter DATETIME(6).
        "TIMESTAMP": (
            "\"{c}\" IS NOT NULL AND \"{c}\" NOT GLOB "
            "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9][T ]"
            "[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*'"
        ),
    }
    violations: dict[tuple[str, str], int] = {}
    for table, info in schema.items():
        for name, ctype, _notnull, _dflt, pk_ord in info["columns"]:
            declared = (ctype or "").strip().upper()
            if declared not in checks:
                continue
            predicate = checks[declared].format(c=name)
            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE {predicate}'
            ).fetchone()[0]
            if count:
                if pk_ord > 0:
                    raise SyncError(
                        f"{table}.{name}: {count} rows violate the declared "
                        f"{declared} type on a PRIMARY KEY column — cannot widen a key"
                    )
                violations[(table, name)] = count
    return violations


def build_create_table(table: str, info: dict,
                       widen: frozenset[tuple[str, str]] = frozenset()) -> str:
    """Emit the translated CREATE TABLE statement for one table."""
    cols = info["columns"]
    pk_cols = [c[0] for c in sorted((c for c in cols if c[4] > 0), key=lambda c: c[4])]
    type_by_col: dict[str, str] = {}
    lines: list[str] = []
    for name, ctype, notnull, dflt, pk_ord in cols:
        if (table, name) in widen:
            mysql_type = "LONGTEXT"
        else:
            mysql_type = translate_column_type(table, name, ctype, pk_ord > 0)
        type_by_col[name] = mysql_type
        line = f"  `{name}` {mysql_type}"
        if notnull:
            line += " NOT NULL"
        # A widened column drops its DEFAULT: literal defaults are not valid
        # on TEXT-class columns in the MySQL dialect, and all values arrive
        # explicitly from the pump anyway.
        if dflt is not None and (table, name) not in widen:
            line += f" DEFAULT {translate_default(dflt, mysql_type)}"
        lines.append(line)
    if pk_cols:
        lines.append("  PRIMARY KEY (" + ", ".join(f"`{c}`" for c in pk_cols) + ")")
    uniq_n = 0
    for idx in info["indexes"]:
        if idx["origin"] == "pk":
            continue  # covered by the PRIMARY KEY clause
        col_list = ", ".join(f"`{c}`" for c in idx["cols"])
        if idx["unique"]:
            # sqlite autoindex names (sqlite_autoindex_t_N) are not portable;
            # emit a clean deterministic name. TEXT columns stay LONGTEXT —
            # Dolt indexes TEXT natively.
            uniq_n += 1
            name = (
                f"uniq_{table}_{uniq_n}"
                if idx["name"].startswith("sqlite_autoindex")
                else idx["name"]
            )
            lines.append(f"  UNIQUE KEY `{name}` ({col_list})")
        else:
            # Non-unique index: LONGTEXT columns need a prefix length.
            parts = [
                f"`{c}`({TEXT_INDEX_PREFIX})" if type_by_col.get(c) == "LONGTEXT" else f"`{c}`"
                for c in idx["cols"]
            ]
            lines.append(f"  KEY `{idx['name']}` ({', '.join(parts)})")
    return f"CREATE TABLE `{table}` (\n" + ",\n".join(lines) + "\n);"


def text_pk_guards(schema: dict[str, dict]) -> list[tuple[str, str]]:
    """(table, column) pairs that map TEXT → VARCHAR and need a length guard."""
    out = []
    for table, info in schema.items():
        for name, ctype, _notnull, _dflt, pk_ord in info["columns"]:
            if pk_ord > 0 and (ctype or "").strip().upper() == "TEXT":
                out.append((table, name))
    return out


def real_columns(schema: dict[str, dict]) -> dict[str, list[str]]:
    """{table: [REAL column names]} for export wrapping + checksum gates."""
    out: dict[str, list[str]] = {}
    for table, info in schema.items():
        cols = [c[0] for c in info["columns"] if (c[1] or "").strip().upper() == "REAL"]
        if cols:
            out[table] = cols
    return out


# ---------------------------------------------------------------------------
# INSERT fallback (pure SQL generation — unit-tested)
# ---------------------------------------------------------------------------


def sql_literal(value) -> str:
    """Render one Python value as a Dolt/MySQL SQL literal (NULL ≠ '')."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)  # repr round-trips doubles exactly
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{escaped}'"
    raise SyncError(f"cannot render SQL literal for {type(value).__name__}")


def build_insert_batches(table: str, col_names: list[str], rows: list[tuple],
                         batch_size: int = INSERT_BATCH_SIZE) -> list[str]:
    """Batched multi-row INSERT statements (the canary-failure fallback pump).

    Never uses `dolt sql -b` — that flag is a documented no-op; statements
    are piped to plain `dolt sql` via stdin.
    """
    cols_sql = ", ".join(f"`{c}`" for c in col_names)
    statements = []
    for i in range(0, len(rows), batch_size):
        values = ",\n".join(
            "(" + ", ".join(sql_literal(v) for v in row) + ")"
            for row in rows[i : i + batch_size]
        )
        statements.append(f"INSERT INTO `{table}` ({cols_sql}) VALUES\n{values};")
    return statements


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------


def acquire_lock(lock_path: Path):
    """Non-blocking flock; returns the open fd (held for process lifetime)."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        log(f"another sync holds {lock_path} — refusing to start")
        sys.exit(2)
    return fd


def refuse_if_server_running(repo: Path) -> None:
    server_lock = repo / ".dolt" / "sql-server.lock"
    if server_lock.exists():
        raise SyncError(
            f"a dolt sql-server holds {server_lock} — stop it before syncing "
            "(concurrent server + CLI writes corrupt the working set)"
        )


# ---------------------------------------------------------------------------
# Dolt repo lifecycle
# ---------------------------------------------------------------------------


def ensure_dolt_identity() -> None:
    for key in ("user.name", "user.email"):
        proc = run(["dolt", "config", "--global", "--get", key], check=False)
        if proc.returncode != 0 or not proc.stdout.strip():
            raise SyncError(
                f"dolt global config missing {key} — run: "
                f"dolt config --global --add {key} <value> "
                "(CI runners need this, or use dolt commit --author)"
            )


def ensure_repo(repo: Path) -> bool:
    """Init the Dolt repo if missing. Returns True if freshly initialized."""
    if (repo / ".dolt").is_dir():
        # Clear any dead prior run. reset --hard alone leaves never-committed
        # tables in the working set; dolt clean removes them.
        dolt(["reset", "--hard"], repo)
        dolt(["clean"], repo)
        return False
    repo.mkdir(parents=True, exist_ok=True)
    dolt(["init"], repo)
    log(f"initialized new Dolt repo at {repo}")
    return True


def head_commit(repo: Path) -> str:
    rows = dolt_csv_query(repo, "SELECT commit_hash FROM dolt_log LIMIT 1")
    return rows[0][0] if rows else ""


def dolt_tables(repo: Path) -> set[str]:
    rows = dolt_csv_query(repo, "SHOW TABLES")
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Canary — proves the NULL vs '' and DATETIME(6) round-trip on every run
# ---------------------------------------------------------------------------


def run_canary(repo: Path, tmpdir: Path) -> bool:
    """Round-trip a (NULL, '', quotes, datetime) fixture through the real
    CSV path. Returns True when the dialect contract holds."""
    fixture_db = tmpdir / "canary.sqlite"
    fixture_csv = tmpdir / "canary.csv"
    if fixture_db.exists():
        fixture_db.unlink()
    conn = sqlite3.connect(fixture_db)
    conn.execute("CREATE TABLE c (id INTEGER PRIMARY KEY, val TEXT, dt TEXT)")
    conn.executemany(
        "INSERT INTO c VALUES (?, ?, ?)",
        [
            (1, None, None),
            (2, "", None),
            (3, "plain", "2026-05-04T00:45:25.457182"),
            (4, 'quotes " and, commas\nand newlines', "2026-01-01T00:00:00"),
        ],
    )
    conn.commit()
    conn.close()

    with open(fixture_csv, "wb") as fh:
        subprocess.run(
            ["sqlite3", "-header", "-csv", str(fixture_db), "SELECT id, val, dt FROM c ORDER BY id;"],
            stdout=fh, check=True,
        )

    dolt(["sql", "-q", f"DROP TABLE IF EXISTS `{CANARY_TABLE}`"], repo)
    dolt(["sql", "-q",
          f"CREATE TABLE `{CANARY_TABLE}` (`id` BIGINT PRIMARY KEY, `val` LONGTEXT, `dt` DATETIME(6))"],
         repo)
    ok = True
    try:
        dolt(["table", "import", "-r", "--file-type", "csv", CANARY_TABLE, str(fixture_csv)], repo)
        rows = dolt_csv_query(
            repo,
            f"SELECT id, (val IS NULL) AS is_null, (val = '') AS is_empty, dt, val "
            f"FROM `{CANARY_TABLE}` ORDER BY id",
        )
        checks = {int(r[0]): r for r in rows}
        ok = (
            len(rows) == 4
            and checks[1][1] == "true"                         # NULL stayed NULL
            and checks[2][1] == "false" and checks[2][2] == "true"  # '' stayed ''
            and checks[3][3] == "2026-05-04 00:45:25.457182"   # microseconds survive
            and checks[4][4] == 'quotes " and, commas\nand newlines'  # quoting survives
        )
    except subprocess.CalledProcessError as exc:
        log(f"canary import failed: {exc.stderr}")
        ok = False
    finally:
        dolt(["sql", "-q", f"DROP TABLE IF EXISTS `{CANARY_TABLE}`"], repo)
    return ok


# ---------------------------------------------------------------------------
# Pump
# ---------------------------------------------------------------------------


def export_table_csv(db_path: Path, table: str, columns: list[str],
                     wrap_real: list[str], out_csv: Path) -> None:
    """Export one table via the sqlite3 CLI CSV emitter (the verified dialect).

    REAL columns are exported through printf('%.17g') so doubles round-trip
    bit-exactly (the CLI's default %!.15g can drop the last ulp); the CASE
    guard keeps NULLs as NULLs (sqlite printf would render NULL as 0).
    """
    select_parts = []
    for name in columns:
        if name in wrap_real:
            select_parts.append(
                f"CASE WHEN \"{name}\" IS NULL THEN NULL "
                f"ELSE printf('%.17g', \"{name}\") END AS \"{name}\""
            )
        else:
            select_parts.append(f'"{name}"')
    sql = f'SELECT {", ".join(select_parts)} FROM "{table}";'
    with open(out_csv, "wb") as fh:
        subprocess.run(["sqlite3", "-header", "-csv", str(db_path), sql], stdout=fh, check=True)


def table_has_empty_strings(conn: sqlite3.Connection, table: str,
                            text_cols: list[str]) -> bool:
    for col in text_cols:
        row = conn.execute(
            f'SELECT 1 FROM "{table}" WHERE "{col}" = \'\' LIMIT 1'
        ).fetchone()
        if row:
            return True
    return False


def pump_table_inserts(conn: sqlite3.Connection, repo: Path, table: str,
                       columns: list[str]) -> None:
    """Deterministic fallback pump: DELETE + batched INSERTs via stdin."""
    col_list = ", ".join('"{}"'.format(c) for c in columns)
    rows = conn.execute(f'SELECT {col_list} FROM "{table}"').fetchall()
    statements = [f"DELETE FROM `{table}`;"]
    statements.extend(build_insert_batches(table, columns, rows))
    dolt(["sql"], repo, input_text="\n".join(statements))


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def gate_row_counts(conn: sqlite3.Connection, repo: Path, tables: list[str]) -> None:
    for t in tables:
        want = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        got_rows = dolt_csv_query(repo, f"SELECT COUNT(*) FROM `{t}`")
        got = int(got_rows[0][0])
        if want != got:
            raise SyncError(f"row-count parity failed on {t}: sqlite={want} dolt={got}")
    log(f"gate: row-count parity OK across {len(tables)} tables")


def gate_real_checksums(conn: sqlite3.Connection, repo: Path,
                        reals: dict[str, list[str]]) -> None:
    for table, cols in reals.items():
        for col in cols:
            w_cnt, w_sum = conn.execute(
                f'SELECT COUNT("{col}"), COALESCE(SUM("{col}"), 0.0) FROM "{table}"'
            ).fetchone()
            rows = dolt_csv_query(
                repo,
                f"SELECT COUNT(`{col}`), COALESCE(SUM(`{col}`), 0.0) FROM `{table}`",
            )
            g_cnt, g_sum = int(rows[0][0]), float(rows[0][1])
            if w_cnt != g_cnt or not math.isclose(
                float(w_sum), g_sum, rel_tol=FLOAT_REL_TOL, abs_tol=FLOAT_REL_TOL
            ):
                raise SyncError(
                    f"REAL checksum failed on {table}.{col}: "
                    f"sqlite=({w_cnt},{w_sum}) dolt=({g_cnt},{g_sum})"
                )
    n = sum(len(v) for v in reals.values())
    log(f"gate: float-tolerant checksums OK on {n} REAL columns")


def split_checksum_targets(
    schema: dict[str, dict],
    targets: list[tuple[str, str]] | None = None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """(present, missing) split of the JSON-checksum target list against the
    introspected schema. A missing table is a hard failure in the gate — a
    silently skipped target would let the log claim byte verification that
    never ran (update JSON_CHECKSUM_COLUMNS on a legitimate rename)."""
    targets = JSON_CHECKSUM_COLUMNS if targets is None else targets
    present = [(t, c) for t, c in targets if t in schema]
    missing = [(t, c) for t, c in targets if t not in schema]
    return present, missing


def gate_json_checksums(conn: sqlite3.Connection, repo: Path,
                        schema: dict[str, dict]) -> None:
    present, missing = split_checksum_targets(schema)
    if missing:
        raise SyncError(
            "JSON checksum gate: listed column(s) absent from the source "
            f"schema: {', '.join(f'{t}.{c}' for t, c in missing)} — the gate "
            "refuses to silently skip a target (the log would overclaim what "
            "was verified). Update JSON_CHECKSUM_COLUMNS if the table was "
            "legitimately renamed or removed."
        )
    for table, col in present:
        pk_cols = [
            c[0] for c in sorted(
                (c for c in schema[table]["columns"] if c[4] > 0), key=lambda c: c[4]
            )
        ]
        if len(pk_cols) != 1:
            raise SyncError(f"JSON checksum gate needs a single-column PK on {table}")
        pk = pk_cols[0]
        want: dict[str, str] = {}
        for key, val in conn.execute(f'SELECT "{pk}", "{col}" FROM "{table}"'):
            want[str(key)] = (
                "" if val is None else hashlib.md5(val.encode("utf-8")).hexdigest()
            )
        got: dict[str, str] = {}
        for row in dolt_csv_query(repo, f"SELECT `{pk}`, MD5(`{col}`) FROM `{table}`"):
            got[row[0]] = row[1]
        if want != got:
            diff = {k for k in set(want) | set(got) if want.get(k) != got.get(k)}
            sample = sorted(diff)[:5]
            raise SyncError(
                f"JSON byte checksum failed on {table}.{col}: "
                f"{len(diff)} mismatched rows (sample PKs: {sample})"
            )
    log(f"gate: per-row MD5 byte checksums OK on {len(present)} JSON columns "
        f"({', '.join(f'{t}.{c}' for t, c in present)})")


def gate_varchar_lengths(conn: sqlite3.Connection, guards: list[tuple[str, str]]) -> None:
    for table, col in guards:
        max_len = conn.execute(
            f'SELECT COALESCE(MAX(LENGTH("{col}")), 0) FROM "{table}"'
        ).fetchone()[0]
        if max_len > VARCHAR_PK_MAX:
            raise SyncError(
                f"{table}.{col}: MAX(LENGTH) = {max_len} exceeds VARCHAR({VARCHAR_PK_MAX})"
            )
    log(f"gate: VARCHAR length guard OK on {len(guards)} TEXT primary keys")


# ---------------------------------------------------------------------------
# Tracked compact export — the diffable "skill X went B→A" story
# ---------------------------------------------------------------------------


def latest_graded_run_id(conn: sqlite3.Connection) -> int:
    """The newest run that actually has compliance rows.

    Deliberately MAX(skill_compliance.run_id), NOT MAX(discovery_runs.id):
    if a discovery scan ran but its compliance pass has not, scoping to the
    discovery run would empty the export (and wipe the curated-mirror
    selection downstream). The export reflects the latest COMPLETED grading
    run.
    """
    row = conn.execute("SELECT MAX(run_id) FROM skill_compliance").fetchone()
    return int(row[0] or 0)


def grades_export_rows(conn: sqlite3.Connection, run_id: int) -> list[tuple]:
    """Rows for the tracked grades.csv, scoped to ONE grading run.

    Scoped, not latest-per-skill-across-all-runs: the old cross-run query
    kept a deleted skill's last grade forever (102 ghost rows for skills
    removed from the repo shipped in the runs <= 9 exports, overstating the
    corpus). A skill absent from the latest graded run is absent from the
    export — its disappearance from the git diff IS the story. Downstream is
    safe: promote-to-curated.py already drops rows whose source dir is gone,
    and every ghost path was verified absent from disk at cutover
    (2026-07-14), so the curated selection is unchanged by the scoping.
    """
    return conn.execute(
        """
        SELECT skill_path, grade, score
        FROM skill_compliance
        WHERE run_id = ?
        ORDER BY skill_path
        """,
        (run_id,),
    ).fetchall()


def write_grades_export(conn: sqlite3.Connection, run_id: int) -> None:
    # No run_id column in the CSV rows on purpose: it would change on every
    # row every sync, drowning the grade-movement diff this file exists to
    # tell. The run_id the rows came from lives in grade-histogram.json.
    rows = grades_export_rows(conn, run_id)
    with open(GRADES_CSV, "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["skill_path", "grade", "score"])
        writer.writerows(rows)

    histogram: dict[str, int] = {}
    for _, grade, _ in rows:
        key = grade if grade else "ungraded"
        histogram[key] = histogram.get(key, 0) + 1
    payload = {
        "run_id": run_id,
        "total": len(rows),
        "grades": {k: histogram[k] for k in sorted(histogram)},
    }
    GRADE_HISTOGRAM.write_text(json.dumps(payload, indent=2) + "\n")
    log(f"wrote {GRADES_CSV.name} ({len(rows)} skills) + {GRADE_HISTOGRAM.name}")


# ---------------------------------------------------------------------------
# Commit / tag / push
# ---------------------------------------------------------------------------


def commit_and_tag(repo: Path, run_id: int, source_sha: str) -> tuple[bool, str | None]:
    """Commit the working set and tag run-<N>. Returns (committed, tag_name)."""
    before = head_commit(repo)
    dolt(["add", "-A"], repo)
    msg = f"freshie sync: run {run_id} from inventory.sqlite ({source_sha})"
    dolt(["commit", "--skip-empty", "-m", msg], repo)
    after = head_commit(repo)
    committed = after != before

    tag_base = f"run-{run_id}"
    existing = {
        r[0]: r[1] for r in dolt_csv_query(repo, "SELECT tag_name, tag_hash FROM dolt_tags")
    }

    if tag_base in existing and existing[tag_base] == after:
        # Retry after a crash between tag and push — the tag already tells the truth.
        return committed, tag_base

    if committed:
        tag = tag_base
        suffix = 0
        while tag in existing:
            # run N was already tagged on an older commit (e.g. compliance
            # re-populated without a new discovery run) — keep history honest
            # with a suffixed tag instead of failing the sync.
            suffix += 1
            tag = f"{tag_base}.{suffix}"
        if suffix:
            log(f"tag {tag_base} exists on an older commit — tagging {tag} instead")
        dolt(["tag", tag, "-m", msg], repo)
        return committed, tag

    # Nothing changed this run. Only tag HEAD if it demonstrably carries run N
    # (crash-between-commit-and-tag retry); otherwise a tag would lie.
    if tag_base not in existing:
        head_msg_rows = dolt_csv_query(repo, "SELECT message FROM dolt_log LIMIT 1")
        head_msg = head_msg_rows[0][0] if head_msg_rows else ""
        if f"run {run_id} " in head_msg or head_msg.endswith(f"run {run_id}"):
            dolt(["tag", tag_base, "-m", msg], repo)
            return committed, tag_base
        log(f"no data changes and HEAD is not run {run_id} — skipping tag")
        return committed, None
    return committed, tag_base


def ensure_remote(repo: Path, org: str, repo_name: str) -> None:
    proc = dolt(["remote", "-v"], repo)
    target = f"{org}/{repo_name}"
    for line in proc.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "origin":
            if target not in line:
                raise SyncError(
                    f"remote 'origin' points elsewhere ({line.strip()}); expected {target}"
                )
            return
    dolt(["remote", "add", "origin", target], repo)
    log(f"added remote origin → {target}")


def push_auth_args(env: dict | None = None) -> list[str]:
    """CI credential path: `dolt push --user <name>` reads the password from
    DOLT_REMOTE_PASSWORD. Active only when BOTH DOLT_REMOTE_USER and
    DOLT_REMOTE_PASSWORD are set; otherwise the interactive `dolt login`
    creds path (check_creds) is used."""
    env = os.environ if env is None else env
    user = env.get("DOLT_REMOTE_USER")
    if user and env.get("DOLT_REMOTE_PASSWORD"):
        return ["--user", user]
    return []


def check_creds() -> None:
    proc = run(["dolt", "creds", "check", "--endpoint", CREDS_ENDPOINT], check=False)
    if "Success" not in proc.stdout:
        raise PushError(
            "dolt creds check failed — no valid DoltHub key. "
            "Run `dolt creds ls` / `dolt login`, or in CI set "
            "DOLT_REMOTE_USER=<name> + DOLT_REMOTE_PASSWORD=<api token> "
            "(the push then runs `dolt push --user <name>` automatically).\n"
            + proc.stdout + proc.stderr
        )


def remote_run_tags(org: str, repo_name: str) -> set[str] | None:
    """Best-effort read of the remote's tag names via the DoltHub SQL API
    (read-only — keeps the exporter strictly one-way). None = inconclusive
    (network/parse failure); callers must then skip tag reconciliation
    rather than assume an empty remote."""
    url = (
        f"https://www.dolthub.com/api/v1alpha1/{org}/{repo_name}/main"
        f"?q=SELECT+tag_name+FROM+dolt_tags"
    )
    proc = run(["curl", "-s", "--max-time", "15", url], check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return None
    return {r["tag_name"] for r in rows if isinstance(r, dict) and r.get("tag_name")}


def stranded_tags(local: set[str], remote: set[str], current: str | None) -> list[str]:
    """Local run-* tags missing from the remote, excluding the current tag
    (pushed separately). These are tags stranded by a prior failed push —
    push() heals them on the next successful sync so `AS OF 'run-N'` works
    against the public record for every run."""
    return sorted(
        t for t in local
        if t.startswith("run-") and t not in remote and t != current
    )


def check_repo_exists(org: str, repo_name: str) -> bool | None:
    """Best-effort DoltHub existence probe. None = inconclusive (network)."""
    url = f"https://www.dolthub.com/api/v1alpha1/{org}/{repo_name}"
    proc = run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "--max-time", "10", url], check=False)
    code = proc.stdout.strip()
    if proc.returncode != 0 or not code.isdigit():
        return None
    return code == "200"


def push(repo: Path, org: str, repo_name: str, tag: str | None) -> None:
    """Gate order: remote → creds → repo-exists → push main → push tag(s).

    Besides the current run's tag, any local run-* tag missing from the
    remote is pushed too — a push failure (exit 3) leaves the run tagged
    locally only, and the next inventory cycle would otherwise never revisit
    it (push used to send only the CURRENT tag, permanently stranding the
    missed one)."""
    ensure_remote(repo, org, repo_name)
    auth = push_auth_args()
    if auth:
        log("using DOLT_REMOTE_USER + DOLT_REMOTE_PASSWORD for push auth "
            "(CI env-var path; skipping `dolt creds check`)")
    else:
        check_creds()
    exists = check_repo_exists(org, repo_name)
    create_help = (
        f"create the database on DoltHub first (push never auto-creates): "
        f"https://www.dolthub.com/new — owner {org!r}, name {repo_name!r}, "
        f"visibility public. Scripted (per dolthub.com/docs/products/dolthub/api): "
        f"POST https://www.dolthub.com/api/v1alpha1/database with header "
        f"'authorization: token <api-token>' and body "
        f'{{"ownerName":"{org}","repoName":"{repo_name}","visibility":"public"}}. '
        f"Then re-run this sync."
    )
    if exists is False:
        raise PushError(f"DoltHub database {org}/{repo_name} does not exist — {create_help}")
    if exists is None:
        log("DoltHub existence probe inconclusive (network) — attempting push anyway")

    tags_to_push = [tag] if tag else []
    remote = remote_run_tags(org, repo_name)
    if remote is None:
        log("remote tag probe inconclusive (network) — pushing only the "
            "current tag; stranded tags (if any) heal on a later sync")
    else:
        local = {
            r[0] for r in dolt_csv_query(repo, "SELECT tag_name FROM dolt_tags")
        }
        for missing in stranded_tags(local, remote, tag):
            log(f"local tag {missing} is missing from the remote (stranded by "
                f"a prior failed push) — pushing it now")
            tags_to_push.append(missing)

    refs = ["main"]
    for t in tags_to_push:
        # Tags do NOT ride along on a branch push; use the explicit refspec
        # form so the tag lands as a tag (a bare name can label the transfer
        # as a branch).
        refs.append(f"refs/tags/{t}:refs/tags/{t}")
    for ref in refs:
        proc = dolt(["push", *auth, "origin", ref], repo, check=False)
        out = proc.stdout + proc.stderr
        if proc.returncode != 0:
            if "PermissionDenied" in out and "Uploading" in out:
                # The classified miss signature: valid creds, repo missing.
                raise PushError(
                    f"push of {ref} rejected with PermissionDenied after upload "
                    f"started — this is the repo-missing signature, not a creds "
                    f"problem. {create_help}\n{out}"
                )
            raise PushError(f"push of {ref} failed:\n{out}")
        log(f"pushed {ref} → {org}/{repo_name}")


# ---------------------------------------------------------------------------
# GC policy
# ---------------------------------------------------------------------------


def dir_size_bytes(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def maybe_gc(repo: Path, state_path: Path, force: bool) -> None:
    state = {"syncs_since_gc": 0, "size_after_gc_bytes": 0}
    if state_path.exists():
        try:
            state.update(json.loads(state_path.read_text()))
        except (json.JSONDecodeError, OSError):
            pass
    state["syncs_since_gc"] = int(state.get("syncs_since_gc", 0)) + 1
    size_now = dir_size_bytes(repo)
    baseline = int(state.get("size_after_gc_bytes", 0)) or size_now
    due = (
        force
        or state["syncs_since_gc"] >= GC_EVERY_N_SYNCS
        or size_now > GC_SIZE_FACTOR * baseline
    )
    if due:
        # Re-check for a live dolt sql-server HERE, not just at lock
        # acquisition: a server started against the repo mid-sync (the sync
        # takes minutes) holds no flock, and `dolt gc` under a live server
        # corrupts its working set. The sync itself already succeeded at this
        # point, so skip gc loudly instead of failing the run — the counter
        # persists, keeping gc due on the next sync.
        server_lock = repo / ".dolt" / "sql-server.lock"
        if server_lock.exists():
            log(f"dolt gc SKIPPED — a dolt sql-server appeared mid-sync "
                f"({server_lock}); gc under a live server corrupts the "
                f"working set. gc stays due for the next sync.")
        else:
            log(f"running dolt gc (syncs_since_gc={state['syncs_since_gc']}, "
                f"size={size_now / 1e6:.0f}MB, baseline={baseline / 1e6:.0f}MB)")
            dolt(["gc"], repo)
            state["syncs_since_gc"] = 0
            state["size_after_gc_bytes"] = dir_size_bytes(repo)
    state_path.write_text(json.dumps(state) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def source_git_sha() -> str:
    proc = run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"], check=False)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    parser.add_argument("--dolt-dir", type=Path, default=DOLT_PARENT / DOLT_DB_NAME)
    parser.add_argument("--org", default=DEFAULT_ORG)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--no-push", action="store_true",
                        help="local sync only (commit + tag, no DoltHub push)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the translated DDL and plan; touch nothing")
    parser.add_argument("--recreate-tables", action="store_true",
                        help="drop + recreate Dolt tables whose schema drifted")
    parser.add_argument("--gc", action="store_true", help="force dolt gc this run")
    args = parser.parse_args()

    if not args.db.exists():
        log(f"source DB not found: {args.db}")
        return 1

    repo: Path = args.dolt_dir
    lock_fd = None
    tmpdir = None
    try:
        if not args.dry_run:
            lock_fd = acquire_lock(repo.parent / ".sync.lock")
            if (repo / ".dolt").is_dir():
                refuse_if_server_running(repo)
            ensure_dolt_identity()

        # Snapshot for read consistency across the whole export.
        shm = Path("/dev/shm")
        tmpdir = Path(tempfile.mkdtemp(
            prefix="dolt-sync-", dir=str(shm) if shm.is_dir() else None
        ))
        snapshot = tmpdir / "inventory-snapshot.sqlite"
        src = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        src.execute("VACUUM INTO ?", (str(snapshot),))
        src.close()
        conn = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)

        schema = introspect_schema(conn)
        allowed, excluded = filter_export_tables(sorted(schema))
        for t in excluded:
            log(f"excluding j-rig runtime table from export: {t} (known "
                f"contaminant — never published going forward; DoltHub runs "
                f"<= 9.1 already carry it and history is not rewritten)")
        schema = {t: schema[t] for t in allowed}
        tables = sorted(schema)
        violations = scan_type_violations(conn, schema)
        widen = frozenset(violations)
        for (t, c), n in sorted(violations.items()):
            log(f"type violation: {t}.{c} has {n} rows breaking its declared "
                f"type — widening to LONGTEXT (SQLite typing is advisory; the "
                f"record keeps what SQLite holds)")
        ddls = {t: build_create_table(t, schema[t], widen) for t in tables}
        # Widened REAL columns are text now — exclude them from the printf
        # export wrapper and the float checksum gate (row-count parity and
        # the import itself still cover them).
        reals = {
            t: [c for c in cols if (t, c) not in widen]
            for t, cols in real_columns(schema).items()
        }
        reals = {t: cols for t, cols in reals.items() if cols}
        guards = text_pk_guards(schema)
        run_id_row = conn.execute("SELECT MAX(id) FROM discovery_runs").fetchone()
        run_id = int(run_id_row[0] or 0)

        if args.dry_run:
            for t in tables:
                print(ddls[t] + "\n")
            log(f"dry run: {len(tables)} tables, run_id={run_id}, "
                f"{sum(len(v) for v in reals.values())} REAL columns, "
                f"{len(guards)} TEXT PKs, {len(widen)} widened columns, "
                f"JSON checks on {[f'{t}.{c}' for t, c in JSON_CHECKSUM_COLUMNS]}")
            return 0

        gate_varchar_lengths(conn, guards)
        ensure_repo(repo)

        canary_ok = run_canary(repo, tmpdir)
        if canary_ok:
            log("canary: NULL/''/DATETIME(6)/quoting round-trip OK — CSV pump")
        else:
            log("canary FAILED — empty-string-bearing tables fall back to INSERT pump")

        existing = dolt_tables(repo)
        for t in tables:
            col_names = [c[0] for c in schema[t]["columns"]]
            if t not in existing:
                dolt(["sql", "-q", ddls[t]], repo)
            elif args.recreate_tables:
                dolt(["sql", "-q", f"DROP TABLE `{t}`"], repo)
                dolt(["sql", "-q", ddls[t]], repo)

            use_insert_fallback = False
            if not canary_ok:
                text_cols = [
                    c[0] for c in schema[t]["columns"]
                    if (c[1] or "").strip().upper() == "TEXT"
                ]
                use_insert_fallback = text_cols and table_has_empty_strings(
                    conn, t, text_cols
                )

            if use_insert_fallback:
                pump_table_inserts(conn, repo, t, col_names)
            else:
                csv_path = tmpdir / f"{t}.csv"
                export_table_csv(snapshot, t, col_names, reals.get(t, []), csv_path)
                if csv_path.stat().st_size == 0:
                    # sqlite3 emits nothing (not even a header) for an empty
                    # table, and dolt refuses an empty file — converge with a
                    # plain DELETE instead.
                    dolt(["sql", "-q", f"DELETE FROM `{t}`"], repo)
                else:
                    proc = dolt(
                        ["table", "import", "-r", "--file-type", "csv", t, str(csv_path)],
                        repo, check=False,
                    )
                    if proc.returncode != 0:
                        raise SyncError(
                            f"import of {t} aborted (schema mismatch is a parity gate — "
                            f"if the SQLite schema legitimately changed, re-run with "
                            f"--recreate-tables):\n{proc.stdout}{proc.stderr}"
                        )
                csv_path.unlink()
        log(f"pumped {len(tables)} tables")

        gate_row_counts(conn, repo, tables)
        gate_real_checksums(conn, repo, reals)
        gate_json_checksums(conn, repo, schema)

        graded_run = latest_graded_run_id(conn)
        if graded_run != run_id:
            log(f"grades export scoped to run {graded_run} (latest run with "
                f"compliance rows; discovery run {run_id} is not graded yet)")
        write_grades_export(conn, graded_run)
        conn.close()

        committed, tag = commit_and_tag(repo, run_id, source_git_sha())
        log(f"commit created: {committed}; tag: {tag or '(none)'}")

        if args.no_push:
            log("--no-push: skipping DoltHub push (history is LOCAL-ONLY until pushed)")
        else:
            push(repo, args.org, args.repo, tag)

        maybe_gc(repo, repo.parent / ".sync-state.json", args.gc)
        log("sync complete")
        return 0

    except PushError as exc:
        log(f"PUSH FAILED (history committed locally but NOT on DoltHub): {exc}")
        return 3
    except SyncError as exc:
        log(f"FAILED: {exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        log(f"FAILED: {' '.join(exc.cmd)} → {exc.stderr or exc.stdout}")
        return 1
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
        if lock_fd is not None:
            os.close(lock_fd)


if __name__ == "__main__":
    sys.exit(main())
