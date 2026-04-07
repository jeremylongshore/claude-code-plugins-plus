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

## Overview
Local development workflow for Juicebox AI-powered people analysis and recruiting API integration. Provides a fast feedback loop with mock profile search results and candidate enrichment data so you can build talent pipeline tools without consuming live API credits. Toggle between mock mode for rapid iteration and sandbox mode for validating against the real Juicebox API.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# JUICEBOX_API_KEY=jb_live_xxxxxxxxxxxx
# JUICEBOX_BASE_URL=https://api.juicebox.work/v1
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
    target: process.env.JUICEBOX_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.JUICEBOX_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3004, () => console.log(`Juicebox dev server on :3004 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic people search and enrichment responses
export function mountMockRoutes(app: any) {
  app.post("/v1/search", (req: any, res: any) => res.json({
    total: 150,
    profiles: [
      { id: "prof_1", name: "Jane Smith", title: "Senior Engineer", company: "Google", location: "San Francisco, CA", skills: ["TypeScript", "React", "GCP"] },
      { id: "prof_2", name: "Alex Chen", title: "Staff ML Engineer", company: "Meta", location: "New York, NY", skills: ["Python", "PyTorch", "MLOps"] },
    ],
  }));
  app.get("/v1/profiles/:id", (req: any, res: any) => res.json({
    id: req.params.id, name: "Jane Smith", title: "Senior Engineer", company: "Google",
    experience: [{ role: "Senior Engineer", company: "Google", years: 3 }],
    education: [{ school: "MIT", degree: "BS Computer Science" }],
  }));
  app.get("/v1/usage", (_req: any, res: any) => res.json({ creditsUsed: 12, creditsRemaining: 488, plan: "starter" }));
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
- Set search `limit` to 5 in development to avoid burning API credits
- Use `/v1/usage` endpoint to monitor credit consumption before switching off mock mode
- Juicebox search queries are natural language — test with specific role titles for better results
- Check `profiles[].skills` array for null values that can break filtering logic
- Log the full request payload to verify boolean filters are serialized correctly

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at Juicebox dashboard |
| `402 Payment Required` | Credits exhausted | Upgrade plan or wait for monthly reset |
| `400 Bad Request` | Malformed search query | Validate query structure before sending |
| `429 Rate Limited` | Too many requests per minute | Add exponential backoff, use mock mode |
| `ECONNREFUSED :3004` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [Juicebox API Docs](https://docs.juicebox.work)

## Next Steps
See `juicebox-debug-bundle`.
