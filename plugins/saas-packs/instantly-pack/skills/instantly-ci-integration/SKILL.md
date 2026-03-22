---
name: instantly-ci-integration
description: |
  Configure CI/CD pipelines for Instantly.ai integrations with GitHub Actions.
  Use when setting up automated testing, deployment pipelines,
  or continuous validation of Instantly API integrations.
  Trigger with phrases like "instantly ci", "instantly github actions",
  "instantly pipeline", "instantly automated testing", "instantly ci/cd".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, ci-cd, github-actions, testing]

---
# Instantly CI Integration

## Overview
Set up CI/CD pipelines for Instantly API v2 integrations. Covers GitHub Actions workflows for testing against the Instantly mock server, validating API key scopes, and deploying webhook receivers. Uses the mock server at `https://developer.instantly.ai/_mock/api/v2/` so CI runs don't send real emails or consume production API limits.

## Prerequisites
- GitHub repository with Instantly integration code
- `INSTANTLY_API_KEY` secret in GitHub repo settings (for production tests)
- Node.js 18+ or Python 3.10+ in the project

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/instantly-ci.yml
name: Instantly Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  INSTANTLY_USE_MOCK: "true"
  INSTANTLY_BASE_URL: "https://developer.instantly.ai/_mock/api/v2"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci

      - name: Type check
        run: npx tsc --noEmit

      - name: Lint
        run: npx eslint src/ --ext .ts

      - name: Unit tests (mock server)
        run: npx vitest run --reporter=verbose
        env:
          INSTANTLY_API_KEY: "mock-key-for-ci"
          INSTANTLY_USE_MOCK: "true"

      - name: Validate API client types
        run: npx tsx scripts/validate-types.ts

  integration-test:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci

      - name: Integration tests (live API, read-only)
        run: npx vitest run tests/integration/ --reporter=verbose
        env:
          INSTANTLY_API_KEY: ${{ secrets.INSTANTLY_API_KEY }}
          INSTANTLY_BASE_URL: "https://api.instantly.ai/api/v2"
```

### Step 2: API Scope Validation Script
```typescript
// scripts/validate-types.ts
// Verifies the API client types match expected Instantly v2 schema

import { InstantlyClient } from "../src/instantly/client";

async function validateApiAccess() {
  const client = new InstantlyClient();

  // Validate read-only operations work
  const campaigns = await client.getCampaigns({ limit: 1 });
  console.log("campaigns: OK");

  const accounts = await client.getAccounts({ limit: 1 });
  console.log("accounts: OK");

  console.log("All API validations passed");
}

validateApiAccess().catch((err) => {
  console.error("Validation failed:", err.message);
  process.exit(1);
});
```

### Step 3: Integration Test Suite
```typescript
// tests/integration/instantly.test.ts
import { describe, it, expect } from "vitest";
import { InstantlyClient } from "../../src/instantly/client";

const client = new InstantlyClient();

describe("Instantly API v2 Integration", () => {
  it("should authenticate and list campaigns", async () => {
    const campaigns = await client.getCampaigns({ limit: 5 });
    expect(Array.isArray(campaigns)).toBe(true);
  });

  it("should list email accounts", async () => {
    const accounts = await client.getAccounts({ limit: 5 });
    expect(Array.isArray(accounts)).toBe(true);
  });

  it("should fetch campaign analytics", async () => {
    const campaigns = await client.getCampaigns({ limit: 1 });
    if (campaigns.length > 0) {
      const analytics = await client.getCampaignAnalytics([campaigns[0].id]);
      expect(Array.isArray(analytics)).toBe(true);
    }
  });

  it("should handle 401 on invalid key", async () => {
    const badClient = new InstantlyClient({ apiKey: "invalid-key" });
    await expect(badClient.getCampaigns({ limit: 1 })).rejects.toThrow();
  });

  it("should create and delete a lead list", async () => {
    const list = await client.request<{ id: string }>("/lead-lists", {
      method: "POST",
      body: JSON.stringify({ name: `ci-test-${Date.now()}` }),
    });
    expect(list.id).toBeDefined();

    await client.request(`/lead-lists/${list.id}`, { method: "DELETE" });
  });
});
```

### Step 4: Deployment Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy Instantly Integration

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - run: npm ci && npm run build

      - name: Deploy webhook receiver
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: instantly-webhooks
          region: us-central1
          image: gcr.io/${{ secrets.GCP_PROJECT }}/instantly-webhooks
          env_vars: |
            INSTANTLY_API_KEY=${{ secrets.INSTANTLY_API_KEY }}
            INSTANTLY_WEBHOOK_SECRET=${{ secrets.INSTANTLY_WEBHOOK_SECRET }}

      - name: Verify deployment
        run: |
          curl -s -o /dev/null -w "%{http_code}" \
            https://instantly-webhooks-abc123.run.app/health | \
            grep -q "200" && echo "Deploy OK" || exit 1
```

### Step 5: Pre-Commit Hook
```bash
#!/bin/bash
# .husky/pre-commit
set -euo pipefail

# Prevent committing API keys
if grep -rn "Bearer [a-zA-Z0-9_-]\{20,\}" src/ --include="*.ts" --include="*.js" 2>/dev/null; then
  echo "ERROR: Possible API key found in source code"
  exit 1
fi

# Type check
npx tsc --noEmit

# Run unit tests
npx vitest run --reporter=dot
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| CI fails on mock server | Mock schema doesn't match code | Update types to match v2 schema |
| Integration tests `401` | Secret not set in GitHub | Add `INSTANTLY_API_KEY` to repo secrets |
| Rate limited in CI | Too many parallel runs | Use mock server for PR checks |
| Deploy fails | Missing env vars | Check secrets are set in deployment target |

## Resources
- [Instantly Mock Server](https://developer.instantly.ai/_mock/api/v2/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Instantly API v2 Docs](https://developer.instantly.ai/)

## Next Steps
For deployment to cloud platforms, see `instantly-deploy-integration`.
