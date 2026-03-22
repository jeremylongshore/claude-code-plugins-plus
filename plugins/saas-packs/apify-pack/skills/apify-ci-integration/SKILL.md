---
name: apify-ci-integration
description: |
  Configure CI/CD pipelines for Apify Actor builds and deployments.
  Use when automating Actor deployment via GitHub Actions,
  running integration tests against Apify, or building CI/CD for scrapers.
  Trigger: "apify CI", "apify GitHub Actions", "apify automated deploy",
  "CI apify", "apify pipeline", "auto deploy actor".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify CI Integration

## Overview

Automate Apify Actor builds, tests, and deployments using GitHub Actions. Covers test-on-PR, deploy-on-merge, integration testing with live Apify API, and Actor build verification.

## Prerequisites

- GitHub repository with Actions enabled
- Apify API token stored as GitHub secret
- Actor code in the repository

## Instructions

### Step 1: Configure GitHub Secrets

```bash
# Store Apify token for CI
gh secret set APIFY_TOKEN --body "apify_api_YOUR_CI_TOKEN"

# Optional: separate tokens for test vs production
gh secret set APIFY_TOKEN_TEST --body "apify_api_test_token"
gh secret set APIFY_TOKEN_PROD --body "apify_api_prod_token"
```

### Step 2: Create Test Workflow

Create `.github/workflows/apify-test.yml`:

```yaml
name: Apify Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - run: npm test -- --coverage

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'  # Only on merge to main
    env:
      APIFY_TOKEN: ${{ secrets.APIFY_TOKEN_TEST }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Verify Apify connection
        run: |
          curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
            https://api.apify.com/v2/users/me | jq '.data.username'

      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 10
```

### Step 3: Create Deploy Workflow

Create `.github/workflows/apify-deploy.yml`:

```yaml
name: Deploy Actor

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
      - 'package-lock.json'
      - '.actor/**'

  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      APIFY_TOKEN: ${{ secrets.APIFY_TOKEN_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build
      - run: npm test

      - name: Install Apify CLI
        run: npm install -g apify-cli

      - name: Login to Apify
        run: apify login --token $APIFY_TOKEN

      - name: Push Actor to Apify
        run: apify push

      - name: Verify deployment
        run: |
          # Get latest build status
          ACTOR_ID=$(jq -r '.name' .actor/actor.json)
          echo "Deployed Actor: $ACTOR_ID"

          # Run a smoke test with minimal input
          apify actors call $ACTOR_ID \
            --input='{"startUrls":[{"url":"https://example.com"}],"maxItems":1}' \
            --timeout=120

      - name: Notify on failure
        if: failure()
        run: |
          echo "::error::Actor deployment failed! Check build logs."
```

### Step 4: Write Integration Tests

```typescript
// tests/integration/apify.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { ApifyClient } from 'apify-client';

const SKIP_INTEGRATION = !process.env.APIFY_TOKEN;

describe.skipIf(SKIP_INTEGRATION)('Apify Integration', () => {
  let client: ApifyClient;

  beforeAll(() => {
    client = new ApifyClient({ token: process.env.APIFY_TOKEN });
  });

  it('should authenticate successfully', async () => {
    const user = await client.user().get();
    expect(user.username).toBeTruthy();
  });

  it('should run a test Actor', async () => {
    const run = await client.actor('apify/website-content-crawler').call(
      {
        startUrls: [{ url: 'https://example.com' }],
        maxCrawlPages: 1,
      },
      { timeout: 120, memory: 256 },
    );

    expect(run.status).toBe('SUCCEEDED');
    expect(run.defaultDatasetId).toBeTruthy();

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    expect(items.length).toBeGreaterThan(0);
  }, 180_000); // 3 minute timeout for this test

  it('should create and delete a named dataset', async () => {
    const name = `ci-test-${Date.now()}`;
    const dataset = await client.datasets().getOrCreate(name);
    expect(dataset.id).toBeTruthy();

    await client.dataset(dataset.id).pushItems([
      { test: true, timestamp: new Date().toISOString() },
    ]);

    const { items } = await client.dataset(dataset.id).listItems();
    expect(items).toHaveLength(1);

    // Cleanup
    await client.dataset(dataset.id).delete();
  });
});
```

### Step 5: Actor Build Verification in CI

```yaml
# .github/workflows/verify-build.yml
name: Verify Actor Build

on:
  pull_request:
    paths: ['src/**', '.actor/**', 'Dockerfile']

jobs:
  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Actor Docker image
        run: |
          docker build -t actor-test -f .actor/Dockerfile .

      - name: Verify entry point
        run: |
          # Check that the built image can at least start
          docker run --rm actor-test node -e "
            const { Actor } = require('apify');
            console.log('Actor module loaded successfully');
          "
```

## CI Configuration for apify-client Apps

For applications that call Actors (not Actor development):

```yaml
# .github/workflows/test.yml
name: Test Apify Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test
        env:
          # Unit tests should mock apify-client
          # Only set token for integration test job
          APIFY_TOKEN: ''

  integration:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration
        env:
          APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}
```

## Branch Protection Rules

```bash
# Require CI to pass before merging
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["unit-tests", "docker-build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null
}
EOF
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `APIFY_TOKEN` not set | Secret not configured | `gh secret set APIFY_TOKEN` |
| Integration test timeout | Slow Actor run | Increase timeout, use smaller input |
| Docker build fails in CI | Local-only deps | Commit `package-lock.json` |
| `apify push` fails | Not logged in | Add `apify login --token` step |
| Flaky integration tests | External service issues | Add retries, use `test.retry(2)` |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)

## Next Steps

For deployment patterns, see `apify-deploy-integration`.
