---
name: glean-performance-tuning
description: 'Optimize Glean search relevance and indexing throughput with batch sizing,

  datasource configuration, and content quality improvements.

  Trigger: "glean performance", "glean search quality", "glean indexing speed".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Performance Tuning

## Overview

Glean's enterprise search API handles search queries across multiple connectors, bulk document indexing, and connector sync throughput. Search latency compounds when querying across dozens of datasources simultaneously. Large indexing jobs (10K+ documents) require careful batching to avoid rate limits and maintain connector sync schedules. Optimizing batch sizes, caching frequent search results, and tuning connector configurations reduces search P95 latency and keeps indexing pipelines within SLA windows.

## Caching Strategy
```typescript
const cache = new Map<string, { data: any; expiry: number }>();
const TTL = { search: 60_000, suggestions: 30_000, datasources: 600_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
// Search results expire fast (1 min). Datasource metadata is stable (10 min).
```

## Batch Operations
```typescript
import PQueue from 'p-queue';
const BATCH_SIZE = 100;

async function indexDocsBatched(glean: any, dsName: string, docs: any[]) {
  const batches = [];
  for (let i = 0; i < docs.length; i += BATCH_SIZE) batches.push(docs.slice(i, i + BATCH_SIZE));
  const queue = new PQueue({ concurrency: 3, interval: 500 });
  await Promise.all(batches.map(batch =>
    queue.add(() => glean.indexDocuments(dsName, batch))
  ));
}
```

## Connection Pooling
```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 15, maxFreeSockets: 5, timeout: 30_000 });
// High socket count for parallel indexing across multiple datasources
```

## Rate Limit Management
```typescript
async function withGleanRateLimit(fn: () => Promise<any>): Promise<any> {
  try { return await fn(); }
  catch (err: any) {
    if (err.status === 429) {
      const retryMs = parseInt(err.headers?.['retry-after'] || '5') * 1000;
      await new Promise(r => setTimeout(r, retryMs));
      return fn();
    }
    throw err;
  }
}
```

## Monitoring
```typescript
const metrics = { searches: 0, indexOps: 0, cacheHits: 0, p95LatencyMs: 0, errors: 0 };
const latencies: number[] = [];
function trackSearch(startMs: number, cached: boolean) {
  const lat = Date.now() - startMs; latencies.push(lat); metrics.searches++;
  if (cached) metrics.cacheHits++;
  latencies.sort((a, b) => a - b);
  metrics.p95LatencyMs = latencies[Math.floor(latencies.length * 0.95)] || 0;
}
```

## Performance Checklist
- [ ] Batch indexing calls at 100 docs per request with 3 concurrent workers
- [ ] Use incremental indexing for real-time updates (< 100 docs)
- [ ] Switch to bulkindexdocuments for daily full refreshes (> 1K docs)
- [ ] Cache repeated search queries with 1-min TTL
- [ ] Set descriptive document titles and full body text for relevance
- [ ] Keep connector sync schedules staggered to avoid burst load
- [ ] Monitor P95 search latency and indexing throughput
- [ ] Enable keep-alive connections with high socket count for parallel ops

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Slow cross-datasource search | Too many connectors queried in parallel | Prioritize datasources, set query scope |
| 429 on bulk indexing | Batch size or concurrency too high | Reduce to 100/batch, 3 concurrent, 500ms interval |
| Stale search results | Index lag after document updates | Use incremental indexing with webhooks on change |
| Connector sync timeout | Large datasource with no checkpointing | Enable incremental sync with cursor tracking |
| Missing documents in results | Incomplete metadata during indexing | Include title, body, author, and updated_at fields |

## Resources
- [Glean Developer Portal](https://developers.glean.com/)
- [Glean Indexing API Guide](https://developers.glean.com/docs/indexing)

## Next Steps
See `glean-reference-architecture`.
