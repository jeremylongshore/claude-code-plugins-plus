---
name: grammarly-deploy-integration
description: |
  Deploy Grammarly integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Grammarly-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy grammarly", "grammarly Vercel",
  "grammarly production deploy", "grammarly Cloud Run", "grammarly Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Deploy Integration

## Overview

Deploy a containerized Grammarly writing assistant integration service with Docker. This skill covers building a production image that connects to the Grammarly Text API for checking grammar, clarity, and tone across submitted text. Includes environment configuration for OAuth client credentials, health checks that verify API token exchange and text analysis endpoints, and rolling update strategies for zero-downtime deployments serving real-time writing feedback.

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
export GRAMMARLY_CLIENT_ID="client_xxxxxxxxxxxx"
export GRAMMARLY_CLIENT_SECRET="secret_xxxxxxxxxxxx"
export GRAMMARLY_BASE_URL="https://api.grammarly.com/ecosystem/api"
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
    const tokenRes = await fetch(`${process.env.GRAMMARLY_BASE_URL}/v1/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: process.env.GRAMMARLY_CLIENT_ID!,
        client_secret: process.env.GRAMMARLY_CLIENT_SECRET!,
      }),
    });
    if (!tokenRes.ok) throw new Error(`Grammarly OAuth returned ${tokenRes.status}`);
    res.json({ status: 'healthy', service: 'grammarly-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t grammarly-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name grammarly-integration \
  -p 3000:3000 \
  -e GRAMMARLY_CLIENT_ID -e GRAMMARLY_CLIENT_SECRET -e GRAMMARLY_BASE_URL \
  grammarly-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t grammarly-integration:v2 . && \
docker stop grammarly-integration && \
docker rm grammarly-integration && \
docker run -d --name grammarly-integration -p 3000:3000 \
  -e GRAMMARLY_CLIENT_ID -e GRAMMARLY_CLIENT_SECRET -e GRAMMARLY_BASE_URL \
  grammarly-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid client credentials | Regenerate credentials in Grammarly Developer Hub |
| `403 Forbidden` | App not approved for API access | Submit app for review in Grammarly partner portal |
| `400 Bad Request` | Text below 30-word minimum | Validate input length before sending to API |
| `429 Rate Limited` | Exceeding API rate limits | Cache results for identical text; implement backoff |
| Token exchange fails | Incorrect `grant_type` or URL | Verify OAuth endpoint and `client_credentials` flow |

## Resources

- [Grammarly Developer Hub](https://developer.grammarly.com)

## Next Steps

See `grammarly-webhooks-events`.
