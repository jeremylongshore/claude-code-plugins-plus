#!/usr/bin/env python3
"""streaming-guard-hook.py — PreToolUse guard that blocks a genuinely-irreversible
Databricks operation on a table that ACTIVE streaming consumers still read
(databricks-streaming-guardian, AP02/AP06).

Three operations are irreversible against a streamed-from Delta table:
  DROP TABLE            — the checkpoint's source is gone; every consumer dies.
  CREATE OR REPLACE     — mints a NEW table UUID even at the same name, so every
                          streaming checkpoint fails with
                          DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE (pain D12).
  VACUUM                — deletes the exact files a streaming checkpoint pins to,
                          causing DELTA_FILE_NOT_FOUND_DETAILED (pain D03) and
                          breaking time travel past retention (D07).

This hook reads the PreToolUse event, and ONLY when the Bash command clearly runs
one of those three ops against a named table, it asks
`system.streaming.query_progress` whether any stream is actively reading that
table. If so it DENIES with a clear message; otherwise it allows.

DESIGN — precision over reach (false-positive blocking is a serious defect):
  * Non-Bash tools, and Bash commands that do not clearly match one of the three
    ops on a resolvable table, are ALLOWED with no output (fast path).
  * The consumer check FAILS OPEN: if the Databricks CLI / warehouse is not
    available, or the check errors, the hook ALLOWS (with a stderr warning) — it
    never blocks on an unverifiable check.
  * It blocks ONLY when it positively confirms an active consumer.

Protocol: reads the event JSON on stdin, writes a PreToolUse decision JSON on
stdout, exits 0. (A hook that errors is treated as non-blocking by Claude Code.)
"""

import json
import os
import re
import shutil
import subprocess
import sys

# Irreversible-op patterns. Each captures the target table identifier. Deliberately
# strict: a clear op keyword + a table reference. Anything ambiguous does not match
# (so we never block a command we did not clearly understand).
TABLE = r"([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*){0,2}|`[^`]+`(?:\.`[^`]+`){0,2})"
OP_PATTERNS = [
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?" + TABLE, re.IGNORECASE), "D12"),
    ("CREATE OR REPLACE TABLE", re.compile(r"\bCREATE\s+OR\s+REPLACE\s+TABLE\s+" + TABLE, re.IGNORECASE), "D12"),
    ("VACUUM", re.compile(r"\bVACUUM\s+" + TABLE, re.IGNORECASE), "D03/D07"),
]

PAIN_MSG = {
    "D12": (
        "CREATE OR REPLACE / DROP mints or removes the table identity a streaming "
        "checkpoint pins to → every active consumer fails with "
        "DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE. Use ALTER / in-place "
        "changes, or stop the consumers and reset their checkpoints deliberately."
    ),
    "D03/D07": (
        "VACUUM deletes the exact files a streaming checkpoint references "
        "(DELTA_FILE_NOT_FOUND_DETAILED) and breaks time travel past retention. "
        "Align VACUUM retention with the consumers' checkpoint lag, or stop them first."
    ),
}


# A destructive op only counts when it runs through an actual SQL-execution
# surface — the Statement Execution API, the `databricks sql` CLI, or spark.sql(…)
# — or when the whole command IS raw SQL (starts with the verb). This is what
# keeps `git commit -m 'drop table feature'` and `echo 'drop table x'` from ever
# being classified as a real DROP (precision-over-reach; false blocks are a defect).
SQL_CONTEXT = re.compile(r"/sql/statements|databricks\s+sql\b|spark\.sql\s*\(", re.IGNORECASE)
RAW_SQL_START = re.compile(r"^\s*(?:DROP|CREATE|VACUUM)\b", re.IGNORECASE)


def _norm_table(raw):
    """Strip backticks; lowercase the bare identifier for comparison."""
    return raw.replace("`", "").strip()


def _has_sql_context(command):
    return bool(SQL_CONTEXT.search(command) or RAW_SQL_START.match(command))


def classify_destructive_op(command):
    """If `command` clearly runs an irreversible op on a table through a SQL
    surface, return (op, table, pain); else None. Pure — the whole precision
    contract is here."""
    if not command or not isinstance(command, str):
        return None
    if not _has_sql_context(command):
        return None
    for op, rx, pain in OP_PATTERNS:
        m = rx.search(command)
        if m:
            return op, _norm_table(m.group(1)), pain
    return None


def active_stream_consumers(table):
    """Return a list of active stream run_ids reading `table`, or None if the check
    could NOT be performed (CLI/warehouse absent, or query failed) — the caller
    must fail OPEN on None, never block on an unverifiable check."""
    wh = os.environ.get("DATABRICKS_WAREHOUSE_ID")
    if not shutil.which("databricks") or not wh:
        return None
    # Newest progress row per run; keep rows still emitting batches (active).
    bare = table.split(".")[-1].lower()
    sql = (
        "SELECT run_id, source_description FROM system.streaming.query_progress "
        "WHERE event_time > now() - INTERVAL 15 MINUTES"
    )
    try:
        proc = subprocess.run(
            [
                "databricks",
                "api",
                "post",
                "/api/2.0/sql/statements",
                "--json",
                json.dumps({"warehouse_id": wh, "statement": sql, "wait_timeout": "20s"}),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return None
        doc = json.loads(proc.stdout or "{}")
        if doc.get("status", {}).get("state") != "SUCCEEDED":
            return None
        rows = doc.get("result", {}).get("data_array", []) or []
        hits = []
        for row in rows:
            run_id = row[0] if row else None
            src = (row[1] or "") if len(row) > 1 else ""
            if table.lower() in src.lower() or bare in src.lower():
                if run_id:
                    hits.append(run_id)
        return sorted(set(hits))
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None


def decide(event):
    """Return a PreToolUse decision dict for the event (allow unless a confirmed
    active consumer of an irreversible-op target)."""
    if event.get("tool_name") != "Bash":
        return _allow()
    command = (event.get("tool_input") or {}).get("command", "")
    hit = classify_destructive_op(command)
    if not hit:
        return _allow()
    op, table, pain = hit
    consumers = active_stream_consumers(table)
    if consumers is None:
        # Unverifiable → fail OPEN (never a false-positive block).
        print(
            f"streaming-guard: could not verify streaming consumers of {table} "
            f"(no Databricks CLI / DATABRICKS_WAREHOUSE_ID) — allowing {op}. "
            f"Verify manually before running an irreversible op.",
            file=sys.stderr,
        )
        return _allow()
    if consumers:
        reason = (
            f"BLOCKED: {op} on `{table}` — {len(consumers)} active streaming "
            f"consumer(s) are reading it (run_ids: {', '.join(consumers[:5])}). " + PAIN_MSG.get(pain, "")
        )
        return _deny(reason)
    return _allow()


def _allow():
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


def _deny(reason):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # No parseable event → do nothing (allow); a broken hook must not block.
        return 0
    decision = decide(event)
    # Only emit on a deny; a bare allow can be silent (fast path).
    if decision["hookSpecificOutput"]["permissionDecision"] == "deny":
        json.dump(decision, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
