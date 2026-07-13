---
name: onenote-deploy-integration
description: 'Deploy OneNote integrations with MSAL token persistence, health checks,
  and container best practices.

  Use when containerizing OneNote services, configuring health endpoints, or managing
  token cache in production.

  Trigger with "onenote deploy", "onenote docker", "onenote container", "onenote health
  check".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Deploy Integration

## Overview

Deploying OneNote integrations into containers breaks local development assumptions: MSAL token caches vanish on restart, health checks must validate Graph API connectivity (not just HTTP 200), and graceful shutdown must flush token state. This skill provides production-ready Dockerfile, Docker Compose, and Kubernetes manifests with MSAL token persistence, health/readiness probes that verify actual Graph reachability, and SIGTERM handling.

## Prerequisites

- Docker 24+ and Docker Compose v2
- Node.js 20 LTS or Python 3.11+
- Azure AD app registration with delegated permissions (`Notes.Read`, `Notes.ReadWrite`)
- Redis (recommended for multi-replica) or persistent volume for token cache

## Instructions

### Dockerfile

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json src/ ./
RUN npm run build

FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
RUN mkdir -p /app/.cache/msal && chown -R node:node /app/.cache
USER node
ENV NODE_ENV=production MSAL_CACHE_DIR=/app/.cache/msal
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -sf http://localhost:3000/health || exit 1
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### MSAL Token Cache Persistence

**File-based (single replica):**

```typescript
// src/auth/token-cache.ts
import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import path from "path";

const CACHE_DIR = process.env.MSAL_CACHE_DIR || "/app/.cache/msal";
const CACHE_FILE = path.join(CACHE_DIR, "token-cache.json");

export async function loadCache(): Promise<string | null> {
  try {
    if (existsSync(CACHE_FILE)) return await readFile(CACHE_FILE, "utf-8");
  } catch (err) { console.error("Failed to load token cache:", err); }
  return null;
}

export async function saveCache(contents: string): Promise<void> {
  await mkdir(CACHE_DIR, { recursive: true });
  await writeFile(CACHE_FILE, contents, { mode: 0o600 });
}
```

**Redis-based (multi-replica):**

```typescript
// src/auth/redis-cache.ts
import { createClient, RedisClientType } from "redis";
const CACHE_KEY = "msal:onenote:token-cache";
let redis: RedisClientType;

export async function initRedisCache(): Promise<void> {
  redis = createClient({ url: process.env.REDIS_URL || "redis://localhost:6379" });
  redis.on("error", (err) => console.error("Redis cache error:", err));
  await redis.connect();
}
export async function loadCache(): Promise<string | null> { return redis.get(CACHE_KEY); }
export async function saveCache(contents: string): Promise<void> {
  await redis.set(CACHE_KEY, contents, { EX: 86400 }); // 24h TTL
}
export async function flushAndDisconnect(): Promise<void> { await redis.quit(); }
```

### Health Check Endpoint

Validates Graph API connectivity, not just HTTP liveness:

```typescript
// src/health.ts
app.get("/health", async (_req, res) => {
  const checks: Record<string, string> = {};
  let healthy = true;
  try { await getGraphClient(); checks.auth = "ok"; }
  catch { checks.auth = "failed"; healthy = false; }
  try {
    await (await getGraphClient()).api("/me/onenote/notebooks").top(1).get();
    checks.graph_api = "ok";
  } catch (err: any) {
    checks.graph_api = err?.statusCode === 429 ? "rate_limited" : "failed";
    if (err?.statusCode !== 429) healthy = false;
  }
  res.status(healthy ? 200 : 503).json({ status: healthy ? "healthy" : "unhealthy", checks });
});

app.get("/ready", async (_req, res) => {
  try { await getGraphClient(); res.json({ ready: true }); }
  catch { res.status(503).json({ ready: false }); }
});
```

### Graceful Shutdown

```typescript
// src/shutdown.ts
export function registerShutdownHandlers(server: any, getCacheContents: () => string): void {
  let shuttingDown = false;
  const shutdown = async (signal: string) => {
    if (shuttingDown) return;
    shuttingDown = true;
    console.log(`${signal} received. Flushing token cache...`);
    try { await saveCache(getCacheContents()); } catch (e) { console.error("Cache flush failed:", e); }
    server.close(() => process.exit(0));
    setTimeout(() => { console.error("Forced exit after 10s"); process.exit(1); }, 10_000);
  };
  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}
```

### Docker Compose (Local Development)

```yaml
version: "3.9"
services:
  onenote-service:
    build: .
    ports: ["3000:3000"]
    environment:
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - REDIS_URL=redis://redis:6379
    depends_on:
      redis: { condition: service_healthy }
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: onenote-integration }
spec:
  replicas: 2
  selector: { matchLabels: { app: onenote-integration } }
  template:
    metadata: { labels: { app: onenote-integration } }
    spec:
      terminationGracePeriodSeconds: 15
      containers:
        - name: onenote
          image: your-registry/onenote-integration:latest
          ports: [{ containerPort: 3000 }]
          env:
            - { name: AZURE_TENANT_ID, valueFrom: { secretKeyRef: { name: onenote-creds, key: tenant-id } } }
            - { name: AZURE_CLIENT_ID, valueFrom: { secretKeyRef: { name: onenote-creds, key: client-id } } }
            - { name: REDIS_URL, value: "redis://redis-service:6379" }
          livenessProbe:
            httpGet: { path: /health, port: 3000 }
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet: { path: /ready, port: 3000 }
            initialDelaySeconds: 5
          resources:
            requests: { memory: "128Mi", cpu: "100m" }
            limits: { memory: "256Mi" }
```

## Output

- `Dockerfile` — multi-stage build with MSAL cache directory and health check
- `docker-compose.yml` — local development stack with Redis
- `k8s/deployment.yaml` — Kubernetes deployment with liveness/readiness probes
- `src/auth/token-cache.ts` — file-based MSAL cache persistence
- `src/auth/redis-cache.ts` — Redis-backed MSAL cache for multi-replica
- `src/health.ts` — health and readiness endpoints validating Graph API
- `src/shutdown.ts` — graceful shutdown with token cache flush

## Error Handling

| Deploy Error | Cause | Fix |
|-------------|-------|-----|
| Token cache empty after restart | Volume not mounted or permissions wrong | Verify volume mount; `chown node:node` on cache dir |
| Health returns 503 | Graph API unreachable or token expired | Check `checks.graph_api`; re-authenticate if cache stale |
| Redis connection refused | Redis not started or wrong URL | Verify `REDIS_URL`; check Redis container health |
| `EACCES` on cache file | Container running as wrong user | Ensure `USER node` in Dockerfile |
| Liveness probe failing | `initialDelaySeconds` too short | Increase to 20-30s for slow token acquisition |

## Examples

```bash
# Build and run locally
echo "AZURE_TENANT_ID=your-tenant" >> .env
echo "AZURE_CLIENT_ID=your-client" >> .env
docker compose up --build
curl http://localhost:3000/health

# Deploy to Kubernetes
kubectl create secret generic onenote-creds \
  --from-literal=tenant-id=$AZURE_TENANT_ID \
  --from-literal=client-id=$AZURE_CLIENT_ID
kubectl apply -f k8s/deployment.yaml
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [MSAL Python Token Cache](https://learn.microsoft.com/en-us/entra/msal/python/)
- [Graph API Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Graph API Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)

## Next Steps

- Set up CI pipelines with `onenote-ci-integration`
- Monitor rate limits in production with `onenote-rate-limits`
- Add performance tuning with `onenote-performance-tuning`
