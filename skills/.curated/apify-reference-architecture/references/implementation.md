# Apify Integration — Implementation Reference

Service-layer, configuration, and health-check building blocks for the full-stack
integration pattern (Pattern 3 in [architecture-patterns.md](architecture-patterns.md)).
These isolate every Apify call behind a typed boundary so the rest of the application
never touches `apify-client` directly.

## Service Layer

A single `ApifyService` class wraps `apify-client` and exposes intent-level methods
(`startScrape`, `getRunStatus`, `getResults`, `checkHealth`). Dependency-inject the
token so the class stays testable and environment-agnostic.

```typescript
// src/services/apify-service.ts
import { ApifyClient } from 'apify-client';

export class ApifyService {
  private client: ApifyClient;

  constructor(token: string) {
    this.client = new ApifyClient({ token });
  }

  async startScrape(urls: string[]): Promise<{ runId: string }> {
    const run = await this.client.actor('username/scraper').start({
      startUrls: urls.map(url => ({ url })),
    });
    return { runId: run.id };
  }

  async getRunStatus(runId: string): Promise<{
    status: string;
    progress?: { finished: number; failed: number };
  }> {
    const run = await this.client.run(runId).get();
    return {
      status: run.status,
      progress: {
        finished: run.stats?.requestsFinished ?? 0,
        failed: run.stats?.requestsFailed ?? 0,
      },
    };
  }

  async getResults<T>(runId: string): Promise<T[]> {
    const run = await this.client.run(runId).get();
    if (run.status !== 'SUCCEEDED') {
      throw new Error(`Run not ready: ${run.status}`);
    }
    const { items } = await this.client
      .dataset(run.defaultDatasetId)
      .listItems();
    return items as T[];
  }

  async checkHealth(): Promise<boolean> {
    try {
      const user = await this.client.user().get();
      return !!user.username;
    } catch {
      return false;
    }
  }
}
```

## Configuration Management

Load configuration once at startup, validate that required env vars are present, and
layer per-environment overrides on top of a single base object. Fail fast here rather
than deep inside a request handler.

```typescript
// src/config/apify.ts
interface ApifyConfig {
  token: string;
  actorId: string;
  defaultMemory: number;
  defaultTimeout: number;
  webhookUrl?: string;
}

export function loadConfig(): ApifyConfig {
  const env = process.env.NODE_ENV || 'development';

  const base: ApifyConfig = {
    token: process.env.APIFY_TOKEN!,
    actorId: process.env.APIFY_ACTOR_ID!,
    defaultMemory: 1024,
    defaultTimeout: 3600,
  };

  const overrides: Record<string, Partial<ApifyConfig>> = {
    development: { defaultMemory: 256, defaultTimeout: 300 },
    staging: { defaultMemory: 512 },
    production: { webhookUrl: process.env.APIFY_WEBHOOK_URL },
  };

  return { ...base, ...overrides[env] };
}
```

## Health Check

Expose Apify reachability as a first-class health signal so orchestrators and dashboards
can detect a bad token or platform outage before a user-facing scrape fails.

```typescript
// src/health.ts
export async function healthCheck(apifyService: ApifyService) {
  const start = Date.now();
  const healthy = await apifyService.checkHealth();

  return {
    service: 'apify',
    status: healthy ? 'healthy' : 'unhealthy',
    latencyMs: Date.now() - start,
    timestamp: new Date().toISOString(),
  };
}
```
