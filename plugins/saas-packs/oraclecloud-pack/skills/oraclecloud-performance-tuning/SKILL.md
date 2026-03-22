---
name: oraclecloud-performance-tuning
description: |
  Performance Tuning for Oracle Cloud.
  Trigger: "oraclecloud performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Performance Tuning

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
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-cost-tuning`.
