---
name: linktree-performance-tuning
description: |
  Performance Tuning for Linktree.
  Trigger: "linktree performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Performance Tuning

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
- [Linktree Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-cost-tuning`.
