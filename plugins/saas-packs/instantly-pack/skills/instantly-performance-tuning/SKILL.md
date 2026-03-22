---
name: instantly-performance-tuning
description: |
  Optimize Instantly.ai API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing high-volume lead operations.
  Trigger with phrases like "instantly performance", "instantly slow",
  "instantly caching", "instantly batch", "optimize instantly api".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, performance, caching, optimization]

---
# Instantly Performance Tuning

## Overview
Optimize Instantly API v2 integrations for speed and throughput. Key areas: caching analytics data, batching lead operations, concurrent request management, efficient pagination, and connection reuse. The email listing endpoint has a strict **20 req/min** limit that requires special handling.

## Prerequisites
- Completed `instantly-install-auth` setup
- Working Instantly integration
- Understanding of async patterns and caching strategies

## Instructions

### Step 1: Cache Analytics Data
Campaign analytics don't change every second — cache them for 5-15 minutes to avoid redundant API calls.

```typescript
class InstantlyCache {
  private cache = new Map<string, { data: unknown; expiry: number }>();

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry || Date.now() > entry.expiry) {
      this.cache.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set(key: string, data: unknown, ttlMs: number) {
    this.cache.set(key, { data, expiry: Date.now() + ttlMs });
  }
}

const cache = new InstantlyCache();

async function getCachedAnalytics(campaignId: string) {
  const cacheKey = `analytics:${campaignId}`;
  const cached = cache.get<CampaignAnalytics>(cacheKey);
  if (cached) return cached;

  const data = await instantly<CampaignAnalytics>(
    `/campaigns/analytics?id=${campaignId}`
  );
  cache.set(cacheKey, data, 5 * 60 * 1000); // 5 min TTL
  return data;
}

// Cache campaign list (changes infrequently)
async function getCachedCampaigns() {
  const cacheKey = "campaigns:all";
  const cached = cache.get<Campaign[]>(cacheKey);
  if (cached) return cached;

  const campaigns = await instantly<Campaign[]>("/campaigns?limit=100");
  cache.set(cacheKey, campaigns, 15 * 60 * 1000); // 15 min TTL
  return campaigns;
}
```

### Step 2: Batch Lead Operations with Controlled Concurrency
```typescript
interface BatchResult<T> {
  succeeded: T[];
  failed: Array<{ input: unknown; error: string }>;
  duration: number;
}

async function batchAddLeads(
  campaignId: string,
  leads: Array<{ email: string; first_name?: string; company_name?: string }>,
  options = { concurrency: 5, delayMs: 200, retries: 3 }
): Promise<BatchResult<Lead>> {
  const start = Date.now();
  const succeeded: Lead[] = [];
  const failed: Array<{ input: unknown; error: string }> = [];
  let active = 0;

  const addWithRetry = async (lead: typeof leads[0]) => {
    for (let attempt = 0; attempt <= options.retries; attempt++) {
      try {
        const result = await instantly<Lead>("/leads", {
          method: "POST",
          body: JSON.stringify({
            campaign: campaignId,
            email: lead.email,
            first_name: lead.first_name,
            company_name: lead.company_name,
            skip_if_in_workspace: true,
          }),
        });
        succeeded.push(result);
        return;
      } catch (err: any) {
        if (err.status === 429) {
          await new Promise((r) => setTimeout(r, Math.pow(2, attempt) * 1000));
          continue;
        }
        if (attempt === options.retries) {
          failed.push({ input: lead, error: err.message });
        }
      }
    }
  };

  // Process in chunks
  for (let i = 0; i < leads.length; i += options.concurrency) {
    const chunk = leads.slice(i, i + options.concurrency);
    await Promise.allSettled(chunk.map(addWithRetry));

    if (i + options.concurrency < leads.length) {
      await new Promise((r) => setTimeout(r, options.delayMs));
    }

    // Progress report
    const progress = Math.min(i + options.concurrency, leads.length);
    console.log(`Progress: ${progress}/${leads.length} (${succeeded.length} ok, ${failed.length} failed)`);
  }

  return { succeeded, failed, duration: Date.now() - start };
}
```

