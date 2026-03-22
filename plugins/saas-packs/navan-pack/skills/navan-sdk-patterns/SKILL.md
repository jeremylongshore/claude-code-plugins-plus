---
name: navan-sdk-patterns
description: |
  Sdk Patterns for Navan.
  Trigger: "navan sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createNavanClient({ apiKey: process.env.NAVAN_API_KEY });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('Navan error:', e.message);
    return null;
  }
}
```

## Resources
- [Navan SDK](https://app.navan.com/app/helpcenter)

## Next Steps
Apply in `navan-core-workflow-a`.
