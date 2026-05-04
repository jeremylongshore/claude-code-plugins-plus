#!/usr/bin/env bash
# Catalog: B7 — Local diff touches files outside candidate's claimed scope
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_CANDIDATE_PATH" || ! -f "$GATE_CANDIDATE_PATH" ]]; then
  gate_skip "no candidate file"
fi

# Extract scope section from candidate body. Recognize "## Scope" or
# "## Files to touch" (case-insensitive on the heading word).
SCOPE_BLOCK=$(/usr/bin/awk '
  BEGIN{flag=0}
  /^## [Ss]cope/ {flag=1; next}
  /^## [Ff]iles to touch/ {flag=1; next}
  /^## / {flag=0}
  flag {print}
' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$SCOPE_BLOCK" ]]; then
  gate_skip "no '## Scope' or '## Files to touch' section in candidate"
fi

# Parse paths: strip blank lines, comments, list markers.
SCOPE_FILES=$(/usr/bin/printf '%s\n' "$SCOPE_BLOCK" \
  | /usr/bin/sed -E 's/^[[:space:]]*[-*][[:space:]]+//; s/^[[:space:]]+//; s/[[:space:]]+$//' \
  | /usr/bin/grep -vE '^(#|$)' \
  | /usr/bin/sed -E 's/^`(.+)`$/\1/')

if [[ -z "$SCOPE_FILES" ]]; then
  gate_skip "scope section present but empty"
fi

REPO_NAME="${GATE_REPO##*/}"
CLONE_DIR="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE_DIR/.git" ]]; then
  gate_skip "no local clone at $CLONE_DIR"
fi

cd "$CLONE_DIR" || gate_skip "cannot cd to clone dir"

DEFAULT_BRANCH=""
if [[ -n "$GATE_DOSSIER_PATH" && -f "$GATE_DOSSIER_PATH" ]]; then
  DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
fi
[[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

CHANGED=$(/usr/bin/git diff "origin/$DEFAULT_BRANCH..HEAD" --name-only 2>/dev/null || /usr/bin/echo "")

if [[ -z "$CHANGED" ]]; then
  gate_pass "no changed files"
fi

DIVERGENT=""
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if ! /usr/bin/printf '%s\n' "$SCOPE_FILES" | /usr/bin/grep -Fxq "$f"; then
    DIVERGENT="${DIVERGENT}${f} "
  fi
done <<< "$CHANGED"

if [[ -n "$DIVERGENT" ]]; then
  gate_warn "diff touches files outside scope: $DIVERGENT" "either expand the candidate's scope section or revert the out-of-scope edits"
fi

gate_pass "all changed files are within declared scope"
