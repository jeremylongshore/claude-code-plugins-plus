---
name: hex-ci-integration
description: |
  Configure Hex CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Hex tests into your build process.
  Trigger with phrases like "hex CI", "hex GitHub Actions",
  "hex automated tests", "CI hex".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex CI Integration

## Overview

Set up CI/CD for Hex data analytics integrations: run unit tests with mocked project run and connection responses on every PR, trigger live Hex project runs and validate outputs on merge to main. Hex provides collaborative data notebooks with scheduled runs and API-triggered execution, so CI pipelines verify data transform logic, trigger post-deploy dashboard refreshes, and monitor run status.

## GitHub Actions Workflow

```yaml
# .github/workflows/hex-ci.yml
name: Hex CI
on:
  pull_request:
    paths: ['src/hex/**', 'tests/**']
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

  trigger-hex-refresh:
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
          HEX_API_TOKEN: ${{ secrets.HEX_API_TOKEN }}
          HEX_PROJECT_ID: ${{ vars.HEX_PROJECT_ID }}
```

## Mock-Based Unit Tests

```typescript
// tests/hex-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { triggerProjectRun, getRunStatus } from '../src/hex-service';

vi.mock('../src/hex-client', () => ({
  HexClient: vi.fn().mockImplementation(() => ({
    runProject: vi.fn().mockResolvedValue({
      runId: 'run_abc123',
      projectId: 'proj_xyz',
      status: 'running',
      startedAt: '2026-04-01T10:00:00Z',
    }),
    getRunStatus: vi.fn().mockResolvedValue({
      runId: 'run_abc123',
      status: 'completed',
      elapsedMs: 4500,
      outputs: { row_count: 1250, last_updated: '2026-04-01T10:00:04Z' },
    }),
    listProjects: vi.fn().mockResolvedValue({
      projects: [{ id: 'proj_xyz', title: 'Revenue Dashboard' }],
    }),
  })),
}));

describe('Hex Service', () => {
  it('triggers a project run and returns run ID', async () => {
    const result = await triggerProjectRun('proj_xyz', { triggered_by: 'ci' });
    expect(result.runId).toBe('run_abc123');
    expect(result.status).toBe('running');
  });

  it('polls run status until complete', async () => {
    const status = await getRunStatus('run_abc123');
    expect(status.status).toBe('completed');
    expect(status.outputs.row_count).toBe(1250);
  });
});
```

## Integration Tests

```typescript
// tests/integration/hex.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasToken = !!process.env.HEX_API_TOKEN;

describe.skipIf(!hasToken)('Hex Live API', () => {
  it('triggers a project run via API', async () => {
    const res = await fetch(
      `https://app.hex.tech/api/v1/project/${process.env.HEX_PROJECT_ID}/run`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.HEX_API_TOKEN}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ inputParams: { triggered_by: 'ci' }, updateCacheResult: true }),
      },
    );
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('runId');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid or expired API token | Regenerate at app.hex.tech account settings |
| `404 Project not found` | Wrong project ID | Verify `HEX_PROJECT_ID` matches the Hex dashboard URL |
| Run status stuck on `running` | Long-running query or connection issue | Set timeout and poll interval (max 5 min) |
| `inputParams` rejected | Parameter name mismatch | Match param names exactly to Hex project input cells |
| Rate limit (429) | Too many run triggers | Deduplicate CI triggers and add cooldown between runs |

## Resources

- [Hex API Reference](https://learn.hex.tech/docs/develop-logic/hex-api/api-reference)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment patterns, see `hex-deploy-integration`.
