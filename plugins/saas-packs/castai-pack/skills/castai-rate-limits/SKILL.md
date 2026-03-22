---
name: castai-rate-limits
description: |
  Handle CAST AI API rate limits with backoff and request queuing.
  Use when hitting 429 errors, optimizing API call patterns,
  or implementing rate-aware batch operations.
  Trigger with phrases like "cast ai rate limit", "cast ai 429",
  "cast ai throttle", "cast ai API limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Rate Limits

## Overview

The CAST AI REST API enforces rate limits per API key. The autoscaler agent communicates cluster state at 15-second intervals. For custom API integrations, implement exponential backoff and request queuing to avoid hitting limits.

## Prerequisites

- CAST AI API key configured
- Understanding of the API endpoints you call

## Rate Limit Behavior

| Aspect | Value |
|--------|-------|
| Rate limit scope | Per API key |
| Response on limit | HTTP 429 with `Retry-After` header |
| Agent sync interval | Every 15 seconds |
| Recommended polling | No more than once per 30 seconds |

## Instructions

### Step 1: Detect Rate Limits from Response Headers

```typescript
async function castaiRequest(path: string): Promise<Response> {
  const response = await fetch(`https://api.cast.ai${path}`, {
    headers: { "X-API-Key": process.env.CASTAI_API_KEY! },
  });

  // Log rate limit headers for monitoring
  const remaining = response.headers.get("X-RateLimit-Remaining");
  const reset = response.headers.get("X-RateLimit-Reset");
  if (remaining) {
    console.log(`Rate limit remaining: ${remaining}, resets: ${reset}`);
  }

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get("Retry-After") ?? "5");
    throw new RateLimitError(retryAfter);
  }

  return response;
}

class RateLimitError extends Error {
  constructor(public retryAfterSeconds: number) {
    super(`Rate limited. Retry after ${retryAfterSeconds}s`);
  }
}
```

### Step 2: Exponential Backoff with Jitter

```typescript
async function withBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;

      let delayMs: number;
      if (err instanceof RateLimitError) {
        delayMs = err.retryAfterSeconds * 1000;
      } else {
        delayMs = Math.min(1000 * Math.pow(2, attempt), 30000);
      }
      // Add jitter to prevent thundering herd
      delayMs += Math.random() * 1000;

      console.log(`Retry ${attempt + 1}/${maxRetries} in ${delayMs}ms`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Request Queue for Batch Operations

```typescript
import PQueue from "p-queue";

// Limit concurrent requests and enforce interval
const castaiQueue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 5,   // Max 5 requests per second
});

async function queuedCastAIRequest<T>(fn: () => Promise<T>): Promise<T> {
  return castaiQueue.add(() => withBackoff(fn));
}

// Batch process multiple clusters
const clusterIds = ["id1", "id2", "id3", "id4", "id5"];
const savings = await Promise.all(
  clusterIds.map((id) =>
    queuedCastAIRequest(() =>
      fetch(`https://api.cast.ai/v1/kubernetes/clusters/${id}/savings`, {
        headers: { "X-API-Key": process.env.CASTAI_API_KEY! },
      }).then((r) => r.json())
    )
  )
);
```

### Step 4: Polling Best Practice

```typescript
// Do NOT poll faster than 30 seconds for cluster state
// The agent syncs every 15s; polling faster adds no value

async function pollClusterStatus(
  clusterId: string,
  intervalMs = 30000
): Promise<void> {
  const timer = setInterval(async () => {
    try {
      const status = await queuedCastAIRequest(() =>
        fetch(
          `https://api.cast.ai/v1/kubernetes/external-clusters/${clusterId}`,
          { headers: { "X-API-Key": process.env.CASTAI_API_KEY! } }
        ).then((r) => r.json())
      );
      console.log(`Cluster ${clusterId}: ${status.agentStatus}`);
    } catch (err) {
      console.error("Poll failed:", err);
    }
  }, intervalMs);
}
```

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| 429 with Retry-After | Check header | Wait exact duration |
| 429 without header | Status code only | Exponential backoff from 1s |
| 5xx errors | Status >= 500 | Retry up to 3 times |
| Connection timeout | Fetch throws | Retry with longer timeout |

## Resources

- [CAST AI API Reference](https://api.cast.ai/v1/spec/openapi.json)
- [p-queue](https://github.com/sindresorhus/p-queue) -- concurrent request queue

## Next Steps

For security configuration, see `castai-security-basics`.
