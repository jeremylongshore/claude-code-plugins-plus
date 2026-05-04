#!/usr/bin/env bash
# Catalog: B3 — Local clone is stale vs origin/<default_branch>
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
if [[ -z "$DEFAULT_BRANCH" ]]; then
  gate_skip "no default_branch in dossier"
fi

REPO_NAME="${GATE_REPO##*/}"
CLONE_DIR="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE_DIR/.git" ]]; then
  gate_skip "no local clone at $CLONE_DIR"
fi

cd "$CLONE_DIR" || gate_skip "cannot cd to clone dir"

/usr/bin/timeout 30 /usr/bin/git fetch origin "$DEFAULT_BRANCH" --quiet 2>/dev/null || true

BEHIND=$(/usr/bin/git rev-list --count "HEAD..origin/$DEFAULT_BRANCH" 2>/dev/null || /usr/bin/echo "0")

if [[ "$BEHIND" -gt 100 ]]; then
  gate_warn "local clone is $BEHIND commits behind origin/$DEFAULT_BRANCH" "rebase: git pull --rebase origin $DEFAULT_BRANCH"
fi

gate_pass "clone is current ($BEHIND commits behind origin/$DEFAULT_BRANCH)"
