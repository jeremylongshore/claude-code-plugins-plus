#!/usr/bin/env bash
# Catalog: G3 — manual CHANGELOG edits in a repo that auto-generates the changelog
# Mitigates: clobbers release tooling, gets reverted on next release, looks careless.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier — cannot determine auto_changelog policy"
fi

AUTO=$(fm_field "$GATE_DOSSIER_PATH" "auto_changelog")
if [[ "$AUTO" != "true" ]]; then
  gate_skip "dossier auto_changelog is not true"
fi

REPO_NAME="${GATE_REPO##*/}"
CLONE="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
[[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

CHANGED=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" --name-only 2>/dev/null || /usr/bin/echo "")

# Match CHANGELOG.md at root or in any subdir (case-sensitive)
HITS=$(/usr/bin/printf '%s\n' "$CHANGED" | /usr/bin/grep -E '(^|/)CHANGELOG\.md$' || /usr/bin/echo "")

if [[ -z "$HITS" ]]; then
  gate_pass "no CHANGELOG.md edits in diff"
fi

LIST=$(/usr/bin/printf '%s' "$HITS" | /usr/bin/tr '\n' ',' | /usr/bin/sed 's/,$//')
gate_warn "diff edits CHANGELOG.md ($LIST) but repo auto-generates changelog" "this repo auto-generates CHANGELOG; let the release tooling write it"
