---
name: perplexity-ci-integration
description: |
  Configure CI/CD for Perplexity Sonar API integrations with GitHub Actions.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Perplexity tests into your build process.
  Trigger with phrases like "perplexity CI", "perplexity GitHub Actions",
  "perplexity automated tests", "CI perplexity pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, testing, ci-cd]

---
# Perplexity CI Integration

## Overview
Set up CI/CD pipelines for Perplexity Sonar API integrations. Key CI concerns: live API calls cost money (use mocks for unit tests, reserve live calls for integration tests), API keys must be in GitHub Secrets, and rate limits apply even in CI.

## Prerequisites
- GitHub repository with Actions enabled
- Perplexity API key for CI (separate from production)
- Test suite with mocked and live test separation

## Instructions

### Step 1: Configure GitHub Secret
```bash
set -euo pipefail
# Store API key as a GitHub secret
gh secret set PERPLEXITY_API_KEY --body "pplx-your-ci-key-here"
```

### Step 2: GitHub Actions Workflow
```yaml
# .github/workflows/perplexity-tests.yml
name: Perplexity Integration Tests

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
        # Unit tests use mocked responses — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run live Perplexity integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 3: Test Structure
```typescript
// tests/perplexity.unit.test.ts — runs on every PR, uses mocks
import { describe, it, expect, vi } from "vitest";
import fixture from "./fixtures/sonar-response.json";

vi.mock("openai", () => ({
  default: vi.fn().mockImplementation(() => ({
    chat: {
      completions: {
        create: vi.fn().mockResolvedValue(fixture),
      },
    },
  })),
}));

describe("Perplexity Search (mocked)", () => {
  it("parses citations from response", async () => {
    const { search } = await import("../src/perplexity/search");
    const result = await search("test query");
    expect(result.citations.length).toBeGreaterThan(0);
  });

  it("formats answer with citation links", async () => {
    const { formatCitationsAsMarkdown } = await import("../src/perplexity/citations");
    const formatted = formatCitationsAsMarkdown("See [1] for details", ["https://example.com"]);
    expect(formatted).toContain("[1](https://example.com)");
  });
});
```

```typescript
// tests/perplexity.integration.test.ts — runs on main only, uses live API
import { describe, it, expect } from "vitest";

const LIVE = !!process.env.PERPLEXITY_API_KEY;

describe.skipIf(!LIVE)("Perplexity Live API", () => {
  it("sonar returns answer with citations", async () => {
    const { search } = await import("../src/perplexity/search");
    const result = await search("What is TypeScript?", {
      model: "sonar",
      maxTokens: 100,
    });

    expect(result.answer).toBeTruthy();
    expect(result.citations.length).toBeGreaterThan(0);
    expect(result.usage.totalTokens).toBeGreaterThan(0);
  }, 15000);

  it("search_domain_filter restricts sources", async () => {
    const { search } = await import("../src/perplexity/search");
    const result = await search("Python latest release", {
      model: "sonar",
      maxTokens: 100,
      searchDomainFilter: ["python.org"],
    });

    expect(result.citations.some((url: string) => url.includes("python.org"))).toBe(true);
  }, 15000);
});
```

### Step 4: Cost-Aware CI
```yaml
# Only run live tests on main branch pushes (not every PR)
# Budget: ~$0.01 per test run (2 sonar queries at $0.005 each)
# Monthly estimate: 30 pushes/month = $0.30

# Add a weekly full integration test
  weekly-integration:
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 6 * * 1'
    env:
      PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm run test:integration:full
        timeout-minutes: 10
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | Run `gh secret set PERPLEXITY_API_KEY` |
| Integration tests timeout | Complex sonar-pro queries | Use `sonar` with `max_tokens: 100` in CI |
| 429 in CI | Parallel jobs hitting rate limit | Serialize integration tests |
| High CI costs | Running live tests on every PR | Gate live tests on main branch only |

## Output
- Unit test suite with mocked Perplexity responses (runs on every PR)
- Integration test suite with live API (runs on main pushes)
- Cost-optimized CI that limits API calls
- GitHub Actions workflow file

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
For deployment patterns, see `perplexity-deploy-integration`.
