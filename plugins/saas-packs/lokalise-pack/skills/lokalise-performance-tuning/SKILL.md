---
name: lokalise-performance-tuning
description: |
  Optimize Lokalise API performance with caching, pagination, and bulk operations.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Lokalise integrations.
  Trigger with phrases like "lokalise performance", "optimize lokalise",
  "lokalise latency", "lokalise caching", "lokalise slow", "lokalise batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Performance Tuning

## Overview
Optimize Lokalise API throughput and response times for translation pipeline integrations. Lokalise enforces a global rate limit of 6 requests per second across most endpoints, making request efficiency critical for projects with thousands of keys. Key bottlenecks include: key listing pagination (default page size is 100, max is 500), file download generation (async, can take seconds for large projects), and bulk key creation (500 keys per batch max).

## Prerequisites
- Lokalise SDK (`@lokalise/node-api`) or REST API access
- Understanding of project size (key count, language count)
- Cache layer (Redis or in-memory LRU)

## Instructions

### Step 1: Use Cursor Pagination with Maximum Page Size
```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Use cursor pagination (faster than offset for large datasets)
async function* getAllKeys(projectId: string) {
  let cursor: string | undefined;
  do {
    const result = await lok.keys().list({
      project_id: projectId,
      limit: 500,           // Maximum allowed
      pagination: 'cursor',
      cursor,
    });
    for (const key of result.items) yield key;
    cursor = result.hasNextCursor() ? result.nextCursor : undefined;
  } while (cursor);
}
// 10,000 keys: 20 API calls instead of 100 (at limit=500 vs default limit=100)
```

### Step 2: Cache Translation Downloads
```typescript
import { LRUCache } from 'lru-cache';

const downloadCache = new LRUCache<string, any>({ max: 100, ttl: 300_000 }); // 5 min

async function cachedDownload(projectId: string, format: string, langIso: string) {
  const key = `${projectId}:${format}:${langIso}`;
  const cached = downloadCache.get(key);
  if (cached) return cached;

  const bundle = await lok.files().download(projectId, {
    format, filter_langs: [langIso], original_filenames: false,
  });
  downloadCache.set(key, bundle);
  return bundle;
}
```

### Step 3: Batch Key Operations
```typescript
// Bulk create keys (up to 500 per request)
async function createKeysBatched(projectId: string, keys: any[]) {
  const BATCH_SIZE = 500;
  const results = [];
  for (let i = 0; i < keys.length; i += BATCH_SIZE) {
    const batch = keys.slice(i, i + BATCH_SIZE);
    const result = await lok.keys().create({ project_id: projectId, keys: batch });
    results.push(...result.items);
    await new Promise(r => setTimeout(r, 200)); // Respect rate limit
  }
  return results;
}
// 2,000 keys: 4 batched requests vs 2,000 individual requests
```

### Step 4: Implement Request Throttling
```typescript
import PQueue from 'p-queue';

// Lokalise rate limit: 6 requests/second
const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 5 });

async function throttledRequest<T>(fn: () => Promise<T>): Promise<T> {
  return queue.add(fn) as Promise<T>;
}

// All API calls go through the queue
const project = await throttledRequest(() => lok.projects().get(projectId));
```

### Step 5: Use Webhooks Instead of Polling
```bash
# Replace polling for translation status with webhooks
curl -X POST "https://api.lokalise.com/api2/projects/PROJECT_ID/webhooks" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  -d '{
    "url": "https://hooks.company.com/lokalise",
    "events": ["project.translation_completed", "project.exported"]
  }'
# Eliminates need to poll project status every N seconds
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded 6 req/s rate limit | Use PQueue throttling, retry with backoff |
| Slow file downloads | Large project with many languages | Filter by language, use async download + webhook |
| Pagination timeout | Offset pagination on 50K+ keys | Switch to cursor pagination |
| Bulk create fails partially | Network timeout on large batch | Reduce batch size to 200, add retry logic |

## Examples
```bash
# Benchmark: time a full key export
time curl -s "https://api.lokalise.com/api2/projects/PROJECT_ID/keys?limit=500" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" | jq '.keys | length'
# Compare with limit=100 to see pagination impact
```

```typescript
// Parallel download of all locales (respecting rate limit)
const locales = ['en', 'fr', 'de', 'ja', 'ko'];
const translations = await Promise.all(
  locales.map(lang => throttledRequest(() => cachedDownload(projectId, 'json', lang)))
);
```
