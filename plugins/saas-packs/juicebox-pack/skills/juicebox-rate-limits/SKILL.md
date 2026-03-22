---
name: juicebox-rate-limits
description: |
  Implement Juicebox rate limiting.
  Trigger: "juicebox rate limit", "juicebox 429", "juicebox throttle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Rate Limits

## Rate Limits by Plan
| Plan | Searches/min | Enrichments/min | Contacts/day |
|------|-------------|-----------------|---------------|
| Starter | 10 | 5 | 100 |
| Professional | 60 | 30 | 1,000 |
| Enterprise | 300 | 100 | 10,000 |

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimitedSearch(query: string) {
  return queue.add(() => client.search({ query, limit: 10 }));
}
```

## Resources
- [Rate Limits](https://docs.juicebox.work/rate-limits)

## Next Steps
See `juicebox-security-basics`.
