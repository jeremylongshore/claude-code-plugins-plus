---
name: clickup-performance-tuning
description: |
  Optimize ClickUp API v2 performance with caching, pagination, connection pooling,
  and request batching patterns.
  Trigger: "clickup performance", "optimize clickup", "clickup latency",
  "clickup caching", "clickup slow", "clickup batch requests", "clickup pagination".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Performance Tuning

## Overview

Optimize ClickUp API v2 throughput and latency. Key strategies: cache hierarchy data, paginate efficiently, pool connections, and batch where possible.

## Baseline Latency (ClickUp API v2)

| Endpoint | Typical P50 | Typical P95 |
|----------|-------------|-------------|
| `GET /user` | 80ms | 200ms |
| `GET /team` | 100ms | 300ms |
| `GET /list/{id}/task` | 150ms | 500ms |
| `POST /list/{id}/task` | 200ms | 600ms |
| `PUT /task/{id}` | 150ms | 400ms |
| `GET /task/{id}` (with custom fields) | 200ms | 700ms |

## 1. Cache Hierarchy Data

Workspaces, spaces, folders, and lists change infrequently. Cache them.

```typescript
import { LRUCache } from 'lru-cache';

const clickupCache = new LRUCache<string, any>({
  max: 1000,
  ttl: 300_000, // 5 min for structural data
});

async function cachedRequest<T>(path: string, ttl?: number): Promise<T> {
  const cached = clickupCache.get(path);
  if (cached) return cached as T;

  const data = await clickupRequest(path);
  clickupCache.set(path, data, ttl ? { ttl } : undefined);
  return data as T;
}

// Hierarchy data: 5 min cache (default)
const spaces = await cachedRequest(`/team/${teamId}/space?archived=false`);

// Task data: 30 sec cache (changes more often)
const task = await cachedRequest(`/task/${taskId}`, 30_000);
```

## 2. Efficient Pagination

Get Tasks returns max 100 tasks per page. Use async generators for memory efficiency.

```typescript
async function* paginateTasks(listId: string, filters: Record<string, string> = {}) {
  let page = 0;
  let hasMore = true;

  while (hasMore) {
    const params = new URLSearchParams({
      page: String(page),
      archived: 'false',
      subtasks: 'true',
      ...filters,
    });

    const data = await clickupRequest(`/list/${listId}/task?${params}`);
    const tasks = data.tasks;

    for (const task of tasks) {
      yield task;
    }

    // ClickUp returns fewer than 100 tasks on last page
    hasMore = tasks.length === 100;
    page++;
  }
}

// Process tasks without loading all into memory
let count = 0;
for await (const task of paginateTasks('900100200300', { 'statuses[]': 'in progress' })) {
  await processTask(task);
  count++;
}
console.log(`Processed ${count} tasks`);
```

## 3. Connection Pooling

```typescript
import { Agent } from 'node:https';

const keepAliveAgent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30_000,
  scheduling: 'lifo',
});

// Use with undici or node-fetch that supports custom agents
// Native fetch in Node 18+ uses keep-alive by default
```

## 4. Parallel with Rate Awareness

```typescript
import PQueue from 'p-queue';

// Respect 100 req/min on Free/Unlimited/Business
const clickupQueue = new PQueue({
  concurrency: 5,
  interval: 60_000,
  intervalCap: 90, // 90% of 100 limit
});

async function parallelTaskFetch(taskIds: string[]) {
  const results = await Promise.all(
    taskIds.map(id =>
      clickupQueue.add(() => clickupRequest(`/task/${id}`))
    )
  );
  return results;
}
```

## 5. Webhook-Based Cache Invalidation

```typescript
// Instead of polling or short TTLs, invalidate cache on webhook events
app.post('/webhooks/clickup', (req, res) => {
  res.status(200).json({ received: true });

  const { event, task_id } = req.body;

  switch (event) {
    case 'taskUpdated':
    case 'taskDeleted':
      clickupCache.delete(`/task/${task_id}`);
      break;
    case 'listUpdated':
    case 'listDeleted':
      // Invalidate all list-related caches
      for (const key of clickupCache.keys()) {
        if (key.includes('/list/')) clickupCache.delete(key);
      }
      break;
  }
});
```

## 6. Reduce Payload Size

```typescript
// Use custom_fields and include_closed parameters to minimize response size
const params = new URLSearchParams({
  archived: 'false',
  include_closed: 'false',
  subtasks: 'false',        // Skip subtask expansion if not needed
  page: '0',
});

// Note: ClickUp v2 doesn't support field selection (no ?fields= parameter)
// Minimize response by filtering client-side
const { tasks } = await clickupRequest(`/list/${listId}/task?${params}`);
const slim = tasks.map((t: any) => ({
  id: t.id, name: t.name, status: t.status.status, priority: t.priority?.priority,
}));
```

## Performance Monitoring

```typescript
async function measuredRequest<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const ms = (performance.now() - start).toFixed(1);
    console.log(`[clickup] ${name}: ${ms}ms`);
    return result;
  } catch (error) {
    const ms = (performance.now() - start).toFixed(1);
    console.error(`[clickup] ${name}: FAILED after ${ms}ms`);
    throw error;
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache | No invalidation | Use webhooks for invalidation |
| Memory growth | Unbounded cache | Set `max` entries on LRU cache |
| Pagination loop | API returns 100 forever | Add max page safety limit |
| Queue backlog | Burst of requests | Increase concurrency or plan tier |

## Resources

- [ClickUp Get Tasks](https://developer.clickup.com/reference/gettasks)
- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)
- [lru-cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `clickup-cost-tuning`.
