---
name: linktree-deploy-integration
description: 'Deploy Integration for Linktree.

  Trigger: "linktree deploy integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree Deploy Integration

## Overview

Deploy a containerized Linktree integration service that synchronizes profile data, manages link collections, and handles appearance customizations through the Linktree API. This skill covers Docker multi-stage builds optimized for the Linktree SDK, environment configuration for API authentication, health checks that verify Linktree API connectivity, and rolling deployment strategies with zero-downtime link management updates.

## Prerequisites

- Docker 24+ and Docker Compose v2 installed
- Valid `LINKTREE_API_KEY` from the Linktree developer portal
- Node.js 20 LTS (build stage)
- Network access to `api.linktr.ee` on port 443
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
RUN groupadd -r linktree && useradd -r -g linktree -m appuser
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
LINKTREE_API_KEY="lt_live_xxxxxxxxxxxxx"   # Linktree API key from developer portal
LINKTREE_BASE_URL="https://api.linktr.ee"  # API base URL
LINKTREE_PROFILE_ID=""                     # Target profile identifier
LOG_LEVEL="info"                           # debug | info | warn | error
NODE_ENV="production"
PORT="3000"
```

## Health Check Endpoint

```typescript
import express from "express";

const app = express();

app.get("/health", async (_req, res) => {
  try {
    const response = await fetch(`${process.env.LINKTREE_BASE_URL}/v1/profile`, {
      headers: { Authorization: `Bearer ${process.env.LINKTREE_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Linktree API returned ${response.status}`);
    const profile = await response.json();
    res.json({ status: "healthy", profile: profile.username, links: profile.links?.length ?? 0 });
  } catch (err) {
    res.status(503).json({ status: "unhealthy", error: (err as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build Image

```bash
docker build -t linktree-integration:$(git rev-parse --short HEAD) .
```

### Step 2: Run Container

```bash
docker run -d --name linktree-svc \
  --env-file .env.production \
  -p 3000:3000 \
  --restart unless-stopped \
  linktree-integration:$(git rev-parse --short HEAD)
```

### Step 3: Verify Health

```bash
curl -s http://localhost:3000/health | jq .
# Expect: { "status": "healthy", "profile": "your-username", "links": 12 }
```

### Step 4: Rolling Update

```bash
docker pull linktree-integration:latest
docker stop linktree-svc && docker rm linktree-svc
docker run -d --name linktree-svc --env-file .env.production -p 3000:3000 linktree-integration:latest
```

## Rollback Procedure

```bash
# List recent images
docker images linktree-integration --format "{{.Tag}} {{.CreatedAt}}" | head -5
# Roll back to previous tag
docker stop linktree-svc && docker rm linktree-svc
docker run -d --name linktree-svc --env-file .env.production -p 3000:3000 linktree-integration:<previous-tag>
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 on health check | Expired or invalid `LINKTREE_API_KEY` | Rotate key in Linktree developer portal and update `.env` |
| Container OOM killed | Link sync processing large profile trees | Increase memory limit to 512MB with `--memory=512m` |
| ECONNREFUSED to API | DNS or firewall blocking `api.linktr.ee` | Verify outbound HTTPS access and DNS resolution |
| Health check timeout | Slow API response under rate limiting | Increase `HEALTHCHECK --timeout` to 10s and add retry backoff |
| Profile not found | Invalid `LINKTREE_PROFILE_ID` | Verify profile ID exists via `GET /v1/profile` manually |

## Resources

- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)

## Next Steps

See `linktree-webhooks-events`.
