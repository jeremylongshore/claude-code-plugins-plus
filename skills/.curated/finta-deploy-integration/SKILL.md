---
name: finta-deploy-integration
description: 'Deploy Finta integrations and reporting dashboards.

  Trigger with phrases like "deploy finta", "finta dashboard".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
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

## Prerequisites

- A reviewed deployment plan that names the integration owner, data destinations, health signal, and rollback operator.
- Runtime secrets injected by the deployment platform; no credentials in images, repositories, build logs, or health responses.
- Staging validation with synthetic data and an approved change window for production.

## Instructions

1. Build a reproducible image, pin and review dependencies, and run the container as a non-root user.
2. Inject only the scoped credentials required by the running service and confirm that logs redact authorization headers and sensitive payloads.
3. Use readiness checks that test the service’s dependencies without returning provider errors or record data to callers.
4. Deploy a small canary, observe aggregate error rate, queue backlog, and idempotency outcomes, then promote or roll back through the declared mechanism.
5. Disable the integration and rotate scoped secrets immediately if an exposure, unintended destination, or unsafe replay is detected.

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

## Output

Record the image digest, environment name, approved configuration references, deployment owner, canary result, aggregate health metrics, and rollback outcome. Do not include secrets, contact data, raw provider responses, or document URLs.

## Examples

Deploy the image to staging with a synthetic workspace and a read-only credential supplied by the platform. Confirm that `/health` returns only a generic status, simulate an upstream failure, and verify the service becomes unready without leaking an error payload. Roll back the canary before enabling any production destination.

## Resources

- [Finta Platform](https://www.trustfinta.com)

## Next Steps

See `finta-webhooks-events`.
