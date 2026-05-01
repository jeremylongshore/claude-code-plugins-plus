#!/usr/bin/env bash
# sync-push.sh — Push local Claude Code config to GitHub repo
# Usage: sync-push.sh [--profile NAME] [--auto] [--force] [--dry-run]
set -euo pipefail
source "$(dirname "$0")/common.sh"

# ── Parse args ──────────────────────────────────────────────────────
PROFILE=""
AUTO=false
FORCE=false
DRY_RUN=false
INCLUDE_GLOBAL=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)        PROFILE="$2"; shift 2 ;;
    --auto)           AUTO=true; shift ;;
    --force)          FORCE=true; shift ;;
    --dry-run)        DRY_RUN=true; shift ;;
    --include-global) INCLUDE_GLOBAL=true; shift ;;
    *) shift ;;
  esac
done

# ── Preflight (early-exit before any network/tool calls) ───────────
if [[ "$(get_state "setup_complete")" != "true" ]]; then
  $AUTO || err "Config sync not set up yet. Run /sync-setup first."
  exit $( $AUTO && echo 0 || echo 1 )
fi

PROFILE=$(get_profile "$PROFILE")

if ! check_jq; then exit 1; fi
if ! check_gh; then exit 1; fi

info "Pushing config to profile: ${BOLD}${PROFILE}${NC}"

# ── Ensure local repo is up to date ────────────────────────────────
ensure_local_repo
REPO_PATH=$(get_local_repo_path)
PROFILE_DIR="${REPO_PATH}/profiles/${PROFILE}"
GLOBAL_DIR="${REPO_PATH}/global"

mkdir -p "$PROFILE_DIR"
mkdir -p "$GLOBAL_DIR"

# ── Detect project root ────────────────────────────────────────────
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_HOME="${HOME}/.claude"

# ── Collect files ───────────────────────────────────────────────────
CHANGED=0
SECRET_WARNINGS=0

copy_if_exists() {
  local src="$1"
  local dest="$2"
  local label="$3"

  if [[ -e "$src" ]]; then
    # Secret scan for files (not directories)
    if [[ -f "$src" ]]; then
      if ! scan_for_secrets "$src"; then
        SECRET_WARNINGS=$((SECRET_WARNINGS + 1))
        if ! $FORCE; then
          warn "Skipping $label (potential secret). Use --force to override."
          return
        else
          warn "Force-pushing $label despite secret warning."
        fi
      fi
    fi

    # Create destination directory
    mkdir -p "$(dirname "$dest")"

    if [[ -d "$src" ]]; then
      # Directory: rsync or cp -r
      if command -v rsync &>/dev/null; then
        rsync -a --delete "$src/" "$dest/" 2>/dev/null
      else
        rm -rf "$dest"
        cp -r "$src" "$dest"
      fi
    else
      cp "$src" "$dest"
    fi

    if $DRY_RUN; then
      info "[dry-run] Would sync: $label"
    else
      CHANGED=$((CHANGED + 1))
    fi
  fi
}

# Project-scoped files
info "Collecting project config from: ${PROJECT_DIR}"

copy_if_exists "${PROJECT_DIR}/.mcp.json" \
  "${PROFILE_DIR}/mcp.json" ".mcp.json"

copy_if_exists "${PROJECT_DIR}/.claude/settings.json" \
  "${PROFILE_DIR}/settings.json" ".claude/settings.json"

copy_if_exists "${PROJECT_DIR}/.claude/agents" \
  "${PROFILE_DIR}/agents" ".claude/agents/"

copy_if_exists "${PROJECT_DIR}/.claude/commands" \
  "${PROFILE_DIR}/commands" ".claude/commands/"

copy_if_exists "${PROJECT_DIR}/.claude/skills" \
  "${PROFILE_DIR}/skills" ".claude/skills/"

copy_if_exists "${PROJECT_DIR}/.claude/hooks/scripts" \
  "${PROFILE_DIR}/hooks/scripts" ".claude/hooks/scripts/"

copy_if_exists "${PROJECT_DIR}/.claude/hooks/config/hooks-config.json" \
  "${PROFILE_DIR}/hooks/config/hooks-config.json" ".claude/hooks/config/hooks-config.json"

copy_if_exists "${PROJECT_DIR}/.claude/hooks/sounds" \
  "${PROFILE_DIR}/hooks/sounds" ".claude/hooks/sounds/"

copy_if_exists "${PROJECT_DIR}/.claude/hooks/HOOKS-README.md" \
  "${PROFILE_DIR}/hooks/HOOKS-README.md" ".claude/hooks/HOOKS-README.md"

copy_if_exists "${PROJECT_DIR}/.claude/rules" \
  "${PROFILE_DIR}/rules" ".claude/rules/"

