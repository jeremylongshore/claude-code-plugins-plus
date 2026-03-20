---
name: linear-deploy-integration
description: |
  Deploy Linear-integrated applications and track deployments.
  Use when deploying to production, setting up deployment tracking,
  or integrating Linear with deployment platforms.
  Trigger with phrases like "deploy linear integration", "linear deployment",
  "linear vercel", "linear production deploy", "track linear deployments".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Deploy Integration

## Overview
Deploy Linear-integrated applications and automatically track deployments. Linear's GitHub integration links PRs to issues using magic words, and deployment platforms can be connected for preview link detection.

## Prerequisites
- Working Linear integration with API key or OAuth
- Deployment platform account (Vercel, Railway, Cloud Run, etc.)
- GitHub integration enabled in Linear (Settings > Integrations > GitHub)

## Instructions

### Step 1: GitHub Actions Deployment with Linear Tracking
Create a CI/CD pipeline that deploys and updates Linear issues on success or failure.

```yaml
# .github/workflows/deploy.yml
name: Deploy and Track in Linear
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Vercel
        id: deploy
        run: |
          npx vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }} > deploy-url.txt 2>&1
          echo "url=$(cat deploy-url.txt | tail -1)" >> $GITHUB_OUTPUT

      - name: Update Linear issues on success
        if: success()
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          # Extract Linear issue IDs from commit messages (e.g., "ENG-123")
          ISSUES=$(git log --oneline ${{ github.event.before }}..${{ github.sha }} | grep -oP '[A-Z]+-\d+' | sort -u)
          for ISSUE_ID in $ISSUES; do
            curl -s -X POST https://api.linear.app/graphql \
              -H "Authorization: $LINEAR_API_KEY" \
              -H "Content-Type: application/json" \
              -d "{\"query\": \"mutation { commentCreate(input: { issueId: \\\"$(curl -s -X POST https://api.linear.app/graphql -H 'Authorization: '$LINEAR_API_KEY -H 'Content-Type: application/json' -d '{\"query\": \"{ issueSearch(query: \\\"'$ISSUE_ID'\\\", first: 1) { nodes { id } } }\"}' | jq -r '.data.issueSearch.nodes[0].id')\\\", body: \\\"Deployed to production: ${{ steps.deploy.outputs.url }}\\\" }) { success } }\"}"
          done

      - name: Notify Linear on failure
        if: failure()
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          echo "Deployment failed — check GitHub Actions logs"
```

### Step 2: Vercel Integration with Preview Links
Linear auto-detects Vercel preview links when the GitHub integration is connected. Configure deployment tracking:

```typescript
// scripts/track-deployment.ts
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

async function trackDeployment(env: string, url: string, commitSha: string) {
  // Find issues referenced in recent commits
  const searchResult = await client.issueSearch(commitSha.substring(0, 7));

  for (const issue of searchResult.nodes) {
    await client.createComment({
      issueId: issue.id,
      body: `Deployed to **${env}**: [${url}](${url})\n\nCommit: \`${commitSha.substring(0, 7)}\``,
    });

    // Auto-transition to "In Review" if deploying to staging
    if (env === "staging") {
      const team = await issue.team;
      const states = await team!.states();
      const reviewState = states.nodes.find(s => s.name === "In Review");
      if (reviewState) {
        await issue.update({ stateId: reviewState.id });
      }
    }
  }
}

trackDeployment(
  process.env.DEPLOY_ENV!,
  process.env.DEPLOY_URL!,
  process.env.GITHUB_SHA!
);
```

### Step 3: Rollback Tracking
```typescript
async function trackRollback(issueIdentifier: string, reason: string) {
  const issues = await client.issueSearch(issueIdentifier);
  const issue = issues.nodes[0];
  if (!issue) return;

  // Add rollback comment
  await client.createComment({
    issueId: issue.id,
    body: `**Rolled back from production**\n\nReason: ${reason}\n\nPrevious deployment reverted. Issue moved back to In Progress.`,
  });

  // Move back to In Progress
  const team = await issue.team;
  const states = await team!.states();
  const inProgress = states.nodes.find(s => s.name === "In Progress");
  if (inProgress) {
    await issue.update({ stateId: inProgress.id, priority: 1 });
  }
}
```

### Step 4: PR-Based Issue Transitions
Linear's GitHub integration auto-transitions issues based on PR activity:
- PR opened with "Fixes ENG-123" in title/body → issue moves to "In Progress"
- PR merged → issue moves to "Done"
- PR closed without merge → issue stays in current state

```markdown
## PR Template (.github/PULL_REQUEST_TEMPLATE.md)
### Linear Issues
<!-- Use magic words: Fixes, Closes, Resolves, or Refs -->
Fixes ENG-XXX

### Deployment Notes
- [ ] Requires database migration
- [ ] Requires environment variable changes
- [ ] Requires Linear webhook reconfiguration
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `LINEAR_API_KEY` not set | Missing secret in CI | Add to GitHub repo Settings > Secrets > Actions |
| Issue not found by identifier | Wrong workspace or deleted | Verify team key matches workspace |
| Preview links not appearing | GitHub integration not connected | Enable in Linear Settings > Integrations > GitHub |
| Webhook timeout in CI | Linear API slow | Add retry logic with 3-attempt backoff |

## Examples

### Environment Matrix Deployment
```yaml
# Deploy to staging on PR, production on merge to main
strategy:
  matrix:
    include:
      - env: staging
        trigger: pull_request
        url_secret: STAGING_URL
      - env: production
        trigger: push
        url_secret: PROD_URL
```

### Deployment Status Dashboard Query
```typescript
// Find all issues deployed in the last sprint
const recentlyDone = await client.issues({
  filter: {
    state: { type: { eq: "completed" } },
    completedAt: { gte: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString() },
  },
  first: 100,
});
console.log(`${recentlyDone.nodes.length} issues completed in last 2 weeks`);
```

## Output
- GitHub Actions workflow deploying and posting Linear comments with deploy URLs
- Automatic issue state transitions on staging/production deploys
- Rollback tracking with priority escalation
- PR template enforcing Linear issue references

## Resources
- [Linear GitHub Integration](https://linear.app/docs/github)
- [Linear API Authentication](https://developers.linear.app/docs/graphql/authentication)
- [Vercel Deploy Hooks](https://vercel.com/docs/deploy-hooks)

## Next Steps
Set up webhooks with `linear-webhooks-events`.
