---
name: supabase-deploy-integration
description: |
  Deploy Supabase integrations to production platforms.
  Use when deploying Supabase-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy supabase", "supabase production",
  "supabase production deploy", "supabase CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, supabase]
---

# Supabase Deploy Integration

## Overview

Deploy Supabase integrations as data pipeline workers — persistent services that
maintain database connections, run scheduled queries, and process data continuously.


## Prerequisites
- Supabase API keys for production environment
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
import { Pool } from '@supabase/supabase-js';

const pool = new Pool({
  connectionString: process.env.SUPABASE_DATABASE_URL,
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

// Graceful shutdown
process.on('SIGTERM', () => pool.end());
```

### Deploy to Cloud Run
```bash
gcloud run deploy supabase-worker \
  --image gcr.io/$PROJECT_ID/supabase-worker \
  --min-instances=1 \
  --set-secrets=SUPABASE_DATABASE_URL=supabase-db-url:latest
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const supabaseStatus = await checkSupabaseConnection();

  return Response.json({
    status: supabaseStatus ? 'healthy' : 'degraded',
    services: {
      supabase: supabaseStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Supabase API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Supabase integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Supabase connectivity.

## Output
- Application deployed to production
- Supabase secrets securely configured
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
- [Supabase Deploy Guide](https://supabase.com/docs/deploy)

## Next Steps
For webhook handling, see `supabase-webhooks-events`.