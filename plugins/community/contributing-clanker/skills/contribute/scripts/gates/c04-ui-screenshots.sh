#!/usr/bin/env bash
# Catalog: C4 — PR touches UI files but PR body has no screenshot / recording
# Mitigates: maintainer asks "any screenshots?" → reads as not-quite-ready submission.
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
UI_FILES=$(/usr/bin/printf '%s\n' "$CHANGED" | /usr/bin/grep -E '\.(tsx|jsx|vue|svelte|html|css|scss)$' || /usr/bin/echo "")

if [[ -z "$UI_FILES" ]]; then
  gate_pass "no UI files touched in diff"
fi

PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$PR_BODY" ]]; then
  gate_inform "UI files changed but no PR body drafted yet — remember to attach a screenshot or recording"
fi

if /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qiE '!\[.*\]\(.*\)|screenshot|screen recording|\bgif\b|\.mp4|\.mov|\.webm|loom\.com|youtu\.be|youtube\.com'; then
  gate_pass "PR body references screenshot or recording"
fi

gate_block "PR touches UI files but PR body has no screenshot or recording" "PRs touching UI need a screenshot or recording — paste an image (![alt](url)) or a Loom/GIF link in the PR body"
