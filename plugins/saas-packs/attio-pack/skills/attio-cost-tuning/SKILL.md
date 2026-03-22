---
name: attio-cost-tuning
description: |
  Optimize Attio API usage costs -- reduce request volume, select the
  right plan, monitor usage, and implement budget alerts.
  Trigger: "attio cost", "attio billing", "reduce attio costs",
  "attio pricing", "attio expensive", "attio budget", "attio usage".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Cost Tuning

## Overview

Attio pricing is based on workspace seats, not API calls. However, API rate limits effectively cap throughput, so optimizing request volume improves both performance and cost efficiency. This skill covers practical strategies to reduce unnecessary API calls.

## Attio Pricing Model

| Plan | Price | Key Limits |
|------|-------|-----------|
| Free | $0/user/mo | 3 users, basic objects, limited automations |
| Plus | $29/user/mo | Unlimited objects, lists, advanced reporting |
| Pro | $59/user/mo | Advanced automations, API access, webhooks |
| Enterprise | Custom | SSO, audit logs, dedicated support, custom rate limits |

**API access requires Plus plan or higher.** Rate limits are per-workspace, not per-seat.

## Instructions

### Step 1: Audit Current API Usage

```typescript
// Instrument all API calls to measure usage patterns
class AttioUsageTracker {
  private calls: Array<{
    method: string;
    path: string;
    timestamp: number;
    durationMs: number;
    cached: boolean;
  }> = [];

  async track<T>(
    method: string,
    path: string,
    operation: () => Promise<T>,
    cached = false
  ): Promise<T> {
    const start = Date.now();
    try {
      const result = await operation();
      this.calls.push({
        method, path, timestamp: start,
        durationMs: Date.now() - start, cached,
      });
      return result;
    } catch (err) {
      this.calls.push({
        method, path, timestamp: start,
        durationMs: Date.now() - start, cached: false,
      });
      throw err;
    }
  }

  report(windowMs = 3600_000): {
    totalCalls: number;
    cachedCalls: number;
    topEndpoints: Array<{ path: string; count: number }>;
  } {
    const cutoff = Date.now() - windowMs;
    const recent = this.calls.filter((c) => c.timestamp > cutoff);
    const cached = recent.filter((c) => c.cached).length;

    const endpointCounts = new Map<string, number>();
    for (const call of recent) {
      const key = `${call.method} ${call.path}`;
      endpointCounts.set(key, (endpointCounts.get(key) || 0) + 1);
    }

    const topEndpoints = [...endpointCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([path, count]) => ({ path, count }));

    return { totalCalls: recent.length, cachedCalls: cached, topEndpoints };
  }
}
```

### Step 2: Reduce Request Volume

**The five biggest cost/rate-limit savers:**

| Strategy | Reduction | Implementation |
|----------|-----------|---------------|
| Cache object schemas | 50-90% of schema reads | Cache `GET /objects` and `/attributes` for 30 min |
| Batch with `$in` filter | N:1 on lookups | Single query instead of N individual fetches |
| Use `limit: 500` | 5x fewer pagination requests | Max page size per request |
| Webhook-driven sync | Eliminate polling | React to changes instead of polling every N seconds |
| Cache records | 30-80% of record reads | LRU cache with webhook invalidation |

### Step 3: Eliminate Polling with Webhooks

```typescript
// BAD: Polling every 30 seconds for changes
setInterval(async () => {
  const records = await client.post("/objects/people/records/query", {
    filter: { updated_at: { $gt: lastCheck.toISOString() } },
    limit: 500,
  });
  for (const record of records.data) await processUpdate(record);
  lastCheck = new Date();
}, 30_000);
// Cost: 2,880 requests/day MINIMUM (even with no changes)

// GOOD: Webhook-driven (0 requests when no changes)
app.post("/webhooks/attio", async (req, res) => {
  res.status(200).json({ received: true });
  const event = req.body;
  if (event.event_type === "record.updated") {
    const record = await client.get(
      `/objects/${event.object.api_slug}/records/${event.record.id.record_id}`
    );
    await processUpdate(record);
  }
});
// Cost: 1 request per actual change
```

### Step 4: Smart Caching Tiers

