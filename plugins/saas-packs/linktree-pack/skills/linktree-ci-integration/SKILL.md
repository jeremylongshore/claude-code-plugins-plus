---
name: linktree-ci-integration
description: 'Ci Integration for Linktree.

  Trigger: "linktree ci integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree CI Integration

## Overview

Configure CI pipelines that validate Linktree link-in-bio API integrations using a two-tier testing approach. Unit tests mock the Linktree REST API to verify profile retrieval, link CRUD operations, and click analytics aggregation without needing an API key. Integration tests authenticate with a real Bearer token on main-branch merges to confirm link ordering, analytics endpoints, and rate limit handling against the live Linktree API. This ensures every PR gets instant feedback while production-critical flows are verified before deploy.

## GitHub Actions Workflow

```yaml
# .github/workflows/linktree-tests.yml
name: Linktree API Tests
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
      - run: npm test -- --testPathPattern=unit  # No Bearer token needed

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
          LINKTREE_API_KEY: ${{ secrets.LINKTREE_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/unit/link-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { reorderLinks } from '../../src/services/link-service';
import * as linktreeApi from '../../src/lib/linktree-api';

vi.mock('../../src/lib/linktree-api');

describe('LinkService', () => {
  it('reorders links and returns updated positions', async () => {
    vi.mocked(linktreeApi.patch).mockResolvedValue({
      links: [
        { id: 'lnk-1', title: 'Portfolio', position: 0 },
        { id: 'lnk-2', title: 'GitHub', position: 1 },
      ],
    });

    const result = await reorderLinks(['lnk-1', 'lnk-2']);
    expect(result.links[0].position).toBe(0);
    expect(linktreeApi.patch).toHaveBeenCalledWith('/links/reorder', {
      link_ids: ['lnk-1', 'lnk-2'],
    });
  });
});
```

## Integration Tests

```typescript
// tests/integration/profile-analytics.test.ts
import { describe, it, expect } from 'vitest';
import { LinktreeClient } from '../../src/lib/linktree-api';

const canRun = !!process.env.LINKTREE_API_KEY;

describe.skipIf(!canRun)('Linktree Analytics (live API)', () => {
  const client = new LinktreeClient({
    apiKey: process.env.LINKTREE_API_KEY!,
  });

  it('fetches click analytics for the authenticated profile', async () => {
    const analytics = await client.get('/analytics', {
      period: 'last_7_days',
    });
    expect(analytics).toHaveProperty('total_clicks');
    expect(typeof analytics.total_clicks).toBe('number');
  });
});
```

## CI Cost Management

```typescript
// tests/helpers/api-budget.ts
let callCount = 0;
const MAX_CALLS_PER_RUN = 30; // Linktree API: 60 req/min for standard tier

export function trackApiCall(): void {
  callCount++;
  if (callCount > MAX_CALLS_PER_RUN) {
    throw new Error(
      `CI API budget exceeded: ${callCount}/${MAX_CALLS_PER_RUN} calls. ` +
      'Linktree standard tier allows 60 req/min — reduce test scope or add delays.'
    );
  }
}

export function getCallCount(): number { return callCount; }
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| 401 Unauthorized | Expired or revoked Bearer token | Regenerate `LINKTREE_API_KEY` in Linktree admin and update GitHub Secrets |
| 429 Rate Limited | Exceeded 60 req/min on standard tier | Add `--maxWorkers=1` and insert small delays between integration tests |
| Empty analytics response | Profile has zero traffic in test period | Use a longer `period` param or seed test clicks via the Links API |
| Link creation returns 409 | Duplicate URL already exists on profile | Add cleanup in `afterEach` to delete test links by ID |
| Integration job never runs | Branch name mismatch in workflow `if` | Confirm default branch is `main`, not `master` |

## Resources

- [Linktree Developer Documentation](https://linktr.ee/marketplace/developer)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `linktree-deploy-integration`.
