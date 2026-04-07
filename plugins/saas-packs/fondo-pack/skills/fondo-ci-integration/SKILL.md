---
name: fondo-ci-integration
description: |
  Automate financial reporting workflows that complement Fondo with CI/CD
  pipelines for expense tracking, budget alerts, and financial data validation.
  Trigger: "fondo CI", "fondo automation", "fondo financial alerts".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo CI Integration

## Overview

Set up CI/CD for Fondo startup tax and bookkeeping integrations: run unit tests with mocked filing and compliance data on every PR, validate live API connectivity for tax filing status and bookkeeping records on merge to main. Fondo handles R&D tax credits, quarterly filings, and ongoing bookkeeping, so CI pipelines verify compliance data transforms, filing deadline monitoring, and automated alert workflows.

## GitHub Actions Workflow

```yaml
# .github/workflows/fondo-ci.yml
name: Fondo CI
on:
  pull_request:
    paths: ['src/fondo/**', 'tests/**']
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
          FONDO_API_KEY: ${{ secrets.FONDO_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/fondo-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { checkFilingDeadlines } from '../src/fondo-service';

vi.mock('../src/fondo-client', () => ({
  FondoClient: vi.fn().mockImplementation(() => ({
    listFilings: vi.fn().mockResolvedValue({
      filings: [
        { id: 'fil_q1', type: '941', quarter: 'Q1-2026', status: 'filed', due_date: '2026-04-30' },
        { id: 'fil_q2', type: '941', quarter: 'Q2-2026', status: 'pending', due_date: '2026-07-31' },
      ],
    }),
    getComplianceStatus: vi.fn().mockResolvedValue({
      r_and_d_credit: { status: 'eligible', estimated: 45000 },
      state_filings: { ca: 'current', de: 'current' },
    }),
    getBookkeepingSummary: vi.fn().mockResolvedValue({
      month: '2026-03', revenue: 120000, expenses: 85000, net: 35000,
    }),
  })),
}));

describe('Fondo Service', () => {
  it('identifies upcoming filing deadlines', async () => {
    const deadlines = await checkFilingDeadlines();
    expect(deadlines.pending).toHaveLength(1);
    expect(deadlines.pending[0].type).toBe('941');
  });
});
```

## Integration Tests

```typescript
// tests/integration/fondo.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.FONDO_API_KEY;

describe.skipIf(!hasKey)('Fondo Live API', () => {
  it('retrieves compliance status', async () => {
    const res = await fetch('https://api.fondo.com/v1/compliance/status', {
      headers: { Authorization: `Bearer ${process.env.FONDO_API_KEY}` },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('state_filings');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at fondo.com dashboard settings |
| Empty filings list | No active filings for entity | Verify correct entity ID in API requests |
| Compliance data stale | Sync delay from accounting system | Add retry logic for recently updated records |
| Rate limit (429) | Too many requests in test suite | Serialize integration tests and add throttling |
| Missing R&D credit data | Entity not enrolled in R&D program | Check enrollment status before querying credit endpoint |

## Resources

- [Fondo Platform](https://www.fondo.com/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment patterns, see `fondo-deploy-integration`.
