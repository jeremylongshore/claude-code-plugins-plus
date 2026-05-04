#!/usr/bin/env bash
# Catalog: E4 — Verify origin points at user's fork (not upstream)
# Mitigates: pushing to someone else's repo by accident, or being unable to
# push at all.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

CLONE="$HOME/000-projects/contributing-clanker/${GATE_REPO##*/}"

if [[ ! -d "$CLONE/.git" ]]; then
  gate_skip "no local clone at $CLONE"
fi

USER_LOGIN=$(gh_safe api user --jq .login 2>/dev/null || /usr/bin/echo "")
if [[ -z "$USER_LOGIN" ]]; then
  gate_skip "could not resolve current gh user login"
fi

ORIGIN_URL=$(/usr/bin/git -C "$CLONE" remote get-url origin 2>/dev/null || /usr/bin/echo "")
if [[ -z "$ORIGIN_URL" ]]; then
  gate_block "no origin remote configured in $CLONE" "set origin to your fork: gh repo fork ${GATE_REPO} --remote --remote-name origin"
fi

# Parse owner from URL — handles SSH (git@github.com:owner/repo.git) and
# HTTPS (https://github.com/owner/repo.git) forms.
ORIGIN_OWNER=$(/usr/bin/printf '%s' "$ORIGIN_URL" | /usr/bin/sed -E 's#^git@github\.com:([^/]+)/.*$#\1#; s#^https?://github\.com/([^/]+)/.*$#\1#')

UPSTREAM_OWNER="${GATE_REPO%%/*}"

if [[ "$ORIGIN_OWNER" == "$UPSTREAM_OWNER" ]]; then
  gate_inform "origin points at upstream ($UPSTREAM_OWNER); pushing directly to upstream — verify you have access"
fi

if [[ "$ORIGIN_OWNER" != "$USER_LOGIN" ]]; then
  gate_block "origin owner is '$ORIGIN_OWNER' but your gh login is '$USER_LOGIN'" "set origin to your fork: gh repo fork ${GATE_REPO} --remote --remote-name origin"
fi

gate_pass "origin points at your fork ($USER_LOGIN/${GATE_REPO##*/})"
