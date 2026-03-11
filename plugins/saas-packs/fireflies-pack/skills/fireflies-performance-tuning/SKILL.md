---
name: fireflies-performance-tuning
description: |
  Optimize Fireflies.ai API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Fireflies.ai integrations.
  Trigger with phrases like "fireflies performance", "optimize fireflies",
  "fireflies latency", "fireflies caching", "fireflies slow", "fireflies batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Performance Tuning

## Overview
Optimize Fireflies.ai transcript retrieval and meeting data processing. Focus on GraphQL query efficiency, transcript caching, and webhook throughput for high-volume meeting analytics pipelines.

## Prerequisites
- Fireflies.ai API key with GraphQL access
- Node.js 18+ with GraphQL client
- Understanding of meeting transcript structure
- Redis available for transcript caching (recommended)

## Instructions

### Step 1: Optimize GraphQL Queries with Field Selection
```typescript
// Only request fields you need - transcripts can be large
const LIGHT_TRANSCRIPT_QUERY = `
  query GetTranscripts($limit: Int) {
    transcripts(limit: $limit) {
      id
      title
      date
      duration
      organizer_email
      participants
    }
  }
`;

// Full transcript only when needed
const FULL_TRANSCRIPT_QUERY = `
  query GetTranscript($id: String!) {
    transcript(id: $id) {
      id
      title
      sentences {
        speaker_name
        text
        start_time
        end_time
      }
      action_items
      summary { overview keywords }
    }
  }
`;

async function getTranscriptSummaries(limit = 50) {
  return graphqlClient.request(LIGHT_TRANSCRIPT_QUERY, { limit });
}
```

### Step 2: Cache Transcripts with TTL
```typescript
import { LRUCache } from 'lru-cache';

const transcriptCache = new LRUCache<string, any>({
  max: 200,  # HTTP 200 OK
  ttl: 1000 * 60 * 30, // 30 min - transcripts are immutable  # 1000: 1 second in ms
});

async function getCachedTranscript(id: string) {
  const cached = transcriptCache.get(id);
  if (cached) return cached;

  const result = await graphqlClient.request(FULL_TRANSCRIPT_QUERY, { id });
  transcriptCache.set(id, result.transcript);
  return result.transcript;
}
```

### Step 3: Batch Process Meeting Data
```typescript
async function batchProcessMeetings(
  meetingIds: string[],
  concurrency = 3
) {
  const results: any[] = [];
  for (let i = 0; i < meetingIds.length; i += concurrency) {
    const batch = meetingIds.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(id => getCachedTranscript(id))
    );
    results.push(...batchResults);
    // Respect rate limits: 50 req/min
    if (i + concurrency < meetingIds.length) {
      await new Promise(r => setTimeout(r, 1200));  # 1200 = configured value
    }
  }
  return results;
}
```

### Step 4: Efficient Webhook Processing
```typescript
import { createHmac } from 'crypto';

// Process webhooks asynchronously with a queue
const webhookQueue: any[] = [];

async function handleWebhook(payload: any) {
  // Acknowledge immediately
  webhookQueue.push(payload);
  // Process in background
  setImmediate(() => processWebhookQueue());
}

async function processWebhookQueue() {
  while (webhookQueue.length > 0) {
    const event = webhookQueue.shift();
    if (event.event_type === 'Transcription completed') {
      // Pre-cache the transcript
      await getCachedTranscript(event.meeting_id);
    }
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| GraphQL timeout | Requesting full transcript list | Use pagination with `limit` param |
| Rate limit 429 | Over 50 requests/minute | Add 1.2s delay between batches |
| Large response OOM | Fetching all sentences | Stream sentences or paginate |
| Stale webhook data | Cache not warmed | Pre-fetch on webhook events |

## Examples

### Meeting Analytics Pipeline
```typescript
async function analyzeMeetingTrends(days = 30) {
  const since = new Date(Date.now() - days * 86400000).toISOString();  # 86400000 = configured value
  const summaries = await getTranscriptSummaries(200);  # HTTP 200 OK

  const recent = summaries.transcripts.filter(
    (t: any) => new Date(t.date) > new Date(since)
  );

  return {
    totalMeetings: recent.length,
    avgDuration: recent.reduce((s: number, t: any) => s + t.duration, 0) / recent.length,
    topParticipants: countParticipants(recent),
  };
}
```

## Resources
- [Fireflies GraphQL API](https://docs.fireflies.ai/graphql)
- [Fireflies Rate Limits](https://docs.fireflies.ai/rate-limits)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale