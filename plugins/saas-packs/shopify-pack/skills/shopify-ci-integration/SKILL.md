---
name: shopify-ci-integration
description: |
  Configure CI/CD pipelines for Shopify apps with GitHub Actions, API version testing,
  and Shopify CLI deployment.
  Trigger with phrases like "shopify CI", "shopify GitHub Actions",
  "shopify automated tests", "CI shopify", "shopify deploy pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify CI Integration

## Overview

Set up CI/CD pipelines for Shopify apps using GitHub Actions, including API version compatibility testing, Shopify CLI deployment, and extension validation.

## Prerequisites

- GitHub repository with Actions enabled
- Shopify Partner account with CLI access
- Test store access token for integration tests

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/shopify-ci.yml
name: Shopify App CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  SHOPIFY_API_VERSION: "2024-10"

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test -- --coverage
        env:
          SHOPIFY_API_KEY: ${{ secrets.SHOPIFY_API_KEY }}
          SHOPIFY_API_SECRET: ${{ secrets.SHOPIFY_API_SECRET }}

  integration-test:
    runs-on: ubuntu-latest
    needs: lint-and-test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run Shopify integration tests
        run: npm run test:integration
        env:
          SHOPIFY_STORE: ${{ secrets.SHOPIFY_TEST_STORE }}
          SHOPIFY_ACCESS_TOKEN: ${{ secrets.SHOPIFY_TEST_TOKEN }}
          SHOPIFY_API_KEY: ${{ secrets.SHOPIFY_API_KEY }}
          SHOPIFY_API_SECRET: ${{ secrets.SHOPIFY_API_SECRET }}

  api-version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for deprecated API version
        run: |
          # Ensure we're not using an expired API version
          VERSION=$(grep -r "apiVersion" src/ --include="*.ts" -h | head -1 | grep -oP '\d{4}-\d{2}')
          echo "Using API version: $VERSION"

          # Check if version is still supported
          SUPPORTED=$(curl -sf -H "X-Shopify-Access-Token: ${{ secrets.SHOPIFY_TEST_TOKEN }}" \
            "https://${{ secrets.SHOPIFY_TEST_STORE }}/admin/api/versions.json" \
            | jq -r ".supported_versions[] | select(.handle == \"$VERSION\") | .supported")

          if [ "$SUPPORTED" != "true" ]; then
            echo "::warning::API version $VERSION is no longer supported!"
            exit 1
          fi

  deploy:
    runs-on: ubuntu-latest
    needs: [lint-and-test, integration-test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm run build
      - name: Deploy with Shopify CLI
        run: npx shopify app deploy --force
        env:
          SHOPIFY_CLI_PARTNERS_TOKEN: ${{ secrets.SHOPIFY_PARTNERS_TOKEN }}
```

### Step 2: Configure Secrets

```bash
# Store these in GitHub repository secrets
gh secret set SHOPIFY_API_KEY --body "your_api_key"
gh secret set SHOPIFY_API_SECRET --body "your_api_secret"
gh secret set SHOPIFY_TEST_STORE --body "your-dev-store.myshopify.com"
gh secret set SHOPIFY_TEST_TOKEN --body "shpat_test_token"
gh secret set SHOPIFY_PARTNERS_TOKEN --body "your_partners_cli_token"
```

### Step 3: Integration Test Structure

```typescript
// tests/integration/shopify.test.ts
import { describe, it, expect, beforeAll } from "vitest";

const SKIP = !process.env.SHOPIFY_ACCESS_TOKEN;

describe.skipIf(SKIP)("Shopify Integration", () => {
  let client: any;

  beforeAll(() => {
    client = getGraphqlClient(process.env.SHOPIFY_STORE!);
  });

  it("should connect to store", async () => {
    const response = await client.request("{ shop { name } }");
    expect(response.data.shop.name).toBeTruthy();
  });

  it("should have required scopes", async () => {
    const response = await client.request(`{
      app { installation { accessScopes { handle } } }
    }`);
    const scopes = response.data.app.installation.accessScopes.map(
      (s: any) => s.handle
    );
    expect(scopes).toContain("read_products");
    expect(scopes).toContain("read_orders");
  });

  it("should query products within rate limits", async () => {
    const response = await client.request(`{
      products(first: 5) {
        edges { node { id title } }
      }
    }`);
    expect(response.extensions.cost.actualQueryCost).toBeLessThan(100);
  });
});
```

## Output

- CI pipeline with lint, typecheck, unit tests, and integration tests
- API version deprecation monitoring
- Automated deployment via Shopify CLI
- Integration tests running against a test store

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `SHOPIFY_PARTNERS_TOKEN` invalid | Token expired | Regenerate at partners.shopify.com |
| Integration tests timeout | Rate limited | Add delays or use test store with Plus |
| API version check fails | Deprecated version | Update to latest supported version |
| Deploy fails | App config mismatch | Run `shopify app config push` first |

## Examples

### Shopify CLI Token for CI

```bash
# Generate a CLI token for CI (no interactive login needed)
# Go to: partners.shopify.com > Settings > CLI tokens
# Create a new token and save as SHOPIFY_PARTNERS_TOKEN secret
```

## Resources

- [Shopify CLI for CI/CD](https://shopify.dev/docs/apps/build/cli-for-apps/ci-cd)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Shopify App Deployment](https://shopify.dev/docs/apps/build/cli-for-apps/deploy)

## Next Steps

For deployment patterns, see `shopify-deploy-integration`.
