# Linear Deploy Integration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Vercel Deployment
```bash
# Install Vercel CLI
npm install -g vercel

# Configure environment variables
vercel env add LINEAR_API_KEY production
vercel env add LINEAR_WEBHOOK_SECRET production

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "env": {
    "LINEAR_API_KEY": "@linear-api-key",
    "LINEAR_WEBHOOK_SECRET": "@linear-webhook-secret"
  },
  "functions": {
    "api/webhooks/linear.ts": {
      "maxDuration": 30
    }
  }
}
```

### Step 2: Google Cloud Run Deployment
```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/linear-integration

# Deploy with secrets
gcloud run deploy linear-integration \
  --image gcr.io/PROJECT_ID/linear-integration \
  --platform managed \
  --region us-central1 \
  --set-secrets="LINEAR_API_KEY=linear-api-key:latest,LINEAR_WEBHOOK_SECRET=linear-webhook-secret:latest" \
  --allow-unauthenticated
```

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/linear-integration', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/linear-integration']

  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'linear-integration'
      - '--image=gcr.io/$PROJECT_ID/linear-integration'
      - '--region=us-central1'
      - '--platform=managed'
```

### Step 3: Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Set environment variables
railway variables set LINEAR_API_KEY=lin_api_xxxx
railway variables set LINEAR_WEBHOOK_SECRET=secret

# Deploy
railway up
```

### Step 4: Deployment Tracking in Linear
```typescript
// scripts/notify-linear-deploy.ts
import { LinearClient } from "@linear/sdk";

interface DeploymentInfo {
  environment: "staging" | "production";
  version: string;
  commitSha: string;
  deployUrl: string;
  issueIdentifiers: string[];
}

async function notifyLinearDeploy(info: DeploymentInfo) {
  const client = new LinearClient({
    apiKey: process.env.LINEAR_API_KEY!,
  });

  // Add deployment comment to each issue
  for (const identifier of info.issueIdentifiers) {
    try {
      const issue = await client.issue(identifier);

      await client.createComment({
        issueId: issue.id,
        body: `## Deployed to ${info.environment}

**Version:** ${info.version}
**Commit:** \`${info.commitSha.slice(0, 7)}\`
**URL:** ${info.deployUrl}
**Time:** ${new Date().toISOString()}`,
      });

      // If production deploy, mark issue as done
      if (info.environment === "production") {
        const team = await issue.team;
        const states = await team?.states();
        const doneState = states?.nodes.find(s => s.type === "completed");

        if (doneState) {
          await client.updateIssue(issue.id, { stateId: doneState.id });
        }
      }

      console.log(`Updated ${identifier}`);
    } catch (error) {
      console.error(`Failed to update ${identifier}:`, error);
    }
  }
}

// Usage
notifyLinearDeploy({
  environment: "production",
  version: process.env.VERSION!,
  commitSha: process.env.COMMIT_SHA!,
  deployUrl: process.env.DEPLOY_URL!,
  issueIdentifiers: process.env.ISSUE_IDS!.split(","),
});
```

### Step 5: GitHub Actions Deployment Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Extract Linear Issues
        id: issues
        run: |
          # Get issues from commits since last deploy
          ISSUES=$(git log ${{ github.event.before }}..${{ github.sha }} --oneline | grep -oE '[A-Z]+-[0-9]+' | sort -u | tr '\n' ',' | sed 's/,$//')
          echo "ids=$ISSUES" >> $GITHUB_OUTPUT

      - name: Deploy to Production
        id: deploy
        run: |
          # Your deploy command here
          DEPLOY_URL=$(vercel --prod --token ${{ secrets.VERCEL_TOKEN }} | tail -1)
          echo "url=$DEPLOY_URL" >> $GITHUB_OUTPUT

      - name: Notify Linear
        run: |
          npx ts-node scripts/notify-linear-deploy.ts
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          VERSION: ${{ github.sha }}
          COMMIT_SHA: ${{ github.sha }}
          DEPLOY_URL: ${{ steps.deploy.outputs.url }}
          ISSUE_IDS: ${{ steps.issues.outputs.ids }}
```

### Step 6: Rollback Tracking
```typescript
// scripts/notify-linear-rollback.ts
import { LinearClient } from "@linear/sdk";

async function notifyRollback(options: {
  version: string;
  reason: string;
  affectedIssues: string[];
}) {
  const client = new LinearClient({
    apiKey: process.env.LINEAR_API_KEY!,
  });

  for (const identifier of options.affectedIssues) {
    const issue = await client.issue(identifier);

    // Reopen the issue
    const team = await issue.team;
    const states = await team?.states();
    const inProgressState = states?.nodes.find(s =>
      s.name.toLowerCase().includes("progress")
    );

    if (inProgressState) {
      await client.updateIssue(issue.id, { stateId: inProgressState.id });
    }

    await client.createComment({
      issueId: issue.id,
      body: `## Production Rollback

**Rolled back version:** ${options.version}
**Reason:** ${options.reason}
**Time:** ${new Date().toISOString()}

This issue has been reopened for investigation.`,
    });
  }
}
```

## Deployment Checklist

```
[ ] Environment variables configured on platform
[ ] Secrets stored securely (not in code)
[ ] Webhook endpoint accessible from internet
[ ] Health check endpoint configured
[ ] Deployment notifications enabled
[ ] Rollback procedure documented
```
