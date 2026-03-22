---
name: customerio-performance-tuning
description: |
  Optimize Customer.io API performance for high throughput.
  Use when improving response times, implementing connection
  pooling, batching, caching, or regional routing.
  Trigger: "customer.io performance", "optimize customer.io",
  "customer.io latency", "customer.io connection pooling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, performance, optimization]

---
# Customer.io Performance Tuning

## Overview

Optimize Customer.io API performance for high-volume integrations: HTTP connection pooling, identify deduplication caching, event batching with flush control, fire-and-forget async tracking, and regional routing.

## Prerequisites

- Working Customer.io integration
- Understanding of your traffic patterns and volume
- Monitoring to measure improvement (see `customerio-observability`)

## Performance Targets

| Operation | Baseline | Optimized | Technique |
|-----------|----------|-----------|-----------|
| Single identify | ~200ms | ~80ms | Connection pooling |
| Single track | ~200ms | ~80ms | Connection pooling |
| 100 events batch | ~20s serial | ~500ms | Parallel batching |
| Duplicate identify | ~200ms | ~0ms | Dedup cache |
| Non-critical track | Blocking | Non-blocking | Fire-and-forget |

## Instructions

### Step 1: HTTP Connection Pooling

```typescript
// lib/customerio-pooled.ts
import { TrackClient, RegionUS } from "customerio-node";
import https from "https";

// The customerio-node SDK creates new connections by default.
// Reuse connections with a keep-alive agent.
const agent = new https.Agent({
  keepAlive: true,
  maxSockets: 25,        // Max concurrent connections
  maxFreeSockets: 10,    // Keep idle connections open
  timeout: 30000,        // 30s socket timeout
  keepAliveMsecs: 15000, // TCP keep-alive probe interval
});

// Apply to the SDK by creating a singleton with the agent
// Note: customerio-node doesn't directly accept an agent,
// but we configure Node.js global agent for HTTPS
https.globalAgent = agent;

// Singleton client — one instance = one connection pool
const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

export { cio };
```

### Step 2: Identify Deduplication Cache

```typescript
// lib/customerio-dedup.ts
// Skip duplicate identify() calls within a time window

class LRUCache<K, V> {
  private map = new Map<K, V>();
  constructor(private maxSize: number) {}

  get(key: K): V | undefined {
    const val = this.map.get(key);
    if (val !== undefined) {
      // Move to end (most recent)
      this.map.delete(key);
      this.map.set(key, val);
    }
    return val;
  }

  set(key: K, val: V): void {
    this.map.delete(key);
    this.map.set(key, val);
    if (this.map.size > this.maxSize) {
      const oldest = this.map.keys().next().value;
      this.map.delete(oldest!);
    }
  }
}

import { createHash } from "crypto";
import { TrackClient, RegionUS } from "customerio-node";

const identifyCache = new LRUCache<string, number>(10_000);
const DEDUP_TTL_MS = 5 * 60 * 1000;  // 5 minutes

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

export async function dedupIdentify(
  userId: string,
  attrs: Record<string, any>
): Promise<void> {
  // Create a hash of userId + attributes
  const hash = createHash("sha256")
    .update(userId + JSON.stringify(attrs))
    .digest("hex")
    .substring(0, 16);

  const cached = identifyCache.get(hash);
  if (cached && Date.now() - cached < DEDUP_TTL_MS) {
    return; // Skip — identical identify() call within TTL window
  }

  await cio.identify(userId, attrs);
  identifyCache.set(hash, Date.now());
}
```

### Step 3: Batch Processor

