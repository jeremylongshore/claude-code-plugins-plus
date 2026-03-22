---
name: coderabbit-sdk-patterns
description: |
  Apply production-ready CodeRabbit automation patterns using GitHub API and PR comments.
  Use when building automation around CodeRabbit reviews, processing review feedback
  programmatically, or integrating CodeRabbit into custom workflows.
  Trigger with phrases like "coderabbit automation", "coderabbit API patterns",
  "automate coderabbit", "coderabbit github api", "process coderabbit reviews".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, automation, github-api, typescript]

---
# CodeRabbit SDK Patterns

## Overview
CodeRabbit does not have a traditional SDK. You interact with it through `.coderabbit.yaml` configuration, PR comment commands (`@coderabbitai`), and the GitHub/GitLab API to process its review output. These patterns show how to automate around CodeRabbit reviews programmatically.

## Prerequisites
- CodeRabbit installed on repository (see `coderabbit-install-auth`)
- GitHub CLI (`gh`) or GitHub API access via personal access token
- Node.js 18+ for automation scripts

## Instructions

### Step 1: Fetch CodeRabbit Reviews via GitHub API
```typescript
// scripts/fetch-coderabbit-reviews.ts
import { Octokit } from "@octokit/rest";

const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });

async function getCodeRabbitReview(owner: string, repo: string, prNumber: number) {
  const reviews = await octokit.pulls.listReviews({ owner, repo, pull_number: prNumber });

  const coderabbitReview = reviews.data.find(
    (r) => r.user?.login === "coderabbitai[bot]"
  );

  if (!coderabbitReview) {
    console.log("No CodeRabbit review found yet. Review typically takes 2-5 minutes.");
    return null;
  }

  return {
    state: coderabbitReview.state,      // "APPROVED" | "CHANGES_REQUESTED" | "COMMENTED"
    body: coderabbitReview.body,         // Walkthrough summary
    submittedAt: coderabbitReview.submitted_at,
  };
}
```

### Step 2: Extract Line-Level Comments
```typescript
async function getCodeRabbitComments(owner: string, repo: string, prNumber: number) {
  const comments = await octokit.pulls.listReviewComments({
    owner, repo, pull_number: prNumber,
  });

  const coderabbitComments = comments.data
    .filter((c) => c.user?.login === "coderabbitai[bot]")
    .map((c) => ({
      file: c.path,
      line: c.line || c.original_line,
      body: c.body,
      severity: categorizeSeverity(c.body),
      url: c.html_url,
    }));

  return coderabbitComments;
}

function categorizeSeverity(body: string): "critical" | "warning" | "suggestion" {
  const lower = body.toLowerCase();
  if (lower.includes("security") || lower.includes("vulnerability") || lower.includes("injection")) {
    return "critical";
  }
  if (lower.includes("bug") || lower.includes("error") || lower.includes("issue")) {
    return "warning";
  }
  return "suggestion";
}
```

### Step 3: Post Commands to CodeRabbit via PR Comments
```typescript
// Programmatically trigger CodeRabbit actions
async function sendCodeRabbitCommand(
  owner: string, repo: string, prNumber: number, command: string
) {
  await octokit.issues.createComment({
    owner, repo, issue_number: prNumber,
    body: `@coderabbitai ${command}`,
  });
}

// Available commands:
// "full review"                    - Complete review from scratch
// "summary"                        - Generate walkthrough summary
// "resolve"                        - Mark all comments resolved
// "generate-docstrings"            - Generate docstrings for functions
// "configuration"                  - Show current config as YAML
// "run <recipe>"                   - Run a finishing touch recipe
```

### Step 4: Build a Review Dashboard Script
```bash
#!/bin/bash
# scripts/coderabbit-dashboard.sh - Review metrics for last 50 PRs
set -euo pipefail

ORG="${1:?Usage: $0 <org> <repo>}"
REPO="${2:?Usage: $0 <org> <repo>}"

echo "=== CodeRabbit Review Dashboard ==="
echo "Repository: $ORG/$REPO"
echo ""

# Count PRs with CodeRabbit reviews
TOTAL=$(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=50" --jq 'length')
REVIEWED=0

for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=50" --jq '.[].number'); do
  HAS_CR=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/reviews" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  [ "$HAS_CR" -gt 0 ] && REVIEWED=$((REVIEWED + 1))
done

echo "Review Coverage: $REVIEWED/$TOTAL PRs reviewed ($(( REVIEWED * 100 / TOTAL ))%)"
```

### Step 5: GitHub Actions Automation
```yaml
# .github/workflows/coderabbit-gate.yml
# Block merge until CodeRabbit has reviewed
name: CodeRabbit Review Gate

on:
  pull_request_review:
    types: [submitted]

jobs:
  check-coderabbit:
    if: github.event.review.user.login == 'coderabbitai[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Check review state
        uses: actions/github-script@v7
        with:
          script: |
            const { data: reviews } = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });
            const crReview = reviews.find(r => r.user.login === 'coderabbitai[bot]');
            if (crReview?.state === 'CHANGES_REQUESTED') {
              core.setFailed('CodeRabbit requested changes. Address feedback before merging.');
            } else {
              core.info(`CodeRabbit review state: ${crReview?.state || 'pending'}`);
            }
```

## Output
- GitHub API integration for fetching CodeRabbit review data
- Automated command posting to trigger CodeRabbit actions
- Review metrics dashboard script
- CI gate that enforces CodeRabbit approval before merge

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review not found | PR too new | Wait 2-5 minutes for review to complete |
| 403 from GitHub API | Token missing scopes | Ensure `repo` scope on personal access token |
| Bot login doesn't match | Different app slug | Check with `coderabbitai[bot]` (includes `[bot]` suffix) |
| Rate limited by GitHub | Too many API calls | Use pagination and caching for bulk queries |

## Resources
- [CodeRabbit Review Commands](https://docs.coderabbit.ai/reference/review-commands)
- [GitHub REST API - Pull Reviews](https://docs.github.com/en/rest/pulls/reviews)
- [Octokit.js](https://github.com/octokit/octokit.js)

## Next Steps
Apply patterns in `coderabbit-core-workflow-a` for real-world review workflows.
