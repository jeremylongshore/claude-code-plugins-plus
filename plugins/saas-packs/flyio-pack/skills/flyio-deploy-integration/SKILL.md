---
name: flyio-deploy-integration
description: 'Advanced Fly.io deployment strategies including blue-green deployments,

  canary releases, multi-region rollouts, and Machines API orchestration.

  Trigger: "fly.io blue-green", "fly.io canary deploy", "fly.io rolling update".

  '
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Deploy Integration

## Overview

Deploy edge applications on Fly.io with Docker containers and the `fly.toml` configuration file. This skill covers building production images optimized for Fly's micro-VM architecture, configuring `fly.toml` for services, health checks, and multi-region placement, verifying API connectivity from edge locations, and executing rolling updates with automatic rollback. Fly.io deploys as Firecracker micro-VMs, so containers start in under a second and scale to zero when idle.

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
EXPOSE 8080
CMD ["node", "dist/index.js"]
```

## Fly.io Configuration

```toml
# fly.toml
app = "my-integration"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  LOG_LEVEL = "info"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/health"
```

## Environment Variables

```bash
export FLY_API_TOKEN="fo1_xxxxxxxxxxxx"
fly secrets set FLYIO_APP_NAME="my-integration"
fly secrets set LOG_LEVEL="info"
```

## Health Check Endpoint

```typescript
import express from 'express';

const app = express();

app.get('/health', async (req, res) => {
  try {
    const region = process.env.FLY_REGION || 'unknown';
    const appName = process.env.FLY_APP_NAME || 'unknown';
    res.json({ status: 'healthy', service: 'flyio-integration', region, app: appName, timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
fly launch --no-deploy
```

### Step 2: Run

```bash
fly deploy --strategy rolling
```

### Step 3: Verify

```bash
fly status
curl -s https://my-integration.fly.dev/health | jq .
```

### Step 4: Rolling Update

```bash
fly deploy --strategy rolling --wait-timeout 300
fly releases --image
fly releases rollback   # if health check fails
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `Machine failed to start` | Missing env vars or port mismatch | Check `fly logs` and verify `internal_port` matches `EXPOSE` |
| `Health check failing` | App not listening on correct port | Ensure app binds to `0.0.0.0:8080` not `127.0.0.1` |
| `No machines in region` | Region not added to app | Run `fly scale count 1 --region iad` |
| `401 Unauthorized` | Invalid `FLY_API_TOKEN` | Regenerate token with `fly tokens create deploy` |
| Slow cold starts | Large image or heavy startup | Use multi-stage build, set `auto_stop_machines = false` for latency-critical apps |

## Resources

- [Fly.io Deploy Docs](https://fly.io/docs/launch/deploy/)
- [fly.toml Reference](https://fly.io/docs/reference/configuration/)

## Next Steps

See `flyio-webhooks-events`.
