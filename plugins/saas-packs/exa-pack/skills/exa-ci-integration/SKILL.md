---
name: exa-ci-integration
description: |
  Configure Exa CI/CD integration with GitHub Actions and automated testing.
  Use when setting up automated testing for Exa integrations,
  configuring CI pipelines, or adding Exa health checks to builds.
  Trigger with phrases like "exa CI", "exa GitHub Actions",
  "exa automated tests", "CI exa", "exa pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, testing, ci-cd]

---
# Exa CI Integration

## Overview
Set up CI/CD pipelines for Exa integrations with unit tests (mocked), integration tests (real API), and health checks. Uses GitHub Actions with secrets for API key management.

## Prerequisites
- GitHub repository with Actions enabled
- Exa API key for testing
- npm/pnpm project with vitest or jest

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/exa-tests.yml
name: Exa Integration Tests

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
      - run: npm run test:unit
        # Unit tests use mocked Exa — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    # Only run if API key is available (not on forks)
    if: github.event_name == 'push' || github.event.pull_request.head.repo.full_name == github.repository
    env:
      EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run test:integration
        timeout-minutes: 5

  exa-health-check:
    runs-on: ubuntu-latest
    env:
      EXA_API_KEY: ${{ secrets.EXA_API_KEY }}
    steps:
      - name: Verify Exa API connectivity
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST https://api.exa.ai/search \
            -H "x-api-key: $EXA_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{"query":"CI health check","numResults":1}')
          echo "Exa API status: $HTTP_CODE"
          [ "$HTTP_CODE" = "200" ] || exit 1
```

### Step 2: Configure Secrets
```bash
# Add API key as repository secret
gh secret set EXA_API_KEY --body "your-exa-api-key"

# For staging/production deployments
gh secret set EXA_API_KEY_STAGING --body "staging-key" --env staging
gh secret set EXA_API_KEY_PROD --body "prod-key" --env production
```

### Step 3: Integration Test Suite
```typescript
// tests/exa.integration.test.ts
import { describe, it, expect } from "vitest";
import Exa from "exa-js";

const describeWithKey = process.env.EXA_API_KEY ? describe : describe.skip;

describeWithKey("Exa API Integration", () => {
  const exa = new Exa(process.env.EXA_API_KEY!);

  it("should search and return results", async () => {
    const result = await exa.search("JavaScript frameworks", {
      type: "auto",
      numResults: 3,
    });
    expect(result.results.length).toBeGreaterThanOrEqual(1);
    expect(result.results[0]).toHaveProperty("url");
    expect(result.results[0]).toHaveProperty("title");
    expect(result.results[0]).toHaveProperty("score");
  }, 10000);

  it("should return content with searchAndContents", async () => {
    const result = await exa.searchAndContents("Node.js best practices", {
      numResults: 2,
      text: { maxCharacters: 500 },
      highlights: { maxCharacters: 200 },
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

  it("should handle invalid queries gracefully", async () => {
    // Empty query should return 400
    await expect(
      exa.search("", { numResults: 1 })
    ).rejects.toThrow();
  }, 10000);
});
```

### Step 4: Release Gate with Exa Verification
```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ["v*"]

jobs:
  verify-and-release:
    runs-on: ubuntu-latest
    env:
      EXA_API_KEY: ${{ secrets.EXA_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
      - name: Verify Exa production connectivity
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | `gh secret set EXA_API_KEY` |
| Integration tests timeout | Slow API response | Increase timeout to 15000ms |
| Tests fail on forks | No access to secrets | Skip integration tests on fork PRs |
| Rate limited in CI | Too many concurrent runs | Use unique test queries per run |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest CI Configuration](https://vitest.dev/guide/ci.html)

## Next Steps
For deployment patterns, see `exa-deploy-integration`.
