---
name: mindtickle-local-dev-loop
description: |
  Local Dev Loop for MindTickle.
  Trigger: "mindtickle local dev loop".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Local Dev Loop

## Overview
Local development workflow for MindTickle sales enablement and readiness API integration. Provides a fast feedback loop with mock training modules, user progress, and coaching data so you can build sales readiness dashboards without needing a live MindTickle instance. Toggle between mock mode for rapid iteration and sandbox mode for validating against the real MindTickle platform.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# MINDTICKLE_API_KEY=mt_xxxxxxxxxxxx
# MINDTICKLE_BASE_URL=https://api.mindtickle.com/v2
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
  app.use("/v2", createProxyMiddleware({
    target: process.env.MINDTICKLE_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.MINDTICKLE_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3007, () => console.log(`MindTickle dev server on :3007 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic sales enablement training data
export function mountMockRoutes(app: any) {
  app.get("/v2/modules", (_req: any, res: any) => res.json([
    { id: "mod_1", title: "Q4 Product Launch", type: "course", status: "published", enrolledCount: 85, completionRate: 0.72 },
    { id: "mod_2", title: "Objection Handling", type: "coaching", status: "published", enrolledCount: 120, completionRate: 0.58 },
  ]));
  app.get("/v2/users/:id/progress", (req: any, res: any) => res.json({
    userId: req.params.id, completedModules: 8, totalModules: 12, averageScore: 82,
    recentActivity: [{ moduleId: "mod_1", score: 91, completedAt: "2025-09-10T15:30:00Z" }],
  }));
  app.get("/v2/leaderboard", (_req: any, res: any) => res.json({
    topPerformers: [
      { userId: "usr_1", name: "Sarah Kim", score: 95, modulesCompleted: 12 },
      { userId: "usr_2", name: "James Park", score: 88, modulesCompleted: 10 },
    ],
  }));
  app.post("/v2/coaching/sessions", (req: any, res: any) => res.status(201).json({ id: "cs_1", ...req.body, status: "scheduled" }));
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
- MindTickle user IDs are org-scoped — IDs from one org will 404 on another
- Progress endpoints return `null` for users who have not started any modules
- Coaching session creation requires both `coachId` and `learnerId` fields
- Use `/v2/modules?status=draft` to test against unpublished content without affecting live users
- Check `completionRate` is a decimal (0.72) not a percentage (72) when building dashboards

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at MindTickle admin console |
| `403 Forbidden` | Key lacks admin scope | Request API access from MindTickle CSM |
| `404 Not Found` | User or module ID invalid | Fetch list endpoints to verify IDs |
| `429 Rate Limited` | Too many requests | Add exponential backoff, use mock mode |
| `ECONNREFUSED :3007` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-debug-bundle`.
