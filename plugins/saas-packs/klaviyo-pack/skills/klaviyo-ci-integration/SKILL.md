---
name: klaviyo-ci-integration
description: |
  Configure CI/CD pipelines for Klaviyo integrations with GitHub Actions.
  Use when setting up automated testing, configuring CI secrets,
  or integrating Klaviyo SDK tests into your build pipeline.
  Trigger with phrases like "klaviyo CI", "klaviyo GitHub Actions",
  "klaviyo automated tests", "CI klaviyo", "klaviyo pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo CI Integration

## Overview

Set up GitHub Actions CI/CD pipelines for Klaviyo integrations with unit tests, integration tests against the real API, and deployment automation.

## Prerequisites

- GitHub repository with Actions enabled
- Klaviyo test API key (from a test/sandbox account)
- `klaviyo-api` SDK and vitest configured

## Instructions

### Step 1: Configure GitHub Secrets

```bash
# Store Klaviyo test credentials as GitHub secrets
gh secret set KLAVIYO_PRIVATE_KEY --body "pk_test_***"
gh secret set KLAVIYO_WEBHOOK_SIGNING_SECRET --body "whsec_test_***"
```

### Step 2: CI Workflow

Create `.github/workflows/klaviyo-ci.yml`:

```yaml
name: Klaviyo Integration CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

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
      - run: npx tsc --noEmit
      - run: npm test -- --coverage
      - name: Check Klaviyo SDK version
        run: npm list klaviyo-api

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      KLAVIYO_PRIVATE_KEY: ${{ secrets.KLAVIYO_PRIVATE_KEY }}
      KLAVIYO_TEST: '1'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
      - name: Verify Klaviyo connectivity
        run: |
          curl -s -w "HTTP %{http_code}\n" -o /dev/null \
            -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
            -H "revision: 2024-10-15" \
            "https://a.klaviyo.com/api/accounts/"
```

### Step 3: Unit Test Examples

```typescript
// tests/unit/klaviyo-events.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiKeySession, EventsApi, ProfileEnum } from 'klaviyo-api';

vi.mock('klaviyo-api', () => ({
  ApiKeySession: vi.fn(),
  EventsApi: vi.fn().mockImplementation(() => ({
    createEvent: vi.fn().mockResolvedValue({ body: { data: { id: 'EVT_MOCK' } } }),
    getEvents: vi.fn().mockResolvedValue({
      body: { data: [], links: { next: null } },
    }),
  })),
  ProfileEnum: { Profile: 'profile' },
  EventEnum: { Event: 'event' },
}));

describe('Event Tracking', () => {
  let eventsApi: EventsApi;

  beforeEach(() => {
    eventsApi = new EventsApi(new ApiKeySession('pk_test'));
  });

  it('tracks a purchase event', async () => {
    const result = await eventsApi.createEvent({
      data: {
        type: 'event' as any,
        attributes: {
          metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
          profile: { data: { type: 'profile', attributes: { email: 'test@example.com' } } },
          properties: { orderId: 'ORD-TEST-001', value: 99.99 },
          time: new Date().toISOString(),
        },
      },
    });
    expect(result.body.data.id).toBe('EVT_MOCK');
  });
});
```

### Step 4: Integration Test (Gated)

```typescript
// tests/integration/klaviyo-live.test.ts
import { describe, it, expect } from 'vitest';
import { ApiKeySession, AccountsApi, ProfilesApi, ProfileEnum } from 'klaviyo-api';

const SKIP = !process.env.KLAVIYO_TEST || !process.env.KLAVIYO_PRIVATE_KEY;

describe.skipIf(SKIP)('Klaviyo Live API', () => {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

  it('authenticates successfully', async () => {
    const accountsApi = new AccountsApi(session);
    const accounts = await accountsApi.getAccounts();
    expect(accounts.body.data).toHaveLength(1);
  });

  it('creates and cleans up a test profile', async () => {
    const profilesApi = new ProfilesApi(session);
    const testEmail = `ci-test-${Date.now()}@example.com`;

    const created = await profilesApi.createProfile({
      data: {
        type: ProfileEnum.Profile,
        attributes: {
          email: testEmail,
          firstName: 'CI',
          lastName: 'Test',
          properties: { source: 'github-actions', timestamp: new Date().toISOString() },
        },
      },
    });

    expect(created.body.data.id).toBeTruthy();
    expect(created.body.data.attributes.email).toBe(testEmail);
  });
});
```

### Step 5: PR Checks Configuration

```yaml
# .github/branch-protection.yml (or set via GitHub UI)
# Required checks: unit-tests
# Integration tests: optional (only on main push)
```

## Output

- Unit tests run on every PR (mocked, no API key needed)
- Integration tests run on main branch pushes (real API)
- SDK version verified in CI
- API connectivity smoke test included

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Missing `gh secret set` | Add secret via repository settings |
| Integration test 429 | Rate limited in CI | Add delays between tests, use dedicated test key |
| Auth failures in CI | Wrong secret name | Verify secret name matches workflow env var |
| Test timeout | Slow Klaviyo response | Increase `timeout-minutes` |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest CI Configuration](https://vitest.dev/guide/ci.html)

## Next Steps

For deployment patterns, see `klaviyo-deploy-integration`.
