#!/usr/bin/env bash
# diff-config.sh — Compare local config against what's in the GitHub repo
# Usage: diff-config.sh [--profile NAME] [--quiet]
set -euo pipefail
source "$(dirname "$0")/common.sh"

PROFILE=""
QUIET=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile) PROFILE="$2"; shift 2 ;;
    --quiet)   QUIET=true; shift ;;
    *) shift ;;
  esac
done

# Early-exit before any network/tool calls
if [[ "$(get_state "setup_complete")" != "true" ]]; then
  $QUIET || err "Config sync not set up."
  exit $( $QUIET && echo 0 || echo 1 )
fi

PROFILE=$(get_profile "$PROFILE")

if ! check_jq; then exit 1; fi
if ! check_gh; then exit 1; fi

# Update repo
ensure_local_repo
REPO_PATH=$(get_local_repo_path)
PROFILE_DIR="${REPO_PATH}/profiles/${PROFILE}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_HOME="${HOME}/.claude"

if [[ ! -d "$PROFILE_DIR" ]]; then
  $QUIET || err "Profile '${PROFILE}' not found in repo."
  exit 1
fi

# ── Compare files ───────────────────────────────────────────────────
LOCAL_CHANGES=0
REMOTE_CHANGES=0
MISSING_LOCAL=0
MISSING_REMOTE=0

compare_file() {
  local local_path="$1"
  local repo_path="$2"
  local label="$3"

  local local_exists=false
  local repo_exists=false

  [[ -e "$local_path" ]] && local_exists=true
  [[ -e "$repo_path" ]] && repo_exists=true

  if ! $local_exists && ! $repo_exists; then
    return
  fi

  if $local_exists && ! $repo_exists; then
    MISSING_REMOTE=$((MISSING_REMOTE + 1))
    if ! $QUIET; then
      echo -e "  ${GREEN}+ local only${NC}  $label"
    fi
    return
  fi

  if ! $local_exists && $repo_exists; then
    MISSING_LOCAL=$((MISSING_LOCAL + 1))
    if ! $QUIET; then
      echo -e "  ${CYAN}+ remote only${NC} $label"
    fi
    return
  fi

  # Both exist — compare
  if [[ -d "$local_path" && -d "$repo_path" ]]; then
    # Directory comparison
    local diff_output
    diff_output=$(diff -rq "$local_path" "$repo_path" 2>/dev/null || true)
    if [[ -n "$diff_output" ]]; then
      LOCAL_CHANGES=$((LOCAL_CHANGES + 1))
      if ! $QUIET; then
        echo -e "  ${YELLOW}~ modified${NC}    $label"
      fi
    fi
  elif [[ -f "$local_path" && -f "$repo_path" ]]; then
    if ! diff -q "$local_path" "$repo_path" &>/dev/null; then
      LOCAL_CHANGES=$((LOCAL_CHANGES + 1))
      if ! $QUIET; then
        echo -e "  ${YELLOW}~ modified${NC}    $label"
      fi
    fi
  fi
}

if ! $QUIET; then
  info "Comparing local config with profile '${PROFILE}'"
  echo ""
fi

compare_file "${PROJECT_DIR}/.mcp.json" "${PROFILE_DIR}/mcp.json" ".mcp.json"
compare_file "${PROJECT_DIR}/.claude/settings.json" "${PROFILE_DIR}/settings.json" ".claude/settings.json"
compare_file "${PROJECT_DIR}/.claude/agents" "${PROFILE_DIR}/agents" ".claude/agents/"
compare_file "${PROJECT_DIR}/.claude/commands" "${PROFILE_DIR}/commands" ".claude/commands/"
compare_file "${PROJECT_DIR}/.claude/skills" "${PROFILE_DIR}/skills" ".claude/skills/"
compare_file "${PROJECT_DIR}/.claude/hooks/scripts" "${PROFILE_DIR}/hooks/scripts" ".claude/hooks/scripts/"
compare_file "${PROJECT_DIR}/.claude/hooks/config/hooks-config.json" "${PROFILE_DIR}/hooks/config/hooks-config.json" "hooks-config.json"
compare_file "${PROJECT_DIR}/.claude/hooks/sounds" "${PROFILE_DIR}/hooks/sounds" ".claude/hooks/sounds/"
compare_file "${PROJECT_DIR}/.claude/rules" "${PROFILE_DIR}/rules" ".claude/rules/"
compare_file "${PROJECT_DIR}/.claude/agent-memory" "${PROFILE_DIR}/agent-memory" ".claude/agent-memory/"
compare_file "${PROJECT_DIR}/.auto-memory" "${PROFILE_DIR}/memory" ".auto-memory/"
compare_file "${CLAUDE_HOME}/settings.json" "${REPO_PATH}/global/settings.json" "~/.claude/settings.json"

TOTAL=$((LOCAL_CHANGES + MISSING_LOCAL + MISSING_REMOTE))

if ! $QUIET; then
  echo ""
  if [[ $TOTAL -eq 0 ]]; then
    ok "Everything is in sync."
  else
    echo -e "${BOLD}Summary:${NC}"
    [[ $LOCAL_CHANGES -gt 0 ]] && echo -e "  ${YELLOW}${LOCAL_CHANGES}${NC} modified (local differs from remote)"
    [[ $MISSING_REMOTE -gt 0 ]] && echo -e "  ${GREEN}${MISSING_REMOTE}${NC} local-only (not yet pushed)"
    [[ $MISSING_LOCAL -gt 0 ]] && echo -e "  ${CYAN}${MISSING_LOCAL}${NC} remote-only (not yet pulled)"
    echo ""
    echo -e "  Run ${BOLD}/sync-push${NC} to upload local changes"
    echo -e "  Run ${BOLD}/sync-pull${NC} to download remote changes"
  fi

  # Show last sync info
  LAST_PUSH=$(get_state "last_push" "never")
  LAST_PULL=$(get_state "last_pull" "never")
  echo ""
  echo -e "  Last push: ${CYAN}${LAST_PUSH}${NC}"
  echo -e "  Last pull: ${CYAN}${LAST_PULL}${NC}"
  echo -e "  Profile:   ${CYAN}${PROFILE}${NC}"
  echo -e "  Machine:   ${CYAN}$(get_machine_id)${NC}"
fi

# Exit code: 0 if in sync, 1 if differences exist
[[ $TOTAL -eq 0 ]]
