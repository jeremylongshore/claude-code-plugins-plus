#!/usr/bin/env bash
# server-health.sh — inventory running `dolt sql-server` processes and flag sprawl.
# bd starts a per-project server on an auto-detected port; over time that becomes
# many servers (one per workspace). This maps each running server to its workspace
# and warns when the count suggests consolidation onto one shared server (:3308 via
# `bd dolt --global`) is warranted.
#
# Usage:  server-health.sh [--warn N]   (default warn threshold: 5 servers)
# Requires: pgrep, /proc (Linux). Read-only — never kills anything.
set -uo pipefail

WARN=5
[ "${1:-}" = "--warn" ] && { WARN="${2:-5}"; }

mapfile -t PIDS < <(pgrep -f 'dolt sql-server' 2>/dev/null || true)
n=0
rows=""
for p in "${PIDS[@]}"; do
  [ -n "$p" ] || continue
  port="$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -oE '\-P [0-9]+' | grep -oE '[0-9]+' || true)"
  [ -n "$port" ] || continue
  cwd="$(readlink "/proc/$p/cwd" 2>/dev/null || echo '?')"
  ws="$(echo "$cwd" | sed 's#'"$HOME"'/##; s#/.beads.*##')"
  rows+="$(printf "%-8s %-8s %s" "$port" "$p" "$ws")"$'\n'
  n=$((n+1))   # counted in the main shell, not a pipe subshell
done
printf "%-8s %-8s %s\n" "PORT" "PID" "WORKSPACE"
[ -n "$rows" ] && printf '%s' "$rows" | sort -n

echo
echo "# $n running dolt sql-server process(es)."
if [ "$n" -gt "$WARN" ]; then
  echo "# ⚠ Sprawl: $n servers > threshold $WARN. Consolidate onto ONE shared server:"
  echo "#     bd config set dolt.shared-server true   # machine-wide"
  echo "#     bd dolt killall                          # per repo (refuses external/other-repo servers)"
  echo "#   The next bd command auto-starts a single server at ~/.beads/shared-server/ on :3308."
else
  echo "# ✓ Server count within threshold ($WARN)."
fi
