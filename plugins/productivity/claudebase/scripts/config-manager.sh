#!/usr/bin/env bash
# config-manager.sh — View and modify claudebase settings
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

ACTION="${1:-show}"
shift || true

case "$ACTION" in
  show)
    if [[ ! -f "$STATE_FILE" ]]; then
      err "Config sync not set up yet. Run /sync-setup first."
      exit 1
    fi

    echo -e "${BOLD}Claudebase Configuration${NC}"
    echo ""
    echo -e "  ${BOLD}repo${NC}              $(get_state "repo_full")"
    echo -e "  ${BOLD}active_profile${NC}    $(get_state "active_profile" "default")"
    echo -e "  ${BOLD}machine_id${NC}        $(get_state "machine_id")"
    echo -e "  ${BOLD}include_global${NC}    $(get_state "include_global" "false")"
    echo -e "  ${BOLD}sync_agent_skills${NC} $(get_state "sync_agent_skills" "false")"
    echo -e "  ${BOLD}auto_push${NC}         $(get_state "auto_push" "false")"
    echo ""
    echo -e "  ${BOLD}setup_date${NC}        $(get_state "setup_date")"
    echo -e "  ${BOLD}last_push${NC}         $(get_state "last_push" "never")"
    echo -e "  ${BOLD}last_pull${NC}         $(get_state "last_pull" "never")"
    echo ""
    echo -e "  ${CYAN}State file:${NC}    ${STATE_FILE}"
    echo -e "  ${CYAN}Manifest:${NC}      ${MANIFEST}"
    echo -e "  ${CYAN}Repo clone:${NC}    ${PLUGIN_DATA}/repo/"
    echo -e "  ${CYAN}Backups:${NC}       ${BACKUPS_DIR}/"
    ;;

  set)
    KEY="${1:-}"
    VALUE="${2:-}"

    if [[ -z "$KEY" ]] || [[ -z "$VALUE" ]]; then
      err "Usage: config set <key> <value>"
      err ""
      err "Configurable keys:"
      err "  include_global     true|false   Sync ~/.claude/settings.json"
      err "  sync_agent_skills  true|false   Sync skills-lock.json"
      err "  auto_push          true|false   Auto-push on session end"
      err "  machine_id         <name>       Machine identifier"
      exit 1
    fi

    ALLOWED_KEYS="include_global sync_agent_skills auto_push machine_id"
    if ! echo "$ALLOWED_KEYS" | grep -qw "$KEY"; then
      err "Unknown config key: $KEY"
      err "Allowed keys: $ALLOWED_KEYS"
      exit 1
    fi

    # Validate boolean keys
    if [[ "$KEY" =~ ^(include_global|sync_agent_skills|auto_push)$ ]]; then
      if [[ "$VALUE" != "true" ]] && [[ "$VALUE" != "false" ]]; then
        err "Value for '$KEY' must be 'true' or 'false'"
        exit 1
      fi
    fi

    OLD_VALUE=$(get_state "$KEY" "unset")
    set_state "$KEY" "$VALUE"
    ok "$KEY: ${OLD_VALUE} → ${VALUE}"
    ;;

  get)
    KEY="${1:-}"
    if [[ -z "$KEY" ]]; then
      err "Usage: config get <key>"
      exit 1
    fi
    get_state "$KEY" "unset"
    ;;

  reset)
    KEY="${1:-}"
    if [[ -z "$KEY" ]]; then
      err "Usage: config reset <key>"
      exit 1
    fi

    ALLOWED_KEYS="include_global sync_agent_skills auto_push"
    if ! echo "$ALLOWED_KEYS" | grep -qw "$KEY"; then
      err "Cannot reset key: $KEY"
      exit 1
    fi

    if [[ -f "$STATE_FILE" ]]; then
      tmp=$(mktemp)
      jq "del(.$KEY)" "$STATE_FILE" > "$tmp" && mv "$tmp" "$STATE_FILE"
      ok "Reset '$KEY' to default."
    fi
    ;;

  *)
    err "Unknown action: $ACTION"
    err "Usage: config <show|set|get|reset>"
    exit 1
    ;;
esac
