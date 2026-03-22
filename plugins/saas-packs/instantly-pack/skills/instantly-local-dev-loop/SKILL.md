---
name: instantly-local-dev-loop
description: |
  Configure Instantly.ai local development with mock server and test workflows.
  Use when setting up a dev environment, testing API calls without sending emails,
  or building integration tests against Instantly endpoints.
  Trigger with phrases like "instantly dev setup", "test instantly locally",
  "instantly mock server", "instantly development environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, development, testing]

---
# Instantly Local Dev Loop

## Overview
Set up a local development workflow for Instantly integrations. Instantly provides a mock server at `https://developer.instantly.ai/_mock/api/v2/` for testing without sending real emails or consuming API limits. This skill covers mock server usage, integration testing, and local webhook development.

## Prerequisites
- Completed `instantly-install-auth` setup
- Node.js 18+ with TypeScript
- A separate Instantly API key for dev/test (recommended)

## Instructions

### Step 1: Configure Dev Environment
```typescript
// src/config.ts
import "dotenv/config";

interface Config {
  baseUrl: string;
  apiKey: string;
  useMock: boolean;
}

export function getConfig(): Config {
  const useMock = process.env.INSTANTLY_USE_MOCK === "true";
  return {
    baseUrl: useMock
      ? "https://developer.instantly.ai/_mock/api/v2"
      : process.env.INSTANTLY_BASE_URL || "https://api.instantly.ai/api/v2",
    apiKey: process.env.INSTANTLY_API_KEY || "",
    useMock,
  };
}
```

```bash
# .env.development
INSTANTLY_API_KEY=your-dev-api-key
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v2
INSTANTLY_USE_MOCK=true

# .env.production
INSTANTLY_API_KEY=your-prod-api-key
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v2
INSTANTLY_USE_MOCK=false
```

### Step 2: Build a Testable API Client
```typescript
// src/instantly.ts
import { getConfig } from "./config";

const config = getConfig();

export async function instantly<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${config.baseUrl}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.apiKey}`,
      ...options.headers,
    },
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers.get("retry-after") || "2", 10);
    console.warn(`Rate limited. Retrying in ${retryAfter}s...`);
    await new Promise((r) => setTimeout(r, retryAfter * 1000));
    return instantly<T>(path, options);
  }

  if (!res.ok) {
    const body = await res.text();
    throw new InstantlyError(res.status, path, body);
  }

  return res.json() as Promise<T>;
}

class InstantlyError extends Error {
  constructor(
    public status: number,
    public path: string,
    public body: string
  ) {
    super(`Instantly API ${status} on ${path}: ${body}`);
    this.name = "InstantlyError";
  }
}
```

### Step 3: Write Integration Tests
```typescript
// tests/instantly.test.ts
import { describe, it, expect, beforeAll } from "vitest";
import { instantly } from "../src/instantly";

describe("Instantly API Integration", () => {
  it("should list campaigns", async () => {
    const campaigns = await instantly<Array<{ id: string; name: string }>>(
      "/campaigns?limit=5"
    );
    expect(Array.isArray(campaigns)).toBe(true);
  });

  it("should list email accounts", async () => {
    const accounts = await instantly<Array<{ email: string }>>(
      "/accounts?limit=5"
    );
    expect(Array.isArray(accounts)).toBe(true);
  });

  it("should create and delete a lead list", async () => {
    const list = await instantly<{ id: string; name: string }>(
      "/lead-lists",
      {
        method: "POST",
        body: JSON.stringify({ name: `test-list-${Date.now()}` }),
      }
    );
    expect(list.id).toBeDefined();
    expect(list.name).toContain("test-list-");

    // Clean up
    await instantly(`/lead-lists/${list.id}`, { method: "DELETE" });
  });

  it("should handle 401 on bad key", async () => {
    const res = await fetch("https://api.instantly.ai/api/v2/campaigns?limit=1", {
      headers: { Authorization: "Bearer invalid-key" },
    });
    expect(res.status).toBe(401);
  });
});
```

### Step 4: Local Webhook Testing with ngrok
```bash
set -euo pipefail
# Start your webhook server locally
# In terminal 1:
npx tsx src/webhook-server.ts  # listens on port 3000

# In terminal 2 — expose with ngrok:
ngrok http 3000

# Register the ngrok URL as a webhook
curl -X POST https://api.instantly.ai/api/v2/webhooks \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Dev Webhook",
    "target_hook_url": "https://abc123.ngrok.io/webhooks/instantly",
    "event_type": "all_events"
  }'
```

```typescript
// src/webhook-server.ts — minimal local webhook receiver
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/instantly", (req, res) => {
  console.log("Webhook received:", JSON.stringify(req.body, null, 2));
  res.status(200).json({ received: true });
});

app.listen(3000, () => console.log("Webhook server on http://localhost:3000"));
```

### Step 5: Test Webhook Delivery
```typescript
// After registering the webhook, test it via API
async function testWebhook(webhookId: string) {
  await instantly(`/webhooks/${webhookId}/test`, { method: "POST" });
  console.log("Test webhook fired — check your local server logs");
}
```

## Project Structure
```
instantly-integration/
├── src/
│   ├── config.ts           # Environment-aware config
│   ├── instantly.ts         # API client with retry
│   └── webhook-server.ts   # Local webhook receiver
├── tests/
│   └── instantly.test.ts   # Integration tests
├── .env.development         # Dev config (mock mode)
├── .env.production          # Prod config
├── package.json
└── tsconfig.json
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Mock returns unexpected data | Mock schema mismatch | Check mock docs at developer.instantly.ai |
| `ECONNREFUSED` on localhost | Webhook server not running | Start it before registering webhook |
| Tests passing locally, failing in CI | Different env vars | Ensure CI uses `.env.development` |
| ngrok tunnel expired | Free tier 2-hour limit | Restart ngrok or upgrade |

## Resources
- [Instantly Mock Server](https://developer.instantly.ai/_mock/api/v2/)
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [ngrok Quick Start](https://ngrok.com/docs/getting-started/)

## Next Steps
For production SDK patterns, see `instantly-sdk-patterns`.
