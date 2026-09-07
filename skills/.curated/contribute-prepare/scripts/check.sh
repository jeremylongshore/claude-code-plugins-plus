#!/usr/bin/env bash
# Read-only readiness check for contribute-prepare.

set -euo pipefail

STATE_DIR="${CONTRIBUTE_STATE_DIR:-}"
WORKSPACE_DIR="${CONTRIBUTE_WORKSPACE_DIR:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR="${2:-}"; shift 2 ;;
    --workspace-dir) WORKSPACE_DIR="${2:-}"; shift 2 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 64 ;;
  esac
done

check_path() {
  local label="$1" value="$2"
  [[ -n "$value" ]] || { printf '%s: unset\n' "$label"; return 1; }
  [[ "$value" == /* && "$value" != "/" && "$value" != "$HOME" ]] || {
    printf '%s: unsafe (%s)\n' "$label" "$value"
    return 1
  }
  [[ -d "$value" ]] || { printf '%s: missing (%s)\n' "$label" "$value"; return 1; }
  printf '%s: ok (%s)\n' "$label" "$value"
}

status=0
check_path state-dir "$STATE_DIR" || status=1
check_path workspace-dir "$WORKSPACE_DIR" || status=1
command -v git >/dev/null 2>&1 || { printf 'git: missing\n'; status=1; }
command -v jq >/dev/null 2>&1 || { printf 'jq: missing\n'; status=1; }
gh auth status >/dev/null 2>&1 || { printf 'gh: unavailable or unauthenticated\n'; status=1; }

exit "$status"
