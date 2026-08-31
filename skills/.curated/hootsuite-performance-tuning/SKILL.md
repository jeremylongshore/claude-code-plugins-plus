---
name: hootsuite-performance-tuning
description: 'Optimize Hootsuite API performance with caching, batching, and connection
  pooling.

  Use when experiencing slow API responses, implementing caching strategies,

  or optimizing request throughput for Hootsuite integrations.

  Trigger with phrases like "hootsuite performance", "optimize hootsuite",

  "hootsuite latency", "hootsuite caching", "hootsuite slow", "hootsuite batch".

  '
allowed-tools: Read, Write, Edit
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite Performance Tuning

## Instructions

### Step 1: Cache Social Profiles

```typescript
import { LRUCache } from 'lru-cache';

const profileCache = new LRUCache<string, any>({ max: 100, ttl: 3600000 });

async function getCachedProfiles(): Promise<any[]> {
  const cached = profileCache.get('profiles');
  if (cached) return cached;

  const response = await fetch('https://platform.hootsuite.com/v1/socialProfiles', {
    headers: { 'Authorization': `Bearer ${await getStoredToken()}` },
  });
  const { data } = await response.json();
  profileCache.set('profiles', data);
  return data;
}
```

### Step 2: Batch Message Scheduling

```typescript
import PQueue from 'p-queue';

const scheduleQueue = new PQueue({ concurrency: 2, interval: 1000, intervalCap: 2 });

async function batchSchedule(posts: Array<{ text: string; profileId: string; time: Date }>) {
  const results = await Promise.allSettled(
    posts.map(post =>
      scheduleQueue.add(() =>
        fetch('https://platform.hootsuite.com/v1/messages', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${process.env.HOOTSUITE_ACCESS_TOKEN}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: post.text, socialProfileIds: [post.profileId], scheduledSendTime: post.time.toISOString() }),
        }).then(r => r.json())
      )
    )
  );
  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  console.log(`Scheduled ${succeeded}/${posts.length} posts`);
}
```

### Step 3: Connection Reuse

```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 5 });
// Pass agent to fetch/axios for connection reuse to platform.hootsuite.com
```

## Overview

Tune scheduling latency and throughput through draft-only sandbox fixtures and aggregate metrics. A gain is invalid if it changes account scope, audience, approval, publication state, or rollback ability.

## Prerequisites

- Baseline latency/quota metrics, draft-only fixture revision, error budget, and rollback revision for cache, concurrency, scheduling, and retry policy.

## Output

Return a tuning receipt with baseline/canary bands, cache/concurrency/schedule revisions, quota/error outcomes, draft/approval assertions, owner approval, and rollback reference. Use aggregates only.

## Error Handling

Roll back for quota saturation, increased errors, audience/approval drift, duplicate schedules, or a public-post path. Do not increase concurrency or cache duration to hide failure.

## Examples

`env=sandbox; p95=420ms->310ms; concurrency=2; schedule=r4; quota=within-budget; draft=pass; public_posts=0; rollback=perf-r3` documents a safe canary.

## Resources

- [Hootsuite API](https://developer.hootsuite.com/docs/api-overview)

## Next Steps

For cost optimization, see `hootsuite-cost-tuning`.
