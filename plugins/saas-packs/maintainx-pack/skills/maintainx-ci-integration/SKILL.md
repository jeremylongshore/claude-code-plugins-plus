---
name: maintainx-ci-integration
description: |
  Integrate MaintainX API testing into CI/CD pipelines.
  Use when setting up automated testing, configuring CI workflows,
  or implementing continuous integration for MaintainX integrations.
  Trigger with phrases like "maintainx ci", "maintainx github actions",
  "maintainx pipeline", "maintainx automated testing", "maintainx ci/cd".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX CI Integration

## Overview
Configure CI/CD pipelines for MaintainX integrations with unit tests (mocked), integration tests (live API), and automated quality gates.

## Prerequisites
- Git repository with MaintainX integration
- GitHub Actions (or GitLab CI)
- Test environment MaintainX API key stored as CI secret

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/maintainx-ci.yml
name: MaintainX Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run test:integration
        env:
          MAINTAINX_API_KEY: ${{ secrets.MAINTAINX_API_KEY_STAGING }}
          MAINTAINX_ENV: staging
      - run: npm run lint
      - run: npm run typecheck

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for secrets
        run: npx gitleaks detect --source . --no-git --verbose
      - name: Audit dependencies
        run: npm audit --production --audit-level=high
```

### Step 2: Unit Tests with Mocked API

```typescript
// tests/work-orders.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');

describe('Work Order Service', () => {
  beforeEach(() => {
    process.env.MAINTAINX_API_KEY = 'test-key';
    vi.resetAllMocks();
  });

  it('creates a work order with required fields', async () => {
    const mockWO = { id: 1, title: 'Test WO', status: 'OPEN', priority: 'LOW' };
    vi.mocked(axios.create).mockReturnValue({
      post: vi.fn().mockResolvedValue({ data: mockWO }),
      interceptors: { response: { use: vi.fn() } },
    } as any);

    const { MaintainXClient } = await import('../src/client');
    const client = new MaintainXClient();
    const result = await client.createWorkOrder({ title: 'Test WO' });

    expect(result.data.id).toBe(1);
    expect(result.data.status).toBe('OPEN');
  });

  it('handles 429 rate limit with retry', async () => {
    const rateLimitErr = {
      response: { status: 429, headers: { 'retry-after': '1' } },
      isAxiosError: true,
    };
    const successResponse = { data: { id: 2, title: 'Retried' } };
    const postMock = vi.fn()
      .mockRejectedValueOnce(rateLimitErr)
      .mockResolvedValueOnce(successResponse);

    vi.mocked(axios.create).mockReturnValue({
      post: postMock,
      interceptors: { response: { use: vi.fn() } },
    } as any);

    // Test that retry logic eventually succeeds
    const { MaintainXClient } = await import('../src/client');
    const client = new MaintainXClient();
    // Wrap with retry logic from sdk-patterns
    const result = await withRetry(() => client.createWorkOrder({ title: 'Retried' }));
    expect(result.data.id).toBe(2);
  });

  it('validates work order status transitions', () => {
    const validTransitions: Record<string, string[]> = {
      OPEN: ['IN_PROGRESS', 'CLOSED'],
      IN_PROGRESS: ['ON_HOLD', 'COMPLETED', 'CLOSED'],
      ON_HOLD: ['IN_PROGRESS', 'CLOSED'],
      COMPLETED: ['CLOSED'],
      CLOSED: [],
    };

    expect(validTransitions['OPEN']).toContain('IN_PROGRESS');
    expect(validTransitions['CLOSED']).not.toContain('OPEN');
    expect(validTransitions['IN_PROGRESS']).toContain('ON_HOLD');
  });
});
```

### Step 3: Integration Tests (Live API)

```typescript
// tests/integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

const INTEGRATION = process.env.INTEGRATION === 'true';

describe.skipIf(!INTEGRATION)('MaintainX Integration', () => {
  let client: any;
  let testWorkOrderId: number;

  beforeAll(async () => {
    const { MaintainXClient } = await import('../src/client');
    client = new MaintainXClient();
  });

  it('authenticates successfully', async () => {
    const { data } = await client.getUsers({ limit: 1 });
    expect(data.users).toBeDefined();
  });

  it('creates and retrieves a work order', async () => {
    const { data: created } = await client.createWorkOrder({
      title: `CI Test - ${new Date().toISOString()}`,
      description: 'Automated CI test. Safe to delete.',
      priority: 'LOW',
    });
    testWorkOrderId = created.id;
    expect(created.id).toBeGreaterThan(0);

    const { data: fetched } = await client.getWorkOrder(created.id);
    expect(fetched.title).toContain('CI Test');
  });

  afterAll(async () => {
    // Clean up test work order
    if (testWorkOrderId) {
      try {
        await client.updateWorkOrder(testWorkOrderId, { status: 'CLOSED' });
      } catch { /* ignore cleanup errors */ }
    }
  });
});
```

### Step 4: Quality Gates

```json
{
  "scripts": {
    "test": "vitest run",
    "test:integration": "INTEGRATION=true vitest run tests/integration.test.ts",
    "lint": "eslint src/ tests/",
    "typecheck": "tsc --noEmit",
    "ci": "npm run lint && npm run typecheck && npm run test -- --coverage"
  }
}
```

## Output
- GitHub Actions workflow with unit tests, integration tests, and security scanning
- Unit tests using vitest with mocked axios responses
- Integration tests that run against a live staging MaintainX API
- Security scanning for leaked secrets and vulnerable dependencies
- Quality gate script combining lint, typecheck, and test coverage

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Integration tests fail in CI | Missing `MAINTAINX_API_KEY_STAGING` secret | Add secret in GitHub repo Settings > Secrets |
| Rate limits during test runs | Too many concurrent CI runs | Use staging environment with higher limits |
| Flaky integration tests | Network timeouts | Add retry logic, increase timeout to 30s |
| Secret scan false positives | Test fixtures with key-like strings | Add `.gitleaksignore` for known false positives |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
For deployment automation, see `maintainx-deploy-integration`.

## Examples

**GitLab CI equivalent**:

```yaml
# .gitlab-ci.yml
stages: [test, integration]

unit-tests:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm run test -- --coverage

integration-tests:
  stage: integration
  image: node:20
  only: [main, develop]
  script:
    - npm ci
    - INTEGRATION=true npm run test:integration
  variables:
    MAINTAINX_API_KEY: $MAINTAINX_API_KEY_STAGING
```
