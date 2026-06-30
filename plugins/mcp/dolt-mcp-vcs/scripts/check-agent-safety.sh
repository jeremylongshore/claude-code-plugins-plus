#!/usr/bin/env bash
# check-agent-safety.sh — the §10 union safety gate (blueprint §3 / blocker B1-iii).
#
# Asserts the mutation-verb taxonomy is enforced at the GRANT layer, across BOTH
# the MCP and the Bash surfaces (the original gate inspected only `mcp__*` and was
# blind to the Bash door). For every agent (and the core skill) it checks the
# tool ALLOWLIST — never the denylist — for:
#
#   1. no `Bash(<cmd>:*)` wildcard that reaches a history-affecting op
#      (bash/sh = arbitrary; dolt/bd/bd-sync/git = push/reset/branch -D/killall);
#   2. no granted MCP tool outside the read/safe set (so a future `…__exec`,
#      `…__merge`, `…__push`, `…__reset` grant fails the build).
#
# `disallowedTools` (the kebab/camel denylists) are intentionally NOT scanned —
# a destructive pattern there is the mitigation, not a violation.
#
# Usage:  scripts/check-agent-safety.sh        (exit 0 = pass, 1 = violation)
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FORBIDDEN_WILDCARD='Bash\((bash|sh|dolt|bd|bd-sync|git):\*\)'
ALLOWED_MCP='query|list_databases|list_dolt_commits|list_dolt_branches|show_tables'
fail=0
checked=0

check_allowlist() {
  local f="$1" field="$2" line val
  line=$(grep -m1 -E "^${field}:" "$f" 2>/dev/null || true)
  [ -n "$line" ] || return 0
  checked=$((checked + 1))
  val=${line#*:}

  if echo "$val" | grep -qE "$FORBIDDEN_WILDCARD"; then
    echo "FAIL: $(basename "$f") — allowlist holds a forbidden wildcard Bash grant:" \
         "$(echo "$val" | grep -oE "$FORBIDDEN_WILDCARD" | tr '\n' ' ')"
    fail=1
  fi

  local tok name
  for tok in $(echo "$val" | grep -oE 'mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_]+' || true); do
    name=${tok##*__}
    if ! echo "$name" | grep -qE "^(${ALLOWED_MCP})$"; then
      echo "FAIL: $(basename "$f") — grants non-read MCP tool '$tok' (not in the read/safe set)"
      fail=1
    fi
  done
}

shopt -s nullglob
for f in "$ROOT"/agents/*.md; do
  check_allowlist "$f" "tools"
done
for f in "$ROOT"/skills/*/SKILL.md; do
  check_allowlist "$f" "allowed-tools"
done

if [ "$fail" -eq 0 ]; then
  echo "PASS: §10 safety gate — $checked allowlist(s) clean (no history-affecting Bash wildcard; no non-read MCP grant)."
else
  echo "----"
  echo "The mutation-verb taxonomy is violated: a read/safe-write agent or the core skill"
  echo "holds a grant that reaches a history-affecting operation. Narrow it to explicit"
  echo "read-only subcommands and move destructive forms to disallowedTools / recommend-only."
fi
exit "$fail"
