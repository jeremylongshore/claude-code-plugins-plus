#!/usr/bin/env bash
# Catalog: B14 — No recent green local check-run for current branch
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

if [[ -z "$GATE_DOSSIER_PATH" || ! -f "$GATE_DOSSIER_PATH" ]]; then
  gate_skip "no dossier"
fi

CMD=$(fm_field "$GATE_DOSSIER_PATH" "local_check_command")
if [[ -z "$CMD" || "$CMD" == "(not detected)" ]]; then
  gate_skip "no local_check_command in dossier"
fi

BRANCH=$(fm_field "$GATE_CANDIDATE_PATH" "branch")
if [[ -z "$BRANCH" ]]; then
  gate_skip "no branch in candidate frontmatter"
fi

REPO_SLUG=$(/usr/bin/printf '%s' "$GATE_REPO" | /usr/bin/tr '/' '_' | /usr/bin/tr '/' '_')
# tr collapses single chars; doubled to satisfy the convention "owner/repo -> owner__repo"
REPO_SLUG=$(/usr/bin/printf '%s' "$GATE_REPO" | /usr/bin/sed 's|/|__|g')

EVIDENCE="$HOME/.contribute-system/check-runs/${REPO_SLUG}__${BRANCH}.json"

if [[ ! -f "$EVIDENCE" ]]; then
  gate_block "no local check evidence for $BRANCH" "run the project's check command: $CMD"
fi

PASSED=$(jq -r '.passed // false' "$EVIDENCE" 2>/dev/null || /usr/bin/echo "false")
TS=$(jq -r '.ts // ""' "$EVIDENCE" 2>/dev/null || /usr/bin/echo "")

if [[ "$PASSED" != "true" ]]; then
  gate_block "last local check run did not pass" "re-run after fixing: $CMD"
fi

if [[ -z "$TS" ]]; then
  gate_warn "evidence file lacks timestamp" "re-run: $CMD"
fi

# Compare ts to now; warn if older than 1h.
NOW_EPOCH=$(/usr/bin/date -u +%s)
TS_EPOCH=$(/usr/bin/date -u -d "$TS" +%s 2>/dev/null || /usr/bin/echo "0")

if [[ "$TS_EPOCH" -eq 0 ]]; then
  gate_warn "could not parse evidence ts=$TS" "re-run: $CMD"
fi

AGE=$(( NOW_EPOCH - TS_EPOCH ))
if [[ "$AGE" -gt 3600 ]]; then
  gate_warn "last green check is $((AGE / 60))min old (>1h)" "re-run: $CMD"
fi

gate_pass "local checks passed at $TS"
