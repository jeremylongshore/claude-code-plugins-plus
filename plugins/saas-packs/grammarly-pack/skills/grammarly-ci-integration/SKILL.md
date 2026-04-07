---
name: grammarly-ci-integration
description: |
  Configure Grammarly CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Grammarly tests into your build process.
  Trigger with phrases like "grammarly CI", "grammarly GitHub Actions",
  "grammarly automated tests", "CI grammarly".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly CI Integration

## Overview

Set up CI/CD for Grammarly text analysis integrations: run unit tests with mocked grammar check and suggestion responses on every PR, validate live API connectivity for text scoring on merge to main. Grammarly's Text API provides writing quality scores, grammar corrections, and tone detection, so CI pipelines verify content quality gates, documentation linting, and automated writing feedback workflows.

## GitHub Actions Workflow

```yaml
# .github/workflows/grammarly-ci.yml
name: Grammarly CI
on:
  pull_request:
    paths: ['src/**', 'docs/**', 'tests/**']
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
          GRAMMARLY_CLIENT_ID: ${{ secrets.GRAMMARLY_CLIENT_ID }}
          GRAMMARLY_CLIENT_SECRET: ${{ secrets.GRAMMARLY_CLIENT_SECRET }}
```

## Mock-Based Unit Tests

```typescript
// tests/grammarly-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { checkDocumentation } from '../src/grammarly-service';

vi.mock('../src/grammarly-client', () => ({
  GrammarlyClient: vi.fn().mockImplementation(() => ({
    checkText: vi.fn().mockResolvedValue({
      overall_score: 87,
      alerts: [
        { type: 'grammar', message: 'Subject-verb disagreement', offset: 12, length: 5, replacements: ['are'] },
        { type: 'clarity', message: 'Consider simplifying', offset: 45, length: 20, replacements: ['use'] },
      ],
      tone: { formal: 0.8, confident: 0.7 },
    }),
    getSuggestions: vi.fn().mockResolvedValue({
      suggestions: [{ text: 'Rephrase for clarity', category: 'engagement' }],
    }),
  })),
}));

describe('Grammarly Service', () => {
  it('checks documentation quality and returns score', async () => {
    const result = await checkDocumentation('The data is ready for review.');
    expect(result.overall_score).toBeGreaterThan(80);
    expect(result.alerts).toHaveLength(2);
  });
});
```

## Integration Tests

```typescript
// tests/integration/grammarly.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasCredentials = !!process.env.GRAMMARLY_CLIENT_ID;

describe.skipIf(!hasCredentials)('Grammarly Live API', () => {
  it('analyzes text via Text API', async () => {
    const tokenRes = await fetch('https://api.grammarly.com/v1/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_id: process.env.GRAMMARLY_CLIENT_ID,
        client_secret: process.env.GRAMMARLY_CLIENT_SECRET,
        grant_type: 'client_credentials',
      }),
    });
    expect(tokenRes.status).toBe(200);
    const { access_token } = await tokenRes.json();
    expect(access_token).toBeDefined();
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid client credentials | Regenerate at developer.grammarly.com |
| OAuth token expired | Token TTL exceeded | Implement token refresh before each test run |
| Score below threshold | Content quality regression | Set minimum score in CI config (e.g., 75) and fix flagged alerts |
| Rate limit (429) | Too many text check requests | Batch text submissions and add throttling |
| Empty suggestions | Text too short for analysis | Ensure test inputs are at least 50 characters |

## Resources

- [Grammarly Developer API](https://developer.grammarly.com/)
- [Grammarly Text API Reference](https://developer.grammarly.com/docs/api)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment, see `grammarly-deploy-integration`.
