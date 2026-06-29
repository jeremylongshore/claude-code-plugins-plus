#!/usr/bin/env bash
# dolt-idle-reaper.sh — gracefully stop idle bd-managed `dolt sql-server`
# processes so they don't accumulate (the "18 sprawled servers" problem).
#
# Safe by design: bd auto-restarts a workspace's dolt server on the next bd
# command, so stopping an idle one is non-destructive — worst case is a ~2s
# respawn latency next time that workspace is used. Data lives in Dolt (durable)
# + the .beads JSONL; stopping a server never loses anything.
#
# "Idle" = the workspace's .beads/ activity files (last-touched, issues.jsonl,
# dolt-server.log — the log updates on every query, so reads count too) have not
# changed in $IDLE_MIN minutes.
#
# Usage:
#   dolt-idle-reaper.sh                 # reap servers idle > IDLE_MIN (default 90)
#   dolt-idle-reaper.sh --dry-run       # show what WOULD be reaped, change nothing
#   IDLE_MIN=120 dolt-idle-reaper.sh    # custom idle threshold
#
# Cron (every 30 min):
#   3,33 * * * * /path/to/dolt-idle-reaper.sh >> ~/.local/state/dolt-reaper/reap.log 2>&1
set -uo pipefail

IDLE_MIN="${IDLE_MIN:-90}"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

LOGDIR="$HOME/.local/state/dolt-reaper"
mkdir -p "$LOGDIR"
LOCK="$LOGDIR/.lock"
exec 9>"$LOCK"
flock -n 9 || { echo "[$(date '+%F %T')] another reaper run is active; skip."; exit 0; }

now=$(date +%s)
idle_secs=$(( IDLE_MIN * 60 ))
reaped=0 kept=0 total=0

# Resolve a server process's workspace root from its cwd (cwd is either the
# workspace root or its .beads/dolt data-dir).
ws_root() {
  local cwd="$1"
  case "$cwd" in
    */.beads/dolt) echo "${cwd%/.beads/dolt}" ;;
    */.beads)      echo "${cwd%/.beads}" ;;
    *)             echo "$cwd" ;;
  esac
}

# Most-recent activity timestamp (epoch) across a workspace's .beads activity files.
latest_activity() {
  local bd="$1/.beads" newest=0 m
  for f in last-touched issues.jsonl dolt-server.log interactions.jsonl; do
    [ -f "$bd/$f" ] || continue
    m=$(stat -c %Y "$bd/$f" 2>/dev/null || echo 0)
    [ "$m" -gt "$newest" ] && newest=$m
  done
  echo "$newest"
}

echo "[$(date '+%F %T')] reaper start (IDLE_MIN=$IDLE_MIN, dry-run=$DRY)"
for pid in $(pgrep -f 'dolt sql-server' 2>/dev/null); do
  total=$((total+1))
  cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null) || { continue; }
  ws=$(ws_root "$cwd")
  short=$(echo "$ws" | sed "s#$HOME/##")
  act=$(latest_activity "$ws")
  if [ "$act" -eq 0 ]; then
    # No activity files found — fall back to the process start time via /proc.
    act=$(stat -c %Y "/proc/$pid" 2>/dev/null || echo "$now")
  fi
  age_min=$(( (now - act) / 60 ))
  if [ "$(( now - act ))" -ge "$idle_secs" ]; then
    if [ "$DRY" -eq 1 ]; then
      echo "  WOULD REAP  pid=$pid idle=${age_min}m  $short"
    else
      kill -TERM "$pid" 2>/dev/null && echo "  reaped      pid=$pid idle=${age_min}m  $short" || echo "  reap-failed pid=$pid  $short"
    fi
    reaped=$((reaped+1))
  else
    kept=$((kept+1))
  fi
done
echo "[$(date '+%F %T')] reaper done — $total servers, $reaped $([ $DRY -eq 1 ] && echo would-reap || echo reaped), $kept kept (active within ${IDLE_MIN}m). bd respawns on next use."
