---
name: glean-deploy-integration
description: 'Deploy Glean custom connectors as scheduled jobs on Cloud Run, Lambda,
  or Fly.io.

  Trigger: "deploy glean connector", "glean connector hosting", "schedule glean indexing".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gcloud:*), Grep
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Deploy Integration

## Overview

Deploy a containerized Glean enterprise search integration service with Docker. This skill covers building a production image that connects to Glean's Indexing and Search APIs for managing document ingestion, custom datasource connectors, and search queries. Includes environment configuration for multi-datasource indexing, health checks that verify API connectivity and indexing status, and rolling update strategies that avoid interrupting active indexing jobs.

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
export GLEAN_API_KEY="glean_xxxxxxxxxxxx"
export GLEAN_BASE_URL="https://company-be.glean.com/api/index/v1"
export GLEAN_DATASOURCE="custom-wiki"
export GLEAN_DOMAIN="company-be.glean.com"
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
    const response = await fetch(`https://${process.env.GLEAN_DOMAIN}/api/index/v1/getdatasourceconfig`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GLEAN_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ datasource: process.env.GLEAN_DATASOURCE }),
    });
    if (!response.ok) throw new Error(`Glean API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'glean-integration', datasource: process.env.GLEAN_DATASOURCE, timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t glean-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name glean-integration \
  -p 3000:3000 \
  -e GLEAN_API_KEY -e GLEAN_BASE_URL -e GLEAN_DATASOURCE -e GLEAN_DOMAIN \
  glean-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t glean-integration:v2 . && \
docker stop glean-integration && \
docker rm glean-integration && \
docker run -d --name glean-integration -p 3000:3000 \
  -e GLEAN_API_KEY -e GLEAN_BASE_URL -e GLEAN_DATASOURCE -e GLEAN_DOMAIN \
  glean-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid indexing token | Regenerate token in Glean admin under Custom Connectors |
| `403 Forbidden` | Datasource not registered | Create datasource in Glean admin before indexing |
| `400 Bad Request` | Malformed document payload | Validate document schema against Glean Indexing API spec |
| `429 Rate Limited` | Exceeding indexing rate limits | Batch documents (max 100 per request) and add backoff |
| Stale search results | Connector not running on schedule | Verify cron schedule or Cloud Scheduler job status |

## Prerequisites

- An approved deployment change, environment-specific secret references, and a destination allowlist that distinguishes sandbox, staging, and production.
- Health, freshness, and synthetic allow/deny baselines plus a tested rollback artifact.
- A canary datasource that carries only approved data and has a named owner.

## Instructions

1. Build and test the immutable artifact with mocked or sandbox fixtures; refuse literal credentials and unknown destinations.
2. Deploy to staging, verify health, bounded index behavior, freshness, and both authorization probes before requesting production approval.
3. Release first to the canary datasource with concurrency and retry caps, monitoring errors and redacted correlation IDs.
4. Promote in stages only while all probes remain within budget; restore the previous artifact/configuration immediately on regression.
5. Retain the release receipt and rollback result, then revoke any temporary deployment credential.

## Output

Produce a deployment receipt with artifact digest, environment, canary datasource, health/freshness/allow/deny outcomes, owner approval, rollout state, and rollback reference. Exclude secrets and indexed content.

## Examples

`artifact=sha256:opaque; env=staging; canary=sandbox-guides; health=pass; freshness=pass; allow=pass; deny=pass; rollback=release-r31` supports a controlled promotion.

## Resources

- [Glean Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- Glean Search API

## Next Steps

See `glean-webhooks-events`.
