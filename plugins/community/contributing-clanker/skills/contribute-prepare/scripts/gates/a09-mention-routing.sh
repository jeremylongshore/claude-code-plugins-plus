#!/usr/bin/env bash
# Catalog: A9 — @-mentions in claim/PR text when CODEOWNERS routing exists
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

# Check for CODEOWNERS in dossier — frontmatter policy_files OR Policy file inventory section
HAS_CODEOWNERS=""
POLICY_FM=$(fm_field "$GATE_DOSSIER_PATH" "policy_files")
if /usr/bin/printf '%s' "$POLICY_FM" | /usr/bin/grep -qi "CODEOWNERS"; then
  HAS_CODEOWNERS=1
fi
if [[ -z "$HAS_CODEOWNERS" ]]; then
  if /usr/bin/awk '/^## Policy file inventory/{flag=1;next} /^## /{flag=0} flag' "$GATE_DOSSIER_PATH" 2>/dev/null | /usr/bin/grep -qi "\*\*CODEOWNERS\*\*"; then
    HAS_CODEOWNERS=1
  fi
fi

if [[ -z "$HAS_CODEOWNERS" ]]; then
  gate_skip "no CODEOWNERS in dossier policy inventory"
fi

# Pick the right draft section based on action
SECTION=""
case "$GATE_ACTION" in
  *post-comment*|*claim*) SECTION="## Claim comment draft" ;;
  *open-pr*|*pr*) SECTION="## PR body" ;;
  *) SECTION="## Claim comment draft" ;;
esac

DRAFT=$(/usr/bin/awk -v s="$SECTION" 'BEGIN{flag=0} $0==s{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$DRAFT" ]]; then
  gate_skip "no draft section found in candidate"
fi

# Count @-mentions, excluding @me, @everyone, @channel.
# Use awk (single pass, no pipeline-failure surface) instead of a chained
# grep | grep | wc — under set -uo pipefail, an empty `grep -oE` returns
# exit 1, killing the whole pipeline, even though "no mentions" is the
# correct/expected answer for most drafts.
MENTIONS=$(/usr/bin/printf '%s' "$DRAFT" | /usr/bin/awk '
  {
    for (i = 1; i <= NF; i++) {
      tok = $i
      gsub(/[,.;:!?)\]"\x27]+$/, "", tok)
      if (tok ~ /^@[a-zA-Z0-9-]{2,}$/ && tok !~ /^@(me|everyone|channel)$/) {
        c++
      }
    }
  }
  END { print c + 0 }
')

if [[ "${MENTIONS:-0}" -ge 1 ]]; then
  gate_warn "$MENTIONS @-mention(s) in draft despite CODEOWNERS routing" "this repo uses CODEOWNERS; explicit @-mentions are usually noise. Drop them unless you have a specific reason to ping someone."
fi

gate_pass "no @-mentions in draft"
