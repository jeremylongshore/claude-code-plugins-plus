#!/usr/bin/env bash
# dolt-push-dolthub.sh — flush + push a bd workspace's Dolt database to its
# DoltHub remote. Built to run on a schedule (cron/systemd timer) so DoltHub
# stays current, instead of pushing per-command (too slow). Idempotent and safe
# to run when nothing changed.
#
# Usage:  dolt-push-dolthub.sh [WORKSPACE_DIR] [--remote NAME]
#   WORKSPACE_DIR  bd workspace to push (default: current dir). Must contain .beads/.
#   --remote NAME  Dolt remote to push (default: origin).
#
# Cron example (every 20 min):
#   */20 * * * * /path/to/dolt-push-dolthub.sh ~/my-workspace >> ~/.local/state/dolt-push.log 2>&1
#
# Requires: bd >= 1.0.4 with a Dolt remote already configured
#           (bd dolt remote add origin https://doltremoteapi.dolthub.com/ORG/REPO).
# Exit: 0 pushed or nothing-to-do · 2 bad usage · 3 no remote configured · 4 push failed.
set -uo pipefail

WORKSPACE="."; REMOTE="origin"
while [ $# -gt 0 ]; do
  case "$1" in
    --remote) REMOTE="$2"; shift 2 ;;
    -*) echo "unknown arg: $1" >&2; exit 2 ;;
    *) WORKSPACE="$1"; shift ;;
  esac
done
command -v bd >/dev/null 2>&1 || { echo "error: bd not on PATH" >&2; exit 2; }
cd "$WORKSPACE" || { echo "error: cannot cd to $WORKSPACE" >&2; exit 2; }
[ -d .beads ] || { echo "error: $WORKSPACE is not a bd workspace (no .beads/)" >&2; exit 2; }

ts() { date '+%Y-%m-%dT%H:%M:%S'; }

# No remote => nothing to push; say so clearly (the #1 "beads not in DoltHub" cause).
if ! bd dolt remote list 2>/dev/null | grep -q "$REMOTE"; then
  echo "[$(ts)] no Dolt remote '$REMOTE' configured in $WORKSPACE — nothing pushed." >&2
  echo "      fix: bd dolt remote add $REMOTE https://doltremoteapi.dolthub.com/ORG/REPO" >&2
  exit 3
fi

# Flush JSONL representation, then push committed Dolt history to DoltHub.
bd export >/dev/null 2>&1 || true
echo "[$(ts)] pushing $WORKSPACE -> remote '$REMOTE' ..."
if bd dolt push --remote "$REMOTE" 2>&1; then
  echo "[$(ts)] push complete."
  exit 0
else
  echo "[$(ts)] push FAILED (remote unreachable, creds, or DoltHub repo missing)." >&2
  exit 4
fi
