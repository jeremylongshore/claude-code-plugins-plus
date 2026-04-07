---
name: appfolio-local-dev-loop
description: |
  Set up local development for AppFolio property management API integration.
  Trigger: "appfolio local dev".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Local Dev Loop

## Overview
Local development workflow for AppFolio property management API integration. Provides a fast feedback loop with mock property, tenant, and lease endpoints so you can build and test integrations without consuming live API quota. Toggle between mock mode for rapid iteration and sandbox mode for pre-deployment validation against the real AppFolio Stack API.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# APPFOLIO_API_KEY=af_live_xxxxxxxxxxxx
# APPFOLIO_BASE_URL=https://api.appfolio.com/api/v1
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
  app.use("/api/v1", createProxyMiddleware({
    target: process.env.APPFOLIO_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.APPFOLIO_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3001, () => console.log(`AppFolio dev server on :3001 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic property management responses
export function mountMockRoutes(app: any) {
  app.get("/api/v1/properties", (_req: any, res: any) => res.json([
    { id: "prop_1", name: "Sunset Apartments", address: { street: "123 Sunset Blvd", city: "Los Angeles", state: "CA" }, property_type: "residential", unit_count: 24 },
    { id: "prop_2", name: "Downtown Office", address: { street: "456 Main St", city: "San Francisco", state: "CA" }, property_type: "commercial", unit_count: 8 },
  ]));
  app.get("/api/v1/tenants", (_req: any, res: any) => res.json([
    { id: "t1", first_name: "Jane", last_name: "Smith", email: "jane@example.com", unit_id: "u1", lease_id: "l1" },
  ]));
  app.get("/api/v1/leases", (_req: any, res: any) => res.json([
    { id: "l1", unit_id: "u1", start_date: "2025-01-01", end_date: "2026-01-01", rent_amount: 2500, status: "active" },
  ]));
  app.post("/api/v1/work-orders", (req: any, res: any) => res.status(201).json({ id: "wo_1", ...req.body, status: "open" }));
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
- Set `DEBUG=express:*` to trace all route matching and middleware execution
- Use `curl -v http://localhost:3001/api/v1/properties` to inspect raw responses
- Check `X-RateLimit-Remaining` header when testing against the live API
- AppFolio sandbox returns `403` for properties you do not own — verify your API key scope
- Enable `axios` interceptors to log request/response pairs during development

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate at AppFolio Stack portal |
| `403 Forbidden` | Key lacks scope for endpoint | Request additional permissions |
| `404 Not Found` | Wrong property ID or path | Verify resource exists in sandbox |
| `429 Too Many Requests` | Rate limit exceeded | Add exponential backoff, use mock mode |
| `ECONNREFUSED :3001` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps
See `appfolio-debug-bundle`.
