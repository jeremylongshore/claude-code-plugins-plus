#!/usr/bin/env bash
# pre-optimize-check.sh — before a manual OPTIMIZE, check whether the table has
# auto-compaction enabled and would collide (bead ehoq / pain D01).
#
# The trap: Databricks silently enables auto-compaction
# (delta.autoOptimize.autoCompact) on any table touched by MERGE/UPDATE/DELETE, or
# it can be on globally via spark.databricks.delta.autoCompact.enabled. A manual
# OPTIMIZE run against such a table races the background compaction and fails with
# ConcurrentDeleteDeleteException. This probe reads the table properties BEFORE you
# run OPTIMIZE and tells you whether a manual run is safe or a collision risk.
#
# Usage:
#   pre-optimize-check.sh --table main.sales.orders          # live (needs CLI + warehouse)
#   pre-optimize-check.sh --table main.sales.orders --props-file props.tsv
#       # advisory mode: props.tsv is a pasted `SHOW TBLPROPERTIES` result
#
# Exit: 0 SAFE to OPTIMIZE · 1 COLLISION RISK (auto-compact on) · 2 bad usage ·
#       3 could not determine (no CLI/warehouse and no --props-file) — treated as
#         "cannot confirm safe", so caller should not blindly OPTIMIZE.
set -euo pipefail

TABLE=""; PROPS_FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --table) TABLE="$2"; shift 2 ;;
    --props-file) PROPS_FILE="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$TABLE" ] || { echo "error: --table <catalog.schema.table> is required" >&2; exit 2; }

# Return the table's property text (from --props-file, else a live SHOW TBLPROPERTIES).
get_props() {
  if [ -n "$PROPS_FILE" ]; then
    cat "$PROPS_FILE"
    return 0
  fi
  local wh="${DATABRICKS_WAREHOUSE_ID:-}"
  if ! command -v databricks >/dev/null 2>&1 || [ -z "$wh" ]; then
    return 3
  fi
  local body
  body=$(printf '{"warehouse_id":"%s","statement":"SHOW TBLPROPERTIES %s","wait_timeout":"20s"}' "$wh" "$TABLE")
  databricks api post /api/2.0/sql/statements --json "$body" 2>/dev/null \
    | jq -r '.result.data_array[]? | @tsv' 2>/dev/null || return 3
}

PROPS="$(get_props)" || { echo "UNKNOWN: could not read TBLPROPERTIES for $TABLE (no CLI/warehouse and no --props-file)" >&2; exit 3; }

# Table-level auto-compact / optimizeWrite properties.
AUTOCOMPACT=$(printf '%s\n' "$PROPS" | grep -iE 'delta\.autoOptimize\.autoCompact' | grep -ic 'true' || true)
# Session/global default (only knowable if the caller pasted it in; note if absent).
GLOBAL=$(printf '%s\n' "$PROPS" | grep -iE 'spark\.databricks\.delta\.autoCompact\.enabled' | grep -ic 'true' || true)

if [ "$AUTOCOMPACT" -gt 0 ] || [ "$GLOBAL" -gt 0 ]; then
  echo "COLLISION RISK: auto-compaction is ENABLED on $TABLE."
  echo "  A manual OPTIMIZE can race the background auto-compaction and fail with"
  echo "  ConcurrentDeleteDeleteException. Options:"
  echo "  - Do NOT run manual OPTIMIZE (let auto-compaction handle it), OR"
  echo "  - Disable auto-compaction first:"
  echo "      ALTER TABLE $TABLE SET TBLPROPERTIES (delta.autoOptimize.autoCompact = false);"
  echo "    run OPTIMIZE, then re-enable — and serialize against any concurrent writers."
  exit 1
fi

echo "SAFE: no table-level auto-compaction detected on $TABLE — a manual OPTIMIZE is"
echo "unlikely to collide. (If auto-compact is on GLOBALLY via a session config not"
echo "shown here, disable it for this session before OPTIMIZE.)"
exit 0
