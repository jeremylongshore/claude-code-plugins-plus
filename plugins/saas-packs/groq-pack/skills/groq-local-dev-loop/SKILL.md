---
name: groq-local-dev-loop
description: |
  Configure Groq local development with hot reload, mocking, and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Groq.
  Trigger with phrases like "groq dev setup", "groq local development",
  "groq dev environment", "develop with groq".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, testing, workflow]

---
# Groq Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Groq. Groq's sub-second response times make it uniquely suited for tight dev loops -- you get LLM responses fast enough to iterate without context-switching.

## Prerequisites
- `groq-sdk` installed
- `GROQ_API_KEY` set (free tier is fine for development)
- Node.js 18+ with tsx for TypeScript execution
- vitest for testing

## Instructions

### Step 1: Project Structure
```
my-groq-project/
├── src/
│   ├── groq/
│   │   ├── client.ts       # Singleton Groq client
│   │   ├── models.ts       # Model constants and selection
│   │   └── completions.ts  # Completion wrappers
│   └── index.ts
├── tests/
│   ├── groq.test.ts         # Unit tests with mocks
│   └── groq.integration.ts  # Live API tests (CI-only)
├── .env.local               # Local secrets (git-ignored)
├── .env.example              # Template for team
└── package.json
```

### Step 2: Package Setup
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "GROQ_INTEGRATION=1 vitest tests/groq.integration.ts"
  },
  "dependencies": {
    "groq-sdk": "^0.12.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0"
  }
}
```

### Step 3: Singleton Client
```typescript
// src/groq/client.ts
import Groq from "groq-sdk";

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (!_client) {
    if (!process.env.GROQ_API_KEY) {
      throw new Error("GROQ_API_KEY not set. Copy .env.example to .env.local");
    }
    _client = new Groq({
      apiKey: process.env.GROQ_API_KEY,
      maxRetries: 2,
      timeout: 30_000,
    });
  }
  return _client;
}

// Reset for testing
export function resetClient(): void {
  _client = null;
}
```

### Step 4: Model Constants
```typescript
// src/groq/models.ts
export const MODELS = {
  FAST: "llama-3.1-8b-instant",         // Dev default: cheapest, fastest
  VERSATILE: "llama-3.3-70b-versatile",  // Production quality
  SPECDEC: "llama-3.3-70b-specdec",      // Speculative decoding variant
  SCOUT: "meta-llama/llama-4-scout-17b-16e-instruct",  // Vision
} as const;

export const DEV_MODEL = MODELS.FAST;  // Use 8B for dev to save quota
```

### Step 5: Unit Tests with Mocking
```typescript
// tests/groq.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import Groq from "groq-sdk";

// Mock the entire groq-sdk module
vi.mock("groq-sdk", () => {
  const mockCreate = vi.fn().mockResolvedValue({
    choices: [{ message: { content: "mocked response" }, finish_reason: "stop" }],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
    model: "llama-3.1-8b-instant",
  });

  return {
    default: vi.fn(() => ({
      chat: { completions: { create: mockCreate } },
      models: { list: vi.fn().mockResolvedValue({ data: [] }) },
    })),
  };
});

describe("Groq Completions", () => {
  it("should create a chat completion", async () => {
    const groq = new Groq();
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "test" }],
    });

    expect(result.choices[0].message.content).toBe("mocked response");
    expect(result.usage.total_tokens).toBe(15);
  });
});
```

### Step 6: Integration Tests (Live API)
```typescript
// tests/groq.integration.ts
import { describe, it, expect } from "vitest";
import Groq from "groq-sdk";

const shouldRun = !!process.env.GROQ_INTEGRATION;

describe.skipIf(!shouldRun)("Groq Integration", () => {
  const groq = new Groq();

  it("should list available models", async () => {
    const models = await groq.models.list();
    expect(models.data.length).toBeGreaterThan(0);
    const ids = models.data.map((m) => m.id);
    expect(ids).toContain("llama-3.1-8b-instant");
  }, 10_000);

  it("should complete a chat request", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply with exactly: PONG" }],
      temperature: 0,
      max_tokens: 10,
    });
    expect(result.choices[0].message.content).toContain("PONG");
  }, 10_000);
});
```

### Step 7: Environment Template
```bash
# .env.example
# Get your key at https://console.groq.com/keys
GROQ_API_KEY=gsk_your_key_here

# Optional: override default dev model
GROQ_MODEL=llama-3.1-8b-instant
```

## Dev Tips
- Use `llama-3.1-8b-instant` during development (lowest quota usage, fastest)
- Set `temperature: 0` for deterministic outputs during debugging
- Set `max_tokens` conservatively to avoid burning through free tier
- Groq free tier: 30 RPM for 70B models, 30 RPM for 8B -- plan your dev loops accordingly

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `GROQ_API_KEY not set` | Missing .env.local | Copy from .env.example |
| Test timeout | Live API call in unit test | Mock groq-sdk in unit tests |
| `429 rate_limit_exceeded` | Free tier RPM hit | Wait 60s or use `test:watch` with longer intervals |
| Port already in use | Another tsx watch running | Kill process or change port |

## Resources
- [groq-sdk npm](https://www.npmjs.com/package/groq-sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)

## Next Steps
See `groq-sdk-patterns` for production-ready code patterns.
