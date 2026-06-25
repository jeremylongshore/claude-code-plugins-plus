#!/usr/bin/env bash
# dep-graph.sh — bead dependency analysis through the dolt-mcp server.
# Surfaces bottlenecks (open issues blocking the most other open work) and any
# direct dependency cycles. Runs SQL via dolt-mcp-client.py.
#
# Usage:  dep-graph.sh                          # uses $DOLT_PORT / $DOLT_DATABASE
#         dep-graph.sh --port 35579 --database beads [--top 10]
#
# Requires: python3, dolt-mcp-server on PATH, a running bd dolt sql-server.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PORT="${DOLT_PORT:-}"; DB="${DOLT_DATABASE:-}"; TOP=10
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --database) DB="$2"; shift 2 ;;
    --top) TOP="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PORT" ] || { echo "error: set --port or DOLT_PORT (see 'bd dolt show')" >&2; exit 2; }
[ -n "$DB" ]   || { echo "error: set --database or DOLT_DATABASE (see 'bd dolt show')" >&2; exit 2; }

q() { python3 "$SCRIPT_DIR/dolt-mcp-client.py" --port "$PORT" --database "$DB" query "$1"; }

echo "# Dependency analysis — database '$DB' (port $PORT)"
echo
echo "## Bottlenecks — open issues blocking the most other OPEN issues (top $TOP)"
q "SELECT b.id AS blocker, b.status, COUNT(*) AS blocking_open, LEFT(b.title,55) AS title
   FROM dependencies d
   JOIN issues b ON b.id=d.depends_on_id
   JOIN issues blocked ON blocked.id=d.issue_id
   WHERE d.type='blocks' AND b.status<>'closed' AND blocked.status<>'closed'
   GROUP BY b.id, b.status, b.title
   ORDER BY blocking_open DESC
   LIMIT ${TOP}"

echo
echo "## Direct cycles — A blocks B and B blocks A (should be none)"
q "SELECT d1.issue_id AS a, d1.depends_on_id AS b
   FROM dependencies d1
   JOIN dependencies d2 ON d2.issue_id=d1.depends_on_id AND d2.depends_on_id=d1.issue_id
   WHERE d1.type='blocks' AND d2.type='blocks' AND d1.issue_id < d1.depends_on_id"
