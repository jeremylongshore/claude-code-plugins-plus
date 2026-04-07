---
name: juicebox-performance-tuning
description: |
  Optimize Juicebox performance.
  Trigger: "juicebox performance", "optimize juicebox".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Performance Tuning

## Overview

Juicebox's AI analysis API handles dataset uploads, analysis queue wait times, and result pagination. Large dataset uploads (100K+ rows) can block the analysis pipeline, while queue contention during peak hours increases wait times. Result sets from broad queries return thousands of profiles requiring efficient pagination. Caching search results, batching enrichment calls, and managing upload chunking reduces end-to-end analysis time by 40-60% and keeps interactive searches responsive.

## Caching Strategy
```typescript
const cache = new Map<string, { data: any; expiry: number }>();
const TTL = { search: 300_000, profile: 600_000, analysis: 900_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
// Analysis results are expensive — cache 15 min. Searches expire at 5 min.
```

## Batch Operations
```typescript
async function enrichBatch(client: any, profileIds: string[], batchSize = 50) {
  const results = [];
  for (let i = 0; i < profileIds.length; i += batchSize) {
    const batch = profileIds.slice(i, i + batchSize);
    const res = await client.enrichBatch({ profile_ids: batch, fields: ['skills_map', 'contact'] });
    results.push(...res.profiles);
    if (i + batchSize < profileIds.length) await new Promise(r => setTimeout(r, 300));
  }
  return results;
}
```

## Connection Pooling
```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 8, maxFreeSockets: 4, timeout: 60_000 });
// Longer timeout for dataset uploads and analysis queue responses
```

## Rate Limit Management
```typescript
async function withRateLimit(fn: () => Promise<any>): Promise<any> {
  try { return await fn(); }
  catch (err: any) {
    if (err.status === 429) {
      const backoff = parseInt(err.headers?.['retry-after'] || '10') * 1000;
      await new Promise(r => setTimeout(r, backoff));
      return fn();
    }
    throw err;
  }
}
```

## Monitoring
```typescript
const metrics = { searches: 0, enrichments: 0, cacheHits: 0, queueWaitMs: 0, errors: 0 };
function track(op: 'search' | 'enrich', startMs: number, cached: boolean) {
  metrics[op === 'search' ? 'searches' : 'enrichments']++;
  metrics.queueWaitMs += Date.now() - startMs;
  if (cached) metrics.cacheHits++;
}
```

## Performance Checklist
- [ ] Use specific filters (location, skills, title) to narrow search scope
- [ ] Cache search results with 5-min TTL to avoid redundant queries
- [ ] Batch profile enrichment in groups of 50 with 300ms delays
- [ ] Chunk large dataset uploads into 10K-row segments
- [ ] Cache analysis results for 15 min (expensive to recompute)
- [ ] Set 60s timeout for upload and analysis endpoints
- [ ] Monitor queue wait times and schedule uploads during off-peak
- [ ] Paginate results with limit=20 and cursor for interactive UIs

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Analysis queue timeout | Peak hour contention | Schedule large analyses off-peak, increase client timeout |
| 429 on bulk enrichment | Too many concurrent enrichment calls | Batch to 50 profiles with 300ms interval |
| Upload failure on large dataset | Payload exceeds limit or connection drop | Chunk into 10K-row segments, retry failed chunks |
| Slow broad search | Unfiltered query returning thousands of results | Add location/skills/title filters, set limit=20 |

## Resources
- [Juicebox API Docs](https://docs.juicebox.work/api)
- [Juicebox Performance Guide](https://docs.juicebox.work/performance)

## Next Steps
See `juicebox-reference-architecture`.
