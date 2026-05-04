#!/usr/bin/env bash
# Catalog: B6 — Commit subjects violate Conventional Commits when required
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

CC=$(fm_field "$GATE_DOSSIER_PATH" "conventional_commits")
if [[ "$CC" != "true" ]]; then
  gate_skip "dossier does not require Conventional Commits"
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

CC_REGEX='^[a-z]+(\([a-z0-9._/-]+\))?!?: .+'
FAILING=""

while IFS= read -r subj; do
  [[ -z "$subj" ]] && continue
  if ! /usr/bin/printf '%s' "$subj" | /usr/bin/grep -qE "$CC_REGEX"; then
    FAILING="${FAILING}  - ${subj}\n"
  fi
done < <(/usr/bin/git log "origin/$DEFAULT_BRANCH..HEAD" --format=%s 2>/dev/null || /usr/bin/echo "")

if [[ -n "$FAILING" ]]; then
  gate_block "commit subjects not Conventional Commits compliant" "fix subjects via git commit --amend or git rebase -i. Failing: $(/usr/bin/printf "$FAILING" | /usr/bin/tr '\n' '|')"
fi

gate_pass "all commit subjects match Conventional Commits"
