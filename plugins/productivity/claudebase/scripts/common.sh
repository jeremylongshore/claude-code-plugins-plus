#!/usr/bin/env bash
# common.sh — Shared utilities for claudebase scripts
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[claudebase]${NC} $*"; }
ok()    { echo -e "${GREEN}[claudebase]${NC} $*"; }
warn()  { echo -e "${YELLOW}[claudebase]${NC} $*"; }
err()   { echo -e "${RED}[claudebase]${NC} $*" >&2; }

# ── Paths ───────────────────────────────────────────────────────────
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data/claudebase}"
MANIFEST="${PLUGIN_ROOT}/.sync-manifest.json"
MANIFEST_LOCAL="${PLUGIN_ROOT}/.sync-manifest.local.json"
STATE_FILE="${PLUGIN_DATA}/state.json"
BACKUPS_DIR="${PLUGIN_DATA}/backups"

# Ensure data directories exist
mkdir -p "${PLUGIN_DATA}" "${BACKUPS_DIR}"

# ── State helpers ───────────────────────────────────────────────────
get_state() {
  local key="$1"
  local default="${2:-}"
  if [[ -f "$STATE_FILE" ]]; then
    local val
    val=$(jq -r ".$key // empty" "$STATE_FILE" 2>/dev/null || true)
    echo "${val:-$default}"
  else
    echo "$default"
  fi
}

set_state() {
  local key="$1"
  local value="$2"
  if [[ -f "$STATE_FILE" ]]; then
    local tmp
    tmp=$(mktemp)
    jq ".$key = \"$value\"" "$STATE_FILE" > "$tmp" && mv "$tmp" "$STATE_FILE"
  else
    echo "{\"$key\": \"$value\"}" > "$STATE_FILE"
  fi
}

# ── GitHub helpers ──────────────────────────────────────────────────
check_gh() {
  if ! command -v gh &>/dev/null; then
    err "gh CLI is not installed."
    err "Install it: https://cli.github.com/"
    return 1
  fi
  if ! gh auth status &>/dev/null; then
    err "gh is not authenticated. Run: gh auth login"
    return 1
  fi
  return 0
}

check_jq() {
  if ! command -v jq &>/dev/null; then
    err "jq is not installed."
    err "Install it: https://jqlang.github.io/jq/download/"
    return 1
  fi
  return 0
}

get_gh_user() {
  gh api user -q '.login' 2>/dev/null
}

# Return the git remote URL for a repo, honoring gh's configured git protocol
# (ssh or https). Falls back to https when unset.
get_remote_url() {
  local repo_full="$1"
  local proto
  proto=$(gh config get -h github.com git_protocol 2>/dev/null || echo "")
  if [[ "$proto" == "ssh" ]]; then
    echo "git@github.com:${repo_full}.git"
  else
    echo "https://github.com/${repo_full}.git"
  fi
}

get_repo_name() {
  local configured
  configured=$(get_state "repo_name" "")
  if [[ -n "$configured" ]]; then
    echo "$configured"
  else
    echo "claude-config"
  fi
}

get_repo_full() {
  local user repo
  user=$(get_gh_user)
  repo=$(get_repo_name)
  echo "${user}/${repo}"
}

get_profile() {
  local profile="${1:-}"
  if [[ -z "$profile" ]]; then
    profile=$(get_state "active_profile" "default")
  fi
  echo "$profile"
}

# ── Machine ID ──────────────────────────────────────────────────────
get_machine_id() {
  local mid
  mid=$(get_state "machine_id" "")
  if [[ -z "$mid" ]]; then
    # Generate from hostname
    mid=$(hostname -s 2>/dev/null || echo "unknown")
    set_state "machine_id" "$mid"
  fi
  echo "$mid"
}

# ── Repo clone/sync helpers ────────────────────────────────────────
get_local_repo_path() {
  echo "${PLUGIN_DATA}/repo"
}

ensure_local_repo() {
  local repo_path
  repo_path=$(get_local_repo_path)
  local repo_full
  repo_full=$(get_repo_full)

  if [[ -d "${repo_path}/.git" ]]; then
    # Repo exists, pull latest
    cd "$repo_path"
    git pull --rebase --quiet 2>/dev/null || true
    cd - >/dev/null
  else
    # Clone the repo. Let stderr surface so real failures (auth, hostkey,
    # network) are visible instead of being mistaken for "empty repo".
    rm -rf "$repo_path"
    gh repo clone "$repo_full" "$repo_path" -- --quiet --depth 1
  fi
}

# ── Manifest helpers ───────────────────────────────────────────────
# Reads a value from the manifest, with local override taking precedence.
# Usage: get_manifest_value '.secret_patterns[]'
get_manifest_value() {
  local query="$1"
  if [[ -f "$MANIFEST_LOCAL" ]]; then
    # Deep merge: local overrides base. For arrays, local replaces entirely.
    local merged
    merged=$(jq -s '.[0] * .[1]' "$MANIFEST" "$MANIFEST_LOCAL" 2>/dev/null || cat "$MANIFEST")
    echo "$merged" | jq -r "$query" 2>/dev/null || true
  else
    jq -r "$query" "$MANIFEST" 2>/dev/null || true
  fi
}

# ── Secret scanning ────────────────────────────────────────────────
scan_for_secrets() {
  local file="$1"
  if [[ ! -f "$file" ]]; then return 0; fi

  local patterns
  patterns=$(get_manifest_value '.secret_patterns[]')

  while IFS= read -r pattern; do
    pattern="${pattern%$'\r'}"  # Strip trailing CR (Windows/CRLF compat)
    [[ -z "$pattern" ]] && continue
    if grep -qE -- "$pattern" "$file" 2>/dev/null; then
      warn "Potential secret detected in: $file"
      warn "Pattern match: $pattern"
      return 1
    fi
  done <<< "$patterns"
  return 0
}

# ── Timestamp ───────────────────────────────────────────────────────
now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}
