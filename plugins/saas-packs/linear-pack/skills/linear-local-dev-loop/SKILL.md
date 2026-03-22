---
name: linear-local-dev-loop
description: |
  Set up local Linear development environment and testing workflow.
  Use when configuring local dev, testing integrations,
  or setting up a development workflow with Linear webhooks.
  Trigger: "linear local development", "linear dev setup",
  "test linear locally", "linear development environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, testing, workflow]

---
# Linear Local Dev Loop

## Overview
Set up an efficient local development workflow for building Linear integrations. Covers project scaffolding, environment config, test utilities, webhook tunneling with ngrok, and integration testing with vitest.

## Prerequisites
- Node.js 18+ with TypeScript
- `@linear/sdk` package
- Separate Linear workspace or team for development (recommended)
- ngrok or cloudflared for webhook tunnel testing

## Instructions

### Step 1: Project Scaffolding
```bash
set -euo pipefail
mkdir linear-integration && cd linear-integration
npm init -y
npm install @linear/sdk dotenv
npm install -D typescript @types/node vitest tsx

# TypeScript config
npx tsc --init --target ES2022 --module NodeNext --moduleResolution NodeNext --strict
```

### Step 2: Environment Configuration
```bash
# .env (never commit)
cat > .env << 'EOF'
LINEAR_API_KEY=lin_api_dev_xxxxxxxxxxxx
LINEAR_WEBHOOK_SECRET=whsec_dev_xxxxxxxxxxxx
LINEAR_DEV_TEAM_KEY=DEV
NODE_ENV=development
EOF

# .env.example (commit this for onboarding)
cat > .env.example << 'EOF'
LINEAR_API_KEY=lin_api_your_key_here
LINEAR_WEBHOOK_SECRET=
LINEAR_DEV_TEAM_KEY=DEV
NODE_ENV=development
EOF

echo -e ".env\n.env.local\n.env.*.local" >> .gitignore
```

### Step 3: Client Module with Connection Verification
```typescript
// src/client.ts
import { LinearClient } from "@linear/sdk";
import "dotenv/config";

let _client: LinearClient | null = null;

export function getClient(): LinearClient {
  if (!_client) {
    const apiKey = process.env.LINEAR_API_KEY;
    if (!apiKey) throw new Error("LINEAR_API_KEY not set — copy .env.example to .env");
    _client = new LinearClient({ apiKey });
  }
  return _client;
}

export async function verifyConnection(): Promise<void> {
  const client = getClient();
  const viewer = await client.viewer;
  const teams = await client.teams();
  console.log(`[Linear] Connected as ${viewer.name} (${viewer.email})`);
  console.log(`[Linear] Teams: ${teams.nodes.map(t => t.key).join(", ")}`);
}
```

### Step 4: Test Data Utilities
```typescript
// src/test-utils.ts
import { getClient } from "./client";

const TEST_PREFIX = "[DEV-TEST]";

export async function getDevTeam() {
  const client = getClient();
  const teamKey = process.env.LINEAR_DEV_TEAM_KEY ?? "DEV";
  const teams = await client.teams({ filter: { key: { eq: teamKey } } });
  const team = teams.nodes[0];
  if (!team) throw new Error(`Team ${teamKey} not found — set LINEAR_DEV_TEAM_KEY`);
  return team;
}

export async function createTestIssue(title?: string) {
  const client = getClient();
  const team = await getDevTeam();
  const result = await client.createIssue({
    teamId: team.id,
    title: `${TEST_PREFIX} ${title ?? new Date().toISOString()}`,
    description: "Automated test issue — safe to delete",
    priority: 4, // Low
  });
  return result.issue;
}

export async function cleanupTestIssues() {
  const client = getClient();
  const team = await getDevTeam();
  const issues = await client.issues({
    filter: {
      team: { id: { eq: team.id } },
      title: { startsWith: TEST_PREFIX },
    },
    first: 100,
  });

  let deleted = 0;
  for (const issue of issues.nodes) {
    await issue.delete();
    deleted++;
  }
  console.log(`Cleaned up ${deleted} test issues`);
}
```

### Step 5: Integration Tests with Vitest
```typescript
// tests/linear.integration.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { getClient } from "../src/client";
import { createTestIssue, cleanupTestIssues, getDevTeam } from "../src/test-utils";

describe("Linear Integration", () => {
  afterAll(async () => {
    await cleanupTestIssues();
  });

  it("authenticates successfully", async () => {
    const client = getClient();
    const viewer = await client.viewer;
    expect(viewer.name).toBeDefined();
    expect(viewer.email).toBeDefined();
  });

  it("creates and updates an issue", async () => {
    const client = getClient();
    const issue = await createTestIssue("vitest create");
    expect(issue).toBeDefined();
    expect(issue?.title).toContain("[DEV-TEST]");

    // Update it
    await client.updateIssue(issue!.id, { priority: 2 });
    const updated = await client.issue(issue!.id);
    expect(updated.priority).toBe(2);
  });

  it("queries workflow states", async () => {
    const team = await getDevTeam();
    const states = await team.states();
    const types = states.nodes.map(s => s.type);
    expect(types).toContain("unstarted");
    expect(types).toContain("completed");
  });
});
```

### Step 6: Package Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "verify": "tsx src/verify-connection.ts",
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "cleanup": "tsx src/cleanup.ts"
  }
}
```

### Step 7: Webhook Local Development with ngrok
```bash
# Terminal 1: Start your webhook server
npm run dev

# Terminal 2: Expose port 3000 via ngrok
ngrok http 3000
# Copy the https://xxxx.ngrok-free.app URL

# Register webhook in Linear:
# Settings > API > Webhooks > New webhook
# URL: https://xxxx.ngrok-free.app/webhooks/linear
# Select: Issues, Comments
```

Minimal webhook receiver for local testing:
```typescript
// src/webhook-dev.ts
import express from "express";
import crypto from "crypto";

const app = express();
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  const body = req.body.toString();
  const sig = req.headers["linear-signature"] as string;
  const secret = process.env.LINEAR_WEBHOOK_SECRET!;

  if (secret && sig) {
    const expected = crypto.createHmac("sha256", secret).update(body).digest("hex");
    if (sig !== expected) {
      console.warn("Signature mismatch — check LINEAR_WEBHOOK_SECRET");
    }
  }

  const event = JSON.parse(body);
  console.log(`[Webhook] ${event.type}.${event.action}:`, event.data?.identifier ?? event.data?.id);
  res.json({ ok: true });
});

app.listen(3000, () => console.log("Webhook server on http://localhost:3000"));
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `LINEAR_API_KEY not set` | Missing .env | Copy `.env.example` to `.env` and fill in values |
| `Team DEV not found` | Wrong team key | Set `LINEAR_DEV_TEAM_KEY` to a valid team key |
| `Cannot find module` | TypeScript path issue | Check `tsconfig.json` module resolution |
| Webhook not received | Tunnel not running | Start `ngrok http 3000` and register the URL |
| `Authentication required` | Expired dev API key | Regenerate in Linear Settings > Account > API |

## Examples

### Quick Connection Test Script
```typescript
// src/verify-connection.ts
import { verifyConnection } from "./client";
verifyConnection()
  .then(() => console.log("Connection OK"))
  .catch((err) => { console.error("Connection FAILED:", err.message); process.exit(1); });
```

## Resources
- [Linear SDK Documentation](https://linear.app/developers/sdk)
- [Linear Webhooks](https://linear.app/developers/webhooks)
- [Vitest Documentation](https://vitest.dev)
- [ngrok Quickstart](https://ngrok.com/docs/getting-started/)
