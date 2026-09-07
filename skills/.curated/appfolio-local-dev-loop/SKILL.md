---
name: appfolio-local-dev-loop
description: 'Set up local development for AppFolio property management API integration.

  Trigger: "appfolio local dev".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Local Dev Loop

## Overview

Local development workflow for AppFolio property management API integration. Provides a fast feedback loop with mock property, tenant, and lease endpoints so you can build and test integrations without consuming live API quota. Toggle between mock mode for rapid iteration and sandbox mode for pre-deployment validation against the real AppFolio Stack API.

## Prerequisites

- A mock-only local environment with synthetic property, tenant, lease, and
  work-order fixtures that contain no production addresses, names, or payments.
- A separately managed sandbox credential and an approved safe-read fixture for
  the dedicated integration lane; it is never loaded by the local dev server.
- A log policy that records request shape and status only, plus an explicit
  owner for sandbox quota, fixture reset, and credential rotation.

## Instructions

1. Run the local server only in mock mode and exercise reads/writes against
   synthetic routes with deterministic fixtures.
2. Test request validation, idempotency, redaction, and error handling in unit
   tests before any sandbox connectivity check.
3. Run the sandbox lane separately with the contract-bound managed client and
   one authorized safe-read fixture; do not turn a local proxy into a live API
   tunnel.
4. Stop when the fixture, credentials, request budget, or output redaction is
   unverified, then correct the environment before continuing.

## Environment Setup

```bash
cp .env.example .env
# Leave provider credentials blank locally. Mock mode is the default.
# MOCK_MODE=true
npm install express axios dotenv tsx typescript @types/node
npm install -D vitest supertest @types/express
```

## Dev Server

```typescript
// src/dev/server.ts
import express from "express";
const app = express();
app.use(express.json());
const MOCK = process.env.MOCK_MODE === "true";
if (!MOCK) throw new Error("Local server is mock-only; use the managed sandbox integration lane");
const { mountMockRoutes } = require("./mocks");
mountMockRoutes(app);
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
npm run test:sandbox                     # Managed, read-only sandbox lane
```

## Debug Tips

- Set `DEBUG=express:*` to trace all route matching and middleware execution
- Use local test assertions for fixture counts and schema shape, not raw tenant payload dumps
- Check `X-RateLimit-Remaining` header when testing against the live API
- AppFolio sandbox returns `403` for properties you do not own — verify your API key scope
- Use interceptors only for redacted endpoint/status/count telemetry during development

## Output

- A deterministic mock-only local server with synthetic property-management
  fixtures and no provider credential dependency
- Unit-test evidence for validation, idempotency, and PII-safe observability
- A separate managed sandbox result containing only redacted safe-read status

## Examples

For a work-order UI change, add a synthetic mock fixture and test the request
schema plus duplicate-submission behavior locally. Assert the returned ID and
status without emitting the request body or tenant record. After unit tests
pass, run the dedicated sandbox lane against one approved safe-read fixture.
If mock mode is disabled, a sandbox credential appears locally, or a response
contains unredacted tenant fields, stop the run and restore the local boundary.

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
