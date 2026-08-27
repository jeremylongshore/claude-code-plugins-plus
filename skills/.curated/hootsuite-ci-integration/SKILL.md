---
name: hootsuite-ci-integration
description: 'Configure Hootsuite CI/CD integration with GitHub Actions and testing.

  Use when setting up automated testing, configuring CI pipelines,

  or integrating Hootsuite tests into your build process.

  Trigger with phrases like "hootsuite CI", "hootsuite GitHub Actions",

  "hootsuite automated tests", "CI hootsuite".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite CI Integration

## Overview

Set up CI/CD for Hootsuite social media management integrations: run unit tests with mocked post scheduling and analytics responses on every PR, validate live API connectivity for social profile queries on merge to main. Hootsuite's API handles scheduled posts, social analytics, and multi-network publishing, so CI pipelines verify scheduling logic, content validation rules, and analytics data aggregation.

## GitHub Actions Workflow

```yaml
# .github/workflows/hootsuite-ci.yml
name: Hootsuite CI
on:
  pull_request:
    paths: ['src/hootsuite/**', 'tests/**']
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
          HOOTSUITE_CLIENT_ID: ${{ secrets.HOOTSUITE_CLIENT_ID }}
          HOOTSUITE_CLIENT_SECRET: ${{ secrets.HOOTSUITE_CLIENT_SECRET }}
          HOOTSUITE_REFRESH_TOKEN: ${{ secrets.HOOTSUITE_REFRESH_TOKEN }}
```

## Mock-Based Unit Tests

```typescript
// tests/hootsuite-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { schedulePost, getPostAnalytics } from '../src/hootsuite-service';

vi.mock('../src/hootsuite-client', () => ({
  HootsuiteClient: vi.fn().mockImplementation(() => ({
    createMessage: vi.fn().mockResolvedValue({
      id: 'msg_abc123',
      state: 'SCHEDULED',
      scheduledSendTime: '2026-04-07T14:00:00Z',
      socialProfileIds: ['sp_twitter', 'sp_linkedin'],
    }),
    getAnalytics: vi.fn().mockResolvedValue({
      postId: 'msg_abc123',
      metrics: { impressions: 1200, clicks: 85, engagement_rate: 0.071 },
    }),
    listSocialProfiles: vi.fn().mockResolvedValue({
      profiles: [
        { id: 'sp_twitter', type: 'TWITTER', name: '@company' },
        { id: 'sp_linkedin', type: 'LINKEDIN', name: 'Company Page' },
      ],
    }),
  })),
}));

describe('Hootsuite Service', () => {
  it('schedules a multi-network post', async () => {
    const result = await schedulePost('Launch day!', {
      profiles: ['sp_twitter', 'sp_linkedin'],
      scheduledTime: '2026-04-07T14:00:00Z',
    });
    expect(result.state).toBe('SCHEDULED');
    expect(result.socialProfileIds).toHaveLength(2);
  });

  it('retrieves post analytics', async () => {
    const analytics = await getPostAnalytics('msg_abc123');
    expect(analytics.metrics.engagement_rate).toBeGreaterThan(0.05);
  });
});
```

## Integration Tests

```typescript
// tests/integration/hootsuite.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasCredentials = !!process.env.HOOTSUITE_CLIENT_ID;

describe.skipIf(!hasCredentials)('Hootsuite Live API', () => {
  it('lists social profiles via OAuth', async () => {
    const tokenRes = await fetch('https://platform.hootsuite.com/oauth2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: process.env.HOOTSUITE_CLIENT_ID!,
        client_secret: process.env.HOOTSUITE_CLIENT_SECRET!,
        refresh_token: process.env.HOOTSUITE_REFRESH_TOKEN!,
      }),
    });
    const { access_token } = await tokenRes.json();
    const res = await fetch('https://platform.hootsuite.com/v1/socialProfiles', {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(res.status).toBe(200);
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Refresh token expired | Re-authorize OAuth flow and update `HOOTSUITE_REFRESH_TOKEN` secret |
| Post scheduling fails | Social profile disconnected | Verify profile connections in Hootsuite dashboard |
| Analytics returns empty | Post too recent (< 24h) | Wait for analytics processing or use older post IDs |
| Rate limit (429) | Exceeded 300 requests/min | Add request throttling and reduce parallel test concurrency |
| Duplicate post detected | Same content scheduled twice | Add idempotency key or content hash check before scheduling |

## Prerequisites

- CI secret references, a sandbox social profile or draft-only API target, fictitious fixtures, protected branches, and a rollback mechanism.

## Instructions

1. Run mocked tests first, including malformed payload, denied account, approval-required, audience mismatch, quota, and cancellation cases.
2. Run a bounded sandbox integration with idempotency; prohibit real public-profile destinations and literal tokens in CI.
3. Emit aggregate counts, opaque IDs, approval/audience policy revisions only; fail on unexpected scope, copy leakage, or public-post path.
4. Canary draft scheduling after protected review, verify no-publication behavior, and restore the last-known-good revision on failure.

## Output

Publish a CI receipt with commit SHA, fixture revision, sandbox profile, test totals, policy checks, draft-canary outcome, and rollback reference. Exclude copy, media, handles, and secrets.

## Examples

`sha=abc123; fixtures=v5; profile=ci-synthetic; tests=18/18; approval=pass; public_posts=0; canary=not-promoted` is a valid pre-production receipt.

## Resources

- [Hootsuite Developer Portal](https://developer.hootsuite.com/)
- [Hootsuite REST API Reference](https://developer.hootsuite.com/docs/api)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment, see `hootsuite-deploy-integration`.
