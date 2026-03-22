---
name: perplexity-local-dev-loop
description: |
  Configure Perplexity local development with mocking, testing, and hot reload.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Perplexity Sonar API.
  Trigger with phrases like "perplexity dev setup", "perplexity local development",
  "perplexity dev environment", "develop with perplexity", "mock perplexity".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, testing, workflow]

---
# Perplexity Local Dev Loop

## Overview
Set up a fast, cost-effective local development workflow for Perplexity Sonar API. Key challenge: every real API call performs a web search and costs money, so mocking and caching are essential for development.

## Prerequisites
- Completed `perplexity-install-auth` setup
- Node.js 18+ with npm/pnpm
- `vitest` for testing

## Instructions

### Step 1: Project Structure
```
my-perplexity-project/
├── src/
│   ├── perplexity/
│   │   ├── client.ts       # OpenAI client wrapper for Perplexity
│   │   ├── search.ts       # Search functions with citation handling
│   │   └── types.ts        # Response type extensions
│   └── index.ts
├── tests/
│   ├── fixtures/           # Saved API responses for mocking
│   │   └── sonar-response.json
│   ├── perplexity.test.ts
│   └── setup.ts
├── .env.local              # API key (git-ignored)
├── .env.example            # Template
└── package.json
```

### Step 2: Type-Safe Client Wrapper
```typescript
// src/perplexity/client.ts
import OpenAI from "openai";

export interface PerplexityResponse extends OpenAI.ChatCompletion {
  citations?: string[];
  search_results?: Array<{
    title: string;
    url: string;
    snippet: string;
  }>;
  related_questions?: string[];
}

export type PerplexityModel = "sonar" | "sonar-pro" | "sonar-reasoning-pro" | "sonar-deep-research";

export function createClient(apiKey?: string): OpenAI {
  return new OpenAI({
    apiKey: apiKey || process.env.PERPLEXITY_API_KEY,
    baseURL: "https://api.perplexity.ai",
  });
}

export async function search(
  client: OpenAI,
  query: string,
  opts: {
    model?: PerplexityModel;
    systemPrompt?: string;
    maxTokens?: number;
    searchRecencyFilter?: "hour" | "day" | "week" | "month";
    searchDomainFilter?: string[];
  } = {}
): Promise<PerplexityResponse> {
  const response = await client.chat.completions.create({
    model: opts.model || "sonar",
    messages: [
      ...(opts.systemPrompt
        ? [{ role: "system" as const, content: opts.systemPrompt }]
        : []),
      { role: "user" as const, content: query },
    ],
    max_tokens: opts.maxTokens,
    ...(opts.searchRecencyFilter && { search_recency_filter: opts.searchRecencyFilter }),
    ...(opts.searchDomainFilter && { search_domain_filter: opts.searchDomainFilter }),
  } as any);

  return response as unknown as PerplexityResponse;
}
```

### Step 3: Save Fixtures for Offline Development
```typescript
// scripts/capture-fixture.ts
import { createClient, search } from "../src/perplexity/client";
import { writeFileSync } from "fs";

async function captureFixture() {
  const client = createClient();
  const response = await search(client, "What is TypeScript 5.5?");

  writeFileSync(
    "tests/fixtures/sonar-response.json",
    JSON.stringify(response, null, 2)
  );
  console.log("Fixture saved with", (response.citations || []).length, "citations");
}

captureFixture();
```

### Step 4: Mock Client for Tests
```typescript
// tests/setup.ts
import { vi } from "vitest";
import fixture from "./fixtures/sonar-response.json";

export function mockPerplexityClient() {
  return {
    chat: {
      completions: {
        create: vi.fn().mockResolvedValue(fixture),
      },
    },
  };
}
```

### Step 5: Write Tests
```typescript
// tests/perplexity.test.ts
import { describe, it, expect } from "vitest";
import { mockPerplexityClient } from "./setup";
import { search } from "../src/perplexity/client";

describe("Perplexity Search", () => {
  it("returns answer with citations", async () => {
    const client = mockPerplexityClient() as any;
    const result = await search(client, "test query");

    expect(result.choices[0].message.content).toBeDefined();
    expect(result.citations).toBeDefined();
    expect(result.citations!.length).toBeGreaterThan(0);
  });

  it.skipIf(!process.env.PERPLEXITY_API_KEY)(
    "live API returns citations",
    async () => {
      const { createClient, search } = await import("../src/perplexity/client");
      const client = createClient();
      const result = await search(client, "What is Node.js?", {
        model: "sonar",
        maxTokens: 100,
      });
      expect(result.citations!.length).toBeGreaterThan(0);
    }
  );
});
```

### Step 6: Dev Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:live": "PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY vitest --run",
    "capture-fixtures": "tsx scripts/capture-fixture.ts"
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Fixture missing | Never captured | Run `npm run capture-fixtures` once |
| Tests hit real API | Missing mock | Ensure mock client is injected |
| Stale fixtures | API response format changed | Re-capture fixtures |
| High dev costs | Making live calls in loop | Use fixtures; reserve live calls for CI |

## Output
- Type-safe Perplexity client wrapper
- Fixture-based test suite that runs offline
- Live integration test gated on API key presence
- Hot-reload dev server

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [Perplexity API Reference](https://docs.perplexity.ai/api-reference/chat-completions-post)

## Next Steps
See `perplexity-sdk-patterns` for production-ready code patterns.
