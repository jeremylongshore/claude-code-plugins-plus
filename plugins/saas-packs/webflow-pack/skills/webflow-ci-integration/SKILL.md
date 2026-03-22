---
name: webflow-ci-integration
description: |
  Configure Webflow CI/CD with GitHub Actions — automated CMS validation,
  integration tests with test tokens, and publish-on-merge workflows.
  Use when setting up automated testing or CI pipelines for Webflow integrations.
  Trigger with phrases like "webflow CI", "webflow GitHub Actions",
  "webflow automated tests", "CI webflow", "webflow pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow CI Integration

## Overview

Set up CI/CD pipelines for Webflow Data API v2 integrations with GitHub Actions.
Includes unit tests with mocked SDK, integration tests with test tokens, CMS schema
validation, and automated publish-on-merge workflows.

## Prerequisites

- GitHub repository with Actions enabled
- Webflow API token (test environment) stored as GitHub secret
- `webflow-api` SDK with vitest test suite

## Instructions

### Step 1: Store Secrets

```bash
# Store Webflow test token as GitHub secret
gh secret set WEBFLOW_API_TOKEN --body "your-test-token"
gh secret set WEBFLOW_SITE_ID --body "your-test-site-id"

# For production deployments
gh secret set WEBFLOW_API_TOKEN_PROD --body "your-prod-token"
```

### Step 2: Unit Test Workflow

Tests that mock the SDK — run on every PR, no API calls:

```yaml
# .github/workflows/webflow-test.yml
name: Webflow Integration Tests

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

  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm run lint
```

### Step 3: Integration Test Workflow

Tests against the real Webflow API — run only on main branch with secrets:

```yaml
# .github/workflows/webflow-integration.yml
name: Webflow Integration Tests

on:
  push:
    branches: [main]
  workflow_dispatch: # Manual trigger

jobs:
  integration:
    runs-on: ubuntu-latest
    # Only run if secrets are available
    if: ${{ vars.WEBFLOW_TESTS_ENABLED == 'true' }}
    env:
      WEBFLOW_API_TOKEN: ${{ secrets.WEBFLOW_API_TOKEN }}
      WEBFLOW_SITE_ID: ${{ secrets.WEBFLOW_SITE_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Verify Webflow connectivity
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
            https://api.webflow.com/v2/sites)
          if [ "$HTTP_CODE" != "200" ]; then
            echo "Webflow API returned HTTP $HTTP_CODE"
            exit 1
          fi
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 4: Integration Test Example

```typescript
// tests/integration/webflow.integration.test.ts
import { describe, it, expect } from "vitest";
import { WebflowClient } from "webflow-api";

const SKIP = !process.env.WEBFLOW_API_TOKEN;

describe.skipIf(SKIP)("Webflow API Integration", () => {
  const webflow = new WebflowClient({
    accessToken: process.env.WEBFLOW_API_TOKEN!,
  });
  const siteId = process.env.WEBFLOW_SITE_ID!;

  it("should list sites", async () => {
    const { sites } = await webflow.sites.list();
    expect(sites).toBeDefined();
    expect(sites!.length).toBeGreaterThan(0);
  });

  it("should get site details", async () => {
    const site = await webflow.sites.get(siteId);
    expect(site.id).toBe(siteId);
    expect(site.displayName).toBeDefined();
  });

  it("should list collections", async () => {
    const { collections } = await webflow.collections.list(siteId);
    expect(collections).toBeDefined();
    for (const col of collections!) {
      expect(col.id).toBeDefined();
      expect(col.displayName).toBeDefined();
      expect(col.fields).toBeDefined();
    }
  });

  it("should handle rate limits gracefully", async () => {
    // The SDK auto-retries on 429 — this should not throw
    const promises = Array.from({ length: 5 }, () =>
      webflow.sites.list()
    );
    const results = await Promise.all(promises);
    expect(results.every(r => r.sites!.length > 0)).toBe(true);
  });
});
```

### Step 5: CMS Schema Validation

Ensure your code matches the live Webflow collection schema:

```typescript
// tests/integration/schema-validation.test.ts
import { describe, it, expect } from "vitest";
import { WebflowClient } from "webflow-api";

const SKIP = !process.env.WEBFLOW_API_TOKEN;

describe.skipIf(SKIP)("CMS Schema Validation", () => {
  const webflow = new WebflowClient({
    accessToken: process.env.WEBFLOW_API_TOKEN!,
  });
  const siteId = process.env.WEBFLOW_SITE_ID!;

  // Define expected schema for your "Blog Posts" collection
  const EXPECTED_FIELDS = [
    { slug: "name", type: "PlainText", required: true },
    { slug: "slug", type: "PlainText", required: true },
    { slug: "post-body", type: "RichText", required: false },
    { slug: "author-name", type: "PlainText", required: false },
    { slug: "publish-date", type: "DateTime", required: false },
  ];

  it("should match expected collection schema", async () => {
    const { collections } = await webflow.collections.list(siteId);
    const blogCollection = collections!.find(c => c.slug === "blog-posts");
    expect(blogCollection).toBeDefined();

    for (const expected of EXPECTED_FIELDS) {
      const field = blogCollection!.fields!.find(f => f.slug === expected.slug);
      expect(field, `Field "${expected.slug}" should exist`).toBeDefined();
      expect(field!.type).toBe(expected.type);
    }
  });
});
```

### Step 6: Publish-on-Merge Workflow

Automatically publish Webflow site when content changes merge to main:

```yaml
# .github/workflows/webflow-publish.yml
name: Publish Webflow Site

on:
  push:
    branches: [main]
    paths:
      - "content/**"
      - "src/webflow/**"

jobs:
  sync-and-publish:
    runs-on: ubuntu-latest
    env:
      WEBFLOW_API_TOKEN: ${{ secrets.WEBFLOW_API_TOKEN_PROD }}
      WEBFLOW_SITE_ID: ${{ secrets.WEBFLOW_SITE_ID_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Sync content to Webflow CMS
        run: npm run sync:webflow
      - name: Publish site
        run: |
          curl -X POST \
            "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/publish" \
            -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"publishToWebflowSubdomain": true}'
```

## Output

- Unit test pipeline (mocked, runs on every PR)
- Integration test pipeline (real API, runs on main)
- CMS schema validation tests
- Automated publish-on-merge workflow
- GitHub secrets configured

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing `gh secret set` | Add secret via GitHub CLI |
| Integration tests timeout | Rate limited or slow API | Increase timeout, reduce parallelism |
| Schema mismatch | Collection changed in Webflow | Update expected schema in tests |
| Publish fails in CI | Wrong production token | Verify `WEBFLOW_API_TOKEN_PROD` secret |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)
- [Webflow API Reference](https://developers.webflow.com/data/reference/rest-introduction)

## Next Steps

For deployment patterns, see `webflow-deploy-integration`.
