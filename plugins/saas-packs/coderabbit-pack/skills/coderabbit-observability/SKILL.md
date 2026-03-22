---
name: coderabbit-observability
description: |
  Monitor CodeRabbit review effectiveness with metrics, dashboards, and alerts.
  Use when tracking review coverage, measuring comment acceptance rates,
  or building dashboards for CodeRabbit adoption across your organization.
  Trigger with phrases like "coderabbit monitoring", "coderabbit metrics",
  "coderabbit observability", "monitor coderabbit", "coderabbit alerts", "coderabbit dashboard".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, monitoring, observability, metrics]

---
# CodeRabbit Observability

## Overview
Monitor CodeRabbit AI code review effectiveness, review latency, and team adoption. Key metrics include time-to-first-review (how fast CodeRabbit posts after PR creation), comment acceptance rate (comments resolved vs dismissed), review coverage (percentage of PRs reviewed), and per-repository review volume.

## Prerequisites
- CodeRabbit installed on GitHub/GitLab organization
- GitHub CLI (`gh`) authenticated with org access
- Access to CodeRabbit dashboard at app.coderabbit.ai

## Key Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Review coverage | > 90% | PRs without review = blind spots |
| Time-to-review | < 5 min | Fast feedback keeps developers in flow |
| Comment acceptance | > 40% | Low acceptance = noisy reviews |
| Comments per PR | 3-8 | Too many = fatigue, too few = not useful |
| Review state: APPROVED | > 60% | High approval = clean code culture |

## Instructions

### Step 1: Measure Review Coverage
```bash
#!/bin/bash
# coderabbit-coverage.sh - Review coverage for a repo
set -euo pipefail

ORG="${1:?Usage: $0 <org> <repo> [days]}"
REPO="${2:?Usage: $0 <org> <repo> [days]}"
DAYS="${3:-30}"

echo "=== CodeRabbit Review Coverage ==="
echo "Repository: $ORG/$REPO"
echo "Period: Last $DAYS days"
echo ""

TOTAL=0
REVIEWED=0
APPROVED=0
CHANGES_REQUESTED=0

SINCE=$(date -d "$DAYS days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -v-${DAYS}d +%Y-%m-%dT%H:%M:%SZ)

for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=all&per_page=50&sort=created&direction=desc" \
  --jq ".[] | select(.created_at > \"$SINCE\") | .number"); do

  TOTAL=$((TOTAL + 1))

  CR_STATE=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | last | .state // "none"' 2>/dev/null || echo "none")

  if [ "$CR_STATE" != "none" ] && [ "$CR_STATE" != "null" ]; then
    REVIEWED=$((REVIEWED + 1))
    [ "$CR_STATE" = "APPROVED" ] && APPROVED=$((APPROVED + 1))
    [ "$CR_STATE" = "CHANGES_REQUESTED" ] && CHANGES_REQUESTED=$((CHANGES_REQUESTED + 1))
  fi
done

if [ "$TOTAL" -gt 0 ]; then
  echo "Total PRs: $TOTAL"
  echo "Reviewed by CodeRabbit: $REVIEWED ($(( REVIEWED * 100 / TOTAL ))%)"
  echo "  Approved: $APPROVED"
  echo "  Changes Requested: $CHANGES_REQUESTED"
else
  echo "No PRs found in the last $DAYS days"
fi
```

### Step 2: Track Comment Volume and Acceptance
```bash
set -euo pipefail
ORG="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== CodeRabbit Comment Analysis ==="
echo ""

TOTAL_COMMENTS=0
PR_COUNT=0

for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=20" --jq '.[].number'); do
  COMMENTS=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/comments" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")

  if [ "$COMMENTS" -gt 0 ]; then
    TOTAL_COMMENTS=$((TOTAL_COMMENTS + COMMENTS))
    PR_COUNT=$((PR_COUNT + 1))
    echo "PR #$PR_NUM: $COMMENTS comments"
  fi
done

if [ "$PR_COUNT" -gt 0 ]; then
  echo ""
  echo "Average comments per PR: $(( TOTAL_COMMENTS / PR_COUNT ))"
  echo ""
  echo "Healthy ranges:"
  echo "  1-3 comments/PR → Profile may be too chill"
  echo "  3-8 comments/PR → Good signal-to-noise ratio"
  echo "  10+ comments/PR → Consider switching to chill profile"
fi
```

