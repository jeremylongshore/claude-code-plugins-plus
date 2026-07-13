#!/usr/bin/env bash
# Catalog: B2 — Local branch name violates project's branch_convention regex
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

CONVENTION=$(fm_field "$GATE_DOSSIER_PATH" "branch_convention")
if [[ -z "$CONVENTION" ]]; then
  gate_skip "no branch_convention in dossier"
fi

REPO_NAME="${GATE_REPO##*/}"
CLONE_DIR="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE_DIR/.git" ]]; then
  gate_skip "no local clone at $CLONE_DIR"
fi

cd "$CLONE_DIR" || gate_skip "cannot cd to clone dir"

BRANCH=$(/usr/bin/git rev-parse --abbrev-ref HEAD 2>/dev/null || /usr/bin/echo "")
if [[ -z "$BRANCH" || "$BRANCH" == "HEAD" ]]; then
  gate_skip "detached HEAD or unknown branch"
fi

if /usr/bin/printf '%s' "$BRANCH" | /usr/bin/grep -qE "$CONVENTION"; then
  gate_pass "branch '$BRANCH' matches convention"
fi

gate_block "branch '$BRANCH' does not match convention /$CONVENTION/" "rename the branch: git branch -m <new-name-matching-convention>"
