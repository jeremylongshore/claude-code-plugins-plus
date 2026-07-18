# Platform Deployment Paths

Pick one platform and follow its deployment path. All three store `NOTION_TOKEN`
as a secret that is injected at runtime, never committed to source. Each imports
the singleton, rate limiter, and cache from [implementation.md](implementation.md).

## Option A: Vercel (serverless functions)

Best for: Next.js apps, API routes, low-traffic webhooks. Cold starts are ~200ms for Node.js.

```bash
# Store the token as a production secret
vercel env add NOTION_TOKEN production
# Paste ntn_xxx when prompted — Vercel encrypts at rest

# Deploy
vercel --prod
```

Vercel API route using the singleton:

```typescript
// app/api/notion/query/route.ts (Next.js App Router)
import { NextResponse } from 'next/server';
import { getNotionClient } from '@/lib/notion-client';
import { rateLimiter } from '@/lib/rate-limiter';
import { notionCache } from '@/lib/cache';

export async function POST(request: Request) {
  const { databaseId, filter } = await request.json();
  const cacheKey = `db:${databaseId}:${JSON.stringify(filter)}`;

  // Check cache first
  const cached = notionCache.get(cacheKey);
  if (cached) return NextResponse.json(cached);

  try {
    const notion = getNotionClient();
    const response = await rateLimiter.execute(() =>
      notion.databases.query({ database_id: databaseId, filter, page_size: 100 })
    );

    const result = {
      pages: response.results.map((page: any) => ({
        id: page.id,
        title: page.properties?.Name?.title?.[0]?.plain_text ?? '',
        lastEdited: page.last_edited_time,
      })),
      hasMore: response.has_more,
    };

    notionCache.set(cacheKey, result, 30); // cache 30 seconds
    return NextResponse.json(result);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.code ?? 'unknown', message: error.message },
      { status: error.status ?? 500 }
    );
  }
}
```

Add the health route:

```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server';
import { healthCheck } from '@/lib/health';

export async function GET() {
  const result = await healthCheck();
  return NextResponse.json(result, { status: result.status === 'healthy' ? 200 : 503 });
}
```

## Option B: Railway (container-based, always-on)

Best for: Long-running sync services, high-frequency webhooks, apps needing persistent state.

```bash
# Set the secret via CLI
railway variables set NOTION_TOKEN=ntn_xxx

# Deploy from the current directory
railway up

# Verify
railway status
```

Railway uses `Dockerfile` or Nixpacks auto-detection. For Node.js, ensure `package.json` has a `start` script:

```json
{
  "scripts": {
    "start": "node dist/index.js",
    "build": "tsc"
  }
}
```

Railway provides persistent volumes and cron jobs, making it ideal for Notion sync services that run on a schedule.

## Option C: Fly.io (edge containers)

Best for: Global distribution, low-latency API proxies, services needing machines in multiple regions.

```toml
# fly.toml
app = "my-notion-service"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[http_service.checks]]
  path = "/health"
  interval = "30s"
  timeout = "5s"
  method = "GET"
  grace_period = "10s"
```

```bash
# Set secrets (encrypted, injected at runtime)
fly secrets set NOTION_TOKEN=ntn_xxx

# Deploy
fly deploy

# Verify health
curl https://my-notion-service.fly.dev/health
```
