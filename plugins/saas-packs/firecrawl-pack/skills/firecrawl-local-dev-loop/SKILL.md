---
name: firecrawl-local-dev-loop
description: |
  Configure Firecrawl local development with self-hosted Docker, mocking, and testing.
  Use when setting up a development environment, running Firecrawl locally to save credits,
  or configuring test workflows with vitest.
  Trigger with phrases like "firecrawl dev setup", "firecrawl local development",
  "firecrawl docker", "firecrawl self-hosted dev", "firecrawl test setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, testing, workflow]

---
# Firecrawl Local Dev Loop

## Overview
Set up a fast development workflow for Firecrawl integrations. Use self-hosted Firecrawl via Docker to avoid burning API credits during development, mock the SDK for unit tests, and run integration tests against the local instance.

## Prerequisites
- Node.js 18+ with npm/pnpm
- Docker + Docker Compose (for self-hosted Firecrawl)
- `@mendable/firecrawl-js` installed

## Instructions

### Step 1: Project Structure
```
my-firecrawl-project/
├── src/
│   ├── scraper.ts          # Firecrawl business logic
│   └── config.ts           # Environment-aware config
├── tests/
│   ├── scraper.test.ts     # Unit tests (mocked SDK)
│   └── integration.test.ts # Integration tests (real API)
├── docker-compose.yml      # Self-hosted Firecrawl
├── .env.local              # Dev secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

### Step 2: Self-Hosted Firecrawl for Zero-Credit Dev
```yaml
# docker-compose.yml
services:
  firecrawl:
    image: mendableai/firecrawl:latest
    ports:
      - "3002:3002"
    environment:
      - PORT=3002
      - USE_DB_AUTHENTICATION=false
      - REDIS_URL=redis://redis:6379
      - NUM_WORKERS_PER_QUEUE=1
      - BULL_AUTH_KEY=devonly
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

```bash
set -euo pipefail
# Start local Firecrawl
docker compose up -d

# Verify it's running
curl -s http://localhost:3002/health | jq .
```

### Step 3: Environment-Aware Configuration
```typescript
// src/config.ts
import FirecrawlApp from "@mendable/firecrawl-js";

export function getFirecrawl(): FirecrawlApp {
  const isDev = process.env.NODE_ENV !== "production";

  return new FirecrawlApp({
    apiKey: process.env.FIRECRAWL_API_KEY || "fc-dev",
    // Point to local Docker instance in dev
    ...(isDev && process.env.FIRECRAWL_API_URL
      ? { apiUrl: process.env.FIRECRAWL_API_URL }
      : {}),
  });
}
```

```bash
# .env.local (for development — zero API credits used)
FIRECRAWL_API_KEY=fc-localdev
FIRECRAWL_API_URL=http://localhost:3002
NODE_ENV=development
```

### Step 4: Unit Tests with Mocked SDK
```typescript
// tests/scraper.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the SDK
vi.mock("@mendable/firecrawl-js", () => ({
  default: vi.fn().mockImplementation(() => ({
    scrapeUrl: vi.fn().mockResolvedValue({
      success: true,
      markdown: "# Hello World\n\nSample content from mock",
      metadata: { title: "Hello World", sourceURL: "https://example.com" },
    }),
    crawlUrl: vi.fn().mockResolvedValue({
      success: true,
      data: [
        {
          markdown: "# Page 1",
          metadata: { sourceURL: "https://example.com/page1" },
        },
      ],
    }),
    mapUrl: vi.fn().mockResolvedValue({
      success: true,
      links: ["https://example.com/a", "https://example.com/b"],
    }),
  })),
}));

import { scrapeAndProcess } from "../src/scraper";

describe("Scraper", () => {
  it("returns cleaned markdown", async () => {
    const result = await scrapeAndProcess("https://example.com");
    expect(result.markdown).toContain("Hello World");
    expect(result.metadata.title).toBe("Hello World");
  });
});
```

### Step 5: Integration Tests Against Local Instance
```typescript
// tests/integration.test.ts
import { describe, it, expect } from "vitest";
import FirecrawlApp from "@mendable/firecrawl-js";

const FIRECRAWL_URL = process.env.FIRECRAWL_API_URL || "http://localhost:3002";

describe.skipIf(!process.env.FIRECRAWL_API_URL)("Firecrawl Integration", () => {
  const firecrawl = new FirecrawlApp({
    apiKey: "fc-test",
    apiUrl: FIRECRAWL_URL,
  });

  it("scrapes a page to markdown", async () => {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["markdown"],
    });
    expect(result.success).toBe(true);
    expect(result.markdown).toBeDefined();
    expect(result.markdown!.length).toBeGreaterThan(50);
  }, 30000);
});
```

### Step 6: Dev Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "FIRECRAWL_API_URL=http://localhost:3002 vitest run tests/integration",
    "firecrawl:up": "docker compose up -d",
    "firecrawl:down": "docker compose down",
    "firecrawl:logs": "docker compose logs -f firecrawl"
  }
}
```

## Output
- Self-hosted Firecrawl running on `localhost:3002`
- Unit tests with mocked SDK (zero API calls)
- Integration tests against local instance
- Hot-reload dev server with `tsx watch`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Docker `ECONNREFUSED` | Container not running | `docker compose up -d` |
| Redis connection refused | Redis not healthy yet | Wait for healthcheck, retry |
| `MODULE_NOT_FOUND` | Missing dependency | `npm install @mendable/firecrawl-js` |
| Integration test timeout | Self-hosted Firecrawl slow | Increase vitest timeout to 30s |
| Port 3002 in use | Another process | `lsof -i :3002` and kill, or change port |

## Examples

### Quick Scrape Script for Dev
```typescript
// scripts/dev-scrape.ts
import { getFirecrawl } from "../src/config";

const firecrawl = getFirecrawl();
const result = await firecrawl.scrapeUrl(process.argv[2] || "https://example.com", {
  formats: ["markdown"],
});
console.log(result.markdown);
```

```bash
npx tsx scripts/dev-scrape.ts https://docs.firecrawl.dev
```

## Resources
- [Firecrawl Self-Hosting](https://docs.firecrawl.dev/contributing/self-host)
- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)

## Next Steps
See `firecrawl-sdk-patterns` for production-ready code patterns.
