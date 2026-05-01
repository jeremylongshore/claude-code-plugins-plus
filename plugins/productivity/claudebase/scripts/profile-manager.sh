#!/usr/bin/env bash
# profile-manager.sh — Manage config sync profiles
# Usage: profile-manager.sh <action> [args...]
#   list                        List all profiles
#   create <name> [--from NAME] Create a new profile
#   delete <name>               Delete a profile
#   info <name>                 Show profile details
#   diff <name1> <name2>       Compare two profiles
set -euo pipefail
source "$(dirname "$0")/common.sh"

ACTION="${1:-list}"
shift || true

if [[ "$(get_state "setup_complete")" != "true" ]]; then
  err "Config sync not set up yet. Run /sync-setup first."
  exit 1
fi

if ! check_jq; then exit 1; fi
if ! check_gh; then exit 1; fi

ensure_local_repo
REPO_PATH=$(get_local_repo_path)
PROFILES_DIR="${REPO_PATH}/profiles"
META_FILE="${REPO_PATH}/.sync-meta.json"
ACTIVE_PROFILE=$(get_profile)

case "$ACTION" in
  list)
    info "Available profiles:"
    echo ""
    for profile_dir in "${PROFILES_DIR}"/*/; do
      [[ ! -d "$profile_dir" ]] && continue
      profile_name=$(basename "$profile_dir")

      # Get metadata
      last_push=$(jq -r ".profiles.\"${profile_name}\".last_push // \"never\"" "$META_FILE" 2>/dev/null || echo "never")
      last_machine=$(jq -r ".profiles.\"${profile_name}\".last_push_machine // \"unknown\"" "$META_FILE" 2>/dev/null || echo "unknown")

      # Count files
      file_count=$(find "$profile_dir" -type f | wc -l | tr -d ' ')

      # Active marker
      marker="  "
      if [[ "$profile_name" == "$ACTIVE_PROFILE" ]]; then
        marker="${GREEN}*${NC} "
      fi

      echo -e "${marker}${BOLD}${profile_name}${NC}"
      echo -e "    Files: ${file_count} | Last push: ${last_push} | From: ${last_machine}"
    done
    echo ""
    echo -e "Active profile: ${CYAN}${ACTIVE_PROFILE}${NC}"
    ;;

  create)
    NAME="${1:-}"
    FROM=""
    shift || true
    while [[ $# -gt 0 ]]; do
      case $1 in
        --from) FROM="$2"; shift 2 ;;
        *) shift ;;
      esac
    done

    if [[ -z "$NAME" ]]; then
      err "Usage: profile-manager.sh create <name> [--from <existing-profile>]"
      exit 1
    fi

    # Validate name
    if [[ ! "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
      err "Profile name must be alphanumeric (with hyphens/underscores)."
      exit 1
    fi

    NEW_DIR="${PROFILES_DIR}/${NAME}"
    if [[ -d "$NEW_DIR" ]]; then
      err "Profile '${NAME}' already exists."
      exit 1
    fi

    if [[ -n "$FROM" ]]; then
      FROM_DIR="${PROFILES_DIR}/${FROM}"
      if [[ ! -d "$FROM_DIR" ]]; then
        err "Source profile '${FROM}' does not exist."
        exit 1
      fi
      info "Creating profile '${NAME}' from '${FROM}'..."
      cp -r "$FROM_DIR" "$NEW_DIR"
    else
      info "Creating empty profile '${NAME}'..."
      mkdir -p "${NEW_DIR}/"{skills,agents,commands,hooks/scripts,hooks/config,hooks/sounds,rules,agent-memory,memory}
      echo "# ${NAME} profile" > "${NEW_DIR}/README.md"
    fi

    # Update metadata
    NOW=$(now_iso)
    tmp=$(mktemp)
    jq ".profiles.\"${NAME}\" = {\"created\": \"${NOW}\", \"last_push\": null, \"last_push_machine\": null, \"last_pull\": null}" \
      "$META_FILE" > "$tmp" && mv "$tmp" "$META_FILE"

    # Commit
    cd "$REPO_PATH"
    git add -A
    git commit -m "Create profile: ${NAME}" --quiet
    git push --quiet 2>/dev/null
    cd - >/dev/null

    ok "Profile '${NAME}' created."
    echo -e "Switch to it: ${BOLD}/sync-profiles switch ${NAME}${NC}"
    ;;

  delete)
    NAME="${1:-}"
    if [[ -z "$NAME" ]]; then
      err "Usage: profile-manager.sh delete <name>"
      exit 1
    fi

    if [[ "$NAME" == "$ACTIVE_PROFILE" ]]; then
      err "Cannot delete the active profile. Switch first."
      exit 1
    fi

    DEL_DIR="${PROFILES_DIR}/${NAME}"
    if [[ ! -d "$DEL_DIR" ]]; then
      err "Profile '${NAME}' does not exist."
      exit 1
    fi

    warn "This will permanently delete profile '${NAME}' from the repo."
    rm -rf "$DEL_DIR"

    # Update metadata
    tmp=$(mktemp)
    jq "del(.profiles.\"${NAME}\")" "$META_FILE" > "$tmp" && mv "$tmp" "$META_FILE"

    cd "$REPO_PATH"
    git add -A
    git commit -m "Delete profile: ${NAME}" --quiet
    git push --quiet 2>/dev/null
    cd - >/dev/null

    ok "Profile '${NAME}' deleted."
    ;;

  info)
    NAME="${1:-$ACTIVE_PROFILE}"
    PROF_DIR="${PROFILES_DIR}/${NAME}"

    if [[ ! -d "$PROF_DIR" ]]; then
      err "Profile '${NAME}' does not exist."
      exit 1
    fi

    created=$(jq -r ".profiles.\"${NAME}\".created // \"unknown\"" "$META_FILE" 2>/dev/null || echo "unknown")
    last_push=$(jq -r ".profiles.\"${NAME}\".last_push // \"never\"" "$META_FILE" 2>/dev/null || echo "never")
    last_machine=$(jq -r ".profiles.\"${NAME}\".last_push_machine // \"unknown\"" "$META_FILE" 2>/dev/null || echo "unknown")
    last_pull=$(jq -r ".profiles.\"${NAME}\".last_pull // \"never\"" "$META_FILE" 2>/dev/null || echo "never")

    echo -e "${BOLD}Profile: ${NAME}${NC}"
    [[ "$NAME" == "$ACTIVE_PROFILE" ]] && echo -e "  ${GREEN}(active)${NC}"
    echo -e "  Created:     ${created}"
    echo -e "  Last push:   ${last_push}"
    echo -e "  Push from:   ${last_machine}"
    echo -e "  Last pull:   ${last_pull}"
    echo ""
    echo "  Contents:"
    # Show what's in the profile
    for item in CLAUDE.md mcp.json settings.json; do
      [[ -f "${PROF_DIR}/${item}" ]] && echo -e "    ${GREEN}+${NC} ${item}"
    done
    for dir in agents commands skills hooks rules agent-memory memory; do
      if [[ -d "${PROF_DIR}/${dir}" ]]; then
        count=$(find "${PROF_DIR}/${dir}" -type f 2>/dev/null | wc -l | tr -d ' ')
        [[ $count -gt 0 ]] && echo -e "    ${GREEN}+${NC} ${dir}/ (${count} files)"
      fi
    done
    ;;

  diff)
    NAME1="${1:-}"
    NAME2="${2:-}"

    if [[ -z "$NAME1" || -z "$NAME2" ]]; then
      err "Usage: profile-manager.sh diff <profile1> <profile2>"
      exit 1
    fi

    DIR1="${PROFILES_DIR}/${NAME1}"
    DIR2="${PROFILES_DIR}/${NAME2}"

    if [[ ! -d "$DIR1" ]]; then
      err "Profile '${NAME1}' does not exist."
      exit 1
    fi
    if [[ ! -d "$DIR2" ]]; then
      err "Profile '${NAME2}' does not exist."
      exit 1
    fi

    info "Comparing profiles: ${BOLD}${NAME1}${NC} vs ${BOLD}${NAME2}${NC}"
    echo ""

    DIFFS=0

    # Collect all unique file paths across both profiles
    ALL_FILES=$(cd "$PROFILES_DIR" && {
      find "$NAME1" -type f 2>/dev/null | sed "s|^${NAME1}/||"
      find "$NAME2" -type f 2>/dev/null | sed "s|^${NAME2}/||"
    } | sort -u)

    while IFS= read -r rel_path; do
      [[ -z "$rel_path" ]] && continue
      [[ "$rel_path" == "README.md" ]] && continue

      f1="${DIR1}/${rel_path}"
      f2="${DIR2}/${rel_path}"

      if [[ -f "$f1" && ! -f "$f2" ]]; then
        echo -e "  ${GREEN}+ ${NAME1} only${NC}  ${rel_path}"
        DIFFS=$((DIFFS + 1))
      elif [[ ! -f "$f1" && -f "$f2" ]]; then
        echo -e "  ${CYAN}+ ${NAME2} only${NC}  ${rel_path}"
        DIFFS=$((DIFFS + 1))
      elif ! diff -q "$f1" "$f2" &>/dev/null; then
        echo -e "  ${YELLOW}~ differs${NC}      ${rel_path}"
        DIFFS=$((DIFFS + 1))
      fi
    done <<< "$ALL_FILES"

    echo ""
    if [[ $DIFFS -eq 0 ]]; then
      ok "Profiles are identical."
    else
      info "${DIFFS} difference(s) found."
    fi
    ;;

  *)
    err "Unknown action: ${ACTION}"
    echo "Usage: profile-manager.sh <list|create|delete|diff|info> [args...]"
    exit 1
    ;;
esac
