#!/usr/bin/env bash
# sync-pull.sh — Pull Claude Code config from GitHub repo and apply locally
# Usage: sync-pull.sh [--profile NAME] [--dry-run] [--no-backup]
set -euo pipefail
source "$(dirname "$0")/common.sh"

# ── Parse args ──────────────────────────────────────────────────────
PROFILE=""
DRY_RUN=false
NO_BACKUP=false
INCLUDE_GLOBAL=false
YES=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)        PROFILE="$2"; shift 2 ;;
    --dry-run)        DRY_RUN=true; shift ;;
    --no-backup)      NO_BACKUP=true; shift ;;
    --include-global) INCLUDE_GLOBAL=true; shift ;;
    --yes|-y)         YES=true; shift ;;
    *) shift ;;
  esac
done

PROFILE=$(get_profile "$PROFILE")

# ── Preflight ───────────────────────────────────────────────────────
if [[ "$(get_state "setup_complete")" != "true" ]]; then
  err "Config sync not set up yet. Run /sync-setup first."
  exit 1
fi

if ! check_jq; then exit 1; fi
if ! check_gh; then exit 1; fi

info "Pulling config from profile: ${BOLD}${PROFILE}${NC}"

# ── Ensure local repo is up to date ────────────────────────────────
ensure_local_repo
REPO_PATH=$(get_local_repo_path)
PROFILE_DIR="${REPO_PATH}/profiles/${PROFILE}"
SHARED_DIR="${REPO_PATH}/shared"
GLOBAL_DIR="${REPO_PATH}/global"

if [[ ! -d "$PROFILE_DIR" ]]; then
  err "Profile '${PROFILE}' does not exist in the repo."
  info "Available profiles:"
  ls -1 "${REPO_PATH}/profiles/" 2>/dev/null | sed 's/^/  - /'
  exit 1
fi

# ── Detect project root ────────────────────────────────────────────
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_HOME="${HOME}/.claude"

# ── Backup current config ──────────────────────────────────────────
if ! $NO_BACKUP && ! $DRY_RUN; then
  BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
  BACKUP_PATH="${BACKUPS_DIR}/${BACKUP_NAME}"
  mkdir -p "$BACKUP_PATH"

  info "Backing up current config to: ${BACKUP_PATH}"

  # Backup project files
  [[ -f "${PROJECT_DIR}/CLAUDE.md" ]] && cp "${PROJECT_DIR}/CLAUDE.md" "${BACKUP_PATH}/" 2>/dev/null || true
  [[ -f "${PROJECT_DIR}/.mcp.json" ]] && cp "${PROJECT_DIR}/.mcp.json" "${BACKUP_PATH}/" 2>/dev/null || true
  [[ -d "${PROJECT_DIR}/.claude" ]] && cp -r "${PROJECT_DIR}/.claude" "${BACKUP_PATH}/dot-claude" 2>/dev/null || true
  [[ -d "${PROJECT_DIR}/.auto-memory" ]] && cp -r "${PROJECT_DIR}/.auto-memory" "${BACKUP_PATH}/auto-memory" 2>/dev/null || true
  [[ -f "${PROJECT_DIR}/skills-lock.json" ]] && cp "${PROJECT_DIR}/skills-lock.json" "${BACKUP_PATH}/skills-lock.json" 2>/dev/null || true
  [[ -f "${CLAUDE_HOME}/settings.json" ]] && cp "${CLAUDE_HOME}/settings.json" "${BACKUP_PATH}/global-settings.json" 2>/dev/null || true

  ok "Backup created: ${BACKUP_NAME}"

  # Cleanup old backups (keep last 10)
  cd "$BACKUPS_DIR"
  ls -dt backup-* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true
  cd - >/dev/null
fi

