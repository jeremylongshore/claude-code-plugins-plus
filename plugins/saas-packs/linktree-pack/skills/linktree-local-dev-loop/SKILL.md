---
name: linktree-local-dev-loop
description: 'Local Dev Loop for Linktree.

  Trigger: "linktree local dev loop".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree Local Dev Loop

## Overview
Local development workflow for Linktree link-in-bio API integration. Provides a fast feedback loop with mock link profiles, analytics, and appearance data so you can build social management tools without hitting the live Linktree API. Toggle between mock mode for rapid UI iteration and live mode for validating profile updates against the real Linktree platform.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# LINKTREE_API_KEY=lt_xxxxxxxxxxxx
# LINKTREE_BASE_URL=https://api.linktr.ee/v1
# MOCK_MODE=true
npm install express axios dotenv tsx typescript @types/node
npm install -D vitest supertest @types/express
```

## Dev Server
```typescript
// src/dev/server.ts
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
const app = express();
app.use(express.json());
const MOCK = process.env.MOCK_MODE === "true";
if (!MOCK) {
  app.use("/v1", createProxyMiddleware({
    target: process.env.LINKTREE_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.LINKTREE_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3005, () => console.log(`Linktree dev server on :3005 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic link-in-bio profile and analytics responses
export function mountMockRoutes(app: any) {
  app.get("/v1/profile", (_req: any, res: any) => res.json({
    id: "usr_1", username: "janedoe", displayName: "Jane Doe", bio: "Designer & creator",
    links: [
      { id: "lnk_1", title: "Portfolio", url: "https://jane.design", position: 0, enabled: true },
      { id: "lnk_2", title: "Shop", url: "https://shop.jane.design", position: 1, enabled: true },
      { id: "lnk_3", title: "Newsletter", url: "https://jane.substack.com", position: 2, enabled: false },
    ],
  }));
  app.get("/v1/analytics", (_req: any, res: any) => res.json({
    totalViews: 12450, totalClicks: 3280, clickRate: 0.263,
    topLinks: [{ id: "lnk_1", title: "Portfolio", clicks: 1890 }],
  }));
  app.put("/v1/links/:id", (req: any, res: any) => res.json({ id: req.params.id, ...req.body, updatedAt: new Date().toISOString() }));
}
```

## Testing Workflow
```bash
npm run dev:mock &                    # Start mock server in background
npm run test                          # Unit tests with vitest
npm run test -- --watch               # Watch mode for rapid iteration
MOCK_MODE=false npm run test:integration  # Integration test against real API
```

## Debug Tips
- Linktree link ordering is zero-indexed — verify `position` field when reordering
- Analytics endpoints may return `null` for new links with no click data yet
- Use `enabled: false` to test hidden links without deleting them
- Check that `url` values include protocol (`https://`) or the API will reject them
- Rate limits are per-user — test with a dedicated dev account

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate at Linktree developer portal |
| `404 Not Found` | Link ID does not exist | Fetch profile first to verify link IDs |
| `422 Unprocessable` | Missing required field (title or url) | Validate payload before PUT/POST |
| `429 Rate Limited` | Too many requests | Add backoff, switch to mock mode |
| `ECONNREFUSED :3005` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-debug-bundle`.
