#!/usr/bin/env bash
# Catalog: F3 — new fixture / sample files that may contain copyrighted external content
# Mitigates: copying real-world web/user content into fixtures triggers license takedowns.
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

ADDED=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" --name-only --diff-filter=A 2>/dev/null || /usr/bin/echo "")

FIXTURES=$(/usr/bin/printf '%s\n' "$ADDED" | /usr/bin/grep -E '(tests/fixtures/|tests/data/|__fixtures__/|(^|/)fixtures/|test_data/|testdata/|(^|/)samples/)' || /usr/bin/echo "")

if [[ -z "$FIXTURES" ]]; then
  gate_pass "no new fixture / sample files added"
fi

LIST=$(/usr/bin/printf '%s' "$FIXTURES" | /usr/bin/tr '\n' ',' | /usr/bin/sed 's/,$//')
gate_inform "new fixture / sample files added — verify provenance manually: $LIST"
