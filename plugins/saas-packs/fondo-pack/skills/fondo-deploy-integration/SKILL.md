---
name: fondo-deploy-integration
description: 'Deploy financial dashboards and reporting tools that consume Fondo data

  to Vercel, Fly.io, or internal infrastructure.

  Trigger: "fondo dashboard deploy", "fondo financial dashboard", "deploy finance
  app".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Deploy Integration

## Overview

Deploy a containerized Fondo tax and accounting integration service with Docker. This skill covers building a production image that connects to Fondo's API for managing tax filings, compliance status, and financial reporting. Includes environment configuration for multi-entity accounting setups, health checks that verify API connectivity to Fondo's compliance endpoints, and rolling update strategies for zero-downtime deployments during critical tax filing periods.

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
export FONDO_API_KEY="fondo_live_xxxxxxxxxxxx"
export FONDO_BASE_URL="https://api.tryfondo.com/v1"
export FONDO_COMPANY_ID="comp_xxxxxxxxxxxx"
export FONDO_FILING_YEAR="2026"
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
    const response = await fetch(`${process.env.FONDO_BASE_URL}/compliance/status`, {
      headers: { 'Authorization': `Bearer ${process.env.FONDO_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Fondo API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'fondo-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t fondo-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name fondo-integration \
  -p 3000:3000 \
  -e FONDO_API_KEY -e FONDO_BASE_URL -e FONDO_COMPANY_ID -e FONDO_FILING_YEAR \
  fondo-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t fondo-integration:v2 . && \
docker stop fondo-integration && \
docker rm fondo-integration && \
docker run -d --name fondo-integration -p 3000:3000 \
  -e FONDO_API_KEY -e FONDO_BASE_URL -e FONDO_COMPANY_ID -e FONDO_FILING_YEAR \
  fondo-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Fondo dashboard settings |
| `403 Forbidden` | Company ID mismatch with API key | Verify `FONDO_COMPANY_ID` in Fondo account settings |
| `404 Not Found` | Filing or entity does not exist | Check filing year and entity IDs against Fondo portal |
| `429 Rate Limited` | Exceeding API rate limits | Implement exponential backoff; cache compliance status |
| Stale compliance data | Webhook not configured for updates | Register webhook endpoint in Fondo settings |

## Resources

- [Fondo Platform](https://www.tryfondo.com)

## Next Steps

See `fondo-webhooks-events`.
