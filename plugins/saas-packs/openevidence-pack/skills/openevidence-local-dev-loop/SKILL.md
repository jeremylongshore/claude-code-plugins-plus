---
name: openevidence-local-dev-loop
description: |
  Local Dev Loop for OpenEvidence.
  Trigger: "openevidence local dev loop".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Local Dev Loop

## Project Structure
```
my-openevidence-app/
├── .env                # OPENEVIDENCE_API_KEY=...
├── src/client.ts       # Singleton
├── tests/fixtures/     # Mock responses
└── scripts/dev.ts
```

## Mock Data
```typescript
export const mockResponse = {
  status: 'success',
  data: { /* mock OpenEvidence response */ }
};
```

## Dev Script
```json
{ "scripts": { "dev": "tsx watch src/index.ts", "test": "vitest" } }
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-sdk-patterns`.
