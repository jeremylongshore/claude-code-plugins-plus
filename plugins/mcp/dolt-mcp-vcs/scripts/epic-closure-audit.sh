#!/usr/bin/env bash
# epic-closure-audit.sh — find OPEN epics whose entire child set is already closed
# (the "stale-open epic" drift: every parent-child child is closed but the epic
# itself is still open, so its GitHub/Plane cluster issue never gets the close
# fan-out). Runs the audit SQL through the dolt-mcp server via dolt-mcp-client.py.
#
# Usage:  epic-closure-audit.sh                 # uses $DOLT_PORT / $DOLT_DATABASE
#         DOLT_PORT=35579 DOLT_DATABASE=beads epic-closure-audit.sh
#         epic-closure-audit.sh --port 35579 --database beads
#
# Requires: python3, dolt-mcp-server on PATH, a running bd dolt sql-server.
# Exit: 0 ok (whether or not drift was found) · non-zero on connection/tool error.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PORT="${DOLT_PORT:-}"; DB="${DOLT_DATABASE:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --database) DB="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PORT" ] || { echo "error: set --port or DOLT_PORT (see 'bd dolt show')" >&2; exit 2; }
[ -n "$DB" ]   || { echo "error: set --database or DOLT_DATABASE (see 'bd dolt show')" >&2; exit 2; }

read -r -d '' SQL <<'EOSQL' || true
SELECT e.id AS epic, COUNT(d.issue_id) AS children,
       SUM(CASE WHEN c.status='closed' THEN 1 ELSE 0 END) AS closed,
       LEFT(e.title,60) AS title
FROM issues e
JOIN dependencies d ON d.depends_on_id=e.id AND d.type='parent-child'
JOIN issues c ON c.id=d.issue_id
WHERE e.issue_type='epic' AND e.status<>'closed'
GROUP BY e.id, e.title
HAVING children>0 AND closed=children
ORDER BY children DESC
EOSQL

echo "# Epic-closure drift audit — database '$DB' (port $PORT)"
echo "# OPEN epics whose every parent-child child is already closed (candidates to close)."
OUT="$(python3 "$SCRIPT_DIR/dolt-mcp-client.py" --port "$PORT" --database "$DB" query "$SQL")"
echo "$OUT"
# Rows beyond the header/separator => drift found
if [ "$(printf '%s\n' "$OUT" | sed '1,2d' | grep -c .)" -eq 0 ]; then
  echo "# ✓ No stale-open-epic drift found."
else
  echo "# ⚠ Above epics have all children closed — close each via: bd-sync close <epic> --also-close-gh"
fi
