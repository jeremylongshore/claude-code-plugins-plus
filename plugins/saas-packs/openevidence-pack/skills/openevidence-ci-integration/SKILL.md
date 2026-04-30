---
name: openevidence-ci-integration
description: 'Ci Integration for OpenEvidence.

  Trigger: "openevidence ci integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence CI Integration

## Overview

Set up CI/CD for OpenEvidence clinical decision support integrations: run unit tests with mocked evidence query and citation responses on every PR, validate live API connectivity for clinical queries on merge to main. OpenEvidence provides AI-powered medical evidence retrieval and clinical decision support, so CI pipelines verify query formatting, evidence parsing, citation extraction, and response quality scoring.

## GitHub Actions Workflow

```yaml
# .github/workflows/openevidence-ci.yml
name: OpenEvidence CI
on:
  pull_request:
    paths: ['src/openevidence/**', 'tests/**']
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
          OPENEVIDENCE_API_KEY: ${{ secrets.OPENEVIDENCE_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/openevidence-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { queryEvidence, extractCitations } from '../src/openevidence-service';

vi.mock('../src/openevidence-client', () => ({
  OpenEvidenceClient: vi.fn().mockImplementation(() => ({
    query: vi.fn().mockResolvedValue({
      answer: 'Current evidence supports early intervention with GLP-1 agonists...',
      confidence: 0.92,
      citations: [
        { title: 'NEJM 2025 Meta-Analysis', doi: '10.1056/NEJMoa2501234', year: 2025 },
        { title: 'Lancet Diabetes Review', doi: '10.1016/S2213-8587(25)00123', year: 2025 },
      ],
      evidenceLevel: 'high',
    }),
    listQueries: vi.fn().mockResolvedValue({
      queries: [{ id: 'q_abc', question: 'GLP-1 efficacy', status: 'completed' }],
    }),
  })),
}));

describe('OpenEvidence Service', () => {
  it('queries clinical evidence with citations', async () => {
    const result = await queryEvidence('GLP-1 agonist efficacy for type 2 diabetes');
    expect(result.confidence).toBeGreaterThan(0.9);
    expect(result.citations).toHaveLength(2);
  });

  it('extracts citation DOIs from response', async () => {
    const citations = await extractCitations('q_abc');
    expect(citations[0].doi).toMatch(/^10\.\d+/);
  });
});
```

## Integration Tests

```typescript
// tests/integration/openevidence.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.OPENEVIDENCE_API_KEY;

describe.skipIf(!hasKey)('OpenEvidence Live API', () => {
  it('queries clinical evidence', async () => {
    const res = await fetch('https://api.openevidence.com/v1/query', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENEVIDENCE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question: 'Aspirin dosing for secondary prevention' }),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('answer');
    expect(body).toHaveProperty('citations');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at openevidence.com account settings |
| Empty citations array | Query too vague for evidence matching | Use specific clinical terms with condition and intervention |
| Low confidence score | Insufficient published evidence | Check evidence level field and handle `low` confidence gracefully |
| Rate limit (429) | Too many queries in test suite | Add throttling between clinical queries (1 req/sec) |
| Response timeout | Complex query requiring deep search | Increase fetch timeout to 30s for clinical evidence lookups |

## Resources

- [OpenEvidence Platform](https://www.openevidence.com/)
- [OpenEvidence API Documentation](https://docs.openevidence.com/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `openevidence-deploy-integration`.
