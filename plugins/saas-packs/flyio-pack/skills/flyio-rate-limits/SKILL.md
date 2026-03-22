---
name: flyio-rate-limits
description: |
  Handle Fly.io Machines API rate limits with backoff, concurrency control,
  and request batching for machine management operations.
  Trigger: "fly.io rate limit", "fly.io 429", "fly.io throttling", "machines API limit".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Rate Limits

## Overview

The Fly.io Machines API has rate limits per organization. Machine create/update/delete operations are more tightly limited than read operations. The API returns 429 with `Retry-After` header when limits are exceeded.

## Key Limits

| Operation | Approximate Limit | Scope |
|-----------|-------------------|-------|
| Machine create/delete | ~10/minute | Per org |
| Machine start/stop | ~30/minute | Per org |
| List/get machines | ~60/minute | Per org |
| App operations | ~20/minute | Per org |

## Instructions

### Retry with Exponential Backoff

```typescript
async function flyApiWithRetry<T>(
  fn: () => Promise<Response>,
  maxRetries = 4
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fn();
    if (res.ok) return res.json();

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '10');
      const delay = retryAfter * 1000 + Math.random() * 2000;
      console.log(`Rate limited. Retry in ${(delay / 1000).toFixed(0)}s`);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
      continue;
    }

    throw new Error(`Fly API ${res.status}: ${await res.text()}`);
  }
  throw new Error('Max retries exceeded');
}
```

### Batch Machine Operations

```typescript
import PQueue from 'p-queue';

// Limit concurrent machine operations
const flyQueue = new PQueue({ concurrency: 3, interval: 10000, intervalCap: 10 });

async function batchCreateMachines(configs: Array<{ region: string; config: any }>) {
  return Promise.all(
    configs.map(c => flyQueue.add(() =>
      flyApiWithRetry(() => fetch(`${FLY_API}/v1/apps/${app}/machines`, {
        method: 'POST', headers,
        body: JSON.stringify(c),
      }))
    ))
  );
}
```

## Resources

- [Machines API](https://fly.io/docs/machines/api/)

## Next Steps

For security, see `flyio-security-basics`.
