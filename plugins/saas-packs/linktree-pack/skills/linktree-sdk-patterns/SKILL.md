---
name: linktree-sdk-patterns
description: |
  Sdk Patterns for Linktree.
  Trigger: "linktree sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createLinktreeClient({ apiKey: process.env.LINKTREE_API_KEY });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('Linktree error:', e.message);
    return null;
  }
}
```

## Resources
- [Linktree SDK](https://linktr.ee/marketplace/developer)

## Next Steps
Apply in `linktree-core-workflow-a`.
