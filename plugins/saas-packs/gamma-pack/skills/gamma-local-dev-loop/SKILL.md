---
name: gamma-local-dev-loop
description: |
  Set up local development workflow for Gamma API integration.
  Use when building automation scripts, testing API calls locally,
  or configuring a dev environment with mock responses.
  Trigger: "gamma local dev", "gamma development setup",
  "gamma test locally", "gamma mock API", "gamma dev workflow".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, development, testing]

---
# Gamma Local Dev Loop

## Overview

Set up an efficient local development workflow for Gamma API integrations. Since Gamma is a REST API with no SDK, the dev loop centers on HTTP request/response testing, mock servers for offline development, and a reusable client wrapper.

## Prerequisites

- Completed `gamma-install-auth` setup
- Node.js 18+ with `tsx` for TypeScript execution
- `GAMMA_API_KEY` in `.env`

## Instructions

### Step 1: Project Structure

```
gamma-integration/
├── src/
│   ├── client.ts          # Reusable Gamma API client
│   ├── generate.ts        # Generation workflows
│   └── poll.ts            # Polling helper
├── test/
│   ├── mock-server.ts     # Local mock for offline dev
│   └── integration.test.ts
├── .env                   # GAMMA_API_KEY (gitignored)
├── .env.example           # Template without secrets
├── package.json
└── tsconfig.json
```

### Step 2: Reusable Client Wrapper

```typescript
// src/client.ts
import "dotenv/config";

const GAMMA_BASE = "https://public-api.gamma.app/v1.0";

export interface GammaClient {
  generate(body: GenerateRequest): Promise<GenerateResponse>;
  poll(generationId: string): Promise<PollResponse>;
  listThemes(): Promise<Theme[]>;
  listFolders(): Promise<Folder[]>;
}

export function createClient(apiKey?: string, baseUrl?: string): GammaClient {
  const key = apiKey ?? process.env.GAMMA_API_KEY;
  if (!key) throw new Error("GAMMA_API_KEY required");
  const base = baseUrl ?? GAMMA_BASE;
  const headers = { "X-API-KEY": key, "Content-Type": "application/json" };

  async function request(method: string, path: string, body?: unknown) {
    const res = await fetch(`${base}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Gamma ${res.status}: ${text}`);
    }
    return res.json();
  }

  return {
    generate: (body) => request("POST", "/generations", body),
    poll: (id) => request("GET", `/generations/${id}`),
    listThemes: () => request("GET", "/themes"),
    listFolders: () => request("GET", "/folders"),
  };
}
```

### Step 3: Poll Helper with Timeout

```typescript
// src/poll.ts
import type { GammaClient } from "./client";

export async function waitForCompletion(
  client: GammaClient,
  generationId: string,
  opts = { intervalMs: 5000, timeoutMs: 120000 }
) {
  const deadline = Date.now() + opts.timeoutMs;
  while (Date.now() < deadline) {
    const result = await client.poll(generationId);
    if (result.status === "completed") return result;
    if (result.status === "failed") throw new Error(`Generation failed: ${result.error}`);
    await new Promise((r) => setTimeout(r, opts.intervalMs));
  }
  throw new Error(`Poll timeout after ${opts.timeoutMs}ms`);
}
```

### Step 4: Mock Server for Offline Dev

```typescript
// test/mock-server.ts
import http from "node:http";

const MOCK_PORT = 9876;
const generations = new Map<string, { status: string; tick: number }>();

const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "application/json");

  // POST /v1.0/generations
  if (req.method === "POST" && req.url === "/v1.0/generations") {
    const id = `mock_${Date.now()}`;
    generations.set(id, { status: "in_progress", tick: 0 });
    res.end(JSON.stringify({ generationId: id }));
    return;
  }

  // GET /v1.0/generations/:id — completes after 3 polls
  const pollMatch = req.url?.match(/\/v1\.0\/generations\/(.+)/);
  if (req.method === "GET" && pollMatch) {
    const gen = generations.get(pollMatch[1]);
    if (!gen) { res.writeHead(404); res.end("{}"); return; }
    gen.tick++;
    if (gen.tick >= 3) gen.status = "completed";
    res.end(JSON.stringify({
      generationId: pollMatch[1],
      status: gen.status,
      ...(gen.status === "completed" && {
        gammaUrl: `https://gamma.app/docs/mock-${pollMatch[1]}`,
        exportUrl: `https://export.gamma.app/mock.pdf`,
        creditsUsed: 10,
      }),
    }));
    return;
  }

  // GET /v1.0/themes
  if (req.url === "/v1.0/themes") {
    res.end(JSON.stringify([
      { id: "theme_1", name: "Professional" },
      { id: "theme_2", name: "Modern" },
    ]));
    return;
  }

  // GET /v1.0/folders
  if (req.url === "/v1.0/folders") {
    res.end(JSON.stringify([{ id: "folder_1", name: "Test Folder" }]));
    return;
  }

  res.writeHead(404);
  res.end("{}");
});

server.listen(MOCK_PORT, () => console.log(`Mock Gamma API on :${MOCK_PORT}`));
```

### Step 5: Development Scripts

```json
{
  "scripts": {
    "dev:mock": "tsx test/mock-server.ts",
    "dev:generate": "tsx src/generate.ts",
    "test": "vitest run",
    "test:integration": "GAMMA_BASE=http://localhost:9876/v1.0 vitest run test/integration"
  }
}
```

### Step 6: Integration Test

```typescript
// test/integration.test.ts
import { describe, it, expect } from "vitest";
import { createClient } from "../src/client";
import { waitForCompletion } from "../src/poll";

const BASE = process.env.GAMMA_BASE ?? "http://localhost:9876/v1.0";

describe("Gamma API", () => {
  const client = createClient("test-key", BASE);

  it("generates and polls to completion", async () => {
    const { generationId } = await client.generate({
      content: "Test presentation",
      outputFormat: "presentation",
    });
    expect(generationId).toBeTruthy();

    const result = await waitForCompletion(client, generationId);
    expect(result.status).toBe("completed");
    expect(result.gammaUrl).toContain("gamma.app");
  });

  it("lists workspace themes", async () => {
    const themes = await client.listThemes();
    expect(themes.length).toBeGreaterThan(0);
  });
});
```

## Dev Loop Summary

| Activity | Command | Hits Live API? |
|----------|---------|----------------|
| Start mock server | `npm run dev:mock` | No |
| Generate (mock) | `GAMMA_BASE=http://localhost:9876/v1.0 npm run dev:generate` | No |
| Run tests | `npm test` (uses mock) | No |
| Live API test | `GAMMA_API_KEY=gma_... tsx src/generate.ts` | Yes |

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `GAMMA_API_KEY required` | Missing env var | Add to `.env` or export |
| Mock returns 404 | Wrong mock port/path | Verify `GAMMA_BASE` points to mock |
| Poll timeout locally | Mock tick count too high | Reduce tick threshold |
| `fetch is not defined` | Node.js < 18 | Upgrade to Node.js 18+ |

## Resources

- [Gamma Developer Docs](https://developers.gamma.app/)
- [Generate API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)

## Next Steps

Proceed to `gamma-sdk-patterns` for reusable API wrapper patterns.
