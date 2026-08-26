---
name: appfolio-deploy-integration
description: 'Deploy AppFolio integration service to cloud infrastructure.

  Trigger: "deploy appfolio".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
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

## Prerequisites

- A verified provider contract and a secret-manager-backed, contract-bound
  AppFolio client; do not put credential values in image layers, compose files,
  shell history, or deployment logs.
- A deployment platform that can perform a real rolling/canary update with
  readiness checks, traffic control, rollback, and a named release owner.
- Separate staging and production identities, a synthetic staging smoke
  fixture, and an incident plan for unknown write or reconciliation state.

## Instructions

1. Build a non-root image with locked dependencies and expose only a local
   liveness endpoint; provider availability belongs to readiness, not process
   survival.
2. Inject the verified client configuration at runtime from the secret manager
   and validate its contract in staging through an authorized safe read.
3. Roll out a new revision gradually, monitor redacted readiness/error signals,
   and retain the prior revision until the traffic window succeeds.
4. On any failed readiness, contract, secret, or reconciliation check, halt
   traffic promotion and roll back through the deployment platform.

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
  CMD node -e "fetch('http://127.0.0.1:3000/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node", "dist/index.js"]
```

## Runtime Configuration

```bash
# Values are injected by the deployment platform's secret manager; do not
# paste live credentials into a terminal command or checked-in configuration.
APPFOLIO_BASE_URL="provider-issued base URL"
APPFOLIO_COMPANY_ID="approved portfolio identifier"
export LOG_LEVEL="info"
export PORT="3000"
export NODE_ENV="production"
```

## Health Check Endpoint

```typescript
import express from 'express';

const app = express();

// Liveness proves this process can serve; it must not restart a healthy worker
// solely because the external provider is degraded.
app.get('/health', (_req, res) => {
  res.json({ status: 'healthy', service: 'appfolio-integration' });
});

app.get('/ready', async (_req, res) => {
  try {
    const response = await createVerifiedAppFolioClient().get('/properties?limit=1');
    if (response.status < 200 || response.status >= 300) throw new Error(`AppFolio API returned ${response.status}`);
    res.json({ status: 'ready', service: 'appfolio-integration', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'not-ready', error: 'provider readiness check failed' });
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
# Submit the immutable image digest to the platform's deployment controller.
# Configure /health as liveness and /ready as readiness, shift traffic in
# stages, and retain the previous revision until the release window completes.
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in AppFolio Stack Partner portal |
| `403 Forbidden` | Missing property access scope | Request additional scopes from AppFolio admin |
| `404 Not Found` | Incorrect base URL or company ID | Verify `APPFOLIO_BASE_URL` matches your subdomain |
| `429 Rate Limited` | Too many requests per minute | Implement exponential backoff with 60s window |
| Container exits immediately | Missing required env vars | Ensure all env vars are set before starting |

## Output

- A non-root container with a local liveness endpoint and a separate,
  redacted provider readiness result
- A secret-manager/runtime configuration boundary rather than credential values
  in images or commands
- A staged deployment receipt with readiness evidence, traffic state, owner,
  rollback target, and reconciliation status

## Examples

For a property-sync release, deploy the new image to staging with a synthetic
safe-read fixture and confirm `/health` stays live while `/ready` reflects the
provider client result. Promote a small production traffic slice only after the
managed identity, redacted readiness, alerts, and rollback target are verified.
If readiness fails, a secret is absent, or a prior write has an unknown outcome,
freeze promotion, return traffic to the prior revision, and assign reconciliation
before attempting another rollout.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)

## Next Steps

See `appfolio-webhooks-events`.
