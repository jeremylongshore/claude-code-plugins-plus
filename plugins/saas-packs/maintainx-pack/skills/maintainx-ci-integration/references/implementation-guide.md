# MaintainX CI Integration - Implementation Guide

> Full implementation details and code examples for the `maintainx-ci-integration` skill.

# MaintainX CI Integration

## Overview

Configure continuous integration pipelines for MaintainX integrations with automated testing, security scanning, and quality gates.

## Prerequisites

- Git repository with MaintainX integration
- CI/CD platform (GitHub Actions, GitLab CI, etc.)
- Test environment with API access

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/maintainx-ci.yml
name: MaintainX Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint:
    name: Lint & Type Check
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

      - name: Run ESLint
        run: npm run lint

      - name: Run TypeScript type check
        run: npm run typecheck

  unit-tests:
    name: Unit Tests
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

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    # Only run on main branch to avoid rate limits
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run integration tests
        env:
          MAINTAINX_API_KEY: ${{ secrets.MAINTAINX_API_KEY_TEST }}
          NODE_ENV: test
        run: npm run test:integration

  security-scan:
    name: Security Scan
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

      - name: Run npm audit
        run: npm audit --production --audit-level=high

      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          extra_args: --only-verified

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: [lint, unit-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

### Step 2: Test Configuration

```typescript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.d.ts'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testTimeout: 30000,
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],

  // Test suites
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/tests/unit/**/*.test.ts'],
    },
    {
      displayName: 'integration',
      testMatch: ['<rootDir>/tests/integration/**/*.test.ts'],
    },
  ],
};
```

```typescript
// tests/setup.ts
import dotenv from 'dotenv';

// Load test environment
dotenv.config({ path: '.env.test' });

// Global test timeout
jest.setTimeout(30000);

// Global setup
beforeAll(() => {
  // Verify test environment
  if (!process.env.MAINTAINX_API_KEY) {
    console.warn('MAINTAINX_API_KEY not set - integration tests will be skipped');
  }
});

// Global teardown
afterAll(() => {
  // Cleanup test data if needed
});
```

### Step 3: Unit Tests with Mocks

```typescript
// tests/unit/client.test.ts
import { MaintainXClient } from '../../src/api/maintainx-client';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('MaintainXClient', () => {
  beforeEach(() => {
    process.env.MAINTAINX_API_KEY = 'test_api_key';
    jest.clearAllMocks();

    mockedAxios.create.mockReturnValue({
      get: jest.fn(),
      post: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    } as any);
  });

  describe('constructor', () => {
    it('should throw if API key not provided', () => {
      delete process.env.MAINTAINX_API_KEY;
      expect(() => new MaintainXClient()).toThrow('MAINTAINX_API_KEY is required');
    });

    it('should create client with valid API key', () => {
      const client = new MaintainXClient();
      expect(client).toBeDefined();
    });
  });

  describe('getWorkOrders', () => {
    it('should fetch work orders', async () => {
      const mockResponse = {
        data: {
          workOrders: [{ id: 'wo_1', title: 'Test' }],
          nextCursor: null,
        },
      };

      const client = new MaintainXClient();
      (client as any).client.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getWorkOrders({ limit: 10 });

      expect(result.workOrders).toHaveLength(1);
      expect(result.workOrders[0].id).toBe('wo_1');
    });

    it('should handle pagination parameters', async () => {
      const client = new MaintainXClient();
      (client as any).client.get = jest.fn().mockResolvedValue({ data: { workOrders: [] } });

      await client.getWorkOrders({ limit: 50, cursor: 'abc123' });

      expect((client as any).client.get).toHaveBeenCalledWith('/workorders', {
        params: { limit: 50, cursor: 'abc123' },
      });
    });
  });

  describe('createWorkOrder', () => {
    it('should create work order with required fields', async () => {
      const mockResponse = {
        data: { id: 'wo_new', title: 'New WO', status: 'OPEN' },
      };

      const client = new MaintainXClient();
      (client as any).client.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.createWorkOrder({ title: 'New WO' });

      expect(result.id).toBe('wo_new');
      expect((client as any).client.post).toHaveBeenCalledWith('/workorders', { title: 'New WO' });
    });
  });
});
```

### Step 4: Integration Tests

```typescript
// tests/integration/api.test.ts
import { MaintainXClient } from '../../src/api/maintainx-client';

// Skip if no API key
const describeIfApiKey = process.env.MAINTAINX_API_KEY
  ? describe
  : describe.skip;

describeIfApiKey('MaintainX API Integration', () => {
  let client: MaintainXClient;
  let createdWorkOrderId: string;

  beforeAll(() => {
    client = new MaintainXClient();
  });

  afterAll(async () => {
    // Cleanup: Delete test work orders
    // Note: Implement if delete endpoint is available
  });

  describe('Work Orders', () => {
    it('should list work orders', async () => {
      const response = await client.getWorkOrders({ limit: 5 });

      expect(response).toHaveProperty('workOrders');
      expect(Array.isArray(response.workOrders)).toBe(true);
    });

    it('should create a work order', async () => {
      const testTitle = `CI Test - ${new Date().toISOString()}`;

      const workOrder = await client.createWorkOrder({
        title: testTitle,
        description: 'Created by CI integration test',
        priority: 'LOW',
      });

      expect(workOrder).toHaveProperty('id');
      expect(workOrder.title).toBe(testTitle);
      expect(workOrder.status).toBe('OPEN');

      createdWorkOrderId = workOrder.id;
    });

    it('should get a single work order', async () => {
      // Skip if create didn't work
      if (!createdWorkOrderId) {
        console.warn('Skipping: No work order created');
        return;
      }

      const workOrder = await client.getWorkOrder(createdWorkOrderId);

      expect(workOrder.id).toBe(createdWorkOrderId);
    });

    it('should filter work orders by status', async () => {
      const response = await client.getWorkOrders({
        status: 'OPEN',
        limit: 10,
      });

      response.workOrders.forEach(wo => {
        expect(wo.status).toBe('OPEN');
      });
    });
  });

  describe('Assets', () => {
    it('should list assets', async () => {
      const response = await client.getAssets({ limit: 5 });

      expect(response).toHaveProperty('assets');
      expect(Array.isArray(response.assets)).toBe(true);
    });
  });

  describe('Locations', () => {
    it('should list locations', async () => {
      const response = await client.getLocations({ limit: 5 });

      expect(response).toHaveProperty('locations');
      expect(Array.isArray(response.locations)).toBe(true);
    });
  });

  describe('Users', () => {
    it('should list users', async () => {
      const response = await client.getUsers({ limit: 5 });

      expect(response).toHaveProperty('users');
      expect(Array.isArray(response.users)).toBe(true);
    });
  });
});
```

### Step 5: GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - build
  - deploy

variables:
  NODE_VERSION: '20'

.node-setup:
  image: node:${NODE_VERSION}
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/

lint:
  extends: .node-setup
  stage: validate
  script:
    - npm ci
    - npm run lint
    - npm run typecheck

unit-tests:
  extends: .node-setup
  stage: test
  script:
    - npm ci
    - npm run test:unit -- --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-tests:
  extends: .node-setup
  stage: test
  only:
    - main
  script:
    - npm ci
    - npm run test:integration
  variables:
    MAINTAINX_API_KEY: $MAINTAINX_API_KEY_TEST

security-scan:
  extends: .node-setup
  stage: validate
  script:
    - npm ci
    - npm audit --production --audit-level=high
  allow_failure: true

build:
  extends: .node-setup
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
```

### Step 6: Package.json Scripts

```json
{
  "scripts": {
    "build": "tsc",
    "lint": "eslint 'src/**/*.ts' 'tests/**/*.ts'",
    "lint:fix": "eslint 'src/**/*.ts' 'tests/**/*.ts' --fix",
    "typecheck": "tsc --noEmit",
    "test": "jest",
    "test:unit": "jest --selectProjects unit",
    "test:integration": "jest --selectProjects integration",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "ci": "npm run lint && npm run typecheck && npm run test:unit && npm run build"
  }
}
```

## Output

- GitHub Actions workflow configured
- GitLab CI pipeline configured
- Unit tests with mocks
- Integration tests with real API
- Security scanning enabled

## Best Practices

1. **Separate test types**: Unit tests run fast on every commit; integration tests on main only
2. **Use test API keys**: Never use production keys in CI
3. **Rate limit awareness**: Add delays between integration tests
4. **Clean up test data**: Delete test work orders after tests
5. **Cache dependencies**: Speed up CI with npm caching

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jest Documentation](https://jestjs.io/)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps

For deployment automation, see `maintainx-deploy-integration`.
