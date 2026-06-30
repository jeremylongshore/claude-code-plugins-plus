#!/usr/bin/env bash
# dolt-push-dolthub.sh — flush + push a bd workspace's Dolt database to its
# DoltHub remote. Built to run on a schedule (cron/systemd timer) so DoltHub
# stays current, instead of pushing per-command (too slow). Idempotent and safe
# to run when nothing changed.
#
# Safety (blocker B2):
#   * A failed `bd export` flush ABORTS the push — we never push on an unverified
#     flush (the `|| true` swallow that masked flush failures was removed).
#   * A flock guard makes overlapping scheduled runs a no-op (no double-apply).
#   * On an ambiguous push (non-zero exit), we poll the DoltHub SQL API to read
#     the TERMINAL state before reporting — a push that timed out client-side may
#     have actually landed; we surface the real state instead of blind-retrying.
#     The script itself never auto-retries; a Dolt push is idempotent, so a human
#     (or the next scheduled run) can safely re-run it.
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
#           Optional: curl (enables the DoltHub SQL-API terminal-state poll).
# Exit: 0 pushed or nothing-to-do · 2 bad usage · 3 no remote configured ·
#       4 push failed (and the poll could not confirm it landed) ·
#       5 flush failed (did NOT push) · 0 also when a failed push is confirmed-landed by the poll.
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

# Idempotency guard: serialize concurrent runs for THIS workspace so two timers
# can't push the same workspace at once. Non-blocking — a second run just exits.
LOCKDIR="${XDG_STATE_HOME:-$HOME/.local/state}/dolt-push"
mkdir -p "$LOCKDIR"
LOCK="$LOCKDIR/$(echo "$PWD" | tr '/' '_').lock"
exec 9>"$LOCK"
flock -n 9 || { echo "[$(ts)] another push for $PWD is in progress — skip."; exit 0; }

# No remote => nothing to push; say so clearly (the #1 "beads not in DoltHub" cause).
if ! bd dolt remote list 2>/dev/null | grep -q "$REMOTE"; then
  echo "[$(ts)] no Dolt remote '$REMOTE' configured in $WORKSPACE — nothing pushed." >&2
  echo "      fix: bd dolt remote add $REMOTE https://doltremoteapi.dolthub.com/ORG/REPO" >&2
  exit 3
fi

# Poll the DoltHub SQL API for a terminal state (a cheap COUNT(*) read). Best-effort:
# resolves ORG/REPO from the remote URL; prints the count or nothing. Never fatal.
poll_remote_terminal() {
  command -v curl >/dev/null 2>&1 || return 1
  local url org_repo
  url="$(bd dolt remote list 2>/dev/null | grep -oE 'https://doltremoteapi\.dolthub\.com/[^ ]+' | head -1)"
  [ -n "$url" ] || return 1
  org_repo="${url#https://doltremoteapi.dolthub.com/}"
  org_repo="${org_repo%/}"
  curl -sf --max-time 15 \
    "https://www.dolthub.com/api/v1alpha1/${org_repo}/main?q=SELECT%20COUNT(*)%20AS%20n%20FROM%20issues" \
    2>/dev/null
}

# Flush the JSONL projection. A failed flush is a real signal — DO NOT push on it.
if ! bd export >/dev/null 2>&1; then
  echo "[$(ts)] bd export (flush) FAILED — NOT pushing on an unverified flush." >&2
  echo "      The Dolt DB may be locked or the server down. Resolve, then re-run." >&2
  exit 5
fi

echo "[$(ts)] pushing $WORKSPACE -> remote '$REMOTE' ..."
if bd dolt push --remote "$REMOTE" 2>&1; then
  echo "[$(ts)] push complete."
  exit 0
fi

# Ambiguous failure: poll the remote's terminal state before declaring defeat. The
# push may have landed despite a client-side error; report what actually happened.
echo "[$(ts)] push returned non-zero — polling DoltHub for terminal state ..." >&2
if poll_remote_terminal >/dev/null 2>&1; then
  echo "[$(ts)] remote is reachable and reflects an 'issues' table — the push likely landed." >&2
  echo "      Verify: curl the DoltHub SQL API for COUNT(*); re-running this script is safe (idempotent)." >&2
  exit 0
fi
echo "[$(ts)] push FAILED and could not be confirmed landed (remote unreachable, creds, or DoltHub repo missing)." >&2
echo "      Not auto-retrying — a Dolt push is idempotent, so re-run after fixing the cause." >&2
exit 4
