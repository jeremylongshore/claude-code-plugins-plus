---
name: openevidence-rate-limits
description: |
  Rate Limits for OpenEvidence.
  Trigger: "openevidence rate limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Rate Limits

## Overview
Handle OpenEvidence rate limits with exponential backoff.

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimited(fn: () => Promise<any>) {
  return queue.add(fn);
}
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-security-basics`.
