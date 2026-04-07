---
name: appfolio-ci-integration
description: |
  Configure CI/CD pipeline for AppFolio property management integrations.
  Trigger: "appfolio CI".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio CI Integration

## Overview

Configure CI pipelines that validate AppFolio property management API integrations using a two-tier strategy. Unit tests mock the AppFolio REST client to verify tenant lookup, work order creation, and property listing logic without consuming API quota. Integration tests run against the AppFolio sandbox environment on main-branch merges only, using Basic Auth credentials stored as GitHub secrets. This keeps PR feedback fast and free while catching real API contract drift before production deploys.

## GitHub Actions Workflow

```yaml
# .github/workflows/appfolio-tests.yml
name: AppFolio API Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint && npm run typecheck
      - run: npm test -- --testPathPattern=unit  # No API credentials needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --testPathPattern=integration
        env:
          APPFOLIO_CLIENT_ID: ${{ secrets.APPFOLIO_CLIENT_ID }}
          APPFOLIO_CLIENT_SECRET: ${{ secrets.APPFOLIO_CLIENT_SECRET }}
          APPFOLIO_BASE_URL: ${{ secrets.APPFOLIO_SANDBOX_URL }}
```

## Mock-Based Unit Tests

```typescript
// tests/unit/work-order-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { createWorkOrder } from '../../src/services/work-order-service';
import * as appfolioClient from '../../src/lib/appfolio-client';

vi.mock('../../src/lib/appfolio-client');

describe('WorkOrderService', () => {
  it('creates a maintenance work order for a property', async () => {
    vi.mocked(appfolioClient.post).mockResolvedValue({
      id: 'wo-4821',
      property_id: 'prop-100',
      category: 'Plumbing',
      status: 'Open',
    });

    const result = await createWorkOrder('prop-100', 'Plumbing', 'Leaking faucet unit 3B');
    expect(result.status).toBe('Open');
    expect(appfolioClient.post).toHaveBeenCalledWith('/work_orders', {
      property_id: 'prop-100',
      category: 'Plumbing',
      description: 'Leaking faucet unit 3B',
    });
  });
});
```

## Integration Tests

```typescript
// tests/integration/tenant-lookup.test.ts
import { describe, it, expect } from 'vitest';
import { AppFolioClient } from '../../src/lib/appfolio-client';

const canRun = process.env.APPFOLIO_CLIENT_ID && process.env.APPFOLIO_CLIENT_SECRET;

describe.skipIf(!canRun)('AppFolio Tenant Lookup (live sandbox)', () => {
  const client = new AppFolioClient({
    clientId: process.env.APPFOLIO_CLIENT_ID!,
    clientSecret: process.env.APPFOLIO_CLIENT_SECRET!,
    baseUrl: process.env.APPFOLIO_BASE_URL!,
  });

  it('lists tenants for a known property', async () => {
    const tenants = await client.get('/tenants', { property_id: 'prop-100' });
    expect(Array.isArray(tenants)).toBe(true);
    expect(tenants[0]).toHaveProperty('lease_status');
  });
});
```

## CI Cost Management

```typescript
// tests/helpers/api-budget.ts
let callCount = 0;
const MAX_CALLS_PER_RUN = 25; // AppFolio sandbox has 100 req/min rate limit

export function trackApiCall(): void {
  callCount++;
  if (callCount > MAX_CALLS_PER_RUN) {
    throw new Error(
      `CI API budget exceeded: ${callCount}/${MAX_CALLS_PER_RUN} calls. ` +
      'Reduce integration test scope or split across jobs.'
    );
  }
}

export function getCallCount(): number { return callCount; }
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| 401 Unauthorized in integration job | Expired or rotated sandbox credentials | Regenerate `APPFOLIO_CLIENT_ID` and `APPFOLIO_CLIENT_SECRET` in GitHub Secrets |
| 429 Too Many Requests | Sandbox rate limit (100 req/min) hit by parallel tests | Run integration tests with `--maxWorkers=1` |
| Tenant list empty | Sandbox data periodically reset by AppFolio | Seed test property via `POST /properties` in a `beforeAll` hook |
| Typecheck fails on API response | AppFolio schema updated without notice | Regenerate types from OpenAPI spec, update interfaces |
| Integration job skipped | Branch protection rule not matching `refs/heads/main` | Verify workflow `if` condition matches your default branch name |

## Resources

- [AppFolio Stack API Documentation](https://www.appfolio.com/stack/partners/api)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `appfolio-deploy-integration`.
