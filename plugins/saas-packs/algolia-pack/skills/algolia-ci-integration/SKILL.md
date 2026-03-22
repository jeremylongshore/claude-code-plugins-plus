---
name: algolia-ci-integration
description: |
  Configure Algolia CI/CD: GitHub Actions for index validation, automated reindexing
  on deploy, and integration testing against real Algolia indices.
  Trigger: "algolia CI", "algolia GitHub Actions", "algolia automated tests",
  "CI algolia", "algolia deploy pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia CI Integration

## Overview

Set up CI/CD pipelines for Algolia: run integration tests against a test index, validate index settings before deploy, and trigger reindexing on release.

## Prerequisites

- GitHub repository with Actions enabled
- Algolia App ID and Admin key (stored as GitHub secrets)
- npm/pnpm project with `algoliasearch` v5

## Instructions

### Step 1: Store Algolia Secrets

```bash
gh secret set ALGOLIA_APP_ID --body "YourApplicationID"
gh secret set ALGOLIA_ADMIN_KEY --body "your_admin_api_key"
gh secret set ALGOLIA_SEARCH_KEY --body "your_search_only_key"
```

### Step 2: GitHub Actions — Test & Validate

```yaml
# .github/workflows/algolia-ci.yml
name: Algolia CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      ALGOLIA_APP_ID: ${{ secrets.ALGOLIA_APP_ID }}
      ALGOLIA_ADMIN_KEY: ${{ secrets.ALGOLIA_ADMIN_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Unit tests (mocked Algolia)
        run: npm test
      - name: Integration tests (real Algolia)
        if: env.ALGOLIA_APP_ID != ''
        run: npm run test:integration
        env:
          # Use timestamped index to avoid cross-PR collision
          ALGOLIA_TEST_INDEX: ci_test_${{ github.run_id }}_products

  validate-settings:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    env:
      ALGOLIA_APP_ID: ${{ secrets.ALGOLIA_APP_ID }}
      ALGOLIA_ADMIN_KEY: ${{ secrets.ALGOLIA_ADMIN_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Validate index settings match config
        run: npx tsx scripts/validate-algolia-settings.ts
```

### Step 3: Index Settings Validation Script

```typescript
// scripts/validate-algolia-settings.ts
import { algoliasearch } from 'algoliasearch';
import expectedSettings from '../config/algolia-settings.json' assert { type: 'json' };

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

async function validateSettings() {
  const actual = await client.getSettings({ indexName: 'products' });
  const errors: string[] = [];

  // Check critical settings match
  const checks: [string, any, any][] = [
    ['searchableAttributes', actual.searchableAttributes, expectedSettings.searchableAttributes],
    ['attributesForFaceting', actual.attributesForFaceting, expectedSettings.attributesForFaceting],
    ['customRanking', actual.customRanking, expectedSettings.customRanking],
  ];

  for (const [field, actual, expected] of checks) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
      errors.push(`${field}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
  }

  if (errors.length > 0) {
    console.error('Settings drift detected:');
    errors.forEach(e => console.error(`  - ${e}`));
    process.exit(1);
  }

  console.log('All Algolia settings match expected configuration.');
}

validateSettings().catch(e => { console.error(e); process.exit(1); });
```

### Step 4: Integration Test Pattern

```typescript
// tests/integration/algolia.integration.test.ts
import { describe, it, expect, afterAll } from 'vitest';
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);
const testIndex = process.env.ALGOLIA_TEST_INDEX || `test_${Date.now()}`;

describe.skipIf(!process.env.ALGOLIA_APP_ID)('Algolia Integration', () => {
  afterAll(async () => {
    // Clean up test index
    try { await client.deleteIndex({ indexName: testIndex }); } catch {}
  });

  it('indexes records and searches', async () => {
    const { taskID } = await client.saveObjects({
      indexName: testIndex,
      objects: [
        { objectID: '1', name: 'Test Widget', category: 'tools' },
        { objectID: '2', name: 'Test Gadget', category: 'electronics' },
      ],
    });
    await client.waitForTask({ indexName: testIndex, taskID });

    const { hits, nbHits } = await client.searchSingleIndex({
      indexName: testIndex,
      searchParams: { query: 'widget' },
    });

    expect(nbHits).toBe(1);
    expect(hits[0].name).toBe('Test Widget');
  });

  it('applies filters correctly', async () => {
    await client.setSettings({
      indexName: testIndex,
      indexSettings: { attributesForFaceting: ['category'] },
    });
    // Wait for settings propagation
    await new Promise(r => setTimeout(r, 2000));

    const { hits } = await client.searchSingleIndex({
      indexName: testIndex,
      searchParams: { query: '', filters: 'category:tools' },
    });

    expect(hits.every(h => h.category === 'tools')).toBe(true);
  });
});
```

### Step 5: Deploy-Triggered Reindex

```yaml
# .github/workflows/algolia-deploy.yml
name: Algolia Reindex on Deploy

on:
  push:
    tags: ['v*']

jobs:
  reindex:
    runs-on: ubuntu-latest
    env:
      ALGOLIA_APP_ID: ${{ secrets.ALGOLIA_APP_ID }}
      ALGOLIA_ADMIN_KEY: ${{ secrets.ALGOLIA_ADMIN_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Full reindex from data source
        run: npx tsx scripts/full-reindex.ts
      - name: Verify index health
        run: npx tsx scripts/verify-index-health.ts
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not available | Secrets not set or wrong name | `gh secret list` to verify |
| Test index collision | Parallel CI runs | Use `${{ github.run_id }}` in index name |
| Integration test timeout | Network latency to Algolia | Increase vitest timeout: `{ test: { timeout: 30000 } }` |
| Settings drift | Manual dashboard change | Run settings validation in CI |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Algolia API Key Security](https://www.algolia.com/doc/guides/security/api-keys/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

For deployment patterns, see `algolia-deploy-integration`.
