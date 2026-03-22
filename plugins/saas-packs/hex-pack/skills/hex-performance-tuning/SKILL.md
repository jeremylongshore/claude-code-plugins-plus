---
name: hex-performance-tuning
description: |
  Optimize Hex API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Hex integrations.
  Trigger with phrases like "hex performance", "optimize hex",
  "hex latency", "hex caching", "hex slow", "hex batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Performance Tuning

## Latency Benchmarks

| Operation | Typical Duration |
|-----------|-----------------|
| ListProjects | 200-500ms |
| RunProject (trigger) | 500ms-2s |
| Project execution | 10s-30min (depends on queries) |
| GetRunStatus (poll) | 100-300ms |

## Instructions

### Cache Project Lists

```typescript
import { LRUCache } from 'lru-cache';
const projectCache = new LRUCache<string, any>({ max: 50, ttl: 300000 }); // 5 min

async function getCachedProjects(client: HexClient) {
  const cached = projectCache.get('projects');
  if (cached) return cached;
  const projects = await client.listProjects();
  projectCache.set('projects', projects);
  return projects;
}
```

### Parallel Independent Runs

```typescript
// Run independent projects in parallel (respecting rate limits)
async function parallelRuns(client: HexClient, configs: Array<{ id: string; params: any }>) {
  return Promise.allSettled(
    configs.map(c => runWithRetry(client, c.id, c.params))
  );
}
```

### Optimize Poll Interval

```typescript
// Adaptive polling: start fast, slow down
async function adaptivePoll(client: HexClient, projectId: string, runId: string) {
  let interval = 2000; // Start at 2s
  while (true) {
    const status = await client.getRunStatus(projectId, runId);
    if (['COMPLETED', 'ERRORED', 'KILLED'].includes(status.status)) return status;
    await new Promise(r => setTimeout(r, interval));
    interval = Math.min(interval * 1.5, 30000); // Max 30s
  }
}
```

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
