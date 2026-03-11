# Customer.io CI Integration - Implementation Guide

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/customerio-integration.yml
name: Customer.io Integration Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'src/lib/customerio/**'
      - 'tests/customerio/**'
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    environment: testing

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage
        env:
          CUSTOMERIO_SITE_ID: ${{ secrets.CUSTOMERIO_TEST_SITE_ID }}
          CUSTOMERIO_API_KEY: ${{ secrets.CUSTOMERIO_TEST_API_KEY }}

      - name: Run integration tests
        run: npm run test:integration
        env:
          CUSTOMERIO_SITE_ID: ${{ secrets.CUSTOMERIO_TEST_SITE_ID }}
          CUSTOMERIO_API_KEY: ${{ secrets.CUSTOMERIO_TEST_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  smoke-test:
    needs: test
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Run smoke tests
        run: |
          curl -s -o /dev/null -w "%{http_code}" \
            -X POST "https://track.customer.io/api/v1/customers/ci-test-${{ github.run_id }}" \
            -u "${{ secrets.CUSTOMERIO_STAGING_SITE_ID }}:${{ secrets.CUSTOMERIO_STAGING_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"email":"ci-test@example.com","_ci_run":"${{ github.run_id }}"}' | grep -q "200"

      - name: Cleanup test user
        if: always()
        run: |
          curl -X DELETE \
            "https://track.customer.io/api/v1/customers/ci-test-${{ github.run_id }}" \
            -u "${{ secrets.CUSTOMERIO_STAGING_SITE_ID }}:${{ secrets.CUSTOMERIO_STAGING_API_KEY }}"
```

### Step 2: Test Fixtures
```typescript
// tests/fixtures/customerio.ts
import { TrackClient, RegionUS } from '@customerio/track';

export function createTestClient(): TrackClient {
  if (!process.env.CUSTOMERIO_SITE_ID || !process.env.CUSTOMERIO_API_KEY) {
    throw new Error('Customer.io test credentials not configured');
  }

  return new TrackClient(
    process.env.CUSTOMERIO_SITE_ID,
    process.env.CUSTOMERIO_API_KEY,
    { region: RegionUS }
  );
}

export function generateTestUserId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `test-user-${timestamp}-${random}`;
}

export async function cleanupTestUser(
  client: TrackClient,
  userId: string
): Promise<void> {
  try {
    await client.destroy(userId);
  } catch (error) {
    console.warn(`Failed to cleanup test user ${userId}:`, error);
  }
}
```

### Step 3: Integration Test Suite
```typescript
// tests/integration/customerio.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createTestClient, generateTestUserId, cleanupTestUser } from '../fixtures/customerio';

describe('Customer.io Integration', () => {
  const client = createTestClient();
  const testUsers: string[] = [];

  afterAll(async () => {
    // Cleanup all test users
    await Promise.all(testUsers.map(id => cleanupTestUser(client, id)));
  });

  describe('Identify', () => {
    it('should create a new user', async () => {
      const userId = generateTestUserId();
      testUsers.push(userId);

      await expect(
        client.identify(userId, {
          email: `${userId}@test.com`,
          created_at: Math.floor(Date.now() / 1000)
        })
      ).resolves.not.toThrow();
    });

    it('should update existing user', async () => {
      const userId = generateTestUserId();
      testUsers.push(userId);

      await client.identify(userId, { email: `${userId}@test.com` });
      await expect(
        client.identify(userId, { plan: 'premium' })
      ).resolves.not.toThrow();
    });
  });

  describe('Track', () => {
    it('should track event for user', async () => {
      const userId = generateTestUserId();
      testUsers.push(userId);

      await client.identify(userId, { email: `${userId}@test.com` });
      await expect(
        client.track(userId, {
          name: 'test_event',
          data: { source: 'integration-test' }
        })
      ).resolves.not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should reject invalid credentials', async () => {
      const badClient = new TrackClient('invalid', 'invalid', { region: RegionUS });
      await expect(
        badClient.identify('test', { email: 'test@test.com' })
      ).rejects.toThrow();
    });
  });
});
```

### Step 4: GitLab CI Configuration
```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

variables:
  NODE_VERSION: "20"

.node_template: &node_template
  image: node:${NODE_VERSION}
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/

test:unit:
  <<: *node_template
  stage: test
  script:
    - npm ci
    - npm run test:unit
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

test:integration:
  <<: *node_template
  stage: test
  environment:
    name: testing
  variables:
    CUSTOMERIO_SITE_ID: $CUSTOMERIO_TEST_SITE_ID
    CUSTOMERIO_API_KEY: $CUSTOMERIO_TEST_API_KEY
  script:
    - npm ci
    - npm run test:integration
  only:
    - main
    - merge_requests

deploy:staging:
  stage: deploy
  environment:
    name: staging
  script:
    - ./scripts/deploy.sh staging
  only:
    - develop

deploy:production:
  stage: deploy
  environment:
    name: production
  script:
    - ./scripts/deploy.sh production
  only:
    - main
  when: manual
```

### Step 5: Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: customerio-lint
        name: Lint Customer.io integration
        entry: npm run lint:customerio
        language: system
        files: 'src/lib/customerio/.*\.(ts|js)$'
        pass_filenames: false

      - id: customerio-types
        name: Type check Customer.io
        entry: npm run typecheck:customerio
        language: system
        files: 'src/lib/customerio/.*\.ts$'
        pass_filenames: false
```

### Step 6: Environment Management
```typescript
// scripts/setup-ci-environment.ts
import { execSync } from 'child_process';

interface CIEnvironment {
  name: string;
  siteId: string;
  apiKey: string;
}

const environments: Record<string, CIEnvironment> = {
  testing: {
    name: 'testing',
    siteId: process.env.CUSTOMERIO_TEST_SITE_ID!,
    apiKey: process.env.CUSTOMERIO_TEST_API_KEY!
  },
  staging: {
    name: 'staging',
    siteId: process.env.CUSTOMERIO_STAGING_SITE_ID!,
    apiKey: process.env.CUSTOMERIO_STAGING_API_KEY!
  },
  production: {
    name: 'production',
    siteId: process.env.CUSTOMERIO_PROD_SITE_ID!,
    apiKey: process.env.CUSTOMERIO_PROD_API_KEY!
  }
};

function validateEnvironment(env: string): void {
  const config = environments[env];
  if (!config) {
    throw new Error(`Unknown environment: ${env}`);
  }
  if (!config.siteId || !config.apiKey) {
    throw new Error(`Missing credentials for environment: ${env}`);
  }
  console.log(`Environment ${env} validated`);
}

// Validate on CI startup
const targetEnv = process.env.CI_ENVIRONMENT || 'testing';
validateEnvironment(targetEnv);
```
