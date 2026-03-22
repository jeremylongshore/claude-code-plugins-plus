---
name: onenote-sdk-patterns
description: |
  Sdk Patterns for OneNote.
  Trigger: "onenote sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createOneNoteClient({ apiKey: process.env.MICROSOFT_GRAPH_TOKEN });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('OneNote error:', e.message);
    return null;
  }
}
```

## Resources
- [OneNote SDK](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
Apply in `onenote-core-workflow-a`.
