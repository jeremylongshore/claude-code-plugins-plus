#!/usr/bin/env bash
# Catalog: C7 — `Co-Authored-By: Claude` trailer present in commits the repo has banned it
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Only run if dossier flags this repo as forbidding the Claude co-author trailer
FORBIDDEN=$(fm_field "$GATE_DOSSIER_PATH" "coauthor_claude_forbidden")
if [[ "$FORBIDDEN" != "true" ]]; then
  gate_skip "dossier does not forbid Co-Authored-By: Claude"
fi

CLONE_DIR="$HOME/000-projects/contributing-clanker/${GATE_REPO##*/}"
if [[ ! -d "$CLONE_DIR/.git" ]]; then
  gate_skip "no clone at $CLONE_DIR (not a git repo)"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
if [[ -z "$DEFAULT_BRANCH" ]]; then
  gate_skip "no default_branch in dossier"
fi

# Inspect commit messages between default branch and HEAD on the working clone
LOG=$(/usr/bin/git -C "$CLONE_DIR" log "${DEFAULT_BRANCH}..HEAD" --format=%B 2>/dev/null || /usr/bin/echo "")

if /usr/bin/printf '%s' "$LOG" | /usr/bin/grep -qiE "Co-Authored-By:[[:space:]]+Claude"; then
  gate_block "commits contain 'Co-Authored-By: Claude' trailer" "remove via git rebase -i and dropping the trailer; this repo's AI policy forbids it"
fi

gate_pass "no Co-Authored-By: Claude trailer in commits"
