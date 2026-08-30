#!/usr/bin/env bash
# Catalog: C19 — PR body claims that don't match the diff
# Mitigates: Round-1 maintainer GAP-6 — close-on-sight pattern: PR body
# claims "added tests" / "updated CHANGELOG" / "added migration notes" but
# `git diff` shows no corresponding files touched. Pure AI-confabulation.
# Fastest path from "AI-assisted" to "AI-fabricated" in maintainer's eye.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

# Need both PR body and a way to inspect the diff
PR_BODY=$(/usr/bin/awk '/^## PR body/{flag=1;next} /^## /{flag=0} flag' "$GATE_CANDIDATE_PATH" 2>/dev/null || /usr/bin/echo "")
LOCAL_CLONE=$(fm_field "$GATE_CANDIDATE_PATH" "local_clone_path")
BRANCH=$(fm_field "$GATE_CANDIDATE_PATH" "branch")

if [[ -z "$PR_BODY" ]]; then
  gate_inform "no PR body drafted yet"
fi
if [[ -z "$LOCAL_CLONE" || ! -d "$LOCAL_CLONE" ]]; then
  gate_skip "no local_clone_path; cannot inspect diff"
fi
if [[ -z "$BRANCH" ]]; then
  gate_skip "no branch in candidate"
fi

# Get the list of changed files vs default branch (heuristic: master/main)
DEFAULT_BRANCH="main"
if [[ -n "$GATE_DOSSIER_PATH" && -f "$GATE_DOSSIER_PATH" ]]; then
  V=$(fm_field "$GATE_DOSSIER_PATH" "default_branch")
  [[ -n "$V" ]] && DEFAULT_BRANCH="$V"
fi

DIFF_FILES=$(cd "$LOCAL_CLONE" 2>/dev/null && git diff --name-only "origin/$DEFAULT_BRANCH..$BRANCH" 2>/dev/null || /usr/bin/echo "")
if [[ -z "$DIFF_FILES" ]]; then
  gate_skip "no diff against origin/$DEFAULT_BRANCH (or git command failed)"
fi

# Claim → expected-path patterns. Each entry: regex_in_body | regex_required_in_diff
declare -a CLAIMS=(
  "(added|wrote|new) tests?\b|added test (coverage|cases)|test cases? added|regression test|test for the (bug|fix)|tests?[[:space:]]*passing:[[:space:]]+(yes|added)|cargo test|pytest|jest|mocha|vitest=tests?/"
  "updated? (the )?CHANGELOG=CHANGELOG"
  "(added|updated) (the )?(migration|migration notes|migrations)=(migration|migrations)/"
  "updated? (the )?(README|docs|documentation)=(README|docs/|.md$)"
  "added? (the )?changeset=\.changeset/"
)

ISSUES=()
for ENTRY in "${CLAIMS[@]}"; do
  CLAIM_REGEX="${ENTRY%%=*}"
  PATH_REGEX="${ENTRY##*=}"
  if /usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -qiE "$CLAIM_REGEX"; then
    if ! /usr/bin/printf '%s' "$DIFF_FILES" | /usr/bin/grep -qiE "$PATH_REGEX"; then
      MATCHED=$(/usr/bin/printf '%s' "$PR_BODY" | /usr/bin/grep -ioE "$CLAIM_REGEX" | /usr/bin/head -1)
      ISSUES+=("body claims '$MATCHED' but diff doesn't touch $PATH_REGEX")
    fi
  fi
done

if [[ "${#ISSUES[@]}" -gt 0 ]]; then
  REASONS=$(/usr/bin/printf '%s; ' "${ISSUES[@]}")
  gate_block "PR body makes claims not backed by the diff: $REASONS" "either add the work to match the claim, OR remove the claim from the PR body. False claims = closure regardless of code quality (PostHog AI_POLICY: 'PRs that clearly weren't run or tested will be closed')."
fi

gate_pass "PR body claims are consistent with diff"