copy_if_exists "${PROJECT_DIR}/.claude/agent-memory" \
  "${PROFILE_DIR}/agent-memory" ".claude/agent-memory/"

# Auto-memory
copy_if_exists "${PROJECT_DIR}/.auto-memory" \
  "${PROFILE_DIR}/memory" ".auto-memory/"

# Agent skills lock file — opt-in
if [[ "$(get_state "sync_agent_skills")" == "true" ]]; then
  copy_if_exists "${PROJECT_DIR}/skills-lock.json" \
    "${PROFILE_DIR}/skills-lock.json" "skills-lock.json"
fi

# User-scoped (global) files — opt-in only
if $INCLUDE_GLOBAL; then
  info "Collecting global config from: ${CLAUDE_HOME}"
  copy_if_exists "${CLAUDE_HOME}/settings.json" \
    "${GLOBAL_DIR}/settings.json" "~/.claude/settings.json"
fi

# ── Detect agent skills (offer opt-in) ─────────────────────────────
if [[ -f "${PROJECT_DIR}/skills-lock.json" ]] && [[ "$(get_state "sync_agent_skills")" != "true" ]] && [[ "$(get_state "sync_agent_skills")" != "declined" ]]; then
  if ! $AUTO; then
    info "Detected ${BOLD}skills-lock.json${NC} (agent skills lock file)."
    echo -n "[claudebase] Sync agent skills across machines? [y/N] "
    read -r ENABLE_SKILLS
    if [[ "$ENABLE_SKILLS" =~ ^[Yy]$ ]]; then
      set_state "sync_agent_skills" "true"
      ok "Agent skills sync enabled."
      # Now copy the lock file
      copy_if_exists "${PROJECT_DIR}/skills-lock.json" \
        "${PROFILE_DIR}/skills-lock.json" "skills-lock.json"
    else
      set_state "sync_agent_skills" "declined"
      info "Skipped. Enable later by running: set sync_agent_skills=true in state.json"
    fi
  fi
fi

# ── Check for actual changes ────────────────────────────────────────
cd "$REPO_PATH"

if [[ -z "$(git status --porcelain)" ]]; then
  ok "No changes to push. Everything is in sync."
  exit 0
fi

if $DRY_RUN; then
  info "Dry run complete. Changes that would be pushed:"
  git status --short
  exit 0
fi

# ── Multi-machine safety check ──────────────────────────────────────
MACHINE_ID=$(get_machine_id)
META_FILE="${REPO_PATH}/.sync-meta.json"

if [[ -f "$META_FILE" ]] && ! $FORCE; then
  LAST_PUSHER=$(jq -r ".profiles.\"${PROFILE}\".last_push_machine // empty" "$META_FILE" 2>/dev/null || true)
  if [[ -n "$LAST_PUSHER" && "$LAST_PUSHER" != "$MACHINE_ID" ]]; then
    LAST_PUSH=$(jq -r ".profiles.\"${PROFILE}\".last_push // empty" "$META_FILE" 2>/dev/null || true)
    warn "Profile '${PROFILE}' was last pushed from '${LAST_PUSHER}' at ${LAST_PUSH}"
    warn "Pull first to avoid overwriting changes, or use --force."
    if $AUTO; then
      warn "Skipping auto-push due to multi-machine conflict."
      exit 0
    fi
    exit 1
  fi
fi

# ── Update metadata ────────────────────────────────────────────────
if [[ -f "$META_FILE" ]]; then
  NOW=$(now_iso)
  tmp=$(mktemp)
  jq ".profiles.\"${PROFILE}\".last_push = \"${NOW}\" |
      .profiles.\"${PROFILE}\".last_push_machine = \"${MACHINE_ID}\" |
      .machines.\"${MACHINE_ID}\".last_seen = \"${NOW}\"" \
    "$META_FILE" > "$tmp" && mv "$tmp" "$META_FILE"
fi

# ── Commit and push ────────────────────────────────────────────────
SUMMARY=$(git diff --stat --cached 2>/dev/null || git diff --stat)
FILE_COUNT=$(git status --porcelain | wc -l | tr -d ' ')

git add -A
git commit -m "Sync profile '${PROFILE}' from ${MACHINE_ID} (${FILE_COUNT} files)" --quiet

info "Pushing to GitHub..."
git push --quiet 2>/dev/null

cd - >/dev/null

# ── Report ──────────────────────────────────────────────────────────
if [[ $SECRET_WARNINGS -gt 0 ]]; then
  warn "${SECRET_WARNINGS} file(s) had potential secret warnings."
fi

ok "Pushed ${FILE_COUNT} file(s) to profile '${PROFILE}'"
set_state "last_push" "$(now_iso)"
set_state "last_push_profile" "$PROFILE"
