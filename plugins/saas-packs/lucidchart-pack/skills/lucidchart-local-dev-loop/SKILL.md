---
name: lucidchart-local-dev-loop
description: |
  Local Dev Loop for Lucidchart.
  Trigger: "lucidchart local dev loop".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Local Dev Loop

## Project Structure
```
my-lucidchart-app/
├── .env                # LUCID_API_KEY=...
├── src/client.ts       # Singleton
├── tests/fixtures/     # Mock responses
└── scripts/dev.ts
```

## Mock Data
```typescript
export const mockResponse = {
  status: 'success',
  data: { /* mock Lucidchart response */ }
};
```

## Dev Script
```json
{ "scripts": { "dev": "tsx watch src/index.ts", "test": "vitest" } }
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-sdk-patterns`.
