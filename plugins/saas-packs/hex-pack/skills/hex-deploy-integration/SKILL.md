---
name: hex-deploy-integration
description: |
  Deploy Hex integrations to production platforms.
  Use when deploying Hex-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy hex", "hex production",
  "hex production deploy", "hex CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hex]
---

# Hex Deploy Integration

## Overview

Deploy Hex integrations as data pipeline workers — persistent services that
maintain database connections, run scheduled queries, and process data continuously.


## Prerequisites
- Hex API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Data Pipeline Worker (Recommended for Data Platforms)

### Why Persistent Worker?
Data platform integrations need persistent database connections and often run
scheduled jobs — ETL pipelines, materialized view refreshes, data syncs.

### Docker Worker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
# Long-running worker with connection pooling
CMD ["node", "worker.js"]
```

### Connection Pooling
```typescript
// worker.ts — maintains connection pool across requests
import { Pool } from '@hex/sdk';

const pool = new Pool({
  connectionString: process.env.HEX_DATABASE_URL,
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

// Graceful shutdown
process.on('SIGTERM', () => pool.end());
```

### Deploy to Cloud Run
```bash
gcloud run deploy hex-worker \
  --image gcr.io/$PROJECT_ID/hex-worker \
  --min-instances=1 \
  --set-secrets=HEX_DATABASE_URL=hex-db-url:latest
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const hexStatus = await checkHexConnection();

  return Response.json({
    status: hexStatus ? 'healthy' : 'degraded',
    services: {
      hex: hexStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Hex API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Hex integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Hex connectivity.

## Output
- Application deployed to production
- Hex secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Hex Deploy Guide](https://docs.hex.com/deploy)

## Next Steps
For webhook handling, see `hex-webhooks-events`.