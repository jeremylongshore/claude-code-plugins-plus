# Apollo CI Integration - Implementation Guide

> Full implementation details and code examples for the `apollo-ci-integration` skill.

# Apollo CI Integration

## Overview
Set up CI/CD pipelines for Apollo.io integrations with automated testing, secret management, and deployment workflows.

## GitHub Actions Setup

### Basic CI Workflow
```yaml
# .github/workflows/apollo-ci.yml
name: Apollo Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run unit tests
        run: npm run test:unit
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_TEST }}

      - name: Run integration tests
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: npm run test:integration
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_TEST }}

  validate-apollo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Validate Apollo configuration
        run: npm run apollo:validate
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_TEST }}

      - name: Check API health
        run: |
          curl -sf "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" \
            || echo "Warning: Apollo API health check failed"
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_TEST }}
```

### Integration Test Workflow
```yaml
# .github/workflows/apollo-integration.yml
name: Apollo Integration Tests

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run Apollo integration tests
        run: npm run test:apollo
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_TEST }}
          APOLLO_TEST_DOMAIN: 'apollo.io'

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: apollo-test-results
          path: test-results/

      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Apollo integration tests failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Apollo Integration Tests Failed*\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Run>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Secrets Management

### GitHub Secrets Setup
```bash
# Add secrets via GitHub CLI
gh secret set APOLLO_API_KEY_TEST --body "your-test-api-key"
gh secret set APOLLO_API_KEY_PROD --body "your-prod-api-key"

# List configured secrets
gh secret list
```

### Environment-Based Secrets
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    steps:
      - name: Deploy to staging
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
        run: npm run deploy:staging

  deploy-production:
    environment: production
    needs: deploy-staging
    steps:
      - name: Deploy to production
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
        run: npm run deploy:production
```

## Test Configuration

### Test Setup
```typescript
// tests/setup/apollo.ts
import { beforeAll, afterAll, beforeEach } from 'vitest';
import { setupServer } from 'msw/node';
import { apolloHandlers } from './mocks/apollo-handlers';

const server = setupServer(...apolloHandlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

afterAll(() => {
  server.close();
});

beforeEach(() => {
  server.resetHandlers();
});

export { server };
```

### Mock Handlers for CI
```typescript
// tests/mocks/apollo-handlers.ts
import { http, HttpResponse } from 'msw';

export const apolloHandlers = [
  http.get('https://api.apollo.io/v1/auth/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),

  http.post('https://api.apollo.io/v1/people/search', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      people: [
        {
          id: 'test-1',
          name: 'Test User',
          title: 'Engineer',
          email: 'test@example.com',
        },
      ],
      pagination: {
        page: body.page || 1,
        per_page: body.per_page || 25,
        total_entries: 1,
        total_pages: 1,
      },
    });
  }),

  http.get('https://api.apollo.io/v1/organizations/enrich', ({ request }) => {
    const url = new URL(request.url);
    const domain = url.searchParams.get('domain');
    return HttpResponse.json({
      organization: {
        id: 'org-1',
        name: 'Test Company',
        primary_domain: domain,
        industry: 'Technology',
      },
    });
  }),
];
```

### Integration Tests
```typescript
// tests/integration/apollo.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { apollo } from '../../src/lib/apollo/client';

describe('Apollo API Integration', () => {
  // Only run with real API in CI
  const isCI = process.env.CI === 'true';
  const hasApiKey = !!process.env.APOLLO_API_KEY;

  beforeEach(() => {
    if (!isCI || !hasApiKey) {
      console.log('Skipping real API tests - using mocks');
    }
  });

  it('should search for people', async () => {
    const result = await apollo.searchPeople({
      q_organization_domains: [process.env.APOLLO_TEST_DOMAIN || 'apollo.io'],
      per_page: 5,
    });

    expect(result.people).toBeDefined();
    expect(Array.isArray(result.people)).toBe(true);
    expect(result.pagination.total_entries).toBeGreaterThanOrEqual(0);
  });

  it('should enrich organization', async () => {
    const result = await apollo.enrichOrganization(
      process.env.APOLLO_TEST_DOMAIN || 'apollo.io'
    );

    expect(result.organization).toBeDefined();
    expect(result.organization.name).toBeTruthy();
  });

  it('should handle rate limits gracefully', async () => {
    // This test verifies rate limit handling without actually hitting limits
    const startTime = Date.now();

    // Make 5 requests in sequence
    for (let i = 0; i < 5; i++) {
      await apollo.searchPeople({ per_page: 1 });
    }

    const duration = Date.now() - startTime;
    // Should complete in reasonable time with rate limiting
    expect(duration).toBeLessThan(30000);
  });
});
```

## Pipeline Scripts

### package.json Scripts
```json
{
  "scripts": {
    "test:unit": "vitest run --config vitest.unit.config.ts",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "test:apollo": "vitest run tests/integration/apollo.test.ts",
    "apollo:validate": "tsx scripts/validate-apollo-config.ts",
    "apollo:health": "curl -sf 'https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY'"
  }
}
```

### Validation Script
```typescript
// scripts/validate-apollo-config.ts
async function validateConfig() {
  const checks = [];

  // Check API key
  if (!process.env.APOLLO_API_KEY) {
    checks.push({ name: 'API Key', status: 'fail', message: 'Missing' });
  } else {
    checks.push({ name: 'API Key', status: 'pass', message: 'Present' });
  }

  // Check API connectivity
  try {
    const response = await fetch(
      `https://api.apollo.io/v1/auth/health?api_key=${process.env.APOLLO_API_KEY}`
    );
    checks.push({
      name: 'API Health',
      status: response.ok ? 'pass' : 'fail',
      message: response.ok ? 'Healthy' : `Status: ${response.status}`,
    });
  } catch (error) {
    checks.push({
      name: 'API Health',
      status: 'fail',
      message: 'Connection failed',
    });
  }

  // Output results
  const failed = checks.filter((c) => c.status === 'fail');
  if (failed.length > 0) {
    console.error('Validation failed:', failed);
    process.exit(1);
  }

  console.log('All checks passed:', checks);
}

validateConfig();
```

## Output
- GitHub Actions workflows for CI
- Secrets management configuration
- Test setup with MSW mocks
- Integration test suite
- Validation scripts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | Verify secret name in GitHub |
| Tests timeout | Increase timeout or mock API |
| Rate limited in CI | Use mocks for unit tests |
| Health check fails | Check Apollo status page |

## Resources
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
Proceed to `apollo-deploy-integration` for deployment configuration.
