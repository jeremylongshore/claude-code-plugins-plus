---
name: figma-performance-tuning
description: |
  Optimize Figma REST API performance with caching, partial fetches, and connection reuse.
  Use when experiencing slow API responses, reducing bandwidth for large files,
  or optimizing request throughput for Figma integrations.
  Trigger with phrases like "figma performance", "figma slow",
  "figma caching", "figma optimize", "figma large file".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Performance Tuning

## Overview
Optimize Figma REST API performance. Large Figma files can return multi-megabyte JSON responses. Key strategies: fetch only what you need, cache aggressively, and batch requests.

## Prerequisites
- Working Figma API integration
- Understanding of your access patterns (which endpoints, how often)

## Instructions

### Step 1: Reduce Payload Size
```typescript
// BAD: fetches the entire file tree (can be 10+ MB for large files)
const file = await fetch(`https://api.figma.com/v1/files/${fileKey}`, {
  headers: { 'X-Figma-Token': token },
}).then(r => r.json());

// GOOD: use depth parameter to limit tree depth
// depth=1 returns only pages (CANVAS nodes), not their children
const fileMeta = await fetch(
  `https://api.figma.com/v1/files/${fileKey}?depth=1`,
  { headers: { 'X-Figma-Token': token } }
).then(r => r.json());

// GOOD: fetch only specific nodes you need
const nodes = await fetch(
  `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${nodeIds.join(',')}`,
  { headers: { 'X-Figma-Token': token } }
).then(r => r.json());

// GOOD: use plugin_data or branch_data params only when needed
// By default, plugin data and branch data are NOT returned
```

### Step 2: Response Caching
```typescript
import { LRUCache } from 'lru-cache';

// File metadata changes rarely -- cache for 5 minutes
const fileCache = new LRUCache<string, any>({
  max: 100,
  ttl: 5 * 60 * 1000, // 5 minutes
});

async function getCachedFile(fileKey: string, token: string) {
  const cached = fileCache.get(fileKey);
  if (cached) return cached;

  const file = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  fileCache.set(fileKey, file);
  return file;
}

// Image URLs expire after 30 days -- cache them but with a shorter TTL
const imageUrlCache = new LRUCache<string, string>({
  max: 1000,
  ttl: 24 * 60 * 60 * 1000, // 1 day (well within 30-day expiry)
});

async function getCachedImageUrl(
  fileKey: string, nodeId: string, format: string, token: string
): Promise<string | null> {
  const cacheKey = `${fileKey}:${nodeId}:${format}`;
  const cached = imageUrlCache.get(cacheKey);
  if (cached) return cached;

  const data = await fetch(
    `https://api.figma.com/v1/images/${fileKey}?ids=${nodeId}&format=${format}`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  const url = data.images[nodeId];
  if (url) imageUrlCache.set(cacheKey, url);
  return url;
}
```

### Step 3: Webhook-Driven Cache Invalidation
```typescript
// Instead of polling, use webhooks to know when to re-fetch
// See figma-webhooks-events for full webhook setup

async function handleFileUpdate(fileKey: string) {
  // Invalidate cached data for this file
  fileCache.delete(fileKey);

  // Proactively re-fetch commonly accessed data
  const token = process.env.FIGMA_PAT!;
  await getCachedFile(fileKey, token);

  console.log(`Cache invalidated and refreshed for ${fileKey}`);
}
```

### Step 4: Batch Node Fetches
```typescript
// The /nodes endpoint accepts multiple IDs -- batch them
// Max practical batch size: ~50-100 IDs per request

async function batchFetchNodes(
  fileKey: string,
  nodeIds: string[],
  token: string,
  batchSize = 50
): Promise<Map<string, any>> {
  const results = new Map<string, any>();

  for (let i = 0; i < nodeIds.length; i += batchSize) {
    const batch = nodeIds.slice(i, i + batchSize);
    const ids = encodeURIComponent(batch.join(','));

    const data = await fetch(
      `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`,
      { headers: { 'X-Figma-Token': token } }
    ).then(r => r.json());

    for (const [id, node] of Object.entries(data.nodes)) {
      results.set(id, node);
    }
  }

  return results;
}
```

### Step 5: Connection Reuse
```typescript
import { Agent } from 'undici';

// Reuse HTTP connections to api.figma.com
const figmaAgent = new Agent({
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  connections: 5,
});

// Use with Node.js 18+ built-in fetch
async function optimizedFetch(path: string, token: string) {
  return fetch(`https://api.figma.com${path}`, {
    headers: { 'X-Figma-Token': token },
    // @ts-ignore -- dispatcher is a Node.js fetch option
    dispatcher: figmaAgent,
  });
}
```

## Output
- Reduced API payload sizes with `depth` and `nodes` endpoints
- Response caching with appropriate TTLs
- Webhook-driven cache invalidation
- Batched node fetches reducing request count
- Connection reuse for lower latency

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache | No invalidation | Use webhooks to invalidate on changes |
| Out of memory | Caching full file JSON | Use `depth=1` or `nodes` endpoint |
| Slow image exports | Large batch, high scale | Reduce scale; batch in groups of 50 |
| Expired image URLs | Cached URL older than 30 days | Set image cache TTL to <24h |

## Resources
- [Figma File Endpoints](https://developers.figma.com/docs/rest-api/file-endpoints/)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [lru-cache](https://github.com/isaacs/node-lru-cache)

## Next Steps
For cost optimization, see `figma-cost-tuning`.
