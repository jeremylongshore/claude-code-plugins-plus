#!/usr/bin/env bash
# Catalog: B5 — Commits missing Signed-off-by when dossier requires DCO
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

DCO=$(fm_field "$GATE_DOSSIER_PATH" "dco_required")
if [[ "$DCO" != "true" ]]; then
  gate_skip "dossier does not require DCO"
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

# Iterate per-commit so we can flag exactly which sha is missing the trailer.
MISSING=""
COMMITS=$(/usr/bin/git rev-list "origin/$DEFAULT_BRANCH..HEAD" 2>/dev/null || /usr/bin/echo "")
if [[ -z "$COMMITS" ]]; then
  gate_pass "no new commits to check"
fi

while read -r sha; do
  [[ -z "$sha" ]] && continue
  BODY=$(/usr/bin/git log -1 --format=%B "$sha" 2>/dev/null || /usr/bin/echo "")
  if ! /usr/bin/printf '%s' "$BODY" | /usr/bin/grep -q "^Signed-off-by:"; then
    MISSING="${MISSING}${sha:0:8} "
  fi
done <<< "$COMMITS"

if [[ -n "$MISSING" ]]; then
  COUNT=$(/usr/bin/printf '%s' "$COMMITS" | /usr/bin/grep -c .)
  gate_block "commits missing Signed-off-by: $MISSING" "git commit --amend -s OR sign all commits: git rebase HEAD~$COUNT --signoff"
fi

gate_pass "all commits have Signed-off-by trailer"