```typescript
import { LRUCache } from "lru-cache";

// Tier 1: Schema data (changes very rarely)
const schemaCache = new LRUCache<string, unknown>({
  max: 100,
  ttl: 30 * 60 * 1000, // 30 minutes
});

// Tier 2: Record data (changes occasionally)
const recordCache = new LRUCache<string, unknown>({
  max: 5000,
  ttl: 5 * 60 * 1000, // 5 minutes
});

// Tier 3: List/query results (changes frequently)
const queryCache = new LRUCache<string, unknown>({
  max: 200,
  ttl: 30 * 1000, // 30 seconds
});

function getCacheForPath(path: string): LRUCache<string, unknown> {
  if (path.includes("/attributes") || path === "/objects") return schemaCache;
  if (path.includes("/records/") && !path.includes("/query")) return recordCache;
  return queryCache;
}
```

### Step 5: Request Budget Monitor

```typescript
class AttioRequestBudget {
  private requestsToday = 0;
  private dayStart = this.todayStart();
  private readonly dailyBudget: number;
  private readonly warningThreshold: number;

  constructor(dailyBudget = 10_000) {
    this.dailyBudget = dailyBudget;
    this.warningThreshold = dailyBudget * 0.8;
  }

  private todayStart(): number {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.getTime();
  }

  recordRequest(): void {
    const today = this.todayStart();
    if (today !== this.dayStart) {
      this.dayStart = today;
      this.requestsToday = 0;
    }
    this.requestsToday++;

    if (this.requestsToday === Math.floor(this.warningThreshold)) {
      console.warn(`Attio budget warning: ${this.requestsToday}/${this.dailyBudget} requests today`);
    }

    if (this.requestsToday >= this.dailyBudget) {
      console.error(`Attio daily budget exceeded: ${this.requestsToday} requests`);
    }
  }

  getUsage(): { today: number; budget: number; percentUsed: number } {
    return {
      today: this.requestsToday,
      budget: this.dailyBudget,
      percentUsed: Math.round((this.requestsToday / this.dailyBudget) * 100),
    };
  }
}
```

### Step 6: SQL Usage Dashboard

If you log API calls to a database:

```sql
-- Daily request volume (last 30 days)
SELECT
  DATE(timestamp) AS day,
  COUNT(*) AS total_requests,
  COUNT(CASE WHEN cached THEN 1 END) AS cache_hits,
  ROUND(COUNT(CASE WHEN cached THEN 1 END) * 100.0 / COUNT(*), 1) AS cache_hit_pct,
  ROUND(AVG(duration_ms), 0) AS avg_latency_ms
FROM attio_api_log
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY day DESC;

-- Top endpoints by volume (identify optimization targets)
SELECT
  method || ' ' || path AS endpoint,
  COUNT(*) AS calls,
  ROUND(AVG(duration_ms), 0) AS avg_ms,
  COUNT(CASE WHEN status = 429 THEN 1 END) AS rate_limited
FROM attio_api_log
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY method, path
ORDER BY calls DESC
LIMIT 10;
```

## Cost Optimization Checklist

```
[ ] Object schema calls cached (30-minute TTL)
[ ] Record lookups cached (5-minute TTL with webhook invalidation)
[ ] Polling replaced with webhooks where possible
[ ] Bulk operations use $in filter (1 request instead of N)
[ ] Pagination uses limit: 500 (max page size)
[ ] Unnecessary API calls identified and eliminated
[ ] Usage monitoring in place with daily budget alerts
[ ] Cache hit rate > 50% on read-heavy workloads
```

## Error Handling

| Cost issue | Root cause | Fix |
|-----------|-----------|-----|
| High request volume | Polling loop | Switch to webhooks |
| Low cache hit rate | Short TTL or no cache | Increase TTL, add webhook invalidation |
| Rate limiting (429s) | Burst without throttling | Add PQueue with intervalCap |
| N+1 queries | Individual record fetches | Batch with `$in` filter |

## Resources

- [Attio Pricing](https://attio.com/pricing)
- [Attio Rate Limiting](https://docs.attio.com/rest-api/guides/rate-limiting)
- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)

## Next Steps

For architecture patterns, see `attio-reference-architecture`.
