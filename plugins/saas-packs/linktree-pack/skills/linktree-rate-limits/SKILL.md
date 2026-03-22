---
name: linktree-rate-limits
description: |
  Rate Limits for Linktree.
  Trigger: "linktree rate limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Rate Limits

## Overview
Handle Linktree rate limits with exponential backoff.

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimited(fn: () => Promise<any>) {
  return queue.add(fn);
}
```

## Resources
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-security-basics`.
