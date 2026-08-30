#!/usr/bin/env bash
# Catalog: A4 — Issue is too old (stale, abandoned, or contested)
# Mitigates: stale issues are a real anti-signal — either the maintainer
# decided not to fix it, the underlying code changed and the issue's premise
# no longer holds, or someone has been silently working on it for months
# without progress. None of those are good for our merge probability.
#
# Thresholds (configurable via dossier `max_issue_age_days:`):
#   issue_age <= 90 days             → PASS
#   issue_age 91-180 days            → WARN ("aging — verify it's still actionable")
#   issue_age 181-365 days           → BLOCK ("stale; recommend pick a fresher target")
#   issue_age > 365 days             → BLOCK + harder ("zombie issue; fix likely landed elsewhere")
#
# A repo with `max_issue_age_days: N` in dossier overrides the default 180.
source "$(dirname "$0")/lib/preamble.sh"

gate_read_input

ISSUE_NUM=$(fm_field "$GATE_CANDIDATE_PATH" "issue_number")
if [[ -z "$ISSUE_NUM" || -z "$GATE_REPO" ]]; then
  gate_skip "no issue_number or repo in candidate"
fi

# Read max_issue_age from dossier, default 180
MAX_AGE_DAYS=180
if [[ -n "$GATE_DOSSIER_PATH" && -f "$GATE_DOSSIER_PATH" ]]; then
  V=$(fm_field "$GATE_DOSSIER_PATH" "max_issue_age_days")
  [[ -n "$V" && "$V" =~ ^[0-9]+$ ]] && MAX_AGE_DAYS="$V"
fi

# Live fetch — issue createdAt + last activity (updatedAt + last comment)
META_JSON=$(gh_safe issue view "$ISSUE_NUM" --repo "$GATE_REPO" --json createdAt,updatedAt,comments --jq '{createdAt, updatedAt, last_comment_at: (.comments | sort_by(.createdAt) | .[-1].createdAt // null)}' || /usr/bin/echo "")

if [[ -z "$META_JSON" ]] ; then
  gate_skip "couldn't fetch issue metadata (gh failure?)"
fi

CREATED=$(/usr/bin/printf '%s' "$META_JSON" | jq -r '.createdAt // ""')
UPDATED=$(/usr/bin/printf '%s' "$META_JSON" | jq -r '.updatedAt // ""')
LAST_COMMENT=$(/usr/bin/printf '%s' "$META_JSON" | jq -r '.last_comment_at // ""')

if [[ -z "$CREATED" ]] ; then
  gate_skip "issue createdAt missing in API response"
fi

NOW_EPOCH=$(/usr/bin/date -u +%s)
CREATED_EPOCH=$(/usr/bin/date -u -d "$CREATED" +%s 2>/dev/null || echo 0)
AGE_DAYS=$(( (NOW_EPOCH - CREATED_EPOCH) / 86400 ))

# Activity recency — most recent of updatedAt or last comment
LATEST_ACT_EPOCH=0
if [[ -n "$UPDATED" ]] ; then
  V=$(/usr/bin/date -u -d "$UPDATED" +%s 2>/dev/null || echo 0)
  [[ "$V" -gt "$LATEST_ACT_EPOCH" ]] && LATEST_ACT_EPOCH="$V"
fi
if [[ -n "$LAST_COMMENT" && "$LAST_COMMENT" != "null" ]] ; then
  V=$(/usr/bin/date -u -d "$LAST_COMMENT" +%s 2>/dev/null || echo 0)
  [[ "$V" -gt "$LATEST_ACT_EPOCH" ]] && LATEST_ACT_EPOCH="$V"
fi
SILENCE_DAYS=$(( (NOW_EPOCH - LATEST_ACT_EPOCH) / 86400 ))

# Verdicts
if [[ "$AGE_DAYS" -gt 365 ]] ; then
  gate_block "issue is ${AGE_DAYS}d old (>365d zombie threshold)" "1+ year-old issues are usually either fixed elsewhere, abandoned, or have premises that no longer apply. Pick a fresher target. Override only with a written rationale referencing what's changed."
fi

if [[ "$AGE_DAYS" -gt "$MAX_AGE_DAYS" ]] ; then
  gate_block "issue is ${AGE_DAYS}d old (max for this repo: ${MAX_AGE_DAYS}d)" "stale issue. Maintainer engagement likely dropped. Pick a fresher target — or override with rationale if you have direct maintainer signal that it's still wanted."
fi

# Activity-based check — even fresh issues with long silence are suspect
if [[ "$SILENCE_DAYS" -gt 90 ]] ; then
  gate_warn "issue is fresh (${AGE_DAYS}d old) but no activity in ${SILENCE_DAYS}d" "comment first to ping for current relevance before investing time"
fi

if [[ "$AGE_DAYS" -gt 90 ]] ; then
  gate_warn "issue is ${AGE_DAYS}d old (aging — under the ${MAX_AGE_DAYS}d block threshold but past the 90d sweet spot)" "verify the underlying premise still holds in current code; verify maintainer still wants this fix"
fi

gate_pass "issue is ${AGE_DAYS}d old, last activity ${SILENCE_DAYS}d ago"
