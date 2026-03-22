---
name: juicebox-local-dev-loop
description: |
  Configure Juicebox local dev workflow.
  Trigger: "juicebox local dev", "juicebox dev setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Local Dev Loop

## Project Structure
```
my-juicebox-app/
├── .env                    # JUICEBOX_API_KEY=jb_live_...
├── src/client.ts           # Singleton
├── src/searches/           # Query definitions
├── tests/fixtures/         # Mock results
└── scripts/dev.ts
```

## Mock Data
```typescript
export const mockSearch = {
  total: 150,
  profiles: [{ id: 'prof_1', name: 'Jane Smith', title: 'Engineer', company: 'Google' }]
};
```

## Cost Control
```typescript
const limit = process.env.NODE_ENV === 'development' ? 5 : 50;
const results = await client.search({ query, limit });
```

## Resources
- [Juicebox Docs](https://docs.juicebox.work)

## Next Steps
See `juicebox-sdk-patterns`.
