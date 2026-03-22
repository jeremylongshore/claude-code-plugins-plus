---
name: onenote-performance-tuning
description: |
  Performance Tuning for OneNote.
  Trigger: "onenote performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Performance Tuning

## Caching
```typescript
const cache = new Map();
async function cached(key: string, fn: () => Promise<any>) {
  const c = cache.get(key);
  if (c?.expiry > Date.now()) return c.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + 300_000 });
  return data;
}
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-cost-tuning`.
