#!/usr/bin/env bash
# Catalog: F4 — Override disclosure required in PR body
# Mitigates: Round-1 maintainer GAP-10 + security GAP-2 + portfolio GAP-3 —
# `--override-gate=<id>` writes audit trail to log.jsonl + candidate .md, but
# both are private to the contributor. From the maintainer's POV, the
# override mechanism is plausible-deniability theater. This gate forces any
# PR submitted with overrides to include a `## Safety override disclosure`
# section in the PR body listing each override + reason.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Read overrides from candidate frontmatter
OVERRIDES=$(/usr/bin/awk '/^overrides:/{flag=1;next} /^[a-z_]+:/{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$OVERRIDES" ]]; then
  gate_pass "no overrides used; nothing to disclose"
fi

# Count overrides
OVERRIDE_COUNT=$(/usr/bin/printf '%s\n' "$OVERRIDES" | /usr/bin/grep -c 'gate:' || /usr/bin/echo 0)

# Read PR body draft from candidate (## PR body section)
PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$PR_BODY" ]]; then
  gate_inform "$OVERRIDE_COUNT overrides used but no PR body drafted yet — re-run at open-pr"
fi

# Look for the disclosure section in the PR body
if /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qiE '^## (Safety override|Override) disclosure'; then
  # Check that each override gate ID is mentioned in the body
  MISSING=()
  while IFS= read -r OG; do
    GID=$(/usr/bin/printf '%s' "$OG" | /usr/bin/grep -oP 'gate:\s*\K[A-Z0-9]+')
    [[ -z "$GID" ]] && continue
    if ! /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qE "\b$GID\b"; then
      MISSING+=("$GID")
    fi
  done < <(/usr/bin/printf '%s\n' "$OVERRIDES" | /usr/bin/grep 'gate:')

  if [[ "${#MISSING[@]}" -eq 0 ]]; then
    gate_pass "all $OVERRIDE_COUNT overrides disclosed in PR body"
  else
    gate_block "PR body has '## Safety override disclosure' section but doesn't mention overrides: ${MISSING[*]}" "list each override gate ID in the disclosure section with the reason you used it"
  fi
fi

gate_block "$OVERRIDE_COUNT safety overrides used but PR body lacks '## Safety override disclosure' section" "add a section to the PR body enumerating each override + reason. This is the maintainer-visible audit trail; without it the override mechanism is invisible to the people the safety system is supposed to protect."