# ── Preview changes ─────────────────────────────────────────────────
if ! $DRY_RUN && ! $YES; then
  PREVIEW_COUNT=0
  preview_file() {
    local src="$1" dest="$2" label="$3"
    [[ ! -e "$src" ]] && return
    if [[ ! -e "$dest" ]]; then
      echo -e "  ${GREEN}+ new${NC}      $label"
      PREVIEW_COUNT=$((PREVIEW_COUNT + 1))
    elif [[ -f "$src" ]] && ! diff -q "$src" "$dest" &>/dev/null; then
      echo -e "  ${YELLOW}~ modified${NC}  $label"
      PREVIEW_COUNT=$((PREVIEW_COUNT + 1))
    elif [[ -d "$src" ]]; then
      if ! diff -rq "$src" "$dest" &>/dev/null 2>&1; then
        echo -e "  ${YELLOW}~ modified${NC}  $label"
        PREVIEW_COUNT=$((PREVIEW_COUNT + 1))
      fi
    fi
  }

  info "Files that will be changed:"
  echo ""

  # Preview shared
  if [[ -d "${SHARED_DIR:-/dev/null}" ]]; then
    preview_file "${SHARED_DIR}/skills" "${PROJECT_DIR}/.claude/skills" "shared/skills/"
    preview_file "${SHARED_DIR}/rules" "${PROJECT_DIR}/.claude/rules" "shared/rules/"
    preview_file "${SHARED_DIR}/agents" "${PROJECT_DIR}/.claude/agents" "shared/agents/"
  fi

  # Preview agent skills
  if [[ "$(get_state "sync_agent_skills")" == "true" ]]; then
    preview_file "${PROFILE_DIR}/skills-lock.json" "${PROJECT_DIR}/skills-lock.json" "skills-lock.json"
  fi

  # Preview profile
  preview_file "${PROFILE_DIR}/mcp.json" "${PROJECT_DIR}/.mcp.json" ".mcp.json"
  preview_file "${PROFILE_DIR}/settings.json" "${PROJECT_DIR}/.claude/settings.json" ".claude/settings.json"
  preview_file "${PROFILE_DIR}/agents" "${PROJECT_DIR}/.claude/agents" ".claude/agents/"
  preview_file "${PROFILE_DIR}/commands" "${PROJECT_DIR}/.claude/commands" ".claude/commands/"
  preview_file "${PROFILE_DIR}/skills" "${PROJECT_DIR}/.claude/skills" ".claude/skills/"
  preview_file "${PROFILE_DIR}/hooks/scripts" "${PROJECT_DIR}/.claude/hooks/scripts" ".claude/hooks/scripts/"
  preview_file "${PROFILE_DIR}/hooks/config/hooks-config.json" "${PROJECT_DIR}/.claude/hooks/config/hooks-config.json" ".claude/hooks/config/hooks-config.json"
  preview_file "${PROFILE_DIR}/hooks/sounds" "${PROJECT_DIR}/.claude/hooks/sounds" ".claude/hooks/sounds/"
  preview_file "${PROFILE_DIR}/hooks/HOOKS-README.md" "${PROJECT_DIR}/.claude/hooks/HOOKS-README.md" ".claude/hooks/HOOKS-README.md"
  preview_file "${PROFILE_DIR}/rules" "${PROJECT_DIR}/.claude/rules" ".claude/rules/"
  preview_file "${PROFILE_DIR}/agent-memory" "${PROJECT_DIR}/.claude/agent-memory" ".claude/agent-memory/"
  preview_file "${PROFILE_DIR}/memory" "${PROJECT_DIR}/.auto-memory" ".auto-memory/"

  if $INCLUDE_GLOBAL && [[ -d "${GLOBAL_DIR:-/dev/null}" ]]; then
    preview_file "${GLOBAL_DIR}/settings.json" "${CLAUDE_HOME}/settings.json" "~/.claude/settings.json"
  fi

  echo ""
  if [[ $PREVIEW_COUNT -eq 0 ]]; then
    ok "No changes to apply. Everything is in sync."
    exit 0
  fi

  info "${PREVIEW_COUNT} file(s) will be overwritten. Backup will be saved to:"
  info "  ${BACKUPS_DIR}/"
  echo ""
  echo -n "[claudebase] Proceed? [y/N] "
  read -r CONFIRM
  if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    info "Pull cancelled."
    exit 0
  fi
  echo ""
fi

# ── Apply files ─────────────────────────────────────────────────────
APPLIED=0

apply_file() {
  local src="$1"
  local dest="$2"
  local label="$3"

  if [[ ! -e "$src" ]]; then return; fi

  if $DRY_RUN; then
    info "[dry-run] Would apply: $label"
    return
  fi

  mkdir -p "$(dirname "$dest")"

  if [[ -d "$src" ]]; then
    # Check if source dir has actual content
    if [[ -z "$(ls -A "$src" 2>/dev/null)" ]]; then return; fi
    if command -v rsync &>/dev/null; then
      rsync -a "$src/" "$dest/" 2>/dev/null
    else
      cp -r "$src/." "$dest/" 2>/dev/null || true
    fi
  else
    cp "$src" "$dest"
  fi

  APPLIED=$((APPLIED + 1))
}

# Step 1: Apply shared files first (base layer)
if [[ -d "$SHARED_DIR" ]]; then
  info "Applying shared config..."

  apply_file "${SHARED_DIR}/skills" \
    "${PROJECT_DIR}/.claude/skills" "shared/skills/"

  apply_file "${SHARED_DIR}/rules" \
    "${PROJECT_DIR}/.claude/rules" "shared/rules/"

  apply_file "${SHARED_DIR}/agents" \
    "${PROJECT_DIR}/.claude/agents" "shared/agents/"
fi

# Step 2: Apply profile files (overlay on top of shared)
info "Applying profile '${PROFILE}' config..."

apply_file "${PROFILE_DIR}/mcp.json" \
  "${PROJECT_DIR}/.mcp.json" ".mcp.json"

apply_file "${PROFILE_DIR}/settings.json" \
  "${PROJECT_DIR}/.claude/settings.json" ".claude/settings.json"

