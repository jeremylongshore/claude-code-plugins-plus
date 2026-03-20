---
name: juicebox-ci-integration
description: |
  Configure Juicebox CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Juicebox tests into your build process.
  Trigger with phrases like "juicebox CI", "juicebox GitHub Actions",
  "juicebox automated tests", "CI juicebox".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox CI Integration

## Overview
Set up GitHub Actions workflows that validate Juicebox API connectivity, run search and enrichment integration tests, and gate deployments on passing Juicebox checks. Juicebox uses token-based auth (`Authorization: token {username}:{api_token}`) against its people search API (800M+ profiles).

## Prerequisites
- GitHub repository with Actions enabled
- Juicebox API credentials (username + API token from https://juicebox.ai/settings)
- Node.js 18+ project with `package.json`
- `gh` CLI authenticated to the target repository

## Instructions

### Step 1: Configure GitHub Secrets

Store Juicebox credentials as repository secrets. Never commit tokens to source control.

```bash
# Set secrets via GitHub CLI
gh secret set JUICEBOX_USERNAME --body "your-username"
gh secret set JUICEBOX_API_TOKEN --body "jb_tok_xxxxxxxxxxxx"

# Production credentials (separate token with higher rate limits)
gh secret set JUICEBOX_API_TOKEN_PROD --body "jb_tok_prod_xxxxxxxxxxxx"

# Verify secrets are registered
gh secret list
```

### Step 2: Create Test Workflow

Create a GitHub Actions workflow that runs API connectivity, search validation, and enrichment tests on every push and PR.

```yaml
# .github/workflows/juicebox-tests.yml
name: Juicebox Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  JUICEBOX_USERNAME: ${{ secrets.JUICEBOX_USERNAME }}
  JUICEBOX_API_TOKEN: ${{ secrets.JUICEBOX_API_TOKEN }}

jobs:
  connectivity:
    name: API Connectivity Check
    runs-on: ubuntu-latest
    steps:
      - name: Verify Juicebox API is reachable
        run: |
          HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
            https://api.juicebox.ai/v1/me)
          if [ "$HTTP_STATUS" != "200" ]; then
            echo "::error::Juicebox API returned HTTP $HTTP_STATUS"
            exit 1
          fi
          echo "Juicebox API connectivity confirmed"

  search-validation:
    name: Search Validation
    runs-on: ubuntu-latest
    needs: connectivity
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Run search integration tests
        run: npx vitest run tests/juicebox/ --reporter=verbose

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: juicebox-test-results
          path: coverage/

  enrichment:
    name: Enrichment Test
    runs-on: ubuntu-latest
    needs: connectivity
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Validate enrichment pipeline
        run: |
          npx vitest run tests/juicebox/enrichment.test.ts --reporter=verbose
```

### Step 3: Add Integration Test Suite

Write tests that exercise real Juicebox API endpoints: authentication, people search, and profile enrichment.

```typescript
// tests/juicebox/search.integration.test.ts
import { describe, it, expect, beforeAll } from 'vitest';

const BASE_URL = 'https://api.juicebox.ai/v1';

function authHeader(): Record<string, string> {
  const username = process.env.JUICEBOX_USERNAME;
  const token = process.env.JUICEBOX_API_TOKEN;
  if (!username || !token) {
    throw new Error('JUICEBOX_USERNAME and JUICEBOX_API_TOKEN required');
  }
  return {
    'Authorization': `token ${username}:${token}`,
    'Content-Type': 'application/json',
  };
}

describe('Juicebox Search Integration', () => {
  it('authenticates with valid credentials', async () => {
    const res = await fetch(`${BASE_URL}/me`, { headers: authHeader() });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.username).toBe(process.env.JUICEBOX_USERNAME);
  });

  it('executes a people search and returns profiles', async () => {
    const res = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({
        query: 'senior software engineer in San Francisco',
        limit: 5,
      }),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.profiles).toBeDefined();
    expect(body.profiles.length).toBeGreaterThan(0);
    expect(body.profiles[0]).toHaveProperty('name');
    expect(body.profiles[0]).toHaveProperty('title');
  });

  it('rejects empty search queries', async () => {
    const res = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({ query: '', limit: 5 }),
    });
    expect(res.status).toBe(400);
  });

  it('respects search limit parameter', async () => {
    const res = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({ query: 'product manager', limit: 3 }),
    });
    const body = await res.json();
    expect(body.profiles.length).toBeLessThanOrEqual(3);
  });
});
```

```typescript
// tests/juicebox/enrichment.test.ts
import { describe, it, expect } from 'vitest';

const BASE_URL = 'https://api.juicebox.ai/v1';

function authHeader(): Record<string, string> {
  return {
    'Authorization': `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`,
    'Content-Type': 'application/json',
  };
}

describe('Juicebox Enrichment Integration', () => {
  it('enriches a profile with contact data', async () => {
    // First, search for a profile to get an ID
    const searchRes = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({ query: 'CTO startup', limit: 1 }),
    });
    const { profiles } = await searchRes.json();
    expect(profiles.length).toBeGreaterThan(0);

    // Enrich the profile
    const enrichRes = await fetch(`${BASE_URL}/profiles/${profiles[0].id}/enrich`, {
      method: 'POST',
      headers: authHeader(),
    });
    expect(enrichRes.status).toBe(200);
    const enriched = await enrichRes.json();
    expect(enriched).toHaveProperty('email');
    expect(enriched).toHaveProperty('linkedin_url');
  });

  it('returns 404 for nonexistent profile enrichment', async () => {
    const res = await fetch(`${BASE_URL}/profiles/nonexistent-id-000/enrich`, {
      method: 'POST',
      headers: authHeader(),
    });
    expect(res.status).toBe(404);
  });
});
```

### Step 4: Configure Branch Protection

Create a required-checks workflow that blocks merges until Juicebox smoke tests pass.

```yaml
# .github/workflows/required-checks.yml
name: Required Juicebox Checks

on:
  pull_request:
    branches: [main]

jobs:
  juicebox-smoke:
    name: Juicebox Smoke Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: API smoke test
        run: |
          curl -sf \
            -H "Authorization: token ${{ secrets.JUICEBOX_USERNAME }}:${{ secrets.JUICEBOX_API_TOKEN }}" \
            https://api.juicebox.ai/v1/me > /dev/null
          echo "Auth OK"
      - name: Search smoke test
        run: |
          RESULT=$(curl -sf \
            -H "Authorization: token ${{ secrets.JUICEBOX_USERNAME }}:${{ secrets.JUICEBOX_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"query":"test","limit":1}' \
            https://api.juicebox.ai/v1/search)
          echo "$RESULT" | jq -e '.profiles | length > 0'
          echo "Search OK"
```

Then enable the branch protection rule:

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Juicebox Smoke Test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'
```

### Step 5: Add Deployment Pipeline

Gate production deployments on Juicebox integration health.

```yaml
# .github/workflows/deploy.yml
name: Deploy with Juicebox Validation

on:
  push:
    branches: [main]

jobs:
  validate-juicebox:
    name: Pre-Deploy Juicebox Validation
    runs-on: ubuntu-latest
    steps:
      - name: Validate production Juicebox credentials
        run: |
          HTTP_STATUS=$(curl -s -o /tmp/jb-response.json -w "%{http_code}" \
            -H "Authorization: token ${{ secrets.JUICEBOX_USERNAME }}:${{ secrets.JUICEBOX_API_TOKEN_PROD }}" \
            https://api.juicebox.ai/v1/me)
          if [ "$HTTP_STATUS" != "200" ]; then
            echo "::error::Production Juicebox credentials failed (HTTP $HTTP_STATUS)"
            cat /tmp/jb-response.json
            exit 1
          fi
          echo "Production credentials validated"

      - name: Validate search endpoint
        run: |
          curl -sf \
            -H "Authorization: token ${{ secrets.JUICEBOX_USERNAME }}:${{ secrets.JUICEBOX_API_TOKEN_PROD }}" \
            -H "Content-Type: application/json" \
            -d '{"query":"engineer","limit":1}' \
            https://api.juicebox.ai/v1/search | jq -e '.profiles'

  deploy:
    name: Deploy Application
    runs-on: ubuntu-latest
    needs: validate-juicebox
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci && npm run build

      - name: Deploy
        run: npm run deploy
        env:
          JUICEBOX_USERNAME: ${{ secrets.JUICEBOX_USERNAME }}
          JUICEBOX_API_TOKEN: ${{ secrets.JUICEBOX_API_TOKEN_PROD }}
```

## Output
- `.github/workflows/juicebox-tests.yml` — three-job workflow (connectivity, search, enrichment)
- `.github/workflows/required-checks.yml` — PR gate with auth and search smoke tests
- `.github/workflows/deploy.yml` — deployment pipeline gated on Juicebox validation
- `tests/juicebox/search.integration.test.ts` — search API test suite
- `tests/juicebox/enrichment.test.ts` — enrichment pipeline test suite
- Branch protection rule requiring the Juicebox smoke test job

## Error Handling

| CI Error | Cause | Resolution |
|----------|-------|------------|
| `Juicebox API returned HTTP 401` | Invalid or expired API token | Regenerate token at juicebox.ai/settings, update via `gh secret set JUICEBOX_API_TOKEN` |
| `Juicebox API returned HTTP 429` | Rate limit exceeded in test runs | Reduce test parallelism, add `--shard` to split across jobs, or use a sandbox token |
| `JUICEBOX_USERNAME not set` | Secret not configured in repo | Run `gh secret set JUICEBOX_USERNAME --body "..."` |
| `jq: error - null output` | Search returned empty results | Verify the test query returns data manually with `curl`; some queries may return 0 results |
| `npm ci` fails | Lock file mismatch | Run `npm install` locally and commit the updated `package-lock.json` |
| Enrichment test 404 | Profile ID expired or removed | Tests should search first then enrich; avoid hardcoded profile IDs |

## Examples

### Running Tests Locally
```bash
# Export credentials
export JUICEBOX_USERNAME="your-username"
export JUICEBOX_API_TOKEN="jb_tok_xxxxxxxxxxxx"

# Run the full Juicebox test suite
npx vitest run tests/juicebox/ --reporter=verbose

# Run only search tests
npx vitest run tests/juicebox/search.integration.test.ts

# Run with coverage
npx vitest run tests/juicebox/ --coverage
```

### Testing a Specific Search Query in CI
```typescript
it('finds data engineers in NYC', async () => {
  const res = await fetch(`${BASE_URL}/search`, {
    method: 'POST',
    headers: authHeader(),
    body: JSON.stringify({
      query: 'data engineer in New York City with Python and Spark',
      limit: 10,
    }),
  });
  const { profiles } = await res.json();
  expect(profiles.length).toBeGreaterThan(0);
  expect(profiles[0].title.toLowerCase()).toContain('data');
});
```

## Resources
- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Vitest Configuration](https://vitest.dev/config/)
- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)

## Next Steps
After CI is configured, use `juicebox-deploy-integration` to set up production deployment with secret management and health checks.
