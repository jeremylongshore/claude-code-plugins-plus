---
name: onenote-local-dev-loop
description: |
  Local Dev Loop for OneNote.
  Trigger: "onenote local dev loop".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Local Dev Loop

## Project Structure
```
my-onenote-app/
├── .env                # MICROSOFT_GRAPH_TOKEN=...
├── src/client.ts       # Singleton
├── tests/fixtures/     # Mock responses
└── scripts/dev.ts
```

## Mock Data
```typescript
export const mockResponse = {
  status: 'success',
  data: { /* mock OneNote response */ }
};
```

## Dev Script
```json
{ "scripts": { "dev": "tsx watch src/index.ts", "test": "vitest" } }
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-sdk-patterns`.