```typescript
// lib/customerio-batch.ts
import { TrackClient, RegionUS } from "customerio-node";

interface BatchItem {
  type: "identify" | "track";
  userId: string;
  data: Record<string, any>;
}

export class CioBatchProcessor {
  private buffer: BatchItem[] = [];
  private timer: NodeJS.Timeout | null = null;
  private client: TrackClient;
  private processing = false;

  constructor(
    private readonly maxBatchSize = 100,
    private readonly flushIntervalMs = 3000,
    private readonly concurrency = 15
  ) {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_TRACK_API_KEY!,
      { region: RegionUS }
    );
    this.startFlushTimer();
  }

  add(item: BatchItem): void {
    this.buffer.push(item);
    if (this.buffer.length >= this.maxBatchSize) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.processing || this.buffer.length === 0) return;
    this.processing = true;

    const batch = this.buffer.splice(0, this.maxBatchSize);
    const startMs = Date.now();

    // Process in parallel chunks
    for (let i = 0; i < batch.length; i += this.concurrency) {
      const chunk = batch.slice(i, i + this.concurrency);
      const results = await Promise.allSettled(
        chunk.map((item) =>
          item.type === "identify"
            ? this.client.identify(item.userId, item.data)
            : this.client.track(item.userId, item.data)
        )
      );

      const failed = results.filter((r) => r.status === "rejected").length;
      if (failed > 0) {
        console.warn(`CIO batch: ${failed}/${chunk.length} failed`);
      }
    }

    const elapsed = Date.now() - startMs;
    console.log(`CIO batch: ${batch.length} items in ${elapsed}ms`);
    this.processing = false;
  }

  private startFlushTimer(): void {
    this.timer = setInterval(() => this.flush(), this.flushIntervalMs);
  }

  async shutdown(): Promise<void> {
    if (this.timer) clearInterval(this.timer);
    await this.flush();
  }
}
```

### Step 4: Fire-and-Forget Async Tracking

```typescript
// lib/customerio-async.ts
// For non-critical analytics events — don't block the request path

import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

export function fireAndForgetTrack(
  userId: string,
  eventName: string,
  data?: Record<string, any>
): void {
  // No await — returns immediately
  cio
    .track(userId, { name: eventName, data })
    .catch((err) => console.error(`CIO async track failed: ${err.message}`));
}

// Usage in Express route — does NOT slow down response
router.get("/dashboard", async (req, res) => {
  fireAndForgetTrack(req.user.id, "dashboard_viewed", {
    timestamp: Math.floor(Date.now() / 1000),
  });

  const data = await loadDashboardData(req.user.id);
  res.json(data);  // Returns immediately without waiting for CIO
});
```

### Step 5: Regional Routing

```typescript
// lib/customerio-region.ts
import { TrackClient, APIClient, RegionUS, RegionEU } from "customerio-node";

// Route to nearest Customer.io region based on configuration
// US accounts: track.customer.io / api.customer.io
// EU accounts: track-eu.customer.io / api-eu.customer.io

interface CioRegionalConfig {
  us: { siteId: string; trackKey: string; appKey: string };
  eu: { siteId: string; trackKey: string; appKey: string };
}

function getClientForUser(
  config: CioRegionalConfig,
  userRegion: "us" | "eu"
): { track: TrackClient; api: APIClient } {
  const creds = config[userRegion];
  const region = userRegion === "eu" ? RegionEU : RegionUS;

  return {
    track: new TrackClient(creds.siteId, creds.trackKey, { region }),
    api: new APIClient(creds.appKey, { region }),
  };
}
```

## Performance Monitoring

```typescript
// Wrap operations to measure latency
async function timedCioCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    const elapsed = Date.now() - start;
    console.log(`CIO ${operation}: ${elapsed}ms`);
    return result;
  } catch (err) {
    const elapsed = Date.now() - start;
    console.error(`CIO ${operation} FAILED: ${elapsed}ms`);
    throw err;
  }
}
```

## Error Handling

| Issue | Solution |
|-------|----------|
| High p99 latency | Enable connection pooling, check DNS resolution |
| Timeout errors | Increase timeout, reduce payload size |
| Memory growth | Cap LRU cache size, limit batch buffer |
| Dedup cache misses | Increase TTL if same identify calls are >5min apart |

## Resources

- [Track API Reference](https://docs.customer.io/integrations/api/track/)
- [About Customer.io APIs](https://docs.customer.io/integrations/api/customerio-apis/)
- [Account Regions](https://docs.customer.io/accounts-and-workspaces/data-centers/)

## Next Steps

After performance tuning, proceed to `customerio-cost-tuning` for cost optimization.
