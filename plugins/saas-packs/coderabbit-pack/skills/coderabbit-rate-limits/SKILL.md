---
name: coderabbit-rate-limits
description: |
  Understand and handle CodeRabbit and GitHub API rate limits for review automation.
  Use when hitting rate limits on @coderabbitai commands, automating review queries,
  or building scripts that interact with CodeRabbit via the GitHub API.
  Trigger with phrases like "coderabbit rate limit", "coderabbit throttling",
  "coderabbit too many requests", "github api rate limit coderabbit".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, rate-limits, github-api]

---
# CodeRabbit Rate Limits

## Overview
CodeRabbit rate limits apply at two levels: (1) CodeRabbit's own processing limits on how many reviews it can run concurrently, and (2) GitHub API rate limits when you build automation that queries CodeRabbit review data. This skill covers both and provides patterns for handling limits gracefully.

## Prerequisites
- CodeRabbit installed on repository
- GitHub CLI (`gh`) or API access for automation
- Understanding of GitHub rate limit headers

## Rate Limit Tiers

### CodeRabbit Review Processing
| Factor | Limit | Notes |
|--------|-------|-------|
| Concurrent reviews per org | Varies by plan | Free: 1, Pro: 5, Enterprise: custom |
| Max PR size | ~3000 files | Larger PRs may timeout |
| Re-review cooldown | ~30 seconds | Between `@coderabbitai full review` commands |
| Command rate | ~10/minute/repo | PR comment commands |

### GitHub API (Affects Automation Scripts)
| Tier | Rate Limit | Reset Window |
|------|-----------|--------------|
| Unauthenticated | 60 req/hour | Rolling |
| Personal Access Token | 5,000 req/hour | Rolling |
| GitHub App | 5,000 req/hour/installation | Rolling |
| `gh` CLI | 5,000 req/hour | Rolling |

## Instructions

### Step 1: Check Current GitHub API Rate Limit
```bash
set -euo pipefail
# Check your current rate limit status
gh api rate_limit --jq '{
  core: {
    limit: .resources.core.limit,
    remaining: .resources.core.remaining,
    reset: (.resources.core.reset | todate)
  },
  search: {
    limit: .resources.search.limit,
    remaining: .resources.search.remaining,
    reset: (.resources.search.reset | todate)
  }
}'
```

### Step 2: Handle Rate Limits in Automation Scripts
```bash
#!/bin/bash
# rate-safe-query.sh - GitHub API queries with rate limit awareness
set -euo pipefail

ORG="${1:?Usage: $0 <org> <repo>}"
REPO="${2:?Usage: $0 <org> <repo>}"

# Check remaining rate limit before bulk queries
REMAINING=$(gh api rate_limit --jq '.resources.core.remaining')
echo "GitHub API calls remaining: $REMAINING"

if [ "$REMAINING" -lt 100 ]; then
  RESET=$(gh api rate_limit --jq '.resources.core.reset | todate')
  echo "WARNING: Low rate limit. Resets at $RESET"
  echo "Consider waiting or reducing query scope."
  exit 1
fi

# Safe pagination: process in small batches
PAGE=1
PER_PAGE=10
while true; do
  RESULT=$(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=$PER_PAGE&page=$PAGE" --jq 'length')
  [ "$RESULT" -eq 0 ] && break

  gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=$PER_PAGE&page=$PAGE" \
    --jq '.[].number' | while read -r PR_NUM; do
    # Process each PR
    echo "Processing PR #$PR_NUM"

    # Rate-limit-safe: check remaining before each sub-query
    SUB_REMAINING=$(gh api rate_limit --jq '.resources.core.remaining')
    if [ "$SUB_REMAINING" -lt 50 ]; then
      echo "Rate limit low ($SUB_REMAINING remaining). Pausing..."
      sleep 60
    fi

    gh api "repos/$ORG/$REPO/pulls/$PR_NUM/reviews" \
      --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null
  done

  PAGE=$((PAGE + 1))
  [ "$PAGE" -gt 5 ] && break   # Safety limit
done
```

