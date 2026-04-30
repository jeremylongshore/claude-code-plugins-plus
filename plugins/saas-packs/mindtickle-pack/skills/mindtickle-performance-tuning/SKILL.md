---
name: mindtickle-performance-tuning
description: 'Optimize MindTickle API integration performance with caching, bulk progress
  queries, and webhook processing.

  Use when learner progress queries are slow, report generation times out, or completion
  webhooks cause backpressure.

  Trigger with "mindtickle performance tuning".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Performance Tuning

## Overview

MindTickle's API serves sales enablement data across courses, quizzes, and analytics — enterprise deployments tracking thousands of reps make bulk progress queries and report generation the primary bottlenecks. This skill covers caching learner data, batching progress operations, and handling rate limits during high-volume training campaigns.

## Instructions

1. Implement Redis caching (or in-memory Map for development) with TTLs matching data volatility
2. Use offset-based pagination for user and course lists to avoid incomplete result sets
3. Queue incoming completion webhooks through Redis to handle campaign burst traffic
4. Wrap all API calls with the rate limit handler before deploying to production

## Prerequisites

- MindTickle API key with admin or integration scope
- Redis instance for caching learner progress and report data
- Node.js 18+ with native fetch
- Webhook endpoint configured for course/quiz completion events

## Caching Strategy

```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

// Course catalog changes rarely — cache 30 minutes
// User progress updates frequently during campaigns — cache 2 minutes
const TTL = { courses: 1800, progress: 120, reports: 600, users: 900 } as const;

async function getCachedCourses(orgId: string): Promise<MindTickleCourse[]> {
  const key = `mt:courses:${orgId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const courses = await mindtickleApi.listCourses(orgId);
  await redis.setex(key, TTL.courses, JSON.stringify(courses));
  return courses;
}

async function getCachedProgress(userId: string, courseId: string): Promise<UserProgress> {
  const key = `mt:progress:${userId}:${courseId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const progress = await mindtickleApi.getUserProgress(userId, courseId);
  await redis.setex(key, TTL.progress, JSON.stringify(progress));
  return progress;
}
```

## Batch Operations

```typescript
import pLimit from "p-limit";

const limit = pLimit(6); // MindTickle allows moderate concurrency

// Bulk fetch progress for all reps in a training campaign
async function batchFetchTeamProgress(
  userIds: string[],
  courseId: string
): Promise<UserProgress[]> {
  return Promise.all(
    userIds.map((uid) => limit(() => getCachedProgress(uid, courseId)))
  );
}

// Paginate through all users in an organization
async function fetchAllUsers(orgId: string): Promise<MindTickleUser[]> {
  const users: MindTickleUser[] = [];
  let offset = 0;
  const pageSize = 200;

  do {
    const page = await mindtickleApi.listUsers(orgId, { offset, limit: pageSize });
    users.push(...page.users);
    offset += pageSize;
    if (page.users.length < pageSize) break;
  } while (true);

  return users;
}
```

## Connection Pooling

```typescript
import { Agent } from "undici";

const mindtickleAgent = new Agent({
  connect: { timeout: 8_000 }, // Report endpoints can be slow
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  pipelining: 1,
  connections: 10, // Persistent pool for MindTickle API
});

async function mindtickleApiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`https://api.mindtickle.com/v2${path}`, {
    ...init,
    // @ts-expect-error undici dispatcher
    dispatcher: mindtickleAgent,
    headers: { Authorization: `Token ${process.env.MINDTICKLE_API_KEY}`, ...init?.headers },
  });
}
```

## Rate Limit Management

```typescript
async function withRateLimit<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.status === 429) {
        const retryAfter = parseInt(err.headers?.["retry-after"] ?? "10", 10);
        const backoff = retryAfter * 1000 * Math.pow(2, attempt);
        console.warn(`MindTickle rate limited. Retrying in ${backoff}ms (attempt ${attempt + 1})`);
        await new Promise((r) => setTimeout(r, backoff));
        continue;
      }
      throw err;
    }
  }
  throw new Error("MindTickle API: max retries exceeded");
}
```

## Monitoring & Metrics

```typescript
import { Counter, Histogram } from "prom-client";

const mtApiLatency = new Histogram({
  name: "mindtickle_api_duration_seconds",
  help: "MindTickle API call latency",
  labelNames: ["endpoint", "status"],
  buckets: [0.1, 0.5, 1, 2, 5, 10], // Reports can take 5-10s
});

const mtCacheHits = new Counter({
  name: "mindtickle_cache_hits_total",
  help: "Cache hits for MindTickle course and progress data",
  labelNames: ["cache_type"], // courses | progress | reports | users
});

const mtWebhookLatency = new Histogram({
  name: "mindtickle_webhook_processing_seconds",
  help: "Time to process MindTickle completion webhooks",
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5],
});
```

## Performance Checklist

- [ ] Cache TTLs set: courses 30min, progress 2min, reports 10min, users 15min
- [ ] Batch size optimized (200 users per page, 6 concurrent progress fetches)
- [ ] Offset-based pagination for user and course lists
- [ ] Connection pooling via undici Agent with 8s timeout for reports
- [ ] Rate limit retry with exponential backoff in place
- [ ] Webhook processor handles burst completions without backpressure
- [ ] Monitoring dashboards tracking API latency, cache hits, and webhook processing time

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Report generation timeouts | Analytics queries over large date ranges | Limit date range to 30 days, cache reports for 10min |
| Stale progress data during live training | Reps complete modules but dashboard shows old state | Invalidate progress cache on completion webhook |
| Webhook processing backpressure | Training campaign triggers 1000+ completions in minutes | Queue webhooks in Redis, process with worker at controlled rate |
| 429 during bulk progress export | Fetching progress for all reps across all courses | Reduce concurrency to 3 and add 500ms delay between course batches |
| Incomplete user list pagination | Offset math error causes skipped or duplicate users | Always check `page.users.length < pageSize` as termination condition |

## Output

After applying these optimizations, expect:
- Course catalog queries under 50ms (cached) vs 300ms+ (uncached)
- Team progress batch fetches completing in seconds instead of minutes
- Webhook processing sustained at 100+ completions/second without backpressure

## Examples

```typescript
// Full optimized team progress fetch — cache + rate limit + batching
const users = await fetchAllUsers("org-123");
const progress = await batchFetchTeamProgress(
  users.map((u) => u.id),
  "course-onboarding-2026"
);

// Alternative: use background refresh for reports instead of on-demand generation
const report = await getCachedReport("quarterly-readiness", { backgroundRefresh: true });
```

## Resources

- [MindTickle Integration Platform](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-reference-architecture`.
