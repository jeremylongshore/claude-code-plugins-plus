---
name: clickhouse-deploy-integration
description: |
  Deploy ClickHouse-backed applications to Vercel, Fly.io, and Cloud Run with
  connection pooling, secrets, and health checks.
  Use when deploying applications that connect to ClickHouse Cloud,
  configuring platform secrets, or setting up deployment pipelines.
  Trigger: "deploy clickhouse app", "clickhouse Vercel", "clickhouse Cloud Run",
  "clickhouse production deploy", "clickhouse Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Deploy Integration

## Overview

Deploy applications that connect to ClickHouse Cloud from serverless and
container platforms with proper connection management and secrets handling.

## Prerequisites

- ClickHouse Cloud instance (or self-hosted with public endpoint)
- Platform CLI installed (vercel, fly, or gcloud)
- Application tested locally against ClickHouse

## Instructions

### Step 1: ClickHouse Connection Module (Platform-Agnostic)

```typescript
// src/db.ts — singleton for serverless-safe connections
import { createClient, ClickHouseClient } from '@clickhouse/client';

let client: ClickHouseClient | null = null;

export function getClickHouse(): ClickHouseClient {
  if (!client) {
    client = createClient({
      url: process.env.CLICKHOUSE_HOST!,         // https://<host>:8443
      username: process.env.CLICKHOUSE_USER!,
      password: process.env.CLICKHOUSE_PASSWORD!,
      database: process.env.CLICKHOUSE_DATABASE ?? 'default',
      request_timeout: 30_000,
      max_open_connections: 5,    // Low for serverless (many cold starts)
      compression: {
        request: true,            // Saves egress bandwidth
        response: true,
      },
    });
  }
  return client;
}
```

### Step 2: Vercel (Serverless Functions)

```bash
# Set secrets
vercel env add CLICKHOUSE_HOST production
vercel env add CLICKHOUSE_USER production
vercel env add CLICKHOUSE_PASSWORD production
vercel env add CLICKHOUSE_DATABASE production
```

```typescript
// api/events/route.ts (Next.js App Router)
import { getClickHouse } from '@/src/db';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const days = Number(searchParams.get('days') ?? 7);

  const client = getClickHouse();
  const rs = await client.query({
    query: `
      SELECT event_type, count() AS cnt
      FROM events
      WHERE created_at >= now() - INTERVAL {days:UInt32} DAY
      GROUP BY event_type ORDER BY cnt DESC
    `,
    query_params: { days },
    format: 'JSONEachRow',
  });

  return NextResponse.json(await rs.json());
}
```

**Vercel gotchas:**
- Serverless function timeout: 30s (Pro) / 10s (Hobby)
- Each invocation may create a new connection — set `max_open_connections` low
- Use Edge Runtime only with HTTP-based clients (ClickHouse client works fine)

### Step 3: Fly.io (Containers)

```toml
# fly.toml
app = "my-clickhouse-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  CLICKHOUSE_DATABASE = "analytics"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
# Set ClickHouse secrets
fly secrets set CLICKHOUSE_HOST="https://abc123.clickhouse.cloud:8443"
fly secrets set CLICKHOUSE_USER="app_writer"
fly secrets set CLICKHOUSE_PASSWORD="secret"

fly deploy
```

### Step 4: Google Cloud Run

```bash
#!/bin/bash
# deploy-cloud-run.sh
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="clickhouse-app"
REGION="us-central1"

# Store secrets in Secret Manager
echo -n "https://abc123.clickhouse.cloud:8443" | \
  gcloud secrets create ch-host --data-file=- --project=$PROJECT_ID
echo -n "secret-password" | \
  gcloud secrets create ch-password --data-file=- --project=$PROJECT_ID

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets="CLICKHOUSE_HOST=ch-host:latest,CLICKHOUSE_PASSWORD=ch-password:latest" \
  --set-env-vars="CLICKHOUSE_USER=app_writer,CLICKHOUSE_DATABASE=analytics" \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi
```

### Step 5: Health Check Endpoint

```typescript
// Works on all platforms
app.get('/health', async (req, res) => {
  const start = Date.now();
  try {
    const client = getClickHouse();
    const { success } = await client.ping();
    const latencyMs = Date.now() - start;

    res.json({
      status: success ? 'healthy' : 'degraded',
      clickhouse: { connected: success, latencyMs },
      version: process.env.npm_package_version,
    });
  } catch (err) {
    res.status(503).json({
      status: 'unhealthy',
      clickhouse: { connected: false, error: (err as Error).message },
    });
  }
});
```

### Step 6: Graceful Shutdown

```typescript
// Critical: flush pending inserts on shutdown
async function gracefulShutdown() {
  console.log('Shutting down...');
  const client = getClickHouse();
  await client.close();    // Waits for pending operations to complete
  process.exit(0);
}

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
```

## Platform Comparison

| Feature | Vercel | Fly.io | Cloud Run |
|---------|--------|--------|-----------|
| Model | Serverless functions | Containers | Containers |
| Persistent connections | No (cold starts) | Yes | Yes (min-instances) |
| Max timeout | 30s (Pro) | Unlimited | 60min |
| Best for | API endpoints | Long-running apps | Event-driven |
| `max_open_connections` | 1-3 | 10-20 | 5-10 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ECONNRESET` on Vercel | Function timeout | Reduce query scope, increase timeout |
| `TLS handshake` failed | Wrong port | Use port 8443 for Cloud |
| Secret not found | Env var not set | Check platform secret config |
| Cold start latency | New connection per invocation | Use `min-instances=1` on Cloud Run |

## Resources

- [ClickHouse Cloud Connection](https://clickhouse.com/docs/cloud/get-started)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps

For data ingestion patterns, see `clickhouse-webhooks-events`.