### Step 3: Handle CodeRabbit Command Rate Limits
```markdown
# If you send too many @coderabbitai commands in quick succession,
# CodeRabbit may not respond to all of them.

# Best practices:
1. Wait for CodeRabbit to finish one command before sending another
2. Don't spam "full review" -- one is enough, it processes the latest
3. Use "summary" instead of "full review" if you just want the walkthrough
4. Wait 2-5 minutes after PR push for the initial review before using commands

# Rate limit symptoms:
# - CodeRabbit doesn't respond to a command
# - Review appears incomplete
# - Multiple partial reviews on the same PR

# Fix: Wait 1-2 minutes and resend the command once.
```

### Step 4: Efficient Bulk Queries with GraphQL
```bash
set -euo pipefail
ORG="${1:-your-org}"
REPO="${2:-your-repo}"

# GraphQL uses far fewer API calls than REST for bulk data
# One GraphQL call = data that would take 20+ REST calls
gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(last: 20, states: [MERGED, CLOSED]) {
      nodes {
        number
        title
        reviews(first: 5) {
          nodes {
            author { login }
            state
            submittedAt
          }
        }
      }
    }
  }
}' -f owner="$ORG" -f repo="$REPO" --jq '
  .data.repository.pullRequests.nodes[] |
  {
    pr: .number,
    title: .title,
    coderabbit_reviews: [.reviews.nodes[] | select(.author.login == "coderabbitai")] | length,
    coderabbit_state: ([.reviews.nodes[] | select(.author.login == "coderabbitai")] | last | .state) // "none"
  }'
```

### Step 5: Cache CodeRabbit Metrics
```bash
#!/bin/bash
# cache-coderabbit-metrics.sh - Cache review data to avoid repeated API calls
set -euo pipefail

ORG="${1:?Usage: $0 <org> <repo>}"
REPO="${2:?Usage: $0 <org> <repo>}"
CACHE_FILE="/tmp/coderabbit-metrics-$ORG-$REPO.json"
CACHE_TTL=3600  # 1 hour

# Check cache freshness
if [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE") ))
  if [ "$CACHE_AGE" -lt "$CACHE_TTL" ]; then
    echo "Using cached data (age: ${CACHE_AGE}s)"
    cat "$CACHE_FILE"
    exit 0
  fi
fi

echo "Fetching fresh data..."
METRICS=$(gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(last: 50, states: [MERGED, CLOSED]) {
      totalCount
      nodes {
        number
        reviews(first: 5) {
          nodes {
            author { login }
            state
          }
        }
      }
    }
  }
}' -f owner="$ORG" -f repo="$REPO" --jq '
  .data.repository.pullRequests | {
    total: .totalCount,
    reviewed: [.nodes[] | select([.reviews.nodes[] | select(.author.login == "coderabbitai")] | length > 0)] | length,
    approved: [.nodes[] | select([.reviews.nodes[] | select(.author.login == "coderabbitai" and .state == "APPROVED")] | length > 0)] | length
  }')

echo "$METRICS" | tee "$CACHE_FILE"
```

## Output
- GitHub API rate limit status checked
- Automation scripts with rate limit awareness
- CodeRabbit command rate limits documented
- Efficient GraphQL queries for bulk data
- Caching strategy to reduce API calls

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `gh api` returns 403 | Rate limit exceeded | Wait for reset or use GraphQL |
| CodeRabbit ignores command | Too many commands | Wait 1-2 min, resend once |
| Bulk script fails mid-run | Rate limit hit during iteration | Add rate limit check in loop |
| GraphQL query fails | Malformed query | Validate query in GitHub GraphQL Explorer |
| Stale cached data | Cache TTL too long | Reduce TTL or force refresh |

## Resources
- [GitHub Rate Limits](https://docs.github.com/en/rest/rate-limit)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [CodeRabbit Review Commands](https://docs.coderabbit.ai/reference/review-commands)

## Next Steps
For security configuration, see `coderabbit-security-basics`.
