#!/usr/bin/env bash
# Catalog: C11 — branch divergence implies force-push will be required
# Mitigates: collaborators with local refs to this branch get rebased out from under them.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

REPO_NAME="${GATE_REPO##*/}"
CLONE="$HOME/000-projects/contributing-clanker/$REPO_NAME"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

BRANCH=$(fm_field "$GATE_CANDIDATE_PATH" "branch")
if [[ -z "$BRANCH" ]]; then
  gate_skip "no branch in candidate frontmatter"
fi

# Confirm the upstream tracking ref exists
if ! /usr/bin/git -C "$CLONE" rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
  gate_skip "no origin/$BRANCH tracking ref — first push, force not implied"
fi

AHEAD=$(/usr/bin/git -C "$CLONE" log "origin/$BRANCH..HEAD" --oneline 2>/dev/null | /usr/bin/grep -c . || /usr/bin/echo 0)
BEHIND=$(/usr/bin/git -C "$CLONE" log "HEAD..origin/$BRANCH" --oneline 2>/dev/null | /usr/bin/grep -c . || /usr/bin/echo 0)

if [[ "$AHEAD" -gt 0 && "$BEHIND" -gt 0 ]]; then
  gate_warn "branch diverges from origin/$BRANCH — push will require force; ensure no other contributors have local refs to this branch" "push directly only if you're the sole owner of this branch"
fi

gate_pass "branch is fast-forward to origin/$BRANCH (no force-push needed)"
