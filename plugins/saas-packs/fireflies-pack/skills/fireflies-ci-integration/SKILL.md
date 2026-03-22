---
name: fireflies-ci-integration
description: |
  Configure CI/CD pipelines for Fireflies.ai integrations with GraphQL testing.
  Use when setting up automated testing, configuring GitHub Actions,
  or validating Fireflies.ai queries in your build process.
  Trigger with phrases like "fireflies CI", "fireflies GitHub Actions",
  "fireflies automated tests", "CI fireflies", "test fireflies pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, testing, ci-cd]

---
# Fireflies.ai CI Integration

## Overview
Set up CI/CD pipelines for Fireflies.ai integrations: GraphQL query validation, mock-based unit tests, and optional live API integration tests with rate limit awareness.

## Prerequisites
- GitHub repository with Actions enabled
- Fireflies.ai test API key (for integration tests)
- Vitest test suite configured

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/fireflies-tests.yml
name: Fireflies Integration Tests

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
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: unit-tests
    environment: staging
    env:
      FIREFLIES_API_KEY: ${{ secrets.FIREFLIES_API_KEY_TEST }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Store Secrets
```bash
set -euo pipefail
# Store test API key as GitHub secret
gh secret set FIREFLIES_API_KEY_TEST --body "your-test-api-key"

# For production deployments
gh secret set FIREFLIES_API_KEY_PROD --env production --body "your-prod-key"
gh secret set FIREFLIES_WEBHOOK_SECRET --env production --body "your-webhook-secret"
```

### Step 3: Unit Tests with Mocks
```typescript
// tests/fireflies-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Fireflies GraphQL Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.FIREFLIES_API_KEY = "test-key";
  });

  it("should send correct auth header", async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({ data: { user: { email: "test@co.com" } } }),
    });

    const { FirefliesClient } = await import("../src/lib/fireflies-client");
    const client = new FirefliesClient("test-key");
    await client.query("{ user { email } }");

    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.fireflies.ai/graphql",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-key",
        }),
      })
    );
  });

  it("should throw on auth_failed error", async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        errors: [{ message: "Invalid API key", code: "auth_failed" }],
      }),
    });

    const { FirefliesClient } = await import("../src/lib/fireflies-client");
    const client = new FirefliesClient("bad-key");
    await expect(client.query("{ user { email } }"))
      .rejects.toThrow("auth_failed");
  });

  it("should parse transcript response", async () => {
    mockFetch.mockResolvedValue({
      json: () => Promise.resolve({
        data: {
          transcripts: [
            { id: "t1", title: "Standup", duration: 15, date: "2026-03-22" },
          ],
        },
      }),
    });

    const { FirefliesClient } = await import("../src/lib/fireflies-client");
    const client = new FirefliesClient("test-key");
    const { transcripts } = await client.getTranscripts(5);
    expect(transcripts[0].title).toBe("Standup");
    expect(transcripts[0].duration).toBe(15);
  });
});
```

### Step 4: Integration Tests (Live API)
```typescript
// tests/integration/fireflies.integration.test.ts
import { describe, it, expect } from "vitest";

const hasApiKey = !!process.env.FIREFLIES_API_KEY;

describe.skipIf(!hasApiKey)("Fireflies Live API", () => {
  it("should authenticate and return user", async () => {
    const res = await fetch("https://api.fireflies.ai/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
      },
      body: JSON.stringify({ query: "{ user { email is_admin } }" }),
    });
    const json = await res.json();
    expect(json.errors).toBeUndefined();
    expect(json.data.user.email).toBeDefined();
  });

  it("should list transcripts without error", async () => {
    const res = await fetch("https://api.fireflies.ai/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
      },
      body: JSON.stringify({
        query: "{ transcripts(limit: 1) { id title } }",
      }),
    });
    const json = await res.json();
    expect(json.errors).toBeUndefined();
    expect(Array.isArray(json.data.transcripts)).toBe(true);
  });
});
```

### Step 5: Test Scripts
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "vitest run tests/integration/",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Rate Limit Considerations in CI
- Free/Pro plans: 50 requests/day -- limit integration tests to main branch only
- Business plans: 60 requests/min -- safe for PR-level tests
- Cache API responses as fixtures for unit tests (see `fireflies-local-dev-loop`)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | Add via `gh secret set` |
| Integration test timeout | Slow API response | Increase timeout, add retry |
| Rate limit in CI | Too many test runs | Run integration tests on main only |
| Auth failure in CI | Expired test key | Rotate key in GitHub secrets |

## Output
- GitHub Actions workflow with unit + integration test jobs
- Mock-based unit tests for offline validation
- Live API integration tests gated to main branch
- Coverage reporting

## Resources
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)
- [Fireflies API Docs](https://docs.fireflies.ai/)

## Next Steps
For deployment patterns, see `fireflies-deploy-integration`.
