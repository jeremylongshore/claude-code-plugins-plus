---
name: mindtickle-sdk-patterns
description: |
  Sdk Patterns for MindTickle.
  Trigger: "mindtickle sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createMindTickleClient({ apiKey: process.env.MINDTICKLE_API_KEY });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('MindTickle error:', e.message);
    return null;
  }
}
```

## Resources
- [MindTickle SDK](https://www.mindtickle.com/platform/integrations/)

## Next Steps
Apply in `mindtickle-core-workflow-a`.
