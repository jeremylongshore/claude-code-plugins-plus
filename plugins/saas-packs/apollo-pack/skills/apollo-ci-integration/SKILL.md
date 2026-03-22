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
tags: [saas, apollo, deployment, testing, ci-cd]

---
# Apollo CI Integration

## Overview
Set up CI/CD pipelines for Apollo.io integrations with GitHub Actions. Uses MSW mocks for unit tests (zero API calls), sandbox tokens for staging, and live API tests gated to main branch only. Apollo's sandbox token returns dummy data without consuming credits.

## Prerequisites
- GitHub repository with Actions enabled
- Apollo master API key + sandbox token
- Node.js 18+

## Instructions

### Step 1: Store Secrets in GitHub
```bash
# Master API key for integration tests (main branch only)
gh secret set APOLLO_API_KEY --body "$APOLLO_API_KEY"

# Sandbox token for staging tests (safe, no credits)
gh secret set APOLLO_SANDBOX_KEY --body "$APOLLO_SANDBOX_KEY"
```

### Step 2: GitHub Actions Workflow
```yaml
# .github/workflows/apollo-ci.yml
name: Apollo CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test
        # Unit tests use MSW mocks — zero API calls

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Apollo Health Check
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "x-api-key: $APOLLO_API_KEY" \
            "https://api.apollo.io/api/v1/auth/health")
          echo "Apollo API: HTTP $STATUS"
          [ "$STATUS" = "200" ] || exit 1
      - run: npm run test:integration
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for hardcoded API keys
        run: |
          if grep -rn 'x-api-key.*[a-zA-Z0-9]\{20,\}' src/ --include='*.ts' --include='*.js'; then
            echo "Potential hardcoded API key found!"
            exit 1
          fi
          echo "No hardcoded secrets"
```

### Step 3: MSW-Based Unit Tests
```typescript
// src/__tests__/apollo.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const BASE = 'https://api.apollo.io/api/v1';
const mockServer = setupServer(
  http.post(`${BASE}/mixed_people/api_search`, () =>
    HttpResponse.json({
      people: [{ id: '1', name: 'Jane Doe', title: 'VP Sales' }],
      pagination: { page: 1, per_page: 25, total_entries: 1, total_pages: 1 },
    }),
  ),
  http.post(`${BASE}/people/match`, () =>
    HttpResponse.json({
      person: { id: '1', name: 'Jane Doe', email: 'jane@test.com', title: 'VP Sales' },
    }),
  ),
  http.get(`${BASE}/auth/health`, () =>
    HttpResponse.json({ is_logged_in: true }),
  ),
);

beforeAll(() => mockServer.listen());
afterEach(() => mockServer.resetHandlers());
afterAll(() => mockServer.close());

describe('People Search', () => {
  it('returns contacts from search', async () => {
    const { searchPeople } = await import('../workflows/lead-search');
    const result = await searchPeople({ domains: ['test.com'] });
    expect(result.people).toHaveLength(1);
    expect(result.people[0].name).toBe('Jane Doe');
  });

  it('handles 429 errors', async () => {
    mockServer.use(
      http.post(`${BASE}/mixed_people/api_search`, () =>
        HttpResponse.json({ message: 'Rate limited' }, { status: 429 }),
      ),
    );
    const { searchPeople } = await import('../workflows/lead-search');
    await expect(searchPeople({ domains: ['test.com'] })).rejects.toThrow();
  });
});
```

### Step 4: Integration Tests (Live API)
```typescript
// src/__tests__/integration/apollo-live.test.ts
import { describe, it, expect } from 'vitest';
import axios from 'axios';

const SKIP = !process.env.APOLLO_API_KEY;
const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

describe.skipIf(SKIP)('Apollo Live Integration', () => {
  it('searches for people at apollo.io', async () => {
    const { data } = await client.post('/mixed_people/api_search', {
      q_organization_domains_list: ['apollo.io'],
      per_page: 5,
    });
    expect(data.people.length).toBeGreaterThan(0);
  });

  it('enriches organization by domain', async () => {
    const { data } = await client.get('/organizations/enrich', { params: { domain: 'apollo.io' } });
    expect(data.organization).toBeDefined();
    expect(data.organization.name).toContain('Apollo');
  });
});
```

## Output
- GitHub Actions workflow with lint, typecheck, unit test, integration test, and secret scan jobs
- MSW mock server for zero-API-call unit tests in PRs
- Live integration tests gated to main branch pushes only
- Apollo health check step before integration tests
- Secret scanning to prevent API key commits

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | `gh secret list` to verify, re-add with `gh secret set` |
| Rate limited in CI | Unit tests use MSW, integration tests run only on main |
| Health check fails | Check [status.apollo.io](https://status.apollo.io); skip flaky on outage |
| Hardcoded key found | Secret scan job fails the build; rotate the key immediately |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Apollo Sandbox Testing](https://docs.apollo.io/docs/test-api-key)
- [MSW (Mock Service Worker)](https://mswjs.io/)

## Next Steps
Proceed to `apollo-deploy-integration` for deployment configuration.
