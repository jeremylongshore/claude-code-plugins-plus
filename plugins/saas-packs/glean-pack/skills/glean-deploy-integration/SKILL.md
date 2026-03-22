---
name: glean-deploy-integration
description: |
  Deploy Glean custom connectors as scheduled jobs on Cloud Run, Lambda, or Fly.io.
  Trigger: "deploy glean connector", "glean connector hosting", "schedule glean indexing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gcloud:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Deploy Integration

## Overview

Deploy Glean custom connectors as scheduled services. Connectors run periodically to sync content from your internal tools into the Glean search index.

## Instructions

### Option A: Cloud Run with Cloud Scheduler

```bash
# Deploy connector as Cloud Run job
gcloud run jobs create glean-wiki-sync \
  --source . \
  --region us-central1 \
  --set-secrets "GLEAN_INDEXING_TOKEN=glean-token:latest" \
  --set-env-vars "GLEAN_DOMAIN=company-be.glean.com,GLEAN_DATASOURCE=wiki"

# Schedule daily at 2 AM
gcloud scheduler jobs create http glean-wiki-daily \
  --schedule "0 2 * * *" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/..." \
  --http-method POST
```

### Option B: GitHub Actions Cron

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily 2 AM UTC

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && node src/connectors/sync-all.js
        env:
          GLEAN_DOMAIN: ${{ secrets.GLEAN_DOMAIN }}
          GLEAN_INDEXING_TOKEN: ${{ secrets.GLEAN_INDEXING_TOKEN }}
```

### Option C: Lambda (Event-Driven)

```typescript
// Trigger on source system changes via EventBridge/SNS
export const handler = async (event: any) => {
  const glean = new GleanClient(process.env.GLEAN_DOMAIN!, process.env.GLEAN_INDEXING_TOKEN!);
  // Incremental index — only changed documents
  await glean.indexDocuments('wiki', transformEvent(event));
};
```

## Resources

- [Glean Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
