#!/usr/bin/env bash
# Catalog: C13 — Required review bots haven't reviewed/commented yet
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

PR_NUMBER=$(fm_field "$GATE_CANDIDATE_PATH" "pr_number")
if [[ -z "$PR_NUMBER" ]]; then
  gate_skip "no pr_number in candidate (no PR yet)"
fi

# Parse review_bots: list from dossier — `  - <name>` lines following `review_bots:`
BOTS_RAW=$(/usr/bin/awk '
  /^---$/ { fm = !fm ? 1 : 2; next }
  fm != 1 { next }
  /^review_bots:/ { collecting = 1; next }
  collecting && /^[[:space:]]+-[[:space:]]+/ {
    sub(/^[[:space:]]+-[[:space:]]+/, "")
    gsub(/^"|"$/, "")
    print
    next
  }
  collecting && /^[A-Za-z]/ { collecting = 0 }
' "$GATE_DOSSIER_PATH" 2>/dev/null || /usr/bin/echo "")

if [[ -z "$BOTS_RAW" ]]; then
  gate_skip "no review_bots listed in dossier"
fi

# Filter "(none detected)" sentinel
declare -a BOTS=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  [[ "$line" == "(none detected)" ]] && continue
  BOTS+=("$line")
done <<< "$BOTS_RAW"

if (( ${#BOTS[@]} == 0 )); then
  gate_skip "review_bots list empty or (none detected)"
fi

# Pull all reviewer + commenter logins from the PR
REVIEWERS=$(gh_safe pr view "$PR_NUMBER" --repo "$GATE_REPO" --json reviews,comments \
  --jq '[.reviews[].author.login, .comments[].author.login] | unique | join(",")' 2>/dev/null || /usr/bin/echo "")

# For each required bot, substring match against the reviewers/commenters list (lowercased)
REVIEWERS_LC=$(/usr/bin/printf '%s' "$REVIEWERS" | /usr/bin/tr '[:upper:]' '[:lower:]')
declare -a MISSING=()
for bot in "${BOTS[@]}"; do
  bot_lc=$(/usr/bin/printf '%s' "$bot" | /usr/bin/tr '[:upper:]' '[:lower:]' | /usr/bin/tr -d '-')
  reviewers_norm=$(/usr/bin/printf '%s' "$REVIEWERS_LC" | /usr/bin/tr -d '-')
  if [[ "$reviewers_norm" != *"$bot_lc"* ]]; then
    MISSING+=("$bot")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  joined=$(IFS=', '; /usr/bin/printf '%s' "${MISSING[*]}")
  gate_warn "waiting on review from: $joined" "wait for these bots to weigh in before flipping to ready-for-review"
fi

gate_pass "all required review bots have engaged on the PR"
