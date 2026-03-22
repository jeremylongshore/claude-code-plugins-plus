---
name: webflow-local-dev-loop
description: |
  Configure a Webflow local development workflow with TypeScript, hot reload, mocked API tests,
  and webhook tunneling via ngrok.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with the Webflow Data API.
  Trigger with phrases like "webflow dev setup", "webflow local development",
  "webflow dev environment", "develop with webflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Webflow Data API v2 integrations
with TypeScript, hot reload, vitest mocking, and ngrok webhook tunneling.

## Prerequisites

- Completed `webflow-install-auth` setup
- Node.js 18+ with npm/pnpm
- API token with required scopes
- ngrok (optional, for webhook testing)

## Instructions

### Step 1: Project Structure

```
my-webflow-project/
├── src/
│   ├── webflow/
│   │   ├── client.ts          # WebflowClient singleton
│   │   ├── collections.ts    # CMS collection operations
│   │   ├── sites.ts           # Site operations
│   │   └── types.ts           # Shared types
│   ├── webhooks/
│   │   └── handler.ts         # Webhook endpoint
│   └── index.ts
├── tests/
│   ├── collections.test.ts
│   └── fixtures/
│       └── mock-items.json
├── .env.local                 # Local secrets (git-ignored)
├── .env.example               # Template for team
├── tsconfig.json
├── vitest.config.ts
└── package.json
```

### Step 2: Package Configuration

```json
{
  "name": "my-webflow-project",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "tunnel": "ngrok http 3000"
  },
  "dependencies": {
    "webflow-api": "^3.3.0",
    "express": "^4.21.0"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0",
    "@types/express": "^5.0.0",
    "@types/node": "^22.0.0"
  }
}
```

### Step 3: Environment Setup

```bash
# .env.example
WEBFLOW_API_TOKEN=your-token-here
WEBFLOW_SITE_ID=your-site-id
WEBFLOW_WEBHOOK_SECRET=your-webhook-secret
NODE_ENV=development
```

```bash
cp .env.example .env.local
# Edit .env.local with real values
```

Load environment in your app:

```typescript
// src/webflow/client.ts
import { WebflowClient } from "webflow-api";
import { config } from "dotenv";

config({ path: ".env.local" });

let client: WebflowClient | null = null;

export function getWebflowClient(): WebflowClient {
  if (!client) {
    const token = process.env.WEBFLOW_API_TOKEN;
    if (!token) throw new Error("WEBFLOW_API_TOKEN not set in .env.local");

    client = new WebflowClient({
      accessToken: token,
    });
  }
  return client;
}

export function getSiteId(): string {
  const siteId = process.env.WEBFLOW_SITE_ID;
  if (!siteId) throw new Error("WEBFLOW_SITE_ID not set in .env.local");
  return siteId;
}
```

### Step 4: Hot Reload Development

```bash
# Start with hot reload — restarts on file changes
npm run dev
```

The `tsx watch` command re-executes your entry file on every save. For an Express
webhook server:

```typescript
// src/index.ts
import express from "express";
import { getWebflowClient, getSiteId } from "./webflow/client.js";

const app = express();
app.use(express.json());

app.get("/health", async (req, res) => {
  const webflow = getWebflowClient();
  try {
    const { sites } = await webflow.sites.list();
    res.json({ status: "healthy", sites: sites?.length });
  } catch (error) {
    res.status(503).json({ status: "unhealthy", error: String(error) });
  }
});

app.listen(3000, () => console.log("Dev server: http://localhost:3000"));
```

### Step 5: Testing with Vitest

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
});
```

```typescript
// tests/setup.ts
import { config } from "dotenv";
config({ path: ".env.local" });
```

```typescript
// tests/collections.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { WebflowClient } from "webflow-api";

// Mock the SDK to avoid real API calls in tests
vi.mock("webflow-api", () => ({
  WebflowClient: vi.fn().mockImplementation(() => ({
    sites: {
      list: vi.fn().mockResolvedValue({
        sites: [
          { id: "site-123", displayName: "Test Site", shortName: "test" },
        ],
      }),
    },
    collections: {
      list: vi.fn().mockResolvedValue({
        collections: [
          {
            id: "col-456",
            displayName: "Blog Posts",
            slug: "blog-posts",
            itemCount: 12,
            fields: [
              { displayName: "Name", slug: "name", type: "PlainText", isRequired: true },
              { displayName: "Slug", slug: "slug", type: "PlainText", isRequired: true },
              { displayName: "Post Body", slug: "post-body", type: "RichText", isRequired: false },
            ],
          },
        ],
      }),
      items: {
        listItems: vi.fn().mockResolvedValue({
          items: [
            { id: "item-789", isDraft: false, fieldData: { name: "Test Post", slug: "test-post" } },
          ],
          pagination: { limit: 100, offset: 0, total: 1 },
        }),
        createItem: vi.fn().mockResolvedValue({
          id: "item-new",
          isDraft: true,
          fieldData: { name: "New Post", slug: "new-post" },
        }),
      },
    },
  })),
}));

describe("Webflow Collections", () => {
  let webflow: WebflowClient;

  beforeEach(() => {
    webflow = new WebflowClient({ accessToken: "test-token" });
  });

  it("should list collections for a site", async () => {
    const { collections } = await webflow.collections.list("site-123");
    expect(collections).toHaveLength(1);
    expect(collections![0].displayName).toBe("Blog Posts");
  });

  it("should list items in a collection", async () => {
    const { items } = await webflow.collections.items.listItems("col-456");
    expect(items).toHaveLength(1);
    expect(items![0].fieldData?.name).toBe("Test Post");
  });

  it("should create a CMS item", async () => {
    const item = await webflow.collections.items.createItem("col-456", {
      fieldData: { name: "New Post", slug: "new-post" },
    });
    expect(item.id).toBe("item-new");
    expect(item.isDraft).toBe(true);
  });
});
```

### Step 6: Webhook Testing with ngrok

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Expose local server
ngrok http 3000

# Copy the https:// URL from ngrok, then register webhook:
curl -X POST https://api.webflow.com/v2/sites/{site_id}/webhooks \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "triggerType": "form_submission",
    "url": "https://your-ngrok-url.ngrok.io/webhooks/webflow"
  }'
```

## Output

- Working dev environment with hot reload (`tsx watch`)
- Mocked test suite (no API calls in CI)
- ngrok tunnel for webhook testing
- Environment variable management via `.env.local`

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `WEBFLOW_API_TOKEN not set` | Missing .env.local | `cp .env.example .env.local` and fill in values |
| Port 3000 in use | Another process | `lsof -ti:3000 \| xargs kill` or change port |
| Test mock type error | SDK version mismatch | Update mock to match current SDK types |
| ngrok tunnel expired | Free tier limit | Restart ngrok or use paid plan |

## Resources

- [Webflow API Quick Start](https://developers.webflow.com/data/reference/rest-introduction/quick-start)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps

See `webflow-sdk-patterns` for production-ready code patterns.
