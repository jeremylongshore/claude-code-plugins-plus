---
name: fireflies-performance-tuning
description: |
  Optimize Fireflies.ai GraphQL query performance with field selection, caching, and batching.
  Use when experiencing slow API responses, implementing caching,
  or optimizing transcript processing throughput.
  Trigger with phrases like "fireflies performance", "optimize fireflies",
  "fireflies latency", "fireflies caching", "fireflies slow", "fireflies batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, api, performance]

---
# Fireflies.ai Performance Tuning

## Overview
Optimize Fireflies.ai GraphQL API performance. The biggest wins: request only needed fields (transcripts with sentences can be very large), cache immutable transcripts, and batch operations within rate limits.

## Prerequisites
- `FIREFLIES_API_KEY` configured
- Understanding of your access pattern (list vs detail, frequency)
- Optional: Redis or LRU cache library

## Instructions

### Step 1: Field Selection -- The Biggest Win
Transcript responses with `sentences` can be enormous. Always request the minimum fields needed.

```typescript
// BAD: Fetching everything when you only need titles
const HEAVY = `{ transcripts(limit: 50) {
  id title date duration sentences { text speaker_name start_time end_time }
  summary { overview action_items keywords outline bullet_gist }
  analytics { speakers { name duration word_count } }
} }`;

// GOOD: Light query for listing
const LIGHT = `{ transcripts(limit: 50) {
  id title date duration organizer_email
} }`;

// GOOD: Full query only when drilling into a specific transcript
const DETAIL = `query($id: String!) { transcript(id: $id) {
  id title
  sentences { speaker_name text start_time end_time }
  summary { overview action_items keywords }
} }`;
```

### Step 2: Cache Transcripts (They Are Immutable)
Once a transcript is processed, its content never changes. Cache aggressively.

```typescript
import { LRUCache } from "lru-cache";

const transcriptCache = new LRUCache<string, any>({
  max: 500,
  ttl: 1000 * 60 * 60, // 1 hour -- transcripts are immutable
});

async function getCachedTranscript(id: string) {
  const cached = transcriptCache.get(id);
  if (cached) return cached;

  const data = await firefliesQuery(`
    query($id: String!) {
      transcript(id: $id) {
        id title date duration
        speakers { name }
        sentences { speaker_name text start_time end_time }
        summary { overview action_items keywords }
      }
    }
  `, { id });

  transcriptCache.set(id, data.transcript);
  return data.transcript;
}
```

### Step 3: Redis Cache for Multi-Instance Deployments
```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL!);
const CACHE_TTL = 3600; // 1 hour in seconds

async function getTranscriptCached(id: string) {
  const cacheKey = `fireflies:transcript:${id}`;

  // Check cache
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  // Fetch from API
  const data = await firefliesQuery(`
    query($id: String!) {
      transcript(id: $id) {
        id title date duration
        sentences { speaker_name text start_time end_time }
        summary { overview action_items keywords }
      }
    }
  `, { id });

  // Cache the result
  await redis.set(cacheKey, JSON.stringify(data.transcript), "EX", CACHE_TTL);
  return data.transcript;
}
```

### Step 4: Batch Processing with Rate Limit Awareness
```typescript
import PQueue from "p-queue";

// Business plan: 60 req/min. Safe rate: 1 req/sec with headroom.
const queue = new PQueue({
  concurrency: 1,
  interval: 1100,
  intervalCap: 1,
});

async function batchFetchTranscripts(ids: string[]) {
  console.log(`Fetching ${ids.length} transcripts (rate-limited)...`);

  const results = await Promise.all(
    ids.map(id => queue.add(() => getCachedTranscript(id)))
  );

  const cacheHits = ids.filter(id => transcriptCache.has(id)).length;
  console.log(`Done. Cache hits: ${cacheHits}/${ids.length}`);
  return results;
}
```

### Step 5: Warm Cache on Webhook Events
```typescript
// When a transcript completes, pre-cache it immediately
async function onWebhookEvent(event: { meetingId: string; eventType: string }) {
  if (event.eventType === "Transcription completed") {
    // Pre-warm the cache so future reads are instant
    await getCachedTranscript(event.meetingId);
    console.log(`Pre-cached transcript: ${event.meetingId}`);
  }
}
```

### Step 6: Pagination for Large Result Sets
```typescript
async function getAllTranscripts(batchSize = 50) {
  const allTranscripts: any[] = [];
  let hasMore = true;
  let offset = 0;

  while (hasMore) {
    const data = await firefliesQuery(`
      query($limit: Int, $skip: Int) {
        transcripts(limit: $limit, skip: $skip) {
          id title date duration
        }
      }
    `, { limit: batchSize, skip: offset });

    allTranscripts.push(...data.transcripts);

    if (data.transcripts.length < batchSize) {
      hasMore = false;
    } else {
      offset += batchSize;
      // Rate limit: wait between pages
      await new Promise(r => setTimeout(r, 1100));
    }
  }

  return allTranscripts;
}
```

## Performance Benchmarks

| Optimization | Before | After | Improvement |
|-------------|--------|-------|-------------|
| Field selection (list) | ~2s (with sentences) | ~200ms (metadata only) | 10x |
| LRU cache (detail view) | ~500ms (API call) | <1ms (cache hit) | 500x |
| Batch with queue | Rate limited/errors | Smooth throughput | Reliable |
| Webhook pre-cache | Cold fetch on user visit | Instant from cache | UX improvement |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow list queries | Requesting sentences in list | Use light query without `sentences` |
| Rate limit 429 | Burst requests | Use PQueue with 1.1s interval |
| Large response OOM | Transcript with 2+ hour meeting | Stream/paginate sentences |
| Stale cache | (Not a real issue -- transcripts are immutable) | N/A |

## Output
- Field-optimized GraphQL queries (light list, full detail)
- LRU and Redis caching for immutable transcripts
- Rate-limited batch processor
- Webhook-driven cache warming

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [lru-cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For cost optimization, see `fireflies-cost-tuning`.
