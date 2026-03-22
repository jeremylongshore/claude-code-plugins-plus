---
name: hex-deploy-integration
description: |
  Deploy Hex integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Hex-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy hex", "hex Vercel",
  "hex production deploy", "hex Cloud Run", "hex Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Deploy Integration

## Overview

Deploy Hex orchestration services that trigger project runs from web endpoints or cron jobs.

## Instructions

### Vercel — On-Demand Data Refresh

```typescript
// api/refresh.ts
export default async function handler(req, res) {
  const response = await fetch(`https://app.hex.tech/api/v1/project/${process.env.HEX_PROJECT_ID}/run`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.HEX_API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputParams: req.body || {}, updateCacheResult: true }),
  });
  res.json(await response.json());
}
```

```bash
vercel env add HEX_API_TOKEN production
vercel env add HEX_PROJECT_ID production
```

### Cloud Run — Scheduled Orchestrator

```bash
gcloud run deploy hex-orchestrator \
  --image gcr.io/$PROJECT_ID/hex-orchestrator \
  --set-secrets=HEX_API_TOKEN=hex-api-token:latest \
  --timeout=600
```

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
