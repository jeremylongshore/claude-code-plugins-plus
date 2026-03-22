---
name: lucidchart-sdk-patterns
description: |
  Sdk Patterns for Lucidchart.
  Trigger: "lucidchart sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createLucidchartClient({ apiKey: process.env.LUCID_API_KEY });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('Lucidchart error:', e.message);
    return null;
  }
}
```

## Resources
- [Lucidchart SDK](https://developer.lucid.co/reference/overview)

## Next Steps
Apply in `lucidchart-core-workflow-a`.
