#!/usr/bin/env bash
# Catalog: G4 — manual version bump in a repo that uses semantic-release / changesets
# Mitigates: clobbers release tooling, breaks semver, signals unfamiliarity with workflow.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier — cannot determine auto_version policy"
fi

AUTO=$(fm_field "$GATE_DOSSIER_PATH" "auto_version")
if [[ "$AUTO" != "true" ]]; then
  gate_skip "dossier auto_version is not true"
fi

REPO_NAME="${GATE_REPO##*/}"
CLONE="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

DEFAULT_BRANCH=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
[[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

DIFF=$(/usr/bin/git -C "$CLONE" diff "$DEFAULT_BRANCH..HEAD" -- package.json Cargo.toml pyproject.toml 2>/dev/null || /usr/bin/echo "")

# Look for added lines that look like version field updates
HITS=$(/usr/bin/printf '%s\n' "$DIFF" | /usr/bin/grep -E '^\+[[:space:]]*("version"[[:space:]]*:|version[[:space:]]*=)' || /usr/bin/echo "")

if [[ -z "$HITS" ]]; then
  gate_pass "no manual version field changes detected"
fi

gate_warn "diff appears to bump a version field (package.json / Cargo.toml / pyproject.toml)" "this repo uses semantic-release / changesets; don't bump versions manually"
