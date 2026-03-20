---
name: apollo-ci-integration
description: |
  Configure Apollo.io CI/CD integration.
  Use when setting up automated testing, continuous integration,
  or deployment pipelines for Apollo integrations.
  Trigger with phrases like "apollo ci", "apollo github actions",
  "apollo pipeline", "apollo ci/cd", "apollo automated tests".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo CI Integration

## Overview
Set up CI/CD pipelines for Apollo.io integrations with GitHub Actions workflows, secret management, MSW-based mock testing, integration test suites, and deployment gating.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- GitHub repository with Actions enabled
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Store Secrets in GitHub
```bash
# Add Apollo API key as a GitHub Actions secret
gh secret set APOLLO_API_KEY --body "$APOLLO_API_KEY"

# Add webhook secret if using webhooks
gh secret set APOLLO_WEBHOOK_SECRET --body "$APOLLO_WEBHOOK_SECRET"
```

### Step 2: Create the CI Workflow
```yaml
# .github/workflows/apollo-ci.yml
name: Apollo CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm test
        env:
          APOLLO_MOCK_ENABLED: 'true'

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
      - name: Apollo Health Check
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST https://api.apollo.io/v1/people/search \
            -H "Content-Type: application/json" \
            -d "{\"api_key\": \"${{ secrets.APOLLO_API_KEY }}\", \"per_page\": 1}")
          if [ "$STATUS" != "200" ]; then
            echo "Apollo API health check failed: HTTP $STATUS"
            exit 1
          fi
          echo "Apollo API health check passed"
```

### Step 3: Write MSW-Based Unit Tests
```typescript
// src/__tests__/apollo-search.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const mockServer = setupServer(
  http.post('https://api.apollo.io/v1/people/search', () =>
    HttpResponse.json({
      people: [{ id: '1', name: 'Jane Doe', title: 'VP Sales', email: 'jane@test.com' }],
      pagination: { page: 1, per_page: 25, total_entries: 1 },
    }),
  ),
  http.post('https://api.apollo.io/v1/people/match', () =>
    HttpResponse.json({
      person: { id: '1', name: 'Jane Doe', email: 'jane@test.com', title: 'VP Sales' },
    }),
  ),
);

beforeAll(() => mockServer.listen());
afterEach(() => mockServer.resetHandlers());
afterAll(() => mockServer.close());

describe('People Search', () => {
  it('returns contacts for a domain', async () => {
    const { searchPeople } = await import('../workflows/lead-search');
    const result = await searchPeople({ domains: ['test.com'] });
    expect(result.people).toHaveLength(1);
    expect(result.people[0].name).toBe('Jane Doe');
  });

  it('handles API errors gracefully', async () => {
    mockServer.use(
      http.post('https://api.apollo.io/v1/people/search', () =>
        HttpResponse.json({ message: 'Rate limited' }, { status: 429 }),
      ),
    );
    const { searchPeople } = await import('../workflows/lead-search');
    await expect(searchPeople({ domains: ['test.com'] })).rejects.toThrow();
  });
});
```

### Step 4: Write Integration Tests (Run Against Live API)
```typescript
// src/__tests__/integration/apollo-live.test.ts
import { describe, it, expect } from 'vitest';
import axios from 'axios';

const SKIP = !process.env.APOLLO_API_KEY;
const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
  headers: { 'Content-Type': 'application/json' },
});

describe.skipIf(SKIP)('Apollo Live Integration', () => {
  it('searches for people at apollo.io', async () => {
    const { data } = await client.post('/people/search', {
      q_organization_domains: ['apollo.io'],
      per_page: 5,
    });
    expect(data.people.length).toBeGreaterThan(0);
    expect(data.pagination.total_entries).toBeGreaterThan(0);
  });

  it('enriches organization by domain', async () => {
    const { data } = await client.get('/organizations/enrich', {
      params: { domain: 'apollo.io' },
    });
    expect(data.organization).toBeDefined();
    expect(data.organization.name).toContain('Apollo');
  });
});
```

### Step 5: Add Pre-Merge Validation
```yaml
# Add to .github/workflows/apollo-ci.yml
  pre-merge-check:
    runs-on: ubuntu-latest
    needs: [lint-and-typecheck, unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - name: Validate Apollo client builds
        run: node -e "require('./dist/apollo/client')"
      - name: Check for leaked secrets
        run: |
          if grep -rn 'api_key.*=.*[a-zA-Z0-9]\{20,\}' src/ --include='*.ts' --include='*.js'; then
            echo "Potential hardcoded API key found!"
            exit 1
          fi
          echo "No hardcoded secrets found"
```

## Output
- GitHub Actions workflow with lint, typecheck, unit test, and integration test jobs
- GitHub Secrets configuration for `APOLLO_API_KEY` and `APOLLO_WEBHOOK_SECRET`
- MSW mock server for unit tests (no API calls in CI)
- Live integration tests gated to `main` branch pushes only
- Pre-merge validation with build check and secret scanning

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found in CI | Verify secret name with `gh secret list` |
| Tests timeout | Increase vitest timeout, ensure mocks are used for unit tests |
| Rate limited in CI | Unit tests must use MSW mocks; integration tests run only on main |
| Health check fails | Check [status.apollo.io](https://status.apollo.io); do not block PR on Apollo outages |

## Examples

### Run CI Locally Before Pushing
```bash
# Run the same checks CI will run
npm run lint && npm run typecheck && npm test
# Optionally run integration tests with live API
APOLLO_API_KEY=$APOLLO_API_KEY npm run test:integration
```

## Resources
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
Proceed to `apollo-deploy-integration` for deployment configuration.
