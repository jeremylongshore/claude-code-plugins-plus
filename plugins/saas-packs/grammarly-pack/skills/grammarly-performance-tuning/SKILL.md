---
name: grammarly-performance-tuning
description: |
  Optimize Grammarly API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Grammarly integrations.
  Trigger with phrases like "grammarly performance", "optimize grammarly",
  "grammarly latency", "grammarly caching", "grammarly slow", "grammarly batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Performance Tuning

## Latency Benchmarks

| API | Typical Latency | Notes |
|-----|----------------|-------|
| Writing Score | 1-3s | Depends on text length |
| AI Detection | 1-2s | Fast for short text |
| Plagiarism | 10-60s | Async, requires polling |

## Instructions

### Cache Score Results

```typescript
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';

const scoreCache = new LRUCache<string, any>({ max: 500, ttl: 3600000 });

async function cachedScore(text: string, token: string) {
  const key = createHash('sha256').update(text).digest('hex');
  const cached = scoreCache.get(key);
  if (cached) return cached;
  const score = await grammarlyClient.score(text);
  scoreCache.set(key, score);
  return score;
}
```

### Parallel API Calls

```typescript
// Score + AI detect in parallel (they're independent)
async function fullAudit(text: string, token: string) {
  const [score, ai] = await Promise.all([
    grammarlyClient.score(text),
    grammarlyClient.detectAI(text),
  ]);
  return { score, ai };
}
```

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For cost optimization, see `grammarly-cost-tuning`.
