---
name: notion-deploy-integration
description: |
  Deploy Node.js applications that use the Notion API to production
  on Vercel, Railway, or Fly.io. Use when deploying Notion-powered
  backends, setting up NOTION_TOKEN in production secrets, configuring
  serverless singleton patterns, or adding health checks that verify
  Notion connectivity. Trigger: "deploy notion app", "notion production",
  "notion vercel deploy", "notion railway", "notion fly.io".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(vercel:*), Bash(railway:*), Bash(fly:*), Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, deployment, serverless]
compatible-with: claude-code
---

# Deploy Notion-Integrated Applications

Ship Node.js apps that talk to the Notion API to Vercel, Railway, or Fly.io. This skill covers environment variable management, the Notion client singleton pattern for serverless, rate limit handling at 3 req/sec, health check endpoints that verify Notion connectivity, and caching strategies to reduce API calls.

## Prerequisites

- Node.js >= 18 project with `@notionhq/client` installed (`npm i @notionhq/client`)
- Working Notion integration tested locally with a valid `NOTION_TOKEN` (starts with `ntn_`)
- Platform CLI installed for your target: `vercel`, `railway`, or `fly`
- Database or page IDs your integration needs access to

## Instructions

### Step 1 — Prepare the Application for Production

Build a production-ready entry point with a Notion client singleton, rate limit handling, response caching, and a health check endpoint.

**Notion client singleton (critical for serverless):**

Serverless functions recycle containers unpredictably. Creating a new `Client` on every invocation wastes cold-start time and risks hitting rate limits. A module-level singleton reuses the client across warm invocations.

```typescript
// src/notion-client.ts — singleton for serverless environments
import { Client, LogLevel, isNotionClientError, APIErrorCode } from '@notionhq/client';

let client: Client | null = null;

export function getNotionClient(): Client {
  if (!client) {
    if (!process.env.NOTION_TOKEN) {
      throw new Error('NOTION_TOKEN environment variable is not set');
    }
    client = new Client({
      auth: process.env.NOTION_TOKEN,
      logLevel: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.DEBUG,
      timeoutMs: 30_000,
    });
  }
  return client;
}
```

**Rate limit handler (Notion enforces 3 requests/second):**

Notion returns HTTP 429 with a `Retry-After` header when you exceed the rate limit. The SDK retries automatically, but production apps should add queuing to avoid cascading failures under load.

```typescript
// src/rate-limiter.ts — token bucket for 3 req/sec
export class NotionRateLimiter {
  private queue: Array<{ resolve: () => void }> = [];
  private activeRequests = 0;
  private readonly maxPerSecond = 3;

  async acquire(): Promise<void> {
    if (this.activeRequests < this.maxPerSecond) {
      this.activeRequests++;
      return;
    }
    return new Promise((resolve) => {
      this.queue.push({ resolve });
    });
  }

  release(): void {
    this.activeRequests--;
    if (this.queue.length > 0) {
      const next = this.queue.shift()!;
      this.activeRequests++;
      setTimeout(() => next.resolve(), 1000 / this.maxPerSecond);
    }
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

export const rateLimiter = new NotionRateLimiter();
```

**Response cache (reduce API calls in production):**

Notion data that changes infrequently (database schemas, user lists, page metadata) should be cached to stay well under the rate limit.

```typescript
// src/cache.ts — TTL cache for Notion responses
interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

export class NotionCache {
  private store = new Map<string, CacheEntry<unknown>>();
  private readonly defaultTtlMs: number;

  constructor(defaultTtlSeconds = 60) {
    this.defaultTtlMs = defaultTtlSeconds * 1000;
  }

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry || Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set<T>(key: string, data: T, ttlSeconds?: number): void {
    const ttlMs = ttlSeconds ? ttlSeconds * 1000 : this.defaultTtlMs;
    this.store.set(key, { data, expiresAt: Date.now() + ttlMs });
  }

  invalidate(pattern: string): void {
    for (const key of this.store.keys()) {
      if (key.includes(pattern)) this.store.delete(key);
    }
  }
}

export const notionCache = new NotionCache(60); // 60-second default TTL
```

**Health check endpoint (include in every deployment):**

```typescript
// src/health.ts — verifies Notion API connectivity
import { getNotionClient } from './notion-client';
import { isNotionClientError } from '@notionhq/client';

export async function healthCheck(): Promise<{
  status: 'healthy' | 'degraded';
  notion: { connected: boolean; latencyMs: number; error?: string };
  timestamp: string;
}> {
  const timestamp = new Date().toISOString();
  const start = Date.now();

  try {
    const notion = getNotionClient();
    await notion.users.me({});
    return {
      status: 'healthy',
      notion: { connected: true, latencyMs: Date.now() - start },
      timestamp,
    };
  } catch (error) {
    const errorCode = isNotionClientError(error) ? error.code : 'unknown';
    return {
      status: 'degraded',
      notion: { connected: false, latencyMs: Date.now() - start, error: errorCode },
      timestamp,
    };
  }
}
```

### Step 2 — Deploy to Your Target Platform

Pick one platform and follow its deployment path. All three store `NOTION_TOKEN` as a secret that is injected at runtime, never committed to source.

**Option A: Vercel (serverless functions)**

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

**Option B: Railway (container-based, always-on)**

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

**Option C: Fly.io (edge containers)**

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

### Step 3 — Monitor Notion API Errors in Production

Set up structured error logging so you can track Notion-specific failures in your monitoring tool (Sentry, Datadog, or platform logs).

```typescript
// src/notion-error-handler.ts — structured error reporting
import { isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

interface NotionErrorReport {
  source: 'notion_api';
  code: string;
  status: number;
  message: string;
  retryable: boolean;
  action: string;
}

export function classifyNotionError(error: unknown): NotionErrorReport {
  if (!isNotionClientError(error)) {
    return {
      source: 'notion_api',
      code: 'unknown',
      status: 500,
      message: error instanceof Error ? error.message : String(error),
      retryable: false,
      action: 'investigate — non-Notion error in API path',
    };
  }

  const report: NotionErrorReport = {
    source: 'notion_api',
    code: error.code,
    status: error.status,
    message: error.message,
    retryable: false,
    action: '',
  };

  switch (error.code) {
    case APIErrorCode.RateLimited:
      report.retryable = true;
      report.action = 'back off — increase cache TTL or reduce polling frequency';
      break;
    case APIErrorCode.Unauthorized:
      report.retryable = false;
      report.action = 'rotate NOTION_TOKEN — token expired or was revoked';
      break;
    case APIErrorCode.ObjectNotFound:
      report.retryable = false;
      report.action = 'check integration permissions — page/database not shared with integration';
      break;
    case APIErrorCode.InternalServerError:
    case APIErrorCode.ServiceUnavailable:
      report.retryable = true;
      report.action = 'retry with exponential backoff — Notion is having issues';
      break;
    case APIErrorCode.ValidationError:
      report.retryable = false;
      report.action = 'fix request payload — check filter syntax and property names';
      break;
    default:
      report.action = 'check Notion API status page and SDK changelog';
  }

  return report;
}

export function logNotionError(error: unknown, context: Record<string, string> = {}): void {
  const report = classifyNotionError(error);
  console.error(JSON.stringify({ ...report, ...context, timestamp: new Date().toISOString() }));
}
```

Wire this into your API routes:

```typescript
} catch (error) {
  logNotionError(error, { route: '/api/notion/query', databaseId });
  // ... return error response
}
```

**Key metrics to monitor:**
- Rate limit hits (429 responses) per minute — alert if sustained above 5/min
- Health check latency — alert if Notion `latencyMs` exceeds 2000ms
- Auth failures (401/403) — alert immediately, means token rotation needed
- Cache hit ratio — should be > 70% in steady state; low ratio means wasted API calls

## Output

After completing these steps you will have:

- Node.js application deployed to Vercel, Railway, or Fly.io
- `NOTION_TOKEN` stored as an encrypted platform secret (never in source code)
- Notion client singleton that reuses connections across serverless invocations
- Rate limiter enforcing the 3 req/sec Notion API limit
- In-memory response cache reducing redundant API calls
- `/health` endpoint that verifies live Notion API connectivity
- Structured error logging classifying Notion API failures by severity

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `NOTION_TOKEN is not set` at runtime | Secret not configured for environment | Re-add secret: `vercel env add` / `railway variables set` / `fly secrets set` |
| Cold start timeout (> 10s) | Large dependency tree or slow Notion handshake | Set `min_machines_running: 1` (Fly.io) or use Railway always-on |
| 429 Rate Limited in logs | Exceeding 3 req/sec sustained | Increase cache TTL, batch queries, add request queuing |
| Health check returns `degraded` | Token expired or Notion outage | Check `status.notion.com`; rotate token if 401 |
| `ObjectNotFound` on database query | Database not shared with integration | Open Notion, click Share, add your integration |
| Serverless function creates multiple clients | Not using singleton pattern | Import `getNotionClient()` from shared module, not `new Client()` |

## Examples

### Minimal Express Server (deploy anywhere)

```typescript
import express from 'express';
import { getNotionClient } from './notion-client';
import { rateLimiter } from './rate-limiter';
import { healthCheck } from './health';
import { logNotionError } from './notion-error-handler';

const app = express();
app.use(express.json());

app.get('/health', async (_req, res) => {
  const result = await healthCheck();
  res.status(result.status === 'healthy' ? 200 : 503).json(result);
});

app.post('/api/query', async (req, res) => {
  const { databaseId, filter } = req.body;
  try {
    const notion = getNotionClient();
    const data = await rateLimiter.execute(() =>
      notion.databases.query({ database_id: databaseId, filter })
    );
    res.json({ results: data.results, hasMore: data.has_more });
  } catch (error) {
    logNotionError(error, { route: '/api/query' });
    res.status(500).json({ error: 'Query failed' });
  }
});

app.listen(Number(process.env.PORT) || 3000);
```

### Deploy Script (platform-agnostic)

```bash
#!/bin/bash
set -euo pipefail

PLATFORM="${1:?Usage: deploy.sh [vercel|railway|fly]}"

echo "Building..."
npm run build

case "$PLATFORM" in
  vercel)
    vercel env add NOTION_TOKEN production 2>/dev/null || true
    vercel --prod
    ;;
  railway)
    railway variables set NOTION_TOKEN="$NOTION_TOKEN"
    railway up
    ;;
  fly)
    fly secrets set NOTION_TOKEN="$NOTION_TOKEN"
    fly deploy
    ;;
  *)
    echo "Unknown platform: $PLATFORM" >&2
    exit 1
    ;;
esac

echo "Verifying health..."
sleep 5
curl -sf "$(echo "$PLATFORM" | xargs -I{} echo "https://my-notion-service.{}.dev/health")" || echo "Health check pending — verify manually"
```

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro) — official REST API docs
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) — official SDK with built-in retry
- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per integration
- [Notion API Status](https://status.notion.com) — check during outages
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables) — secret management
- [Railway Variables](https://docs.railway.app/reference/variables) — encrypted secrets
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/) — runtime secret injection

## Next Steps

- Add webhook receivers with `notion-webhooks-events` skill
- Set up database sync pipelines with `notion-sync-databases` skill
- Implement page content extraction with `notion-extract-content` skill
