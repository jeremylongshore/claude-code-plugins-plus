#!/usr/bin/env bash
# Catalog: B1 — Local branch is based on a non-default upstream branch
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier — cannot determine default_branch"
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

if /usr/bin/git merge-base --is-ancestor "origin/$DEFAULT_BRANCH" HEAD 2>/dev/null; then
  gate_pass "HEAD descends from origin/$DEFAULT_BRANCH"
fi

gate_block "HEAD is not a descendant of origin/$DEFAULT_BRANCH" "rebase onto the default branch: git fetch origin $DEFAULT_BRANCH && git rebase origin/$DEFAULT_BRANCH"
