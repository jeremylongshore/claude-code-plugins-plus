---
name: openevidence-performance-tuning
description: 'Performance Tuning for OpenEvidence.

  Trigger: "openevidence performance tuning".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Performance Tuning

## Overview

OpenEvidence's clinical API handles evidence query response times, citation batch retrieval, and complex multi-condition query optimization. Clinical evidence queries can take 2-5 seconds as the system searches across thousands of medical studies and synthesizes responses. Citation batch retrieval for systematic reviews generates heavy load when fetching 50-200 references per query. Caching evidence responses, batching citation fetches, and optimizing query specificity reduces clinician wait times by 50-70% and keeps complex queries within acceptable latency bounds.

## Caching Strategy
```typescript
const cache = new Map<string, { data: any; expiry: number }>();
const TTL = { evidence: 1_800_000, citations: 3_600_000, queries: 300_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
// Citations are stable (1hr). Evidence summaries update with new studies (30 min).
```

## Batch Operations
```typescript
async function fetchCitationsBatch(client: any, citationIds: string[], batchSize = 25) {
  const results = [];
  for (let i = 0; i < citationIds.length; i += batchSize) {
    const batch = citationIds.slice(i, i + batchSize);
    const res = await Promise.all(batch.map(id => client.getCitation(id)));
    results.push(...res);
    if (i + batchSize < citationIds.length) await new Promise(r => setTimeout(r, 500));
  }
  return results;
}
```

## Connection Pooling
```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 6, maxFreeSockets: 3, timeout: 30_000 });
// Moderate socket count — evidence queries are sequential, citations parallel
```

## Rate Limit Management
```typescript
async function withRateLimit(fn: () => Promise<any>): Promise<any> {
  try { return await fn(); }
  catch (err: any) {
    if (err.status === 429) {
      const retryMs = parseInt(err.headers?.['retry-after'] || '10') * 1000;
      await new Promise(r => setTimeout(r, retryMs));
      return fn();
    }
    throw err;
  }
}
```

## Monitoring
```typescript
const metrics = { queries: 0, citationFetches: 0, cacheHits: 0, avgLatencyMs: 0, errors: 0 };
function track(op: 'query' | 'citation', startMs: number, cached: boolean) {
  metrics[op === 'query' ? 'queries' : 'citationFetches']++;
  const lat = Date.now() - startMs;
  metrics.avgLatencyMs = (metrics.avgLatencyMs * (metrics.queries - 1) + lat) / metrics.queries;
  if (cached) metrics.cacheHits++;
}
```

## Performance Checklist
- [ ] Cache evidence responses with 30-min TTL (studies update periodically)
- [ ] Cache citation metadata with 1-hour TTL (stable once published)
- [ ] Batch citation retrieval in groups of 25 with 500ms pauses
- [ ] Use specific condition + intervention queries instead of broad searches
- [ ] Prefetch commonly queried drug interaction evidence
- [ ] Enable HTTP keep-alive for persistent API connections
- [ ] Monitor average query latency (target < 3s for simple queries)
- [ ] Set client timeout to 30s for complex multi-condition queries

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Slow evidence query (> 5s) | Broad multi-condition search | Narrow query to specific condition + intervention |
| 429 on citation batch | Too many parallel citation fetches | Batch to 25, add 500ms delay between groups |
| Stale evidence summary | Cache too long for rapidly evolving topic | Reduce TTL for high-churn topics (e.g., COVID) |
| Timeout on complex query | Multi-study synthesis exceeding limit | Increase timeout to 30s, simplify query scope |
| Missing citations | Study not yet indexed | Retry after 24h, check study publication date |

## Resources
- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence API Docs](https://www.openevidence.com/developers)

## Next Steps
See `openevidence-reference-architecture`.
