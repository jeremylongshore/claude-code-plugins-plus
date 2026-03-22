---
name: coderabbit-ci-integration
description: |
  Configure CodeRabbit as a CI gate with GitHub Actions, branch protection, and review enforcement.
  Use when setting up CodeRabbit as a required check, gating merges on review approval,
  or integrating CodeRabbit status into your CI pipeline.
  Trigger with phrases like "coderabbit CI", "coderabbit GitHub Actions",
  "coderabbit required check", "coderabbit merge gate", "coderabbit CI pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, ci-cd, github-actions]

---
# CodeRabbit CI Integration

## Overview
Integrate CodeRabbit into your CI/CD pipeline as a merge gate. CodeRabbit posts a GitHub Check on each PR, and you can require this check to pass before merging. This skill covers branch protection rules, GitHub Actions workflows that react to CodeRabbit reviews, and strategies for enforcing review quality in CI.

## Prerequisites
- CodeRabbit GitHub App installed on your repository
- GitHub repository with branch protection enabled
- `.coderabbit.yaml` committed to repository root
- GitHub Actions enabled on the repository

## Instructions

### Step 1: Enable CodeRabbit as a Required Status Check
```markdown
1. Go to GitHub repo > Settings > Branches > Branch protection rules
2. Click "Add rule" (or edit existing rule for `main`)
3. Enable "Require status checks to pass before merging"
4. Search for "coderabbitai" in the status checks list
5. Select it as a required check
6. Save changes

Result: PRs cannot be merged until CodeRabbit completes its review.
```

### Step 2: Configure Review Approval Behavior
```yaml
# .coderabbit.yaml - Control when CodeRabbit blocks merge
reviews:
  request_changes_workflow: true   # CodeRabbit marks review as "Changes Requested" for issues
  # When true: PRs with issues show as "Changes Requested" (blocks merge if reviews required)
  # When false: CodeRabbit only posts "Comment" reviews (never blocks merge)

  profile: "assertive"             # Controls comment volume
  # chill: fewer comments, only critical issues
  # assertive: balanced, blocks on significant issues
  # nitpicky: detailed comments, blocks more frequently

  auto_review:
    enabled: true
    drafts: false                  # Don't run CI-blocking reviews on drafts
    base_branches:
      - main
      - develop
      - "release/*"
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
```

### Step 3: Create a Review Gate Workflow
```yaml
# .github/workflows/coderabbit-gate.yml
name: CodeRabbit Review Gate

on:
  pull_request_review:
    types: [submitted]

jobs:
  check-review:
    # Only run when CodeRabbit submits a review
    if: github.event.review.user.login == 'coderabbitai[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Evaluate CodeRabbit review
        uses: actions/github-script@v7
        with:
          script: |
            const reviews = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const crReview = reviews.data
              .filter(r => r.user.login === 'coderabbitai[bot]')
              .pop();

            if (!crReview) {
              core.info('No CodeRabbit review found yet.');
              return;
            }

            core.info(`CodeRabbit review state: ${crReview.state}`);

            if (crReview.state === 'CHANGES_REQUESTED') {
              core.setFailed('CodeRabbit requested changes. Address review feedback before merging.');
            }
```

### Step 4: Add PR Size Check with CodeRabbit
```yaml
# .github/workflows/pr-size-check.yml
name: PR Size Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check PR size
        run: |
          CHANGES=$(git diff --stat origin/${{ github.base_ref }}...HEAD | tail -1)
          LINES=$(echo "$CHANGES" | grep -oP '\d+ insertion' | grep -oP '\d+' || echo 0)
          DELETIONS=$(echo "$CHANGES" | grep -oP '\d+ deletion' | grep -oP '\d+' || echo 0)
          TOTAL=$((LINES + DELETIONS))

          echo "Total lines changed: $TOTAL"

          if [ "$TOTAL" -gt 1000 ]; then
            echo "::warning::PR has $TOTAL lines changed. CodeRabbit works best with PRs under 500 lines."
            echo "Consider splitting into smaller PRs for better review quality."
          fi
```

### Step 5: Notify on CodeRabbit Findings
```yaml
# .github/workflows/coderabbit-notify.yml
name: CodeRabbit Notification

on:
  pull_request_review:
    types: [submitted]

jobs:
  notify:
    if: >
      github.event.review.user.login == 'coderabbitai[bot]' &&
      github.event.review.state == 'changes_requested'
    runs-on: ubuntu-latest
    steps:
      - name: Post Slack notification
        uses: slackapi/slack-github-action@v1.27.1
        with:
          payload: |
            {
              "text": "CodeRabbit found issues in PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*CodeRabbit Review*: Changes requested on <${{ github.event.pull_request.html_url }}|PR #${{ github.event.pull_request.number }}>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Step 6: Enforce CodeRabbit via Branch Protection API
```bash
set -euo pipefail
# Programmatically set CodeRabbit as a required check
OWNER="your-org"
REPO="your-repo"
BRANCH="main"

gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --method PUT \
  --field 'required_status_checks={"strict":true,"contexts":["coderabbitai"]}' \
  --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
  --field 'enforce_admins=true' \
  --field 'restrictions=null'

echo "Branch protection updated: CodeRabbit review required for merge"
```

## Output
- CodeRabbit configured as a required status check on protected branches
- GitHub Actions workflow that gates merges on CodeRabbit approval
- PR size warnings to improve review quality
- Slack notifications for CodeRabbit findings
- Branch protection enforced via API

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| "coderabbitai" not in status checks list | App not installed or no PRs reviewed yet | Install App, create a test PR, then configure |
| Review blocks all PRs | `request_changes_workflow: true` with aggressive profile | Switch to `chill` or set to `false` |
| CI times out waiting for review | Large PR or CodeRabbit backlog | Reviews take 2-15 min depending on PR size |
| Draft PRs blocked | `drafts: true` in config | Set `drafts: false` to skip draft PR reviews |
| Status check stays pending | CodeRabbit outage | Check status.coderabbit.ai; admin merge if needed |

## Resources
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-a-branch-protection-rule)
- [GitHub Actions: Pull Request Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request_review)

## Next Steps
For deployment and multi-repo rollout, see `coderabbit-deploy-integration`.
