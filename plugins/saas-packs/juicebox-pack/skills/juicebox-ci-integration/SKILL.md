---
name: juicebox-ci-integration
description: |
  Configure Juicebox CI/CD.
  Trigger: "juicebox ci", "juicebox pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox CI Integration

## Overview

Set up CI/CD for Juicebox AI data analysis integrations: run unit tests with mocked dataset and analysis responses on every PR, validate live API connectivity for data queries on merge to main. Juicebox provides AI-powered data exploration and visualization, so CI pipelines verify dataset upload logic, analysis execution, and result parsing workflows.

## GitHub Actions Workflow

```yaml
# .github/workflows/juicebox-ci.yml
name: Juicebox CI
on:
  pull_request:
    paths: ['src/juicebox/**', 'tests/**']
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
          JUICEBOX_API_KEY: ${{ secrets.JUICEBOX_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/juicebox-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { analyzeDataset, getAnalysisResults } from '../src/juicebox-service';

vi.mock('../src/juicebox-client', () => ({
  JuiceboxClient: vi.fn().mockImplementation(() => ({
    createAnalysis: vi.fn().mockResolvedValue({
      analysisId: 'ana_abc123',
      status: 'processing',
      datasetId: 'ds_xyz',
    }),
    getAnalysis: vi.fn().mockResolvedValue({
      analysisId: 'ana_abc123',
      status: 'completed',
      results: {
        summary: 'Revenue increased 15% QoQ',
        charts: [{ type: 'bar', title: 'Revenue by Quarter' }],
        insights: ['Q4 drove majority of growth', 'APAC region outperformed'],
      },
    }),
    listDatasets: vi.fn().mockResolvedValue({
      datasets: [{ id: 'ds_xyz', name: 'Sales Data', rowCount: 50000 }],
    }),
  })),
}));

describe('Juicebox Service', () => {
  it('creates an analysis from dataset', async () => {
    const result = await analyzeDataset('ds_xyz', 'What drove revenue growth?');
    expect(result.analysisId).toBe('ana_abc123');
    expect(result.status).toBe('processing');
  });

  it('retrieves completed analysis with insights', async () => {
    const results = await getAnalysisResults('ana_abc123');
    expect(results.status).toBe('completed');
    expect(results.results.insights).toHaveLength(2);
  });
});
```

## Integration Tests

```typescript
// tests/integration/juicebox.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.JUICEBOX_API_KEY;

describe.skipIf(!hasKey)('Juicebox Live API', () => {
  it('lists available datasets', async () => {
    const res = await fetch('https://api.juicebox.ai/v1/datasets', {
      headers: { Authorization: `Bearer ${process.env.JUICEBOX_API_KEY}` },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('datasets');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at juicebox.ai account settings |
| Analysis stuck on `processing` | Large dataset or complex query | Increase polling timeout to 120s |
| Dataset not found (404) | Dataset ID changed or deleted | Use `listDatasets` to get a valid ID dynamically |
| Rate limit (429) | Too many concurrent analyses | Queue analyses and limit to 2 parallel runs |
| Empty insights array | Insufficient data for AI analysis | Ensure test dataset has 100+ rows with varied data |

## Resources

- [Juicebox Documentation](https://docs.juicebox.ai/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `juicebox-deploy-integration`.
