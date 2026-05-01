#!/usr/bin/env bash
# ensure-repo.sh — Create or verify the GitHub config repo exists
set -euo pipefail
source "$(dirname "$0")/common.sh"

REPO_NAME="${1:-$(get_repo_name)}"
PROFILE="${2:-default}"

info "Checking dependencies..."
if ! check_jq; then exit 1; fi
if ! check_gh; then
  exit 1
fi

USER=$(get_gh_user)
REPO_FULL="${USER}/${REPO_NAME}"

info "Checking if repo ${REPO_FULL} exists..."
if gh repo view "$REPO_FULL" &>/dev/null; then
  ok "Repo ${REPO_FULL} already exists."
else
  info "Creating private repo ${REPO_FULL}..."
  gh repo create "$REPO_NAME" --private --description "Claude Code configuration sync" --clone=false
  ok "Created repo ${REPO_FULL}"
fi

# Save identifying state now. setup_complete is deferred until after the
# first successful push, so a half-finished setup isn't mistaken for a
# working one by later sync commands.
set_state "repo_name" "$REPO_NAME"
set_state "repo_full" "$REPO_FULL"
set_state "active_profile" "$PROFILE"
set_state "setup_date" "$(now_iso)"

# Clone/update local copy
info "Syncing local repo copy..."
REPO_PATH=$(get_local_repo_path)
REMOTE_URL=$(get_remote_url "$REPO_FULL")

if [[ -d "${REPO_PATH}/.git" ]]; then
  cd "$REPO_PATH"
  git remote set-url origin "$REMOTE_URL" 2>/dev/null || true
  git pull --rebase --quiet 2>/dev/null || true
  cd - >/dev/null
else
  rm -rf "$REPO_PATH"
  # Distinguish "empty repo" from real failures (auth, SSH hostkey, network).
  # gh repo view exposes isEmpty; use it to decide whether to init locally.
  IS_EMPTY=$(gh repo view "$REPO_FULL" --json isEmpty -q '.isEmpty' 2>/dev/null || echo "")
  if [[ "$IS_EMPTY" == "true" ]]; then
    info "Remote repo is empty — initializing locally."
    mkdir -p "$REPO_PATH"
    cd "$REPO_PATH"
    git init --quiet
    git remote add origin "$REMOTE_URL"
    cd - >/dev/null
  else
    # Non-empty (or unknown): clone it, and let stderr surface real errors.
    # gh repo clone already uses the configured git protocol, so we don't
    # need to rewrite the remote URL afterwards.
    if ! gh repo clone "$REPO_FULL" "$REPO_PATH" -- --quiet; then
      err "Failed to clone ${REPO_FULL}."
      err "Common causes: SSH hostkey not trusted, expired auth, network, or repo permissions."
      err "Try one of:"
      err "  ssh -T git@github.com                              # verify SSH hostkey"
      err "  gh auth status                                      # check auth"
      err "  gh config set -h github.com git_protocol https      # switch to HTTPS"
      exit 1
    fi
  fi
fi

# Initialize repo structure if empty
REPO_PATH=$(get_local_repo_path)
cd "$REPO_PATH"

NEEDS_INIT=false
[[ ! -d "profiles/${PROFILE}" ]] && NEEDS_INIT=true

if $NEEDS_INIT; then
  info "Initializing repo structure with profile: ${PROFILE}"

  # Create directories
  mkdir -p "profiles/${PROFILE}/"{skills,agents,commands,hooks/scripts,hooks/config,hooks/sounds,rules,agent-memory,memory}
  mkdir -p "shared/"{skills,rules,agents}
  mkdir -p "global"

  # Create .sync-meta.json
  MACHINE_ID=$(get_machine_id)
  cat > ".sync-meta.json" <<METAEOF
{
  "version": "1.0",
  "created": "$(now_iso)",
  "profiles": {
    "${PROFILE}": {
      "created": "$(now_iso)",
      "last_push": null,
      "last_push_machine": null,
      "last_pull": null
    }
  },
  "machines": {
    "${MACHINE_ID}": {
      "first_seen": "$(now_iso)",
      "last_seen": "$(now_iso)"
    }
  }
}
METAEOF

  # Create placeholder files so directories are tracked
  echo "# Shared Claude Code Instructions" > "shared/CLAUDE.md"
  echo "# ${PROFILE} profile" > "profiles/${PROFILE}/README.md"

  # Create .gitignore
  cat > ".gitignore" <<'GIEOF'
# Machine-specific files (never sync)
settings.local.json
hooks-config.local.json
*.log
.DS_Store
GIEOF

  # Commit and push. If the push fails, bail out *without* marking setup
  # complete so the user can re-run after fixing auth/network.
  git add -A
  git commit -m "Initialize claudebase repo with profile: ${PROFILE}" --quiet
  git branch -M main
  if ! git push -u origin main --quiet; then
    err "Failed to push initial commit to ${REPO_FULL}."
    err "Fix the underlying git auth issue and re-run setup."
    exit 1
  fi

  ok "Repo initialized with profile: ${PROFILE}"
else
  ok "Repo already initialized. Active profile: ${PROFILE}"
fi

cd - >/dev/null

# Only now is setup truly complete — remote is reachable and has content.
set_state "setup_complete" "true"

ok "Setup complete!"
echo ""
echo -e "  Repo:    ${CYAN}https://github.com/${REPO_FULL}${NC}"
echo -e "  Profile: ${CYAN}${PROFILE}${NC}"
echo -e "  Machine: ${CYAN}$(get_machine_id)${NC}"
echo ""
echo -e "Available commands:"
echo -e "  ${BOLD}/sync-push${NC}      — Push current config to GitHub"
echo -e "  ${BOLD}/sync-pull${NC}      — Pull config from GitHub"
echo -e "  ${BOLD}/sync-status${NC}    — Compare local vs remote"
echo -e "  ${BOLD}/sync-profiles${NC}  — Manage named profiles"
echo -e "  ${BOLD}/sync-config${NC}    — View/change settings"
echo ""
echo -e "Type ${BOLD}/sync${NC} to see all commands."
