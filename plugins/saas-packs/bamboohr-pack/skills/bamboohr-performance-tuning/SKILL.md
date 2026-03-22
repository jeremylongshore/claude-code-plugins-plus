---
name: bamboohr-performance-tuning
description: |
  Optimize BambooHR API performance with caching, batch reports, incremental sync,
  and connection pooling. Use when experiencing slow API responses,
  implementing caching, or optimizing sync throughput.
  Trigger with phrases like "bamboohr performance", "optimize bamboohr",
  "bamboohr latency", "bamboohr caching", "bamboohr slow", "bamboohr batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, performance]
compatible-with: claude-code
---

# BambooHR Performance Tuning

## Overview

Optimize BambooHR API performance through request reduction, caching, incremental sync, and connection pooling. The biggest wins come from eliminating N+1 query patterns using custom reports and the changed-since endpoint.

## Prerequisites

- BambooHR API client configured
- Redis or in-memory cache available (optional)
- Performance monitoring in place

## Instructions

### Step 1: Eliminate N+1 Queries with Custom Reports

The single biggest performance improvement: use `POST /reports/custom` instead of individual employee GETs.

```typescript
// BAD: 501 API calls for 500 employees
const dir = await client.getDirectory();                      // 1 call
for (const emp of dir.employees) {
  await client.getEmployee(emp.id, ['salary', 'hireDate']);   // 500 calls
}

// GOOD: 1 API call for all employees with all needed fields
const report = await client.customReport([
  'firstName', 'lastName', 'department', 'jobTitle',
  'hireDate', 'workEmail', 'status', 'location',
  'supervisor', 'employeeNumber',
]);
// 1 call, returns all employees with all fields
```

**Performance impact:** 500x reduction in API calls. Custom reports return all active employees in one request.

### Step 2: Incremental Sync with Changed-Since

```typescript
import { readFileSync, writeFileSync } from 'fs';

const LAST_SYNC_FILE = '.bamboohr-last-sync';

async function incrementalSync(client: BambooHRClient): Promise<string[]> {
  // Read last sync timestamp
  let lastSync: string;
  try {
    lastSync = readFileSync(LAST_SYNC_FILE, 'utf-8').trim();
  } catch {
    lastSync = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(); // Default: 24h ago
  }

  // GET /employees/changed/?since=... — returns only changed employee IDs
  const changed = await client.request<{
    employees: Record<string, { id: string; lastChanged: string }>;
  }>('GET', `/employees/changed/?since=${lastSync}`);

  const changedIds = Object.keys(changed.employees || {});
  console.log(`${changedIds.length} employees changed since ${lastSync}`);

  if (changedIds.length === 0) return [];

  // Fetch only changed employees' details
  // For large sets, use custom report with filter; for small sets, individual GETs
  if (changedIds.length > 20) {
    // Bulk: use custom report (returns all, then filter client-side)
    const report = await client.customReport([
      'firstName', 'lastName', 'department', 'status',
    ]);
    const changedData = report.employees.filter(e =>
      changedIds.includes(e.id?.toString()),
    );
    // Process changedData...
  } else {
    // Small set: individual GETs are fine
    for (const id of changedIds) {
      const emp = await client.getEmployee(id, ['firstName', 'lastName', 'department', 'status']);
      // Process emp...
    }
  }

  // Save sync timestamp
  writeFileSync(LAST_SYNC_FILE, new Date().toISOString());
  return changedIds;
}
```

**Also available for table data:**

```typescript
// GET /employees/changed/tables/{tableName}?since=...
const changedJobs = await client.request<any>(
  'GET', `/employees/changed/tables/jobInfo?since=${lastSync}`,
);
// Returns { employees: { "123": { lastChanged: "..." }, ... } }
```

### Step 3: Response Caching

```typescript
import { LRUCache } from 'lru-cache';

// BambooHR directory data changes infrequently — cache aggressively
const cache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000, // 5 minutes for directory data
});

async function cachedRequest<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs?: number,
): Promise<T> {
  const cached = cache.get(key) as T | undefined;
  if (cached) {
    console.log(`Cache hit: ${key}`);
    return cached;
  }

  const result = await fetcher();
  cache.set(key, result, { ttl: ttlMs });
  return result;
}

// Usage
const directory = await cachedRequest(
  'directory',
  () => client.getDirectory(),
  5 * 60 * 1000, // Cache for 5 min
);

// Single employee — shorter cache
const employee = await cachedRequest(
  `employee:${id}`,
  () => client.getEmployee(id, fields),
  60 * 1000, // Cache for 1 min
);
```

