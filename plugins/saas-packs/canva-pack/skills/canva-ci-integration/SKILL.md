---
name: canva-ci-integration
description: |
  Configure CI/CD pipelines for Canva Connect API integrations with GitHub Actions.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Canva API tests into your build process.
  Trigger with phrases like "canva CI", "canva GitHub Actions",
  "canva automated tests", "CI canva", "canva pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva CI Integration

## Overview

Set up CI/CD pipelines for Canva Connect API integrations. Uses MSW mock server for unit tests and real API calls for integration tests.

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/canva-integration.yml
name: Canva Integration Tests

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
      - run: npm test -- --coverage
        # Unit tests use MSW mocks — no real API calls

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: unit-tests
    env:
      CANVA_CLIENT_ID: ${{ secrets.CANVA_CLIENT_ID }}
      CANVA_CLIENT_SECRET: ${{ secrets.CANVA_CLIENT_SECRET }}
      CANVA_ACCESS_TOKEN: ${{ secrets.CANVA_ACCESS_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Verify Canva API connectivity
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $CANVA_ACCESS_TOKEN" \
            "https://api.canva.com/rest/v1/users/me")
          if [ "$HTTP_CODE" != "200" ]; then
            echo "Canva API check failed: HTTP $HTTP_CODE"
            exit 1
          fi

      - name: Run integration tests
        run: npm run test:integration
```

### Step 2: Configure Secrets

```bash
# Store OAuth credentials as GitHub secrets
gh secret set CANVA_CLIENT_ID --body "OCAxxxxxxxxxxxxxxxx"
gh secret set CANVA_CLIENT_SECRET --body "xxxxxxxxxxxxxxxx"

# For integration tests, store a long-lived access token
# (refresh it periodically via a separate workflow or manually)
gh secret set CANVA_ACCESS_TOKEN --body "cnvat_xxxxxxxxxxxxxxxx"
```

### Step 3: Unit Tests with MSW Mocks

```typescript
// tests/unit/designs.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { canvaMockServer } from '../mocks/canva-server';

beforeAll(() => canvaMockServer.listen());
afterAll(() => canvaMockServer.close());

describe('Design CRUD', () => {
  it('should create a design', async () => {
    const res = await fetch('https://api.canva.com/rest/v1/designs', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer mock-token', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        design_type: { type: 'custom', width: 1080, height: 1080 },
        title: 'CI Test Design',
      }),
    });
    expect(res.ok).toBe(true);
    const data = await res.json();
    expect(data.design.id).toBeDefined();
  });
});
```

### Step 4: Integration Tests

```typescript
// tests/integration/canva-api.test.ts
import { describe, it, expect } from 'vitest';

const TOKEN = process.env.CANVA_ACCESS_TOKEN;

describe.skipIf(!TOKEN)('Canva Connect API', () => {
  it('should authenticate and return user identity', async () => {
    const res = await fetch('https://api.canva.com/rest/v1/users/me', {
      headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.team_user.user_id).toBeDefined();
  });

  it('should list designs', async () => {
    const res = await fetch('https://api.canva.com/rest/v1/designs?limit=1', {
      headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.items).toBeInstanceOf(Array);
  });
});
```

### Step 5: Token Refresh Workflow

```yaml
# .github/workflows/refresh-canva-token.yml
name: Refresh Canva Token

on:
  schedule:
    - cron: '0 */3 * * *'  # Every 3 hours (tokens expire in ~4 hours)

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Refresh Canva access token
        run: |
          BASIC_AUTH=$(echo -n "${{ secrets.CANVA_CLIENT_ID }}:${{ secrets.CANVA_CLIENT_SECRET }}" | base64)
          RESPONSE=$(curl -s -X POST "https://api.canva.com/rest/v1/oauth/token" \
            -H "Authorization: Basic $BASIC_AUTH" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "grant_type=refresh_token&refresh_token=${{ secrets.CANVA_REFRESH_TOKEN }}")

          NEW_ACCESS=$(echo "$RESPONSE" | jq -r '.access_token')
          NEW_REFRESH=$(echo "$RESPONSE" | jq -r '.refresh_token')

          if [ "$NEW_ACCESS" != "null" ]; then
            gh secret set CANVA_ACCESS_TOKEN --body "$NEW_ACCESS"
            gh secret set CANVA_REFRESH_TOKEN --body "$NEW_REFRESH"
            echo "Token refreshed successfully"
          else
            echo "Token refresh failed: $RESPONSE"
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Integration test 401 | Token expired | Run refresh workflow or re-authorize |
| Secret not found | Missing `gh secret set` | Add secret via CLI |
| Mock not matching | URL mismatch | Verify full `api.canva.com/rest/v1` prefix |
| Rate limited in CI | Parallel test runs | Serialize integration tests |

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [MSW for API Mocking](https://mswjs.io/)

## Next Steps

For deployment patterns, see `canva-deploy-integration`.
