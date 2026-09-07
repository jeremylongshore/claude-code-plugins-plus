# Platform Deployment — Vercel, Fly.io, Cloud Run

Full per-platform deploy walkthroughs. All three consume the same
platform-agnostic connection module (`src/db.ts`) shown in SKILL.md Step 1 —
only secrets handling and runtime model differ.

## Vercel (Serverless Functions)

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

## Fly.io (Containers)

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

## Google Cloud Run

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

## Platform Comparison

| Feature | Vercel | Fly.io | Cloud Run |
|---------|--------|--------|-----------|
| Model | Serverless functions | Containers | Containers |
| Persistent connections | No (cold starts) | Yes | Yes (min-instances) |
| Max timeout | 30s (Pro) | Unlimited | 60min |
| Best for | API endpoints | Long-running apps | Event-driven |
| `max_open_connections` | 1-3 | 10-20 | 5-10 |
