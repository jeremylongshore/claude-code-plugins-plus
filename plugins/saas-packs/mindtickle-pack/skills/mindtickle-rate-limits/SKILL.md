---
name: mindtickle-rate-limits
description: |
  Rate Limits for MindTickle.
  Trigger: "mindtickle rate limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Rate Limits

## Overview
Handle MindTickle rate limits with exponential backoff.

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimited(fn: () => Promise<any>) {
  return queue.add(fn);
}
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-security-basics`.
