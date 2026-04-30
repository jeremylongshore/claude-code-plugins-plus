---
name: mindtickle-deploy-integration
description: 'Deploy Integration for MindTickle.

  Trigger: "mindtickle deploy integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Deploy Integration

## Overview

Deploy a containerized MindTickle integration service that manages sales readiness courses, tracks learner progress across quizzes and certifications, and synchronizes enablement data through the MindTickle API. This skill covers Docker multi-stage builds for the MindTickle SDK, API token configuration, health checks that verify course catalog access, and rolling deployments with zero disruption to active training sessions and learner progress tracking.

## Prerequisites

- Docker 24+ and Docker Compose v2 installed
- Valid `MINDTICKLE_API_KEY` from the MindTickle admin console (Settings > API)
- Node.js 20 LTS (build stage)
- Network access to `api.mindtickle.com` on port 443
- Target deployment host with at least 256MB available memory

## Docker Configuration

```dockerfile
FROM node:20-slim AS builder
WORKDIR /build
COPY package*.json tsconfig.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build

FROM node:20-slim
RUN groupadd -r mindtickle && useradd -r -g mindtickle -m appuser
WORKDIR /app
COPY --from=builder /build/dist ./dist/
COPY --from=builder /build/node_modules ./node_modules/
COPY package*.json ./
RUN npm prune --production
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Environment Variables

```bash
MINDTICKLE_API_KEY="mt_xxxxxxxxxxxxxxxx"        # API key from admin console
MINDTICKLE_BASE_URL="https://api.mindtickle.com" # API base URL
MINDTICKLE_COMPANY_ID=""                         # Company identifier for multi-tenant access
MINDTICKLE_WEBHOOK_SECRET=""                     # HMAC secret for inbound webhook verification
LOG_LEVEL="info"                                 # debug | info | warn | error
NODE_ENV="production"
PORT="3000"
```

## Health Check Endpoint

```typescript
import express from "express";

const app = express();

app.get("/health", async (_req, res) => {
  try {
    const response = await fetch(`${process.env.MINDTICKLE_BASE_URL}/v2/courses`, {
      headers: {
        Authorization: `Bearer ${process.env.MINDTICKLE_API_KEY}`,
        "X-Company-Id": process.env.MINDTICKLE_COMPANY_ID ?? "",
      },
    });
    if (!response.ok) throw new Error(`MindTickle API returned ${response.status}`);
    const data = await response.json();
    res.json({ status: "healthy", activeCourses: data.courses?.length ?? 0 });
  } catch (err) {
    res.status(503).json({ status: "unhealthy", error: (err as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build Image

```bash
docker build -t mindtickle-integration:$(git rev-parse --short HEAD) .
```

### Step 2: Run Container

```bash
docker run -d --name mindtickle-svc \
  --env-file .env.production \
  -p 3000:3000 \
  --restart unless-stopped \
  mindtickle-integration:$(git rev-parse --short HEAD)
```

### Step 3: Verify Health

```bash
curl -s http://localhost:3000/health | jq .
# Expect: { "status": "healthy", "activeCourses": 24 }
```

### Step 4: Rolling Update

```bash
docker pull mindtickle-integration:latest
docker stop mindtickle-svc && docker rm mindtickle-svc
docker run -d --name mindtickle-svc --env-file .env.production -p 3000:3000 mindtickle-integration:latest
```

## Rollback Procedure

```bash
# List recent images
docker images mindtickle-integration --format "{{.Tag}} {{.CreatedAt}}" | head -5
# Roll back to previous tag
docker stop mindtickle-svc && docker rm mindtickle-svc
docker run -d --name mindtickle-svc --env-file .env.production -p 3000:3000 mindtickle-integration:<previous-tag>
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 on course listing | Expired or revoked `MINDTICKLE_API_KEY` | Regenerate key in MindTickle admin console under Settings > API |
| 403 company access denied | Invalid `MINDTICKLE_COMPANY_ID` or key lacks tenant scope | Verify company ID and ensure API key has multi-tenant permissions |
| Learner sync timeouts | Large user base exceeding pagination limits | Implement cursor-based pagination with `page_size=100` and retry logic |
| Webhook HMAC mismatch | Incorrect `MINDTICKLE_WEBHOOK_SECRET` or payload tampering | Re-copy webhook secret from admin console; verify raw body is used for HMAC |
| Quiz progress 404 | Course or module was archived during sync | Add pre-check with `GET /v2/courses/{id}` to confirm course is active before progress writes |

## Resources

- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-webhooks-events`.
