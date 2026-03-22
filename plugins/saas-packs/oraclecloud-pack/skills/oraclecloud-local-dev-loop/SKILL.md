---
name: oraclecloud-local-dev-loop
description: |
  Local Dev Loop for Oracle Cloud.
  Trigger: "oraclecloud local dev loop".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Local Dev Loop

## Project Structure
```
my-oraclecloud-app/
├── .env                # OCI_CONFIG_FILE=...
├── src/client.ts       # Singleton
├── tests/fixtures/     # Mock responses
└── scripts/dev.ts
```

## Mock Data
```typescript
export const mockResponse = {
  status: 'success',
  data: { /* mock Oracle Cloud response */ }
};
```

## Dev Script
```json
{ "scripts": { "dev": "tsx watch src/index.ts", "test": "vitest" } }
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-sdk-patterns`.
