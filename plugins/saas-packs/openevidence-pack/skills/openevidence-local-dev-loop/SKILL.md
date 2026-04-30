---
name: openevidence-local-dev-loop
description: 'Local Dev Loop for OpenEvidence.

  Trigger: "openevidence local dev loop".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Local Dev Loop

## Overview
Local development workflow for OpenEvidence clinical decision support API integration. Provides a fast feedback loop with mock evidence queries, citation responses, and clinical summary data so you can build health-tech tools without consuming live API quota. Toggle between mock mode for rapid iteration and sandbox mode for validating against the real OpenEvidence platform. Always use de-identified data in development.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# OPENEVIDENCE_API_KEY=oe_xxxxxxxxxxxx
# OPENEVIDENCE_BASE_URL=https://api.openevidence.com/v1
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
    target: process.env.OPENEVIDENCE_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.OPENEVIDENCE_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3008, () => console.log(`OpenEvidence dev server on :3008 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic clinical decision support responses (de-identified)
export function mountMockRoutes(app: any) {
  app.post("/v1/query", (req: any, res: any) => res.json({
    query: req.body.question,
    answer: "Based on current evidence, first-line treatment for type 2 diabetes includes metformin combined with lifestyle modifications. HbA1c targets should be individualized.",
    citations: [
      { title: "ADA Standards of Care 2025", source: "Diabetes Care", doi: "10.2337/dc25-S009", year: 2025 },
      { title: "Metformin Meta-Analysis", source: "NEJM", doi: "10.1056/NEJMoa2412345", year: 2024 },
    ],
    confidenceScore: 0.92,
  }));
  app.get("/v1/topics", (_req: any, res: any) => res.json([
    { id: "top_1", name: "Diabetes Management", questionCount: 245 },
    { id: "top_2", name: "Hypertension", questionCount: 189 },
    { id: "top_3", name: "Oncology Screening", questionCount: 134 },
  ]));
  app.get("/v1/citations/:doi", (req: any, res: any) => res.json({
    doi: req.params.doi, title: "ADA Standards of Care 2025", abstract: "Annual update to diabetes management guidelines...",
    journal: "Diabetes Care", year: 2025, evidenceLevel: "Level I",
  }));
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
- Never use real patient data in development — all mock data must be de-identified
- `confidenceScore` ranges from 0 to 1 — display as percentage in UI
- Citation DOIs may be null for preprints or conference abstracts
- Query responses can be slow (2-5s) on the live API — set appropriate timeouts
- Use `topics` endpoint to validate query categorization before submitting full queries

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at OpenEvidence developer portal |
| `400 Bad Request` | Empty or malformed query | Validate question field is non-empty string |
| `422 Unprocessable` | Query outside supported medical domains | Check supported topics first |
| `429 Rate Limited` | Too many queries per minute | Add backoff, switch to mock mode |
| `ECONNREFUSED :3008` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps
See `openevidence-debug-bundle`.
