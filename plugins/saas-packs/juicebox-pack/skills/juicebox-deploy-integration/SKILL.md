---
name: juicebox-deploy-integration
description: 'Deploy Juicebox integrations.

  Trigger: "deploy juicebox", "juicebox production deploy".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Deploy Integration

## Overview

Deploy a containerized Juicebox AI analysis integration service with Docker. This skill covers building a production image that connects to the Juicebox API for managing datasets, running AI-powered analyses, and retrieving structured insights. Includes environment configuration for dataset access and analysis pipelines, health checks that verify API connectivity and dataset availability, and rolling update strategies for zero-downtime deployments serving real-time analysis results.

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
export JUICEBOX_API_KEY="jb_live_xxxxxxxxxxxx"
export JUICEBOX_BASE_URL="https://api.juicebox.ai/v1"
export JUICEBOX_WORKSPACE_ID="ws_xxxxxxxxxxxx"
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
    const response = await fetch(`${process.env.JUICEBOX_BASE_URL}/datasets`, {
      headers: { 'Authorization': `Bearer ${process.env.JUICEBOX_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Juicebox API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'juicebox-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t juicebox-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name juicebox-integration \
  -p 3000:3000 \
  -e JUICEBOX_API_KEY -e JUICEBOX_BASE_URL -e JUICEBOX_WORKSPACE_ID \
  juicebox-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t juicebox-integration:v2 . && \
docker stop juicebox-integration && \
docker rm juicebox-integration && \
docker run -d --name juicebox-integration -p 3000:3000 \
  -e JUICEBOX_API_KEY -e JUICEBOX_BASE_URL -e JUICEBOX_WORKSPACE_ID \
  juicebox-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Juicebox workspace settings |
| `403 Forbidden` | Workspace access denied | Verify `JUICEBOX_WORKSPACE_ID` matches your API key |
| `404 Not Found` | Dataset or analysis ID not found | Check IDs from Juicebox dashboard |
| `429 Rate Limited` | Exceeding API rate limits | Implement exponential backoff; batch analysis requests |
| Analysis timeout | Large dataset processing | Increase timeout or use async analysis endpoint with polling |

## Resources

- [Juicebox API Docs](https://docs.juicebox.ai)

## Next Steps

See `juicebox-webhooks-events`.