**Redis caching for multi-instance deployments:**

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function redisCached<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSec = 300,
): Promise<T> {
  const cached = await redis.get(`bamboohr:${key}`);
  if (cached) return JSON.parse(cached);

  const result = await fetcher();
  await redis.setex(`bamboohr:${key}`, ttlSec, JSON.stringify(result));
  return result;
}

// Invalidate on webhook
async function invalidateCache(employeeId: string) {
  await redis.del(`bamboohr:employee:${employeeId}`);
  await redis.del('bamboohr:directory'); // Directory includes this employee
}
```

### Step 4: Connection Pooling

```typescript
import { Agent } from 'https';

// Reuse TCP connections for BambooHR API calls
const keepAliveAgent = new Agent({
  keepAlive: true,
  maxSockets: 5,        // Max 5 parallel connections
  maxFreeSockets: 2,
  timeout: 30_000,
  keepAliveMsecs: 10_000,
});

// Pass to fetch via undici or node-fetch
// For native fetch in Node 20+, connection pooling is automatic
```

### Step 5: Request Batching with DataLoader

```typescript
import DataLoader from 'dataloader';

// Batch individual employee GETs into a custom report
const employeeLoader = new DataLoader<string, Record<string, string>>(
  async (ids) => {
    // One custom report instead of N individual GETs
    const report = await client.customReport([
      'id', 'firstName', 'lastName', 'department', 'jobTitle',
    ]);

    const byId = new Map(report.employees.map(e => [e.id, e]));
    return ids.map(id => byId.get(id) || new Error(`Employee ${id} not found`));
  },
  {
    maxBatchSize: 100,
    batchScheduleFn: cb => setTimeout(cb, 50), // Batch window: 50ms
    cache: true,
  },
);

// Usage — automatically batched into one API call
const [emp1, emp2, emp3] = await Promise.all([
  employeeLoader.load('1'),
  employeeLoader.load('2'),
  employeeLoader.load('3'),
]);
```

### Step 6: Performance Monitoring

```typescript
class BambooHRMetrics {
  private requests: { duration: number; status: number; endpoint: string }[] = [];

  record(endpoint: string, status: number, durationMs: number) {
    this.requests.push({ duration: durationMs, status, endpoint });

    // Keep last 1000 requests
    if (this.requests.length > 1000) this.requests.shift();
  }

  summary() {
    const durations = this.requests.map(r => r.duration).sort((a, b) => a - b);
    const errors = this.requests.filter(r => r.status >= 400);

    return {
      totalRequests: this.requests.length,
      errorRate: (errors.length / Math.max(this.requests.length, 1) * 100).toFixed(1) + '%',
      p50: durations[Math.floor(durations.length * 0.5)] || 0,
      p95: durations[Math.floor(durations.length * 0.95)] || 0,
      p99: durations[Math.floor(durations.length * 0.99)] || 0,
      topEndpoints: this.topEndpoints(),
    };
  }

  private topEndpoints() {
    const counts = new Map<string, number>();
    for (const r of this.requests) {
      counts.set(r.endpoint, (counts.get(r.endpoint) || 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  }
}
```

## Output

- N+1 queries eliminated via custom reports (500x reduction)
- Incremental sync using changed-since endpoint
- Multi-tier caching (LRU in-memory + Redis)
- Connection pooling with keep-alive
- DataLoader-based request batching
- Performance metrics with p50/p95/p99

## Performance Reference

| Optimization | Before | After | Improvement |
|-------------|--------|-------|-------------|
| Custom reports vs N+1 | 501 calls | 1 call | 500x |
| Incremental sync | Full pull | Delta only | 10-100x |
| Directory caching (5 min) | Every request | 1/5 min | 50x |
| Connection pooling | New conn/request | Reused | 2-3x latency |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | All caches expire simultaneously | Stagger TTLs with jitter |
| Stale data | Cache TTL too long | Invalidate on webhook events |
| DataLoader timeout | Custom report too slow | Reduce batch size |
| Memory pressure | LRU cache too large | Set `max` entries limit |

## Resources

- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
- [LRU Cache Documentation](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `bamboohr-cost-tuning`.
