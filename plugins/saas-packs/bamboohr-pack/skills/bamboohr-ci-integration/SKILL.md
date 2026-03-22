---
name: bamboohr-ci-integration
description: |
  Configure CI/CD pipelines for BambooHR integrations with GitHub Actions,
  automated testing, and secret management.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating BambooHR API tests into your build process.
  Trigger with phrases like "bamboohr CI", "bamboohr GitHub Actions",
  "bamboohr automated tests", "CI bamboohr", "bamboohr pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, ci-cd]
compatible-with: claude-code
---

# BambooHR CI Integration

## Overview

Set up CI/CD pipelines for BambooHR integrations with proper secret management, unit tests with mocked API, and optional integration tests against the real BambooHR API.

## Prerequisites

- GitHub repository with Actions enabled
- BambooHR test API key (sandbox company or test account)
- npm/pnpm project with test suite configured

## Instructions

### Step 1: Configure GitHub Secrets

```bash
# Required for integration tests
gh secret set BAMBOOHR_API_KEY --body "your-test-api-key"
gh secret set BAMBOOHR_COMPANY_DOMAIN --body "your-test-company"

# Optional: webhook testing
gh secret set BAMBOOHR_WEBHOOK_SECRET --body "your-webhook-hmac-secret"
```

### Step 2: GitHub Actions Workflow

```yaml
# .github/workflows/bamboohr-integration.yml
name: BambooHR Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run daily to catch BambooHR API changes early
    - cron: '0 6 * * 1-5'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run typecheck
      - name: Unit tests (mocked BambooHR API)
        run: npm test -- --coverage --reporter=verbose
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    # Only run on main branch and schedule (not PRs from forks)
    if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
    needs: unit-tests
    env:
      BAMBOOHR_API_KEY: ${{ secrets.BAMBOOHR_API_KEY }}
      BAMBOOHR_COMPANY_DOMAIN: ${{ secrets.BAMBOOHR_COMPANY_DOMAIN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Integration tests (real BambooHR API)
        run: npm run test:integration
        timeout-minutes: 5
      - name: API health check
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -u "${BAMBOOHR_API_KEY}:x" \
            -H "Accept: application/json" \
            "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory")
          echo "BambooHR API status: $STATUS"
          [ "$STATUS" -eq 200 ] || exit 1
```

### Step 3: Test Structure

```typescript
// tests/unit/bamboohr-client.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { BambooHRClient } from '../../src/bamboohr/client';

const BASE = 'https://api.bamboohr.com/api/gateway.php/testco/v1';

const handlers = [
  http.get(`${BASE}/employees/directory`, () =>
    HttpResponse.json({
      employees: [
        { id: '1', displayName: 'Jane', jobTitle: 'Eng', department: 'Dev' },
      ],
    }),
  ),
  http.get(`${BASE}/employees/:id/`, () =>
    HttpResponse.json({ id: '1', firstName: 'Jane', lastName: 'Smith' }),
  ),
  http.post(`${BASE}/reports/custom`, () =>
    HttpResponse.json({ title: 'Report', employees: [] }),
  ),
  // Simulate rate limit
  http.get(`${BASE}/employees/ratelimited`, () =>
    new HttpResponse(null, { status: 503, headers: { 'Retry-After': '1' } }),
  ),
];

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('BambooHRClient', () => {
  const client = new BambooHRClient({ companyDomain: 'testco', apiKey: 'fake' });

  it('fetches employee directory', async () => {
    const dir = await client.getDirectory();
    expect(dir.employees).toHaveLength(1);
    expect(dir.employees[0].displayName).toBe('Jane');
  });

  it('fetches single employee with fields', async () => {
    const emp = await client.getEmployee(1, ['firstName', 'lastName']);
    expect(emp.firstName).toBe('Jane');
  });

  it('runs custom reports', async () => {
    const report = await client.customReport(['firstName', 'department']);
    expect(report.title).toBe('Report');
  });

  it('handles 503 rate limit with Retry-After', async () => {
    await expect(
      client.request('GET', '/employees/ratelimited'),
    ).rejects.toThrow(/503/);
  });
});
```

```typescript
// tests/integration/bamboohr-live.test.ts
import { describe, it, expect } from 'vitest';
import { BambooHRClient } from '../../src/bamboohr/client';

const HAS_CREDS = !!process.env.BAMBOOHR_API_KEY && !!process.env.BAMBOOHR_COMPANY_DOMAIN;

describe.skipIf(!HAS_CREDS)('BambooHR Live API', () => {
  const client = new BambooHRClient({
    companyDomain: process.env.BAMBOOHR_COMPANY_DOMAIN!,
    apiKey: process.env.BAMBOOHR_API_KEY!,
  });

  it('should fetch employee directory', async () => {
    const dir = await client.getDirectory();
    expect(dir.employees.length).toBeGreaterThan(0);
    expect(dir.employees[0]).toHaveProperty('displayName');
    expect(dir.employees[0]).toHaveProperty('jobTitle');
  }, 15_000);

  it('should run a custom report', async () => {
    const report = await client.customReport(['firstName', 'lastName', 'department']);
    expect(report).toHaveProperty('employees');
    expect(Array.isArray(report.employees)).toBe(true);
  }, 15_000);

  it('should fetch time off types', async () => {
    const types = await client.request('GET', '/meta/time_off/types');
    expect(types).toBeTruthy();
  }, 15_000);
});
```

### Step 4: PR Status Check

```yaml
# Branch protection — require these checks to pass
# Settings > Branches > Branch protection rules
required_status_checks:
  - 'unit-tests'
  # integration-tests is optional (may fail if API is down)
```

### Step 5: Scheduled API Health Monitoring

```yaml
# .github/workflows/bamboohr-health.yml
name: BambooHR API Health

on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours

jobs:
  health-check:
    runs-on: ubuntu-latest
    env:
      BAMBOOHR_API_KEY: ${{ secrets.BAMBOOHR_API_KEY }}
      BAMBOOHR_COMPANY_DOMAIN: ${{ secrets.BAMBOOHR_COMPANY_DOMAIN }}
    steps:
      - name: Check BambooHR API
        run: |
          STATUS=$(curl -s -o /tmp/response.json -w "%{http_code}" \
            -u "${BAMBOOHR_API_KEY}:x" \
            -H "Accept: application/json" \
            "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory")

          if [ "$STATUS" -ne 200 ]; then
            echo "::error::BambooHR API returned $STATUS"
            exit 1
          fi

          COUNT=$(cat /tmp/response.json | jq '.employees | length')
          echo "BambooHR API healthy: $COUNT employees"
```

## Output

- Unit test pipeline with mocked BambooHR API
- Integration test pipeline with real API (gated on secrets)
- Scheduled health monitoring workflow
- PR status checks configured
- Coverage reports uploaded

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not available in PR | Fork PR (no secrets access) | Use `if` guard on integration job |
| Integration test timeout | BambooHR API slow | Set `timeout-minutes: 5` |
| Flaky 503 in tests | Rate limiting in CI | Add retry logic to test helpers |
| Health check false alarm | BambooHR maintenance | Check status page before alerting |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [MSW for Testing](https://mswjs.io/)

## Next Steps

For deployment patterns, see `bamboohr-deploy-integration`.
