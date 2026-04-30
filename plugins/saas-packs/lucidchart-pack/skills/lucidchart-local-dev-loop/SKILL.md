---
name: lucidchart-local-dev-loop
description: 'Local Dev Loop for Lucidchart.

  Trigger: "lucidchart local dev loop".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Local Dev Loop

## Overview
Local development workflow for Lucidchart diagramming API integration. Provides a fast feedback loop with mock document, page, and shape data so you can build diagram automation tools without needing a live Lucid account. Toggle between mock mode for rapid iteration and sandbox mode for validating diagram CRUD operations against the real Lucid API.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# LUCID_API_KEY=lucid_xxxxxxxxxxxx
# LUCID_BASE_URL=https://api.lucid.co/v1
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
    target: process.env.LUCID_BASE_URL,
    changeOrigin: true,
    headers: { "Lucid-Api-Key": process.env.LUCID_API_KEY! },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3006, () => console.log(`Lucidchart dev server on :3006 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic diagramming document and shape responses
export function mountMockRoutes(app: any) {
  app.get("/v1/documents", (_req: any, res: any) => res.json([
    { id: "doc_1", title: "System Architecture", pageCount: 3, createdAt: "2025-06-01T10:00:00Z", owner: "jane@co.com" },
    { id: "doc_2", title: "Data Flow Diagram", pageCount: 1, createdAt: "2025-07-15T14:30:00Z", owner: "alex@co.com" },
  ]));
  app.get("/v1/documents/:id/pages", (req: any, res: any) => res.json([
    { id: "pg_1", title: "Overview", index: 0, shapes: 12 },
    { id: "pg_2", title: "Detail View", index: 1, shapes: 24 },
  ]));
  app.get("/v1/documents/:id/pages/:pageId/shapes", (_req: any, res: any) => res.json([
    { id: "sh_1", type: "rectangle", text: "API Gateway", x: 100, y: 50, width: 200, height: 80 },
    { id: "sh_2", type: "diamond", text: "Auth Check", x: 100, y: 200, width: 120, height: 120 },
  ]));
  app.post("/v1/documents", (req: any, res: any) => res.status(201).json({ id: "doc_new", ...req.body, createdAt: new Date().toISOString() }));
}
```

## Testing Workflow
```bash
npm run dev:mock &                    # Start mock server in background
npm run test                          # Unit tests with vitest
npm run test -- --watch               # Watch mode for rapid iteration
MOCK_MODE=false npm run test:integration  # Integration test against real Lucid API
```

## Debug Tips
- Lucid uses `Lucid-Api-Key` header (not `Authorization: Bearer`) for API authentication
- Shape coordinates use absolute pixel positioning — verify x/y values when programmatically placing shapes
- Document IDs are opaque strings — never hardcode them across environments
- Use the `/v1/documents/:id/export` endpoint to generate PNG/PDF previews for visual regression tests
- Check OAuth scopes if document list returns empty despite having documents

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at developer.lucid.co |
| `403 Forbidden` | Key lacks document scope | Request additional OAuth scopes |
| `404 Not Found` | Document or page ID invalid | Fetch document list to verify IDs |
| `413 Payload Too Large` | Too many shapes in single request | Batch shape creation (max 50 per call) |
| `ECONNREFUSED :3006` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [Lucid Developer Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-debug-bundle`.
