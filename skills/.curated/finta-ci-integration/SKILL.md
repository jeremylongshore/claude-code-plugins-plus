---
name: finta-ci-integration
description: 'Automate Finta data export and reporting in CI pipelines.

  Trigger with phrases like "finta CI", "finta automated reporting".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta CI Integration

## Overview

Automate checks for Finta-related integrations without exposing fundraising data or granting credentials to untrusted code.

## Prerequisites

- A CI environment with protected secrets available only to trusted, protected-branch jobs.
- Synthetic fixtures and a staging endpoint for any integration test.
- A named owner and rollback procedure for deployment-related workflow changes.

## Instructions

1. Run schema, formatting, and unit checks without provider credentials.
2. Restrict any authenticated staging check to protected branches and least-privilege secrets.
3. Use synthetic records, redact logs, and fail closed on unexpected destination, permission, or schema results.
4. Require an explicit approval before production deployment and retain the test receipt.

## Output

Emit a CI receipt containing commit SHA, checks run, synthetic fixture version, aggregate result, and redacted failure references. Do not print secrets, raw exports, or investor data.

## Examples

A pull request runs lint and fixture-based mapping tests with no secrets. After merge, a protected job validates one synthetic staging record and reports its opaque correlation ID; an unexpected field causes the deployment step to stop.

Set up CI/CD for Finta fundraising integrations: run unit tests with mocked investor pipeline data on every PR, validate live API connectivity for round and investor queries on merge to main. Finta centralizes fundraising CRM data including rounds, investor contacts, and pipeline stages, so CI focuses on verifying data sync logic, pipeline stage transitions, and automated investor reporting workflows.

## GitHub Actions Workflow

```yaml
# .github/workflows/finta-ci.yml
name: Finta CI
on:
  pull_request:
    paths: ['src/finta/**', 'tests/**']
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
          FINTA_API_KEY: ${{ secrets.FINTA_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/finta-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { summarizeRound } from '../src/finta-service';

const mockRound = {
  id: 'round_seed_01',
  name: 'Seed Round',
  target_amount: 2_000_000,
  raised_amount: 1_250_000,
  investors: [
    { name: 'Acme Ventures', committed: 500_000, stage: 'committed' },
    { name: 'Beta Capital', committed: 750_000, stage: 'committed' },
  ],
};

vi.mock('../src/finta-client', () => ({
  FintaClient: vi.fn().mockImplementation(() => ({
    getRound: vi.fn().mockResolvedValue(mockRound),
    listInvestors: vi.fn().mockResolvedValue({ investors: mockRound.investors, total: 2 }),
    getPipelineSummary: vi.fn().mockResolvedValue({ stages: { committed: 2, in_progress: 3 } }),
  })),
}));

describe('Finta Service', () => {
  it('summarizes fundraising round progress', async () => {
    const summary = await summarizeRound('round_seed_01');
    expect(summary.percentRaised).toBeCloseTo(62.5);
    expect(summary.investorCount).toBe(2);
  });
});
```

## Integration Tests

```typescript
// tests/integration/finta.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.FINTA_API_KEY;

describe.skipIf(!hasKey)('Finta Live API', () => {
  it('lists fundraising rounds', async () => {
    const res = await fetch('https://api.finta.io/v1/rounds', {
      headers: { Authorization: `Bearer ${process.env.FINTA_API_KEY}` },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('rounds');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at finta.io dashboard |
| Empty rounds list | No active fundraising rounds | Create a test round in sandbox |
| Pipeline stage mismatch | Custom stage names in workspace | Fetch stages dynamically with `listStages()` |
| Rate limit (429) | Burst of API calls in parallel tests | Serialize integration tests or add throttling |
| Investor data stale | Webhook sync delay | Add polling retry for recently updated investors |

## Resources

- [Finta API Documentation](https://docs.finta.io/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment, see `finta-deploy-integration`.
