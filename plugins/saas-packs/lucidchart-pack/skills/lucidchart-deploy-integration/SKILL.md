---
name: lucidchart-deploy-integration
description: 'Deploy Integration for Lucidchart.

  Trigger: "lucidchart deploy integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Deploy Integration

## Overview

Deploy a containerized Lucidchart integration service that manages diagram documents, manipulates shapes and connectors programmatically, and synchronizes visual collaboration data through the Lucid API. This skill covers Docker multi-stage builds for the Lucid SDK, OAuth2 token configuration, health checks that validate document API access, and rolling deployments with safe diagram state preservation during updates.

## Prerequisites

- Docker 24+ and Docker Compose v2 installed
- Valid `LUCID_API_KEY` (OAuth2 client credentials) from the Lucid developer portal
- Node.js 20 LTS (build stage)
- Network access to `api.lucid.co` on port 443
- Target deployment host with at least 512MB available memory (diagram rendering is memory-intensive)

## Docker Configuration

```dockerfile
FROM node:20-slim AS builder
WORKDIR /build
COPY package*.json tsconfig.json ./
RUN npm ci
COPY src/ ./src/
RUN npm run build

FROM node:20-slim
RUN groupadd -r lucid && useradd -r -g lucid -m appuser
WORKDIR /app
COPY --from=builder /build/dist ./dist/
COPY --from=builder /build/node_modules ./node_modules/
COPY package*.json ./
RUN npm prune --production
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Environment Variables

```bash
LUCID_API_KEY="lucid_xxxxxxxxxxxxxxxx"       # OAuth2 API key from developer portal
LUCID_CLIENT_SECRET=""                        # OAuth2 client secret
LUCID_BASE_URL="https://api.lucid.co"        # API base URL
LUCID_ACCOUNT_ID=""                           # Target Lucid account identifier
LOG_LEVEL="info"                              # debug | info | warn | error
NODE_ENV="production"
PORT="3000"
```

## Health Check Endpoint

```typescript
import express from "express";

const app = express();

app.get("/health", async (_req, res) => {
  try {
    const response = await fetch(`${process.env.LUCID_BASE_URL}/v1/documents`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${process.env.LUCID_API_KEY}`,
        "Lucid-Api-Version": "1",
      },
    });
    if (!response.ok) throw new Error(`Lucid API returned ${response.status}`);
    const data = await response.json();
    res.json({ status: "healthy", documentCount: data.documents?.length ?? 0 });
  } catch (err) {
    res.status(503).json({ status: "unhealthy", error: (err as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build Image

```bash
docker build -t lucidchart-integration:$(git rev-parse --short HEAD) .
```

### Step 2: Run Container

```bash
docker run -d --name lucidchart-svc \
  --env-file .env.production \
  -p 3000:3000 \
  --memory=512m \
  --restart unless-stopped \
  lucidchart-integration:$(git rev-parse --short HEAD)
```

### Step 3: Verify Health

```bash
curl -s http://localhost:3000/health | jq .
# Expect: { "status": "healthy", "documentCount": 47 }
```

### Step 4: Rolling Update

```bash
docker pull lucidchart-integration:latest
docker stop lucidchart-svc && docker rm lucidchart-svc
docker run -d --name lucidchart-svc --env-file .env.production -p 3000:3000 --memory=512m lucidchart-integration:latest
```

## Rollback Procedure

```bash
# List recent images
docker images lucidchart-integration --format "{{.Tag}} {{.CreatedAt}}" | head -5
# Roll back to previous tag
docker stop lucidchart-svc && docker rm lucidchart-svc
docker run -d --name lucidchart-svc --env-file .env.production -p 3000:3000 --memory=512m lucidchart-integration:<previous-tag>
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 403 on document access | OAuth2 scopes missing `lucidchart.document.content` | Re-authorize with required scopes in Lucid developer portal |
| Container OOM killed | Large diagram rendering exceeds memory | Increase memory limit to 1GB with `--memory=1g` for complex documents |
| Token refresh failures | Expired `LUCID_CLIENT_SECRET` or clock skew | Regenerate client credentials and verify server time sync (NTP) |
| Health check timeout | Rate limiting on `/v1/documents` endpoint | Increase `HEALTHCHECK --timeout` to 15s; cache document count locally |
| Shape API 422 errors | Invalid page or layer ID in diagram mutations | Validate document structure with `GET /v1/documents/{id}/pages` before writes |

## Resources

- [Lucid Developer Docs](https://developer.lucid.co/reference/overview)

## Next Steps

See `lucidchart-webhooks-events`.
