---
name: salesloft-ci-integration
description: |
  Set up CI/CD pipelines for SalesLoft integrations with GitHub Actions.
  Use when automating SalesLoft integration tests, validating OAuth tokens,
  or running cadence sync validation in CI.
  Trigger: "salesloft CI", "salesloft GitHub Actions", "salesloft automated tests".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft CI Integration

## Overview

GitHub Actions workflows for testing SalesLoft API integrations: unit tests with mocked responses, integration tests against the live API, and OAuth token validation.

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/salesloft-ci.yml
name: SalesLoft Integration
on:
  push:
    branches: [main]
  pull_request:

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with: { name: coverage, path: coverage/ }

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      SALESLOFT_API_KEY: ${{ secrets.SALESLOFT_TEST_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Verify SalesLoft connectivity
        run: |
          curl -sf -H "Authorization: Bearer $SALESLOFT_API_KEY" \
            https://api.salesloft.com/v2/me.json | jq '.data.email'
      - run: npm run test:integration
```

### Step 2: Configure Secrets

```bash
# Store test API key (read-only scoped)
gh secret set SALESLOFT_TEST_API_KEY --body "your-test-token"

# For webhook testing
gh secret set SALESLOFT_WEBHOOK_SECRET --body "your-webhook-secret"
```

### Step 3: Integration Test Structure

```typescript
// tests/integration/salesloft.test.ts
import { describe, it, expect } from 'vitest';
import { createClient } from '../../src/salesloft/client';

const SKIP = !process.env.SALESLOFT_API_KEY;

describe.skipIf(SKIP)('SalesLoft Integration', () => {
  const api = createClient();

  it('authenticates and returns user', async () => {
    const { data } = await api.get('/me.json');
    expect(data.data.email).toBeTruthy();
  });

  it('lists people with pagination', async () => {
    const { data } = await api.get('/people.json', {
      params: { per_page: 5 },
    });
    expect(data.metadata.paging).toHaveProperty('total_count');
    expect(data.data.length).toBeLessThanOrEqual(5);
  });

  it('lists cadences', async () => {
    const { data } = await api.get('/cadences.json', {
      params: { per_page: 5 },
    });
    expect(Array.isArray(data.data)).toBe(true);
  });

  it('handles rate limit headers', async () => {
    const resp = await api.get('/people.json', { params: { per_page: 1 } });
    expect(resp.headers).toHaveProperty('x-ratelimit-limit-per-minute');
  });
});
```

### Step 4: Pre-merge Validation

```yaml
# Branch protection: require these checks
required_status_checks:
  strict: true
  contexts:
    - "unit-tests"
```

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| Secret not found | Missing `SALESLOFT_TEST_API_KEY` | `gh secret set` |
| Integration test 401 | Token expired | Refresh and update secret |
| Rate limit in CI | Parallel runs | Use separate test API keys per branch |
| Flaky integration tests | SalesLoft maintenance | Add retry and skip conditions |

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [SalesLoft API Logs](https://developers.salesloft.com/docs/platform/guides/api-logs/)

## Next Steps

For deployment patterns, see `salesloft-deploy-integration`.
