---
name: appfolio-rate-limits
description: |
  Handle AppFolio API rate limits with throttling and backoff.
  Trigger: "appfolio rate limit".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio rate limits | sed 's/\b\(.\)/\u\1/g'

## Overview
AppFolio API enforces rate limits per partner. Implement throttling to stay within limits.

## Rate Limit Handler
```typescript
import Bottleneck from "bottleneck";

const limiter = new Bottleneck({
  maxConcurrent: 5,
  minTime: 200,  // 5 requests/second max
});

async function throttledRequest(client: any, path: string) {
  return limiter.schedule(() => client.http.get(path));
}

// 429 retry
async function withRetry(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 1; i <= maxRetries; i++) {
    try { return await fn(); }
    catch (err: any) {
      if (err.response?.status !== 429 || i === maxRetries) throw err;
      const delay = Math.min(1000 * Math.pow(2, i), 30000);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
