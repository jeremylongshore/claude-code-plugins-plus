#!/usr/bin/env bash
# Catalog: B12 — diff introduces new dependencies without prior issue conversation
# Mitigates: maintainers strongly prefer dep additions to be discussed first.
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

DIFF=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" -- package.json Cargo.toml pyproject.toml requirements.txt go.mod 2>/dev/null || /usr/bin/echo "")

if [[ -z "$DIFF" ]]; then
  gate_pass "no manifest files changed"
fi

# Heuristic: look for added dep lines across the supported manifest formats.
NEW_DEPS=$(/usr/bin/printf '%s\n' "$DIFF" \
  | /usr/bin/grep -E '^\+([[:space:]]*"[A-Za-z0-9_@/.-]+"[[:space:]]*:[[:space:]]*"[^"]+",?$|[[:space:]]*[a-zA-Z][A-Za-z0-9_-]*[[:space:]]*=[[:space:]]*".*"$|[a-zA-Z][A-Za-z0-9_.-]*([<>=!~].*)?$)' \
  | /usr/bin/grep -vE '^\+\+\+|^\+[[:space:]]*#|^\+[[:space:]]*"version"' \
  | /usr/bin/sed -E 's/^\+[[:space:]]*//; s/[[:space:]]*=.*$//; s/^"//; s/".*$//; s/[<>=!~].*$//' \
  | /usr/bin/grep -v '^[[:space:]]*$' \
  || /usr/bin/echo "")

if [[ -z "$NEW_DEPS" ]]; then
  gate_pass "no new dependency entries detected in manifest diffs"
fi

LIST=$(/usr/bin/printf '%s' "$NEW_DEPS" | /usr/bin/tr '\n' ',' | /usr/bin/sed 's/,$//')
gate_warn "diff appears to add new dependencies: $LIST" "new dependencies usually warrant an issue conversation first; check the issue thread for prior discussion"