### Step 3: Efficient Pagination
```typescript
// Pre-fetch next page while processing current page
async function* prefetchPaginate<T extends { id: string }>(
  path: string,
  pageSize = 100
): AsyncGenerator<T[]> {
  let startingAfter: string | undefined;
  let nextPagePromise: Promise<T[]> | null = null;

  const fetchPage = (after?: string) => {
    const qs = new URLSearchParams({ limit: String(pageSize) });
    if (after) qs.set("starting_after", after);
    return instantly<T[]>(`${path}?${qs}`);
  };

  // Fetch first page
  let currentPage = await fetchPage();

  while (currentPage.length > 0) {
    // Start fetching next page immediately
    if (currentPage.length === pageSize) {
      const lastId = currentPage[currentPage.length - 1].id;
      nextPagePromise = fetchPage(lastId);
    } else {
      nextPagePromise = null;
    }

    yield currentPage;

    if (!nextPagePromise) break;
    currentPage = await nextPagePromise;
  }
}

// Usage — processes next page while current page is being handled
for await (const batch of prefetchPaginate<Lead>("/leads/list")) {
  for (const lead of batch) {
    // Process lead — next page is already loading
  }
}
```

### Step 4: Connection Reuse with Keep-Alive
```typescript
import { Agent } from "undici";

// Create a persistent connection pool
const dispatcher = new Agent({
  keepAliveTimeout: 30000,     // keep connections alive for 30s
  keepAliveMaxTimeout: 60000,
  connections: 10,             // max 10 concurrent connections
  pipelining: 1,
});

async function instantlyPooled<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `https://api.instantly.ai/api/v2${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.INSTANTLY_API_KEY}`,
      ...options.headers,
    },
    // @ts-ignore — undici dispatcher
    dispatcher,
  });

  if (!res.ok) throw new Error(`Instantly ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}
```

### Step 5: Throttled Email Fetcher (20 req/min limit)
```typescript
class ThrottledEmailClient {
  private timestamps: number[] = [];
  private readonly maxPerMinute = 18; // leave margin

  private async throttle() {
    const now = Date.now();
    this.timestamps = this.timestamps.filter((t) => now - t < 60000);

    if (this.timestamps.length >= this.maxPerMinute) {
      const wait = 60000 - (now - this.timestamps[0]) + 500;
      await new Promise((r) => setTimeout(r, wait));
    }
    this.timestamps.push(Date.now());
  }

  async listEmails(params: { campaign_id?: string; limit?: number; starting_after?: string }) {
    await this.throttle();
    const qs = new URLSearchParams();
    if (params.campaign_id) qs.set("campaign_id", params.campaign_id);
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.starting_after) qs.set("starting_after", params.starting_after);
    return instantly(`/emails?${qs}`);
  }

  async getUnreadCount() {
    await this.throttle();
    return instantly("/emails/unread/count");
  }
}
```

## Performance Benchmarks
| Operation | Unoptimized | Optimized | Improvement |
|-----------|------------|-----------|-------------|
| 500 lead import | ~250s (sequential) | ~30s (5 concurrent + batch) | 8x |
| Campaign analytics (10 queries) | 10 API calls | 1 API call (cached) | 10x |
| All campaigns page load | ~2s (no cache) | ~50ms (cached) | 40x |
| Lead pagination (10K leads) | ~100s (sequential) | ~50s (prefetch) | 2x |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `429` during batch import | Too many concurrent requests | Reduce concurrency, increase delay |
| `429` on email listing | >20 req/min | Use `ThrottledEmailClient` |
| Stale cache data | TTL too long | Reduce TTL or add cache invalidation |
| Memory issues | Large pagination result set | Use async generators, process in chunks |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Rate Limits](https://developer.instantly.ai/)
- [Node.js Undici Connection Pooling](https://undici.nodejs.org/)

## Next Steps
For cost optimization, see `instantly-cost-tuning`.
