---
name: openevidence-deploy-integration
description: |
  Deploy Integration for OpenEvidence.
  Trigger: "openevidence deploy integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Deploy Integration

## Overview

Deploy a containerized OpenEvidence clinical evidence integration service with Docker. This skill covers building a HIPAA-conscious production image that connects to the OpenEvidence API for querying clinical evidence, retrieving medical literature summaries, and validating treatment recommendations. Includes environment configuration with audit logging and data-at-rest encryption flags, health checks that verify API connectivity without exposing PHI, and rolling update strategies that maintain service availability during critical clinical query periods.

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
RUN mkdir -p /app/audit-logs && chown app:app /app/audit-logs
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

## Environment Variables

```bash
export OPENEVIDENCE_API_KEY="oe_live_xxxxxxxxxxxx"
export OPENEVIDENCE_BASE_URL="https://api.openevidence.com/v1"
export OPENEVIDENCE_ORG_ID="org_xxxxxxxxxxxx"
export HIPAA_AUDIT_LOG="true"
export HIPAA_ENCRYPT_AT_REST="true"
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
    const response = await fetch(`${process.env.OPENEVIDENCE_BASE_URL}/status`, {
      headers: { 'Authorization': `Bearer ${process.env.OPENEVIDENCE_API_KEY}` },
    });
    if (!response.ok) throw new Error(`OpenEvidence API returned ${response.status}`);
    // Health response must not contain PHI or query content
    res.json({ status: 'healthy', service: 'openevidence-integration', audit: process.env.HIPAA_AUDIT_LOG === 'true', timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t openevidence-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name openevidence-integration \
  -p 3000:3000 \
  -v /var/log/openevidence:/app/audit-logs \
  -e OPENEVIDENCE_API_KEY -e OPENEVIDENCE_BASE_URL -e OPENEVIDENCE_ORG_ID \
  -e HIPAA_AUDIT_LOG=true -e HIPAA_ENCRYPT_AT_REST=true \
  openevidence-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:3000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t openevidence-integration:v2 . && \
docker stop openevidence-integration && \
docker rm openevidence-integration && \
docker run -d --name openevidence-integration -p 3000:3000 \
  -v /var/log/openevidence:/app/audit-logs \
  -e OPENEVIDENCE_API_KEY -e OPENEVIDENCE_BASE_URL -e OPENEVIDENCE_ORG_ID \
  -e HIPAA_AUDIT_LOG=true -e HIPAA_ENCRYPT_AT_REST=true \
  openevidence-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in OpenEvidence admin portal |
| `403 Forbidden` | Organization access denied | Verify `OPENEVIDENCE_ORG_ID` matches API key scope |
| `404 Not Found` | Evidence query endpoint unavailable | Check API version and endpoint path |
| `429 Rate Limited` | Exceeding clinical query rate limits | Implement backoff; cache evidence responses |
| Audit log not writing | Volume mount missing or permissions | Verify `/var/log/openevidence` exists and is writable |

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps

See `openevidence-webhooks-events`.
