---
name: firecrawl-ci-integration
description: |
  Configure Firecrawl CI/CD integration with GitHub Actions and automated scraping tests.
  Use when setting up automated testing of Firecrawl integrations, configuring CI pipelines,
  or validating scraping behavior in pull requests.
  Trigger with phrases like "firecrawl CI", "firecrawl GitHub Actions",
  "firecrawl automated tests", "CI firecrawl", "test firecrawl in CI".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, testing, ci-cd]

---
# Firecrawl CI Integration

## Overview
Set up CI/CD pipelines to test Firecrawl integrations automatically. Covers GitHub Actions workflow, API key secrets management, integration tests that validate real scraping, and mock-based unit tests for PRs.

## Prerequisites
- GitHub repository with Actions enabled
- Firecrawl API key for testing (separate from production)
- `@mendable/firecrawl-js` installed

## Instructions

### Step 1: Configure Secrets
```bash
set -euo pipefail
# Store test API key in GitHub Actions secrets
gh secret set FIRECRAWL_API_KEY --body "fc-test-key-here"
```

### Step 2: GitHub Actions Workflow
```yaml
# .github/workflows/firecrawl-tests.yml
name: Firecrawl Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test -- --coverage
        # Unit tests use mocked SDK — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'  # Only on merge, not PRs (saves credits)
    env:
      FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run test:integration
        timeout-minutes: 5
```

### Step 3: Integration Tests
```typescript
// tests/firecrawl.integration.test.ts
import { describe, it, expect } from "vitest";
import FirecrawlApp from "@mendable/firecrawl-js";

const SKIP = !process.env.FIRECRAWL_API_KEY;

describe.skipIf(SKIP)("Firecrawl Integration", () => {
  const firecrawl = new FirecrawlApp({
    apiKey: process.env.FIRECRAWL_API_KEY!,
  });

  it("scrapes a page to markdown", async () => {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["markdown"],
    });
    expect(result.success).toBe(true);
    expect(result.markdown).toBeDefined();
    expect(result.markdown!.length).toBeGreaterThan(50);
    expect(result.metadata?.title).toBeDefined();
  }, 30000);

  it("maps a site for URLs", async () => {
    const result = await firecrawl.mapUrl("https://docs.firecrawl.dev");
    expect(result.links).toBeDefined();
    expect(result.links!.length).toBeGreaterThan(0);
  }, 30000);

  it("extracts structured data", async () => {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["extract"],
      extract: {
        schema: {
          type: "object",
          properties: {
            title: { type: "string" },
            description: { type: "string" },
          },
        },
      },
    });
    expect(result.extract).toBeDefined();
    expect(result.extract?.title).toBeDefined();
  }, 30000);
});
```

### Step 4: Mock-Based Unit Tests (No API Key)
```typescript
// tests/scraper.unit.test.ts
import { describe, it, expect, vi } from "vitest";

vi.mock("@mendable/firecrawl-js", () => ({
  default: vi.fn().mockImplementation(() => ({
    scrapeUrl: vi.fn().mockResolvedValue({
      success: true,
      markdown: "# Test Page\n\nContent here",
      metadata: { title: "Test", sourceURL: "https://example.com" },
    }),
    mapUrl: vi.fn().mockResolvedValue({
      success: true,
      links: ["https://example.com/a", "https://example.com/b"],
    }),
  })),
}));

import { processPage } from "../src/scraper";

describe("Scraper Unit Tests", () => {
  it("processes scraped content correctly", async () => {
    const result = await processPage("https://example.com");
    expect(result.title).toBe("Test");
    expect(result.content).toContain("Content here");
  });
});
```

### Step 5: Credit-Aware CI
```yaml
# Only run expensive crawl tests on release tags
integration-crawl:
  runs-on: ubuntu-latest
  if: startsWith(github.ref, 'refs/tags/v')
  env:
    FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: "20"
    - run: npm ci
    - run: npm run test:crawl
      timeout-minutes: 10
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | `gh secret set FIRECRAWL_API_KEY` |
| Integration test timeout | Slow scrape response | Increase timeout to 30s+ |
| Tests pass locally, fail in CI | Missing env var | Use `skipIf(!process.env.FIRECRAWL_API_KEY)` |
| Credit burn from PRs | Integration tests on every PR | Run integration tests only on merge |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/using-secrets-in-github-actions)
- [Vitest](https://vitest.dev/)
- [Firecrawl Node SDK](https://docs.firecrawl.dev/sdks/node)

## Next Steps
For deployment patterns, see `firecrawl-deploy-integration`.
