---
name: oraclecloud-sdk-patterns
description: |
  Sdk Patterns for Oracle Cloud.
  Trigger: "oraclecloud sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud SDK Patterns

## Singleton Client
```typescript
let instance: any = null;
export function getClient() {
  if (!instance) instance = createOracleCloudClient({ apiKey: process.env.OCI_CONFIG_FILE });
  return instance;
}
```

## Error Wrapper
```typescript
async function safe<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    console.error('Oracle Cloud error:', e.message);
    return null;
  }
}
```

## Resources
- [Oracle Cloud SDK](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
Apply in `oraclecloud-core-workflow-a`.
