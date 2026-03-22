---
name: lucidchart-rate-limits
description: |
  Rate Limits for Lucidchart.
  Trigger: "lucidchart rate limits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Rate Limits

## Overview
Handle Lucidchart rate limits with exponential backoff.

## Implementation
```typescript
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 5, interval: 60_000, intervalCap: 60 });

async function rateLimited(fn: () => Promise<any>) {
  return queue.add(fn);
}
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-security-basics`.
