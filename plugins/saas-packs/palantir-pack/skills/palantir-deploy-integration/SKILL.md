---
name: palantir-deploy-integration
description: |
  Deploy Palantir integrations to production platforms.
  Use when deploying Palantir-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy palantir", "palantir production",
  "palantir production deploy", "palantir CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Deploy Integration

## Overview

Deploy Palantir integrations as data pipeline workers — persistent services that
maintain database connections, run scheduled queries, and process data continuously.


## Prerequisites
- Palantir API keys for production environment
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
import { Pool } from '@palantir/sdk';

const pool = new Pool({
  connectionString: process.env.PALANTIR_DATABASE_URL,
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

// Graceful shutdown
process.on('SIGTERM', () => pool.end());
```

### Deploy to Cloud Run
```bash
gcloud run deploy palantir-worker \
  --image gcr.io/$PROJECT_ID/palantir-worker \
  --min-instances=1 \
  --set-secrets=PALANTIR_DATABASE_URL=palantir-db-url:latest
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const palantirStatus = await checkPalantirConnection();

  return Response.json({
    status: palantirStatus ? 'healthy' : 'degraded',
    services: {
      palantir: palantirStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Palantir API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Palantir integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Palantir connectivity.

## Output
- Application deployed to production
- Palantir secrets securely configured
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
- [Palantir Deploy Guide](https://docs.palantir.com/deploy)

## Next Steps
For webhook handling, see `palantir-webhooks-events`.