---
name: grammarly-performance-tuning
description: 'Optimize Grammarly API performance with caching, batching, and connection
  pooling.

  Use when experiencing slow API responses, implementing caching strategies,

  or optimizing request throughput for Grammarly integrations.

  Trigger with phrases like "grammarly performance", "optimize grammarly",

  "grammarly latency", "grammarly caching", "grammarly slow", "grammarly batch".

  '
allowed-tools: Read, Write, Edit
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
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

## Overview

Tune latency and throughput using bounded synthetic fixtures and aggregate metrics. A performance gain is invalid if it expands text retention, access scope, error rate, or duplication risk.

## Prerequisites

- Baseline latency percentiles, error/quota rates, synthetic fixture revision, and an approved error budget.
- A rollback revision for cache, concurrency, chunking, and retry settings, plus retention-safe telemetry.

## Output

Return a tuning receipt with baseline/canary percentile bands, cache/concurrency/chunking revisions, quota and error outcomes, fixture result, retention check, owner approval, and rollback reference. Use aggregates only.

## Error Handling

Roll back for quota saturation, increased errors, retained text in telemetry, duplicated submissions, or incorrect synthetic results. Do not raise concurrency or cache duration to hide a failure.

## Examples

`env=sandbox; p95=420ms->310ms; concurrency=2; cache=r4; quota=within-budget; fixture=pass; rollback=perf-r3` documents a safe canary.

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For cost optimization, see `grammarly-cost-tuning`.
