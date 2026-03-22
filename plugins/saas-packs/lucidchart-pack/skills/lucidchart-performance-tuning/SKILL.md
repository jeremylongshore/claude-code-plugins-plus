---
name: lucidchart-performance-tuning
description: |
  Performance Tuning for Lucidchart.
  Trigger: "lucidchart performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Performance Tuning

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
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-cost-tuning`.
