---
name: appfolio-deploy-integration
description: 'Deploy AppFolio integration service to cloud infrastructure.

  Trigger: "deploy appfolio".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Deploy Integration

## Overview

Deploy a containerized AppFolio property management integration service with Docker. This skill covers building a production-ready image that connects to the AppFolio Stack API for managing properties, tenants, and work orders. Includes environment configuration for multi-property setups, health checks that verify API connectivity, and rolling update strategies for zero-downtime deployments across your property portfolio.

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
export APPFOLIO_API_KEY="af_live_xxxxxxxxxxxx"
export APPFOLIO_BASE_URL="https://your-company.appfolio.com/api/v1"
export APPFOLIO_COMPANY_ID="your-company"
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
    const response = await fetch(`${process.env.APPFOLIO_BASE_URL}/properties`, {
      headers: { 'Authorization': `Bearer ${process.env.APPFOLIO_API_KEY}` },
    });
    if (!response.ok) throw new Error(`AppFolio API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'appfolio-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t appfolio-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name appfolio-integration \
  -p 3000:3000 \
  -e APPFOLIO_API_KEY -e APPFOLIO_BASE_URL -e APPFOLIO_COMPANY_ID \
  appfolio-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t appfolio-integration:v2 . && \
docker stop appfolio-integration && \
docker rm appfolio-integration && \
docker run -d --name appfolio-integration -p 3000:3000 \
  -e APPFOLIO_API_KEY -e APPFOLIO_BASE_URL -e APPFOLIO_COMPANY_ID \
  appfolio-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in AppFolio Stack Partner portal |
| `403 Forbidden` | Missing property access scope | Request additional scopes from AppFolio admin |
| `404 Not Found` | Incorrect base URL or company ID | Verify `APPFOLIO_BASE_URL` matches your subdomain |
| `429 Rate Limited` | Too many requests per minute | Implement exponential backoff with 60s window |
| Container exits immediately | Missing required env vars | Ensure all env vars are set before starting |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)

## Next Steps

See `appfolio-webhooks-events`.