apply_file "${PROFILE_DIR}/agents" \
  "${PROJECT_DIR}/.claude/agents" ".claude/agents/"

apply_file "${PROFILE_DIR}/commands" \
  "${PROJECT_DIR}/.claude/commands" ".claude/commands/"

apply_file "${PROFILE_DIR}/skills" \
  "${PROJECT_DIR}/.claude/skills" ".claude/skills/"

apply_file "${PROFILE_DIR}/hooks/scripts" \
  "${PROJECT_DIR}/.claude/hooks/scripts" ".claude/hooks/scripts/"

apply_file "${PROFILE_DIR}/hooks/config/hooks-config.json" \
  "${PROJECT_DIR}/.claude/hooks/config/hooks-config.json" ".claude/hooks/config/hooks-config.json"

apply_file "${PROFILE_DIR}/hooks/sounds" \
  "${PROJECT_DIR}/.claude/hooks/sounds" ".claude/hooks/sounds/"

apply_file "${PROFILE_DIR}/hooks/HOOKS-README.md" \
  "${PROJECT_DIR}/.claude/hooks/HOOKS-README.md" ".claude/hooks/HOOKS-README.md"

apply_file "${PROFILE_DIR}/rules" \
  "${PROJECT_DIR}/.claude/rules" ".claude/rules/"

apply_file "${PROFILE_DIR}/agent-memory" \
  "${PROJECT_DIR}/.claude/agent-memory" ".claude/agent-memory/"

apply_file "${PROFILE_DIR}/memory" \
  "${PROJECT_DIR}/.auto-memory" ".auto-memory/"

# Step 3: Apply agent skills lock file — opt-in only
if [[ "$(get_state "sync_agent_skills")" == "true" ]]; then
  apply_file "${PROFILE_DIR}/skills-lock.json" \
    "${PROJECT_DIR}/skills-lock.json" "skills-lock.json"

  # List skills from lock file for manual re-fetch (not auto-executed for security)
  if ! $DRY_RUN && [[ -f "${PROJECT_DIR}/skills-lock.json" ]]; then
    SKILL_SOURCES=$(jq -r '.skills | to_entries[] | .value.source' "${PROJECT_DIR}/skills-lock.json" 2>/dev/null || true)
    if [[ -n "$SKILL_SOURCES" ]]; then
      info "Agent skills found in skills-lock.json. Install them manually:"
      while IFS= read -r source; do
        [[ -z "$source" ]] && continue
        info "  npx skills add ${source}"
      done <<< "$SKILL_SOURCES"
    fi
  fi
fi

# Step 4: Apply global (user-level) config — opt-in only
if $INCLUDE_GLOBAL && [[ -d "$GLOBAL_DIR" ]]; then
  info "Applying global config..."
  apply_file "${GLOBAL_DIR}/settings.json" \
    "${CLAUDE_HOME}/settings.json" "~/.claude/settings.json"
fi

# ── Update metadata ────────────────────────────────────────────────
if ! $DRY_RUN; then
  META_FILE="${REPO_PATH}/.sync-meta.json"
  if [[ -f "$META_FILE" ]]; then
    NOW=$(now_iso)
    MACHINE_ID=$(get_machine_id)
    tmp=$(mktemp)
    jq ".profiles.\"${PROFILE}\".last_pull = \"${NOW}\" |
        .machines.\"${MACHINE_ID}\".last_seen = \"${NOW}\"" \
      "$META_FILE" > "$tmp" && mv "$tmp" "$META_FILE"

    cd "$REPO_PATH"
    git add .sync-meta.json
    git commit -m "Update pull metadata for ${MACHINE_ID}" --quiet 2>/dev/null || true
    git push --quiet 2>/dev/null || true
    cd - >/dev/null
  fi

  set_state "last_pull" "$(now_iso)"
  set_state "last_pull_profile" "$PROFILE"
  set_state "active_profile" "$PROFILE"
fi

# ── Verify ──────────────────────────────────────────────────────────
WARNINGS=0
if ! $DRY_RUN; then
  # Check key files parse correctly
  if [[ -f "${PROJECT_DIR}/.claude/settings.json" ]]; then
    if ! jq empty "${PROJECT_DIR}/.claude/settings.json" 2>/dev/null; then
      warn "settings.json may be malformed — check manually"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
  if [[ -f "${PROJECT_DIR}/.mcp.json" ]]; then
    if ! jq empty "${PROJECT_DIR}/.mcp.json" 2>/dev/null; then
      warn ".mcp.json may be malformed — check manually"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
fi

# ── Report ──────────────────────────────────────────────────────────
if $DRY_RUN; then
  ok "Dry run complete."
else
  ok "Applied ${APPLIED} item(s) from profile '${PROFILE}'"
  if [[ $WARNINGS -gt 0 ]]; then
    warn "${WARNINGS} file(s) had validation warnings."
  fi
fi
