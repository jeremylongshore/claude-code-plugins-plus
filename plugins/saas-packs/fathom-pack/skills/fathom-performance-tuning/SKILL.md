---
name: fathom-performance-tuning
description: 'Optimize Fathom API performance with caching and batch processing.

  Trigger with phrases like "fathom performance", "fathom caching", "optimize fathom".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Performance Tuning

## Overview

Fathom's meeting intelligence API serves transcript downloads, bulk meeting sync, and action item aggregation. Transcript payloads are large (50-500KB each), making bulk sync of historical meetings a major latency bottleneck. The 60 req/min rate limit requires careful batching. Caching immutable transcripts aggressively while keeping action item data fresh reduces download latency by 70% and prevents rate limit errors during bulk operations.

## Caching Strategy
```typescript
const cache = new Map<string, { data: any; expiry: number }>();
const TTL = { transcript: 3_600_000, actionItems: 120_000, meetings: 300_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
// Transcripts are immutable — cache 1hr. Action items change — cache 2min.
```

## Batch Operations
```typescript
async function syncMeetingsBatch(client: any, ids: string[], batchSize = 50) {
  const results = [];
  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize);
    const res = await Promise.all(batch.map(id => client.getTranscript(id)));
    results.push(...res);
    if (i + batchSize < ids.length) await new Promise(r => setTimeout(r, 61_000)); // 60 req/min
  }
  return results;
}
```

## Connection Pooling
```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 6, maxFreeSockets: 3, timeout: 45_000 });
// Transcript downloads are large — longer timeout, fewer concurrent sockets
```

## Rate Limit Management
```typescript
async function withFathomRateLimit(fn: () => Promise<any>): Promise<any> {
  try { return await fn(); }
  catch (err: any) {
    if (err.status === 429) {
      const retryAfter = parseInt(err.headers?.['retry-after'] || '60') * 1000;
      await new Promise(r => setTimeout(r, retryAfter));
      return fn();
    }
    throw err;
  }
}
```

## Monitoring
```typescript
const metrics = { downloads: 0, cacheHits: 0, rateLimits: 0, avgLatencyMs: 0 };
function trackDownload(startMs: number, cached: boolean, rateLimited: boolean) {
  metrics.downloads++;
  metrics.avgLatencyMs = (metrics.avgLatencyMs * (metrics.downloads - 1) + (Date.now() - startMs)) / metrics.downloads;
  if (cached) metrics.cacheHits++; if (rateLimited) metrics.rateLimits++;
}
```

## Performance Checklist
- [ ] Cache transcripts with 1-hour TTL (immutable after generation)
- [ ] Use webhooks instead of polling for new meeting notifications
- [ ] Batch transcript downloads in groups of 50 with 60s pauses
- [ ] Set action item cache TTL to 2 min for freshness
- [ ] Enable HTTP keep-alive with 45s timeout for large payloads
- [ ] Track rate limit hits and back off with Retry-After header
- [ ] Parallelize independent meeting metadata and transcript fetches
- [ ] Aggregate action items client-side to reduce API round-trips

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Rate Limited | Exceeded 60 req/min | Parse Retry-After, batch with 61s delay between groups |
| Transcript timeout | Large payload on slow connection | Increase timeout to 45s, enable keep-alive |
| Stale action items | Cache TTL too aggressive | Reduce action item TTL to 2 min |
| Missing transcript | Meeting still processing | Check meeting status before download, retry after 30s |
| Partial sync failure | Network interruption mid-batch | Track progress, resume from last successful ID |

## Resources
- [Fathom API Docs](https://fathom.video/developers)

## Next Steps
See `fathom-reference-architecture`.
