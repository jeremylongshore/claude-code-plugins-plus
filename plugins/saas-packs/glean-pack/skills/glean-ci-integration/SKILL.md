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

Set up CI/CD for Glean enterprise search integrations: run unit tests with mocked search and indexing responses on every PR, validate connector document transforms and search quality against a staging Glean instance on merge to main. Glean indexes content across SaaS tools, so CI pipelines focus on connector data transforms, indexing API calls, and search relevance regression testing.

## GitHub Actions Workflow

```yaml
# .github/workflows/glean-ci.yml
name: Glean CI
on:
  pull_request:
    paths: ['src/connectors/**', 'tests/**']
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --reporter=verbose

  integration-tests:
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          GLEAN_API_KEY: ${{ secrets.GLEAN_API_KEY }}
          GLEAN_DOMAIN: ${{ secrets.GLEAN_DOMAIN }}
```

## Mock-Based Unit Tests

```typescript
// tests/glean-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { indexDocuments, searchDocuments } from '../src/glean-service';

vi.mock('../src/glean-client', () => ({
  GleanClient: vi.fn().mockImplementation(() => ({
    indexDocuments: vi.fn().mockResolvedValue({ indexed: 3, failed: 0 }),
    search: vi.fn().mockResolvedValue({
      results: [
        { title: 'Onboarding Guide', datasource: 'confluence', url: 'https://wiki.co/onboard' },
        { title: 'Deploy Process', datasource: 'notion', url: 'https://notion.so/deploy' },
      ],
      totalResults: 2,
    }),
    getDatasources: vi.fn().mockResolvedValue(['confluence', 'notion', 'gdrive']),
  })),
}));

describe('Glean Service', () => {
  it('indexes documents and returns count', async () => {
    const result = await indexDocuments([
      { title: 'Doc 1', body: 'Content', datasource: 'custom' },
    ]);
    expect(result.indexed).toBe(3);
    expect(result.failed).toBe(0);
  });

  it('searches across datasources', async () => {
    const results = await searchDocuments('onboarding');
    expect(results.totalResults).toBe(2);
    expect(results.results[0].datasource).toBe('confluence');
  });
});
```

## Integration Tests

```typescript
// tests/integration/glean.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.GLEAN_API_KEY;

describe.skipIf(!hasKey)('Glean Live API', () => {
  it('searches enterprise content', async () => {
    const res = await fetch(`https://${process.env.GLEAN_DOMAIN}-be.glean.com/api/v1/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GLEAN_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: 'test', pageSize: 1 }),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('results');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API token or wrong domain | Verify token at admin.glean.com |
| Indexing returns 0 documents | Document format doesn't match schema | Validate document structure against Glean connector spec |
| Search quality regression | Index not yet updated | Add wait between indexing and search quality checks |
| Datasource not found | Connector not configured in staging | Set up test datasource in Glean admin before CI runs |
| Rate limit (429) | Too many indexing calls | Batch documents (max 100 per call) and add throttling |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Glean Indexing API](https://developers.glean.com/docs/indexing_api/overview)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment patterns, see `glean-deploy-integration`.
