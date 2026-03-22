---
name: openevidence-sdk-patterns
description: |
  Sdk Patterns for OpenEvidence.
  Trigger: "openevidence sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createOpenEvidenceClient({ apiKey: process.env.OPENEVIDENCE_API_KEY });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('OpenEvidence error:', e.message);
    return null;
  }
}
```

## Resources
- [OpenEvidence SDK](https://www.openevidence.com)

## Next Steps
Apply in `openevidence-core-workflow-a`.
