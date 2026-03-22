---
name: linear-deploy-integration
description: |
  Deploy Linear-integrated applications and track deployments.
  Use when deploying to production, linking deploys to issues,
  or setting up deployment tracking with Vercel/Railway/Cloud Run.
  Trigger: "deploy linear integration", "linear deployment",
  "linear vercel", "track linear deployments", "linear deploy tracking".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(aws:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, deployment]

---
# Linear Deploy Integration

## Overview
Deploy Linear-integrated applications with automatic deployment tracking. Linear's GitHub integration links PRs to issues using magic words (`Fixes`, `Closes`, `Resolves`) and auto-detects Vercel preview links. This skill adds custom deployment comments, state transitions, and rollback tracking.

## Prerequisites
- Working Linear integration with API key or OAuth
- Deployment platform (Vercel, Railway, Cloud Run, etc.)
- GitHub integration enabled in Linear (Settings > Integrations > GitHub)

## Instructions

### Step 1: Deployment Workflow with Linear Tracking
```yaml
# .github/workflows/deploy.yml
name: Deploy and Track

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for commit scanning

      - name: Deploy
        id: deploy
        run: |
          # Replace with your deploy command
          DEPLOY_URL=$(npx vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }} 2>&1 | tail -1)
          echo "url=$DEPLOY_URL" >> $GITHUB_OUTPUT

      - name: Track deployment in Linear
        if: success()
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          npx tsx scripts/track-deployment.ts \
            --env production \
            --url "${{ steps.deploy.outputs.url }}" \
            --sha "${{ github.sha }}" \
            --before "${{ github.event.before }}"

      - name: Create failure issue
        if: failure()
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          curl -s -X POST https://api.linear.app/graphql \
            -H "Authorization: $LINEAR_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{
              "query": "mutation($i: IssueCreateInput!) { issueCreate(input: $i) { success } }",
              "variables": { "i": { "teamId": "${{ vars.LINEAR_TEAM_ID }}", "title": "[Deploy] Failed: ${{ github.sha }}", "priority": 1 } }
            }'
```

### Step 2: Deployment Tracking Script
```typescript
// scripts/track-deployment.ts
import { LinearClient } from "@linear/sdk";
import { execSync } from "child_process";
import { parseArgs } from "util";

const { values } = parseArgs({
  options: {
    env: { type: "string" },
    url: { type: "string" },
    sha: { type: "string" },
    before: { type: "string" },
  },
});

async function trackDeployment() {
  const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

  // Extract Linear issue IDs from commit messages since last deploy
  const log = execSync(
    `git log --oneline ${values.before}..${values.sha} 2>/dev/null || echo ""`
  ).toString();

  const issueIds = [...new Set(log.match(/[A-Z]+-\d+/g) ?? [])];
  console.log(`Found ${issueIds.length} Linear issues in commits: ${issueIds.join(", ")}`);

  for (const identifier of issueIds) {
    const results = await client.issueSearch(identifier);
    const issue = results.nodes.find(i => i.identifier === identifier);
    if (!issue) continue;

    // Add deployment comment
    await client.createComment({
      issueId: issue.id,
      body: `Deployed to **${values.env}**: [${values.url}](${values.url})\n\nCommit: \`${values.sha?.substring(0, 7)}\``,
    });

    // Auto-transition based on environment
    const team = await issue.team;
    const states = await team!.states();

    if (values.env === "staging") {
      const reviewState = states.nodes.find(s =>
        s.name.toLowerCase().includes("review")
      );
      if (reviewState) await issue.update({ stateId: reviewState.id });
    } else if (values.env === "production") {
      const doneState = states.nodes.find(s => s.type === "completed");
      if (doneState) await issue.update({ stateId: doneState.id });
    }

    console.log(`Updated ${identifier} — deployed to ${values.env}`);
  }
}

trackDeployment().catch(console.error);
```

### Step 3: Rollback Tracking
```typescript
async function trackRollback(
  client: LinearClient,
  issueIdentifier: string,
  reason: string
) {
  const results = await client.issueSearch(issueIdentifier);
  const issue = results.nodes[0];
  if (!issue) return;

  // Add rollback comment
  await client.createComment({
    issueId: issue.id,
    body: `**Rolled back from production**\n\nReason: ${reason}\n\nIssue moved back to In Progress.`,
  });

  // Move back to In Progress with elevated priority
  const team = await issue.team;
  const states = await team!.states();
  const inProgress = states.nodes.find(s =>
    s.name.toLowerCase() === "in progress"
  );
  if (inProgress) {
    await issue.update({ stateId: inProgress.id, priority: 1 });
  }
}
```

### Step 4: PR Template for Deployment Tracking
```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## Linear Issues
<!-- Linear auto-links when you use magic words -->
Fixes ENG-XXX

## Deployment Notes
- [ ] Requires database migration
- [ ] Requires environment variable changes
- [ ] Requires Linear webhook reconfiguration
- [ ] Requires secret rotation
```

### Step 5: Deployment Dashboard Query
```typescript
// Query recently deployed issues
async function getDeploymentSummary(client: LinearClient, days = 14) {
  const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

  const completed = await client.issues({
    filter: {
      state: { type: { eq: "completed" } },
      completedAt: { gte: since },
    },
    first: 100,
    orderBy: "completedAt",
  });

  console.log(`${completed.nodes.length} issues completed in last ${days} days:`);
  for (const issue of completed.nodes) {
    const assignee = await issue.assignee;
    console.log(`  ${issue.identifier}: ${issue.title} (${assignee?.name ?? "unassigned"})`);
  }

  return completed.nodes;
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `LINEAR_API_KEY` not set | Missing CI secret | Add to GitHub repo Settings > Secrets |
| Issue not found | Wrong workspace or deleted | Verify team key matches workspace |
| Preview links not appearing | GitHub integration off | Enable in Linear Settings > Integrations > GitHub |
| Deploy comment missing | Issue ID not in commits | Follow branch naming: `feature/ENG-123-desc` |

## Examples

### Multi-Environment Matrix
```yaml
strategy:
  matrix:
    include:
      - env: staging
        trigger: pull_request
      - env: production
        trigger: push
```

## Resources
- [Linear GitHub Integration](https://linear.app/docs/github)
- [Vercel Deploy Hooks](https://vercel.com/docs/deploy-hooks)
- [Linear API Authentication](https://linear.app/developers/graphql)
