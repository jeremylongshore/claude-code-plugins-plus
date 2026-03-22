---
name: hex-rate-limits
description: |
  Implement Hex rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Hex.
  Trigger with phrases like "hex rate limit", "hex throttling",
  "hex 429", "hex retry", "hex backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Rate Limits

## Rate Limits

| Endpoint | Per Minute | Per Hour |
|----------|-----------|----------|
| RunProject | 20 | 60 |
| GetRunStatus | No hard limit | - |
| ListProjects | No hard limit | - |
| CancelRun | No hard limit | - |

## Instructions

### Queue-Based Run Triggering

```typescript
import PQueue from 'p-queue';

const hexQueue = new PQueue({
  concurrency: 1,
  interval: 60000,   // Per minute
  intervalCap: 15,   // Leave buffer (limit is 20)
});

let hourlyCount = 0;
setInterval(() => { hourlyCount = 0; }, 3600000);

async function queuedRun(client: HexClient, projectId: string, params: any) {
  if (hourlyCount >= 55) throw new Error('Approaching hourly limit');
  return hexQueue.add(async () => {
    hourlyCount++;
    return client.runProject(projectId, params);
  });
}
```

### Backoff on 429

```typescript
async function runWithBackoff(client: HexClient, projectId: string, params: any) {
  for (let i = 0; i < 3; i++) {
    try { return await client.runProject(projectId, params); }
    catch (err: any) {
      if (!err.message.includes('429')) throw err;
      const delay = 30000 * Math.pow(2, i);
      console.log(`Rate limited, waiting ${delay / 1000}s`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

## Resources

- [Hex API](https://learn.hex.tech/docs/api/api-overview)
