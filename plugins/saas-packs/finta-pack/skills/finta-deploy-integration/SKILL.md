---
name: finta-deploy-integration
description: 'Deploy Finta integrations and reporting dashboards.

  Trigger with phrases like "deploy finta", "finta dashboard".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Deploy Integration

## Overview

Deploy a containerized Finta fundraising integration service with Docker. This skill covers building a production image that connects to the Finta API for managing fundraising rounds, investor pipelines, and deal flow analytics. Includes environment configuration for multi-round tracking, health checks that verify API connectivity to Finta's investor management endpoints, and rolling update strategies for zero-downtime deployments during active fundraising campaigns.

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
export FINTA_API_KEY="finta_live_xxxxxxxxxxxx"
export FINTA_BASE_URL="https://api.trustfinta.com/v1"
export FINTA_WORKSPACE_ID="ws_xxxxxxxxxxxx"
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
    const response = await fetch(`${process.env.FINTA_BASE_URL}/rounds`, {
      headers: { 'Authorization': `Bearer ${process.env.FINTA_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Finta API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'finta-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t finta-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name finta-integration \
  -p 3000:3000 \
  -e FINTA_API_KEY -e FINTA_BASE_URL -e FINTA_WORKSPACE_ID \
  finta-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t finta-integration:v2 . && \
docker stop finta-integration && \
docker rm finta-integration && \
docker run -d --name finta-integration -p 3000:3000 \
  -e FINTA_API_KEY -e FINTA_BASE_URL -e FINTA_WORKSPACE_ID \
  finta-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Finta workspace settings |
| `403 Forbidden` | Workspace access denied | Verify `FINTA_WORKSPACE_ID` matches your API key |
| `404 Not Found` | Round or investor ID not found | Check IDs from Finta dashboard |
| `429 Rate Limited` | Exceeding API rate limits | Implement exponential backoff with 30s window |
| Empty investor list | API key lacks read scope | Request full-access key from workspace admin |

## Resources

- [Finta Platform](https://www.trustfinta.com)

## Next Steps

See `finta-webhooks-events`.
