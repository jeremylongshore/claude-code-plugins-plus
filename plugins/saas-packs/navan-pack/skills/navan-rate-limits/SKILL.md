---
name: navan-rate-limits
description: |
  Rate Limits for Navan.
  Trigger: "navan rate limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Rate Limits

## Overview
Handle Navan rate limits with exponential backoff.

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimited(fn: () => Promise<any>) {
  return queue.add(fn);
}
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-security-basics`.
