---
name: snowflake-deploy-integration
description: |
  Deploy Snowflake integrations to production platforms.
  Use when deploying Snowflake-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy snowflake", "snowflake production",
  "snowflake production deploy", "snowflake CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, snowflake]
---

# Snowflake Deploy Integration

## Overview

Deploy Snowflake integrations as data pipeline workers — persistent services that
maintain database connections, run scheduled queries, and process data continuously.


## Prerequisites
- Snowflake API keys for production environment
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
import { Pool } from '@snowflake/sdk';

const pool = new Pool({
  connectionString: process.env.SNOWFLAKE_DATABASE_URL,
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

// Graceful shutdown
process.on('SIGTERM', () => pool.end());
```

### Deploy to Cloud Run
```bash
gcloud run deploy snowflake-worker \
  --image gcr.io/$PROJECT_ID/snowflake-worker \
  --min-instances=1 \
  --set-secrets=SNOWFLAKE_DATABASE_URL=snowflake-db-url:latest
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const snowflakeStatus = await checkSnowflakeConnection();

  return Response.json({
    status: snowflakeStatus ? 'healthy' : 'degraded',
    services: {
      snowflake: snowflakeStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Snowflake API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Snowflake integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Snowflake connectivity.

## Output
- Application deployed to production
- Snowflake secrets securely configured
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
- [Snowflake Deploy Guide](https://docs.snowflake.com/deploy)

## Next Steps
For webhook handling, see `snowflake-webhooks-events`.