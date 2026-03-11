# Linear Cost Tuning - Implementation Details

## Usage Tracker

```typescript
// lib/usage-tracker.ts
interface UsageStats {
  requests: number;
  complexity: number;
  bytesTransferred: number;
  period: { start: Date; end: Date };
}

class UsageTracker {
  private stats: UsageStats = {
    requests: 0,
    complexity: 0,
    bytesTransferred: 0,
    period: { start: new Date(), end: new Date() },
  };

  recordRequest(complexity: number, bytes: number): void {
    this.stats.requests++;
    this.stats.complexity += complexity;
    this.stats.bytesTransferred += bytes;
    this.stats.period.end = new Date();
  }

  getDaily(): {
    avgRequestsPerHour: number;
    avgComplexityPerRequest: number;
    projectedMonthlyRequests: number;
  } {
    const hours =
      (this.stats.period.end.getTime() - this.stats.period.start.getTime()) /
      (1000 * 60 * 60);
    return {
      avgRequestsPerHour: this.stats.requests / Math.max(hours, 1),
      avgComplexityPerRequest: this.stats.complexity / Math.max(this.stats.requests, 1),
      projectedMonthlyRequests: (this.stats.requests / Math.max(hours, 1)) * 24 * 30,
    };
  }

  reset(): void {
    this.stats = {
      requests: 0, complexity: 0, bytesTransferred: 0,
      period: { start: new Date(), end: new Date() },
    };
  }
}

export const usageTracker = new UsageTracker();
```

## Conditional Fetching

```typescript
// lib/conditional-fetch.ts
interface ETagCache {
  data: any;
  etag: string;
  timestamp: Date;
}

const etagCache = new Map<string, ETagCache>();

async function fetchWithETag(key: string, fetcher: () => Promise<any>) {
  const cached = etagCache.get(key);
  if (cached && Date.now() - cached.timestamp.getTime() < 5 * 60 * 1000) {
    return cached.data;
  }

  const data = await fetcher();
  etagCache.set(key, {
    data,
    etag: JSON.stringify(data).slice(0, 50),
    timestamp: new Date(),
  });
  return data;
}
```

## Request Coalescing

```typescript
// lib/coalesce.ts
class RequestCoalescer {
  private pending = new Map<string, Promise<any>>();

  async execute<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const existing = this.pending.get(key);
    if (existing) return existing;

    const promise = fn().finally(() => {
      this.pending.delete(key);
    });

    this.pending.set(key, promise);
    return promise;
  }
}

const coalescer = new RequestCoalescer();

// Multiple simultaneous calls reuse the same request
const [teams1, teams2] = await Promise.all([
  coalescer.execute("teams", () => client.teams()),
  coalescer.execute("teams", () => client.teams()), // Reuses first
]);
```

## Webhook Event Filtering

```typescript
async function shouldProcessEvent(event: any): boolean {
  if (event.data?.actor?.isBot) return false;

  if (event.type === "Issue" && event.action === "update") {
    const importantFields = ["state", "priority", "assignee"];
    const changedFields = Object.keys(event.updatedFrom || {});
    if (!changedFields.some(f => importantFields.includes(f))) {
      return false;
    }
  }

  const allowedTeams = ["ENG", "PROD"];
  if (event.data?.team?.key && !allowedTeams.includes(event.data.team.key)) {
    return false;
  }

  return true;
}
```

## Lazy Loading Pattern

```typescript
// lib/lazy-client.ts
class LazyLinearClient {
  private client: LinearClient;
  private teamsCache: any[] | null = null;
  private statesCache = new Map<string, any[]>();

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  async getTeams() {
    if (!this.teamsCache) {
      const teams = await this.client.teams();
      this.teamsCache = teams.nodes;
    }
    return this.teamsCache;
  }

  async getStatesForTeam(teamKey: string) {
    if (!this.statesCache.has(teamKey)) {
      const teams = await this.client.teams({
        filter: { key: { eq: teamKey } },
      });
      const states = await teams.nodes[0].states();
      this.statesCache.set(teamKey, states.nodes);
    }
    return this.statesCache.get(teamKey)!;
  }

  invalidateTeams() {
    this.teamsCache = null;
    this.statesCache.clear();
  }
}
```

## Monitoring Dashboard Metrics

```typescript
const metrics = {
  totalRequests: counter("linear_requests_total"),
  requestDuration: histogram("linear_request_duration_seconds"),
  complexityCost: histogram("linear_complexity_cost"),
  cacheHits: counter("linear_cache_hits_total"),
  cacheMisses: counter("linear_cache_misses_total"),
  webhooksReceived: counter("linear_webhooks_received_total"),
  webhooksFiltered: counter("linear_webhooks_filtered_total"),
};
```
