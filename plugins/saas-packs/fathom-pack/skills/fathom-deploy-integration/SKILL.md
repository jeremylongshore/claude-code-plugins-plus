---
name: fathom-deploy-integration
description: 'Deploy Fathom webhook handlers and meeting sync services.

  Trigger with phrases like "deploy fathom", "fathom webhook server", "fathom cloud
  function".

  '
allowed-tools: Read, Write, Edit, Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Deploy Integration

## Overview

Deploy a containerized Fathom AI meeting integration service with Docker. This skill covers building a production image that connects to the Fathom API for processing meeting transcripts, summaries, and action items. Includes environment configuration for webhook handling, health checks that verify Fathom API connectivity and transcript retrieval, and rolling update strategies to maintain continuous meeting data processing without losing webhook events.

## Docker Configuration

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-slim
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Environment Variables

```bash
export FATHOM_API_KEY="fthm_live_xxxxxxxxxxxx"
export FATHOM_BASE_URL="https://api.fathom.video/v1"
export FATHOM_WEBHOOK_SECRET="whsec_xxxxxxxxxxxx"
export LOG_LEVEL="info"
export PORT="3000"
export NODE_ENV="production"
```

## Health Check Endpoint

```typescript
import express from 'express';

const app = express();

app.get('/health', async (req, res) => {
  try {
    const response = await fetch(`${process.env.FATHOM_BASE_URL}/meetings`, {
      headers: { 'Authorization': `Bearer ${process.env.FATHOM_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Fathom API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'fathom-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t fathom-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name fathom-integration \
  -p 3000:3000 \
  -e FATHOM_API_KEY -e FATHOM_BASE_URL -e FATHOM_WEBHOOK_SECRET \
  fathom-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t fathom-integration:v2 . && \
docker stop fathom-integration && \
docker rm fathom-integration && \
docker run -d --name fathom-integration -p 3000:3000 \
  -e FATHOM_API_KEY -e FATHOM_BASE_URL -e FATHOM_WEBHOOK_SECRET \
  fathom-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Fathom developer settings |
| `403 Forbidden` | Insufficient API scopes | Request meetings and transcripts access |
| `404 Not Found` | Meeting ID does not exist | Verify meeting ID from webhook payload |
| `429 Rate Limited` | Exceeding API rate limits | Implement backoff; batch transcript fetches |
| Webhook signature mismatch | Wrong `FATHOM_WEBHOOK_SECRET` | Re-copy secret from Fathom webhook settings |

## Resources

- [Fathom API Docs](https://developers.fathom.video)

## Next Steps

See `fathom-webhooks-events`.
