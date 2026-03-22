---
name: flexport-performance-tuning
description: |
  Optimize Flexport API performance with pagination tuning, response caching,
  parallel requests, and connection pooling for logistics data.
  Trigger: "flexport performance", "flexport slow API", "flexport caching", "optimize flexport".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Performance Tuning

## Overview

Optimize Flexport API integration performance. The API is rate-limited and serves logistics data that changes infrequently (shipments update hourly, products rarely). Cache aggressively for reads, batch writes, and use maximum page sizes.

## Instructions

### Step 1: Maximize Page Size

```typescript
// Default per=25. Use per=100 (max) to reduce API calls by 4x
async function fetchAllShipments(): Promise<Shipment[]> {
  const all: Shipment[] = [];
  let page = 1;
  while (true) {
    const res = await flexport(`/shipments?per=100&page=${page}`);
    all.push(...res.data.records);
    if (res.data.records.length < 100) break;
    page++;
  }
  return all;
  // 1000 shipments = 10 API calls instead of 40
}
```

### Step 2: Cache Responses

```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000,  // 5 min for shipment data
});

// Products change rarely — cache longer
const productCache = new LRUCache<string, any>({
  max: 1000,
  ttl: 60 * 60 * 1000,  // 1 hour
});

async function cachedFlexport(path: string, ttlCache = cache): Promise<any> {
  const cached = ttlCache.get(path);
  if (cached) return cached;
  const data = await flexport(path);
  ttlCache.set(path, data);
  return data;
}
```

### Step 3: Parallel Requests with Concurrency Control

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 10 });

// Fetch details for multiple shipments in parallel
async function enrichShipments(ids: string[]) {
  return Promise.all(
    ids.map(id => queue.add(() => flexport(`/shipments/${id}`)))
  );
}
```

### Step 4: Webhook-Driven Cache Invalidation

```typescript
// Instead of polling, invalidate cache on webhook events
async function handleWebhook(event: any) {
  if (event.type.startsWith('shipment.')) {
    cache.delete(`/shipments/${event.data.shipment_id}`);
    cache.delete('/shipments');  // Invalidate list cache
  }
  if (event.type.startsWith('product.')) {
    productCache.delete(`/products/${event.data.product_id}`);
  }
}
```

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Shipment list load | < 500ms | Cache with 5min TTL |
| Product lookup | < 100ms | Cache with 1hr TTL |
| Bulk shipment fetch | < 3s for 100 | Parallel with p-queue |
| Dashboard refresh | < 2s | Stale-while-revalidate |

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [lru-cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `flexport-cost-tuning`.
