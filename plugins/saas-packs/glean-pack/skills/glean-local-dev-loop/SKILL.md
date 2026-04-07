---
name: glean-local-dev-loop
description: |
  Configure Glean local development with mock search responses, test datasources, and connector development workflow.
  Trigger: "glean dev setup", "glean local development", "glean connector development".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Local Dev Loop

## Overview
Local development workflow for Glean enterprise search API integration. Provides a fast feedback loop with mock search results, connector testing, and document indexing simulation so you can build custom datasource connectors and search UIs without needing a live Glean deployment. Toggle between mock mode for rapid connector iteration and sandbox mode for validating against your Glean instance.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# GLEAN_API_KEY=glean_xxxxxxxxxxxx
# GLEAN_INSTANCE=https://your-company.glean.com
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
  app.use("/api", createProxyMiddleware({
    target: process.env.GLEAN_INSTANCE,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.GLEAN_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3003, () => console.log(`Glean dev server on :3003 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic enterprise search responses
export function mountMockRoutes(app: any) {
  app.post("/api/search", (req: any, res: any) => res.json({
    results: [
      { title: "Q4 Engineering Roadmap", url: "https://wiki.co/roadmap", score: 0.97, datasource: "confluence",
        snippets: [{ snippet: "The <b>roadmap</b> includes migration to..." }] },
      { title: "Onboarding Guide", url: "https://wiki.co/onboard", score: 0.88, datasource: "notion",
        snippets: [{ snippet: "New hire <b>onboarding</b> steps..." }] },
    ],
    totalCount: 2,
  }));
  app.post("/api/index/documents", (req: any, res: any) => res.json({
    status: "OK", documentsIndexed: req.body.documents?.length || 0,
  }));
  app.get("/api/datasources", (_req: any, res: any) => res.json([
    { name: "confluence", displayName: "Confluence", docCount: 1250 },
    { name: "notion", displayName: "Notion", docCount: 430 },
  ]));
}
```

## Testing Workflow
```bash
npm run dev:mock &                    # Start mock server in background
npm run test                          # Unit tests with vitest
npm run test -- --watch               # Watch mode for rapid iteration
MOCK_MODE=false npm run test:integration  # Integration test against real Glean instance
```

## Debug Tips
- Use `curl -X POST http://localhost:3003/api/search -d '{"query":"test"}'` to verify mock search
- Glean connectors must return documents with `id`, `title`, `body.textContent`, and `datasource` fields
- Check connector transform output shape before pushing to the indexing API
- Enable verbose logging on the Glean SDK client to trace API call timing
- Verify OAuth scopes if search returns empty results against a live instance

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key or expired token | Regenerate at Glean admin console |
| `403 Forbidden` | Key lacks indexing scope | Request Indexing API permissions from admin |
| `400 Bad Request` | Malformed document payload | Validate required fields: id, title, body |
| `429 Rate Limited` | Too many indexing requests | Batch documents (max 100 per request) |
| `ECONNREFUSED :3003` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [Glean Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Glean Search API](https://developers.glean.com/api-info/search/getting-started/overview)

## Next Steps
See `glean-debug-bundle`.
