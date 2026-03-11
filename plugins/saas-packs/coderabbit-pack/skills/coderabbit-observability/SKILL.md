---
name: coderabbit-observability
description: |
  Set up comprehensive observability for CodeRabbit integrations with metrics, traces, and alerts.
  Use when implementing monitoring for CodeRabbit operations, setting up dashboards,
  or configuring alerting for CodeRabbit integration health.
  Trigger with phrases like "coderabbit monitoring", "coderabbit metrics",
  "coderabbit observability", "monitor coderabbit", "coderabbit alerts", "coderabbit tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Observability

## Overview
Monitor CodeRabbit AI code review effectiveness, review latency, and team adoption. Key metrics include time-to-first-review (how fast CodeRabbit posts its review after PR creation), comment acceptance rate (comments resolved vs dismissed), review coverage (percentage of PRs reviewed), and per-repository review volume.

## Prerequisites
- CodeRabbit Pro or Enterprise plan
- GitHub or GitLab organization with CodeRabbit installed
- Access to CodeRabbit dashboard at app.coderabbit.ai

## Instructions

### Step 1: Track Review Metrics via GitHub Webhooks
```typescript
// coderabbit-metrics.ts - Process GitHub webhook events
function handlePullRequestReview(event: any) {
  if (event.review.user.login === 'coderabbitai') {
    const prCreatedAt = new Date(event.pull_request.created_at);
    const reviewPostedAt = new Date(event.review.submitted_at);
    const timeToReview = (reviewPostedAt.getTime() - prCreatedAt.getTime()) / 1000;  # 1000: 1 second in ms

    emitHistogram('coderabbit_time_to_review_sec', timeToReview, { repo: event.repository.name });
    emitCounter('coderabbit_reviews_total', 1, { repo: event.repository.name, state: event.review.state });
  }
}
```

### Step 2: Measure Comment Acceptance Rate
```bash
# Query GitHub API for CodeRabbit review comments and their resolution status
gh api repos/ORG/REPO/pulls/comments \
  --jq '[.[] | select(.user.login=="coderabbitai")] | {
    total: length,
    resolved: [.[] | select(.resolved == true)] | length
  } | {total, resolved, acceptance_rate: (.resolved / .total * 100)}'
```

### Step 3: Monitor Review Coverage
```typescript
// Check what percentage of PRs get CodeRabbit reviews
async function reviewCoverage(org: string, repo: string, days: number) {
  const prs = await github.pulls.list({ owner: org, repo, state: 'closed', per_page: 100 });
  let reviewed = 0;
  for (const pr of prs) {
    const reviews = await github.pulls.listReviews({ owner: org, repo, pull_number: pr.number });
    if (reviews.data.some(r => r.user?.login === 'coderabbitai')) reviewed++;
  }
  return { total: prs.length, reviewed, coverage: (reviewed / prs.length * 100).toFixed(1) };
}
```

### Step 4: Set Up Alerts
```yaml
groups:
  - name: coderabbit
    rules:
      - alert: CodeRabbitReviewSlow
        expr: histogram_quantile(0.95, rate(coderabbit_time_to_review_sec_bucket[1h])) > 600  # 600: timeout: 10 minutes
        annotations: { summary: "CodeRabbit P95 review time exceeds 10 minutes" }
      - alert: CodeRabbitNotReviewing
        expr: rate(coderabbit_reviews_total[6h]) == 0 and rate(github_prs_opened_total[6h]) > 0
        annotations: { summary: "PRs opening but CodeRabbit not reviewing -- check installation" }
      - alert: LowCommentAcceptance
        expr: coderabbit_comment_acceptance_rate < 30
        for: 7d
        annotations: { summary: "CodeRabbit comment acceptance rate below 30% -- review config" }
```

### Step 5: Build a Dashboard
Key panels: review latency distribution, comment acceptance rate over time, PRs reviewed vs total PRs (coverage), reviews per repository (bar chart), and most common comment categories (helps tune `.coderabbit.yaml` instructions).

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No reviews posting | GitHub App lost permissions | Reinstall CodeRabbit App on the org |
| Review delayed >15 min | Large PR or service backlog | Expected for 1000+ line PRs; split PRs |
| Low acceptance rate | Reviews too nitpicky | Change profile from `nitpicky` to `assertive` |
| Missing repos in metrics | Repos not added to App | Add repos in GitHub App installation settings |

## Examples

**Basic usage**: Apply coderabbit observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize coderabbit observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack