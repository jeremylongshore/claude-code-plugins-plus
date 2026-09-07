#!/usr/bin/env bash
# Explicit initialization for contribute-prepare. Never run at install or load.

set -euo pipefail

STATE_DIR=""
WORKSPACE_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR="${2:-}"; shift 2 ;;
    --workspace-dir) WORKSPACE_DIR="${2:-}"; shift 2 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 64 ;;
  esac
done

validate_path() {
  local label="$1" value="$2"
  [[ -n "$value" ]] || { printf '%s is required\n' "$label" >&2; exit 64; }
  [[ "$value" == /* ]] || { printf '%s must be absolute: %s\n' "$label" "$value" >&2; exit 64; }
  [[ "$value" != "/" ]] || { printf '%s cannot be /\n' "$label" >&2; exit 64; }
  [[ "$value" != "$HOME" ]] || { printf '%s cannot equal the home directory\n' "$label" >&2; exit 64; }
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || {
    printf '%s cannot contain newline characters\n' "$label" >&2
    exit 64
  }
}

validate_path state-dir "$STATE_DIR"
validate_path workspace-dir "$WORKSPACE_DIR"
[[ "$STATE_DIR" != "$WORKSPACE_DIR" ]] || {
  printf 'state-dir and workspace-dir must be distinct\n' >&2
  exit 64
}

mkdir -p \
  "$STATE_DIR/candidates" \
  "$STATE_DIR/research" \
  "$STATE_DIR/user-gates" \
  "$STATE_DIR/check-runs" \
  "$STATE_DIR/test-logs" \
  "$WORKSPACE_DIR"

if [[ ! -f "$STATE_DIR/profile.md" ]]; then
  printf '%s\n' \
    '# Contribution profile' \
    '' \
    'List preferred languages, target repositories, and contribution constraints.' \
    > "$STATE_DIR/profile.md"
fi

touch "$STATE_DIR/log.jsonl"

printf 'contribute-prepare initialized\n'
printf 'state: %s\n' "$STATE_DIR"
printf 'workspace: %s\n' "$WORKSPACE_DIR"
printf 'Export these paths in the host profile before using preparation tools.\n'