### Step 3: Build a GitHub Actions Dashboard
```yaml
# .github/workflows/coderabbit-metrics.yml
name: CodeRabbit Weekly Metrics

on:
  schedule:
    - cron: '0 9 * * 1'    # Every Monday at 9 AM UTC
  workflow_dispatch:         # Manual trigger

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const { data: pulls } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'closed',
              per_page: 50,
              sort: 'updated',
              direction: 'desc',
            });

            let reviewed = 0;
            let approved = 0;
            let changesRequested = 0;
            let totalComments = 0;

            for (const pr of pulls) {
              const { data: reviews } = await github.rest.pulls.listReviews({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: pr.number,
              });

              const crReview = reviews.find(r => r.user.login === 'coderabbitai[bot]');
              if (crReview) {
                reviewed++;
                if (crReview.state === 'APPROVED') approved++;
                if (crReview.state === 'CHANGES_REQUESTED') changesRequested++;
              }

              const { data: comments } = await github.rest.pulls.listReviewComments({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: pr.number,
              });
              totalComments += comments.filter(c => c.user.login === 'coderabbitai[bot]').length;
            }

            const summary = [
              `## CodeRabbit Weekly Metrics`,
              `- **Coverage**: ${reviewed}/${pulls.length} PRs reviewed (${Math.round(reviewed/pulls.length*100)}%)`,
              `- **Approved**: ${approved}`,
              `- **Changes Requested**: ${changesRequested}`,
              `- **Avg Comments/PR**: ${reviewed > 0 ? Math.round(totalComments/reviewed) : 0}`,
            ].join('\n');

            core.summary.addRaw(summary).write();
            core.info(summary);
```

### Step 4: Set Up Alerts for Review Gaps
```yaml
# .github/workflows/coderabbit-alert.yml
name: CodeRabbit Review Alert

on:
  pull_request:
    types: [opened]

jobs:
  check-review-expected:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for CodeRabbit review
        uses: actions/github-script@v7
        with:
          script: |
            // Wait 10 minutes, then check if CodeRabbit reviewed
            await new Promise(r => setTimeout(r, 600000));

            const { data: reviews } = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const crReview = reviews.find(r => r.user.login === 'coderabbitai[bot]');

            if (!crReview) {
              core.warning(
                'CodeRabbit has not reviewed this PR after 10 minutes. ' +
                'Check: App installation, .coderabbit.yaml, base_branches config.'
              );
            }
```

### Step 5: CodeRabbit Dashboard Summary
```markdown
# Build a summary dashboard with these data points:

## Weekly Dashboard Template

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| PRs opened | | | |
| PRs reviewed by CR | | | |
| Coverage % | | | |
| Avg comments/PR | | | |
| Approval rate | | | |
| Time to first review | | | |

## Action Items:
- Coverage < 90%: Check App installation, base_branches config
- Avg comments > 10: Switch to "chill" profile
- Avg comments < 2: Switch to "assertive" profile
- Approval rate < 50%: Review path_instructions for relevance
```

## Output
- Review coverage metrics calculated per repository
- Comment volume and acceptance rate tracked
- Weekly metrics GitHub Action workflow
- Alert workflow for missing reviews
- Dashboard template for team reporting

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Coverage below 90% | Some PRs not reviewed | Check `base_branches` and `ignore_title_keywords` |
| Low acceptance rate | Too many false positives | Tune `path_instructions` and switch to `chill` |
| No metrics data | No closed PRs in period | Extend the time window |
| API rate limited | Too many `gh api` calls | Add pagination and caching |

## Resources
- [CodeRabbit Dashboard](https://app.coderabbit.ai)
- [GitHub REST API - Pulls](https://docs.github.com/en/rest/pulls)
- [GitHub Actions Job Summaries](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary)

## Next Steps
For incident response, see `coderabbit-incident-runbook`.
