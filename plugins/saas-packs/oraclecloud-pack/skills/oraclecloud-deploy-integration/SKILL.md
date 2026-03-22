---
name: oraclecloud-deploy-integration
description: |
  Deploy Oracle Cloud integrations to production platforms.
  Use when deploying Oracle Cloud-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy oraclecloud", "oraclecloud production",
  "oraclecloud production deploy", "oraclecloud CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Deploy Integration

## Overview

Deploy Oracle Cloud integrations as data pipeline workers — persistent services that
maintain database connections, run scheduled queries, and process data continuously.


## Prerequisites
- Oracle Cloud API keys for production environment
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
import { Pool } from '@oraclecloud/sdk';

const pool = new Pool({
  connectionString: process.env.ORACLECLOUD_DATABASE_URL,
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

// Graceful shutdown
process.on('SIGTERM', () => pool.end());
```

### Deploy to Cloud Run
```bash
gcloud run deploy oraclecloud-worker \
  --image gcr.io/$PROJECT_ID/oraclecloud-worker \
  --min-instances=1 \
  --set-secrets=ORACLECLOUD_DATABASE_URL=oraclecloud-db-url:latest
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const oraclecloudStatus = await checkOracleCloudConnection();

  return Response.json({
    status: oraclecloudStatus ? 'healthy' : 'degraded',
    services: {
      oraclecloud: oraclecloudStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Oracle Cloud API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Oracle Cloud integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Oracle Cloud connectivity.

## Output
- Application deployed to production
- Oracle Cloud secrets securely configured
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
- [Oracle Cloud Deploy Guide](https://docs.oraclecloud.com/deploy)

## Next Steps
For webhook handling, see `oraclecloud-webhooks-events`.