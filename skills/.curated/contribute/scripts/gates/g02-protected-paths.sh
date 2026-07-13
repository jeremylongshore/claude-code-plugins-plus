#!/usr/bin/env bash
# Catalog: G2 — diff touches infrastructure / CI paths that maintainers gate-keep
# Mitigates: drive-by edits to .github/workflows or terraform/ rarely land first try.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

REPO_NAME="${GATE_REPO##*/}"
CLONE="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

DEFAULT_BRANCH=""
if [[ -n "$GATE_DOSSIER_PATH" && -f "$GATE_DOSSIER_PATH" ]]; then
  DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
fi
[[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

CHANGED=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" --name-only 2>/dev/null || /usr/bin/echo "")

PROTECTED=$(/usr/bin/printf '%s\n' "$CHANGED" | /usr/bin/grep -E '(\.github/workflows/|^infrastructure/|^terraform/|^helm/|^k8s/|^kubernetes/|^\.circleci/|^charts/)' || /usr/bin/echo "")

if [[ -z "$PROTECTED" ]]; then
  gate_pass "diff does not touch protected infrastructure / CI paths"
fi

LIST=$(/usr/bin/printf '%s' "$PROTECTED" | /usr/bin/tr '\n' ',' | /usr/bin/sed 's/,$//')
gate_warn "diff touches protected paths: $LIST" "infrastructure / CI changes deserve maintainer pre-approval; consider opening a Design Issue first to discuss the change"
