---
name: glean-ci-integration
description: |
  CI/CD for Glean connectors with automated indexing tests and search quality validation.
  Trigger: "glean CI", "glean GitHub Actions", "glean connector CI/CD".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean CI Integration

## Overview

Set up CI/CD for Glean custom connectors: test document transforms on every PR, validate indexing against staging, and monitor search quality.

## Instructions

### GitHub Actions Workflow

```yaml
name: Glean Connector CI
on:
  pull_request:
    paths: ['src/connectors/**']
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci && npm test

  index-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && node src/connectors/run.js
        env:
          GLEAN_DOMAIN: ${{ secrets.GLEAN_DOMAIN_STAGING }}
          GLEAN_INDEXING_TOKEN: ${{ secrets.GLEAN_INDEXING_TOKEN_STAGING }}

  search-quality:
    needs: index-staging
    runs-on: ubuntu-latest
    steps:
      - run: |
          # Verify key searches return expected results
          node scripts/search-quality-check.js
        env:
          GLEAN_DOMAIN: ${{ secrets.GLEAN_DOMAIN_STAGING }}
          GLEAN_CLIENT_TOKEN: ${{ secrets.GLEAN_CLIENT_TOKEN_STAGING }}
```

### Search Quality Test

```typescript
// scripts/search-quality-check.ts
const queries = [
  { query: 'onboarding', expectDatasource: 'wiki', minResults: 1 },
  { query: 'deployment process', expectDatasource: 'confluence', minResults: 1 },
];

for (const q of queries) {
  const results = await glean.search(q.query, { datasource: q.expectDatasource });
  if (results.results.length < q.minResults) {
    throw new Error(`Search quality fail: "${q.query}" returned ${results.results.length} results`);
  }
}
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
