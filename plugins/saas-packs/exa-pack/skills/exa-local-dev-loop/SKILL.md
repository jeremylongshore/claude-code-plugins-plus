---
name: exa-local-dev-loop
description: |
  Configure Exa local development with hot reload, testing, and mock responses.
  Use when setting up a development environment, writing tests against Exa,
  or establishing a fast iteration cycle.
  Trigger with phrases like "exa dev setup", "exa local development",
  "exa test setup", "develop with exa", "mock exa".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, testing, development]

---
# Exa Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Exa integrations. Covers project structure, mock responses for unit tests, integration test patterns, and hot-reload configuration.

## Prerequisites
- `exa-js` installed and `EXA_API_KEY` configured
- Node.js 18+ with npm/pnpm
- `vitest` for testing (or `jest`)

## Instructions

### Step 1: Project Structure
```
my-exa-project/
├── src/
│   ├── exa/
│   │   ├── client.ts       # Singleton Exa client
│   │   ├── search.ts       # Search wrappers
│   │   └── types.ts        # Typed interfaces
│   └── index.ts
├── tests/
│   ├── exa.unit.test.ts    # Mock-based unit tests
│   └── exa.integration.test.ts  # Real API tests (needs key)
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
├── tsconfig.json
├── vitest.config.ts
└── package.json
```

### Step 2: Package Setup
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:unit": "vitest --testPathPattern=unit",
    "test:integration": "vitest --testPathPattern=integration",
    "build": "tsc"
  },
  "dependencies": {
    "exa-js": "^1.0.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0",
    "typescript": "^5.0.0"
  }
}
```

### Step 3: Mock Exa for Unit Tests
```typescript
// tests/exa.unit.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the exa-js module
vi.mock("exa-js", () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      search: vi.fn().mockResolvedValue({
        results: [
          { url: "https://example.com/1", title: "Test Result 1", score: 0.95 },
          { url: "https://example.com/2", title: "Test Result 2", score: 0.87 },
        ],
      }),
      searchAndContents: vi.fn().mockResolvedValue({
        results: [
          {
            url: "https://example.com/1",
            title: "Test Result 1",
            score: 0.95,
            text: "This is the full text content of the page.",
            highlights: ["Key excerpt from the page"],
            summary: "A summary of the page content.",
          },
        ],
      }),
      findSimilar: vi.fn().mockResolvedValue({
        results: [
          { url: "https://similar.com/1", title: "Similar Page", score: 0.82 },
        ],
      }),
      getContents: vi.fn().mockResolvedValue({
        results: [
          { url: "https://example.com/1", title: "Page", text: "Content" },
        ],
      }),
    })),
  };
});

import Exa from "exa-js";

describe("Exa Search", () => {
  let exa: any;

  beforeEach(() => {
    exa = new Exa("test-key");
  });

  it("should return search results", async () => {
    const result = await exa.search("test query", { numResults: 5 });
    expect(result.results).toHaveLength(2);
    expect(result.results[0].score).toBeGreaterThan(0.9);
  });

  it("should return content with searchAndContents", async () => {
    const result = await exa.searchAndContents("test", { text: true });
    expect(result.results[0].text).toBeDefined();
    expect(result.results[0].highlights).toHaveLength(1);
  });
});
```

### Step 4: Integration Tests (Real API)
```typescript
// tests/exa.integration.test.ts
import { describe, it, expect } from "vitest";
import Exa from "exa-js";

// Skip if no API key available (CI without secrets)
const describeWithKey = process.env.EXA_API_KEY
  ? describe
  : describe.skip;

describeWithKey("Exa Integration", () => {
  const exa = new Exa(process.env.EXA_API_KEY!);

  it("should execute a basic search", async () => {
    const result = await exa.search("test connectivity", { numResults: 1 });
    expect(result.results.length).toBeGreaterThanOrEqual(1);
    expect(result.results[0].url).toMatch(/^https?:\/\//);
  }, 10000); // 10s timeout for API calls

  it("should return text content", async () => {
    const result = await exa.searchAndContents("TypeScript tutorial", {
      numResults: 1,
      text: { maxCharacters: 500 },
    });
    expect(result.results[0].text).toBeDefined();
    expect(result.results[0].text!.length).toBeGreaterThan(0);
  }, 15000);

  it("should find similar pages", async () => {
    const result = await exa.findSimilar("https://nodejs.org", {
      numResults: 3,
    });
    expect(result.results.length).toBeGreaterThanOrEqual(1);
  }, 10000);
});
```

### Step 5: Environment Configuration
```bash
set -euo pipefail
# Create .env.example template (commit this)
cat > .env.example << 'EOF'
# Exa API — get key at https://dashboard.exa.ai
EXA_API_KEY=
EOF

# Create local env (git-ignored)
cp .env.example .env.local
echo "EXA_API_KEY=your-key-here" > .env.local
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module 'exa-js'` | Not installed | Run `npm install exa-js` |
| Test timeout | Slow API response | Increase vitest timeout to 15000ms |
| Mock not applied | Import order issue | Ensure `vi.mock()` is before imports |
| Integration test fails in CI | No API key secret | Add `EXA_API_KEY` to CI secrets or skip |

## Examples

### Vitest Config for Exa Projects
```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    testTimeout: 15000,   // Exa API calls can take a few seconds
    setupFiles: ["dotenv/config"],
  },
});
```

## Resources
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)
- [exa-js on npm](https://www.npmjs.com/package/exa-js)

## Next Steps
See `exa-sdk-patterns` for production-ready code patterns.
