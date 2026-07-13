# Documenso CI Integration - Implementation Guide

## GitHub Actions Configuration

### Workflow: Test & Deploy

```yaml
# .github/workflows/ci.yml
name: Documenso Integration CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint-and-type-check:
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

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

  unit-tests:
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
        run: npm run test:unit

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    needs: [lint-and-type-check, unit-tests]
    # Only run on main branch or when PR is approved
    if: github.ref == 'refs/heads/main' || github.event.pull_request.draft == false
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
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
          DOCUMENSO_BASE_URL: https://stg-app.documenso.com/api/v2/
          TEST_RECIPIENT_EMAIL: ci-test@yourcompany.com
        run: npm run test:integration

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
        run: |
          npm ci
          npm run build
          npm run deploy:staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_PRODUCTION_API_KEY }}
        run: |
          npm ci
          npm run build
          npm run deploy:production
```

### Secrets Configuration

```bash
# Required GitHub Secrets
DOCUMENSO_STAGING_API_KEY    # Staging environment key
DOCUMENSO_PRODUCTION_API_KEY # Production environment key
DOCUMENSO_WEBHOOK_SECRET     # Webhook validation secret
```

### Test Isolation Strategy

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  pull_request:
    types: [opened, synchronize]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  integration:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-suite: [documents, templates, webhooks]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run ${{ matrix.test-suite }} tests
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
          TEST_PREFIX: ci-${{ github.run_id }}-${{ matrix.test-suite }}
        run: npm run test:integration -- --grep "${{ matrix.test-suite }}"

      - name: Cleanup test data
        if: always()
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
          TEST_PREFIX: ci-${{ github.run_id }}-${{ matrix.test-suite }}
        run: npm run test:cleanup
```

## Test Scripts

### Integration Test Setup

```typescript
// tests/integration/setup.ts
import { Documenso } from "@documenso/sdk-typescript";

const TEST_PREFIX = process.env.TEST_PREFIX ?? `test-${Date.now()}`;

export function getTestClient(): Documenso {
  const apiKey = process.env.DOCUMENSO_API_KEY;
  if (!apiKey) {
    throw new Error("DOCUMENSO_API_KEY required for integration tests");
  }

  return new Documenso({
    apiKey,
    serverURL: process.env.DOCUMENSO_BASE_URL,
  });
}

export function generateTestTitle(name: string): string {
  return `${TEST_PREFIX}-${name}`;
}

// Track created resources for cleanup
const createdDocuments: string[] = [];
const createdTemplates: string[] = [];

export function trackDocument(id: string): void {
  createdDocuments.push(id);
}

export function trackTemplate(id: string): void {
  createdTemplates.push(id);
}

// Cleanup function
export async function cleanupTestData(): Promise<void> {
  const client = getTestClient();

  console.log(`Cleaning up ${createdDocuments.length} documents...`);
  for (const id of createdDocuments) {
    try {
      await client.documents.deleteV0({ documentId: id });
    } catch (error) {
      console.warn(`Failed to delete document ${id}`);
    }
  }

  console.log(`Cleaning up ${createdTemplates.length} templates...`);
  for (const id of createdTemplates) {
    try {
      await client.templates.deleteV0({ templateId: id });
    } catch (error) {
      console.warn(`Failed to delete template ${id}`);
    }
  }
}
```

### Cleanup Script

```typescript
// scripts/cleanup-ci-data.ts
import { Documenso } from "@documenso/sdk-typescript";

async function cleanup() {
  const prefix = process.env.TEST_PREFIX;
  if (!prefix) {
    console.log("No TEST_PREFIX set, skipping cleanup");
    return;
  }

  const client = new Documenso({
    apiKey: process.env.DOCUMENSO_API_KEY ?? "",
    serverURL: process.env.DOCUMENSO_BASE_URL,
  });

  console.log(`Cleaning up test data with prefix: ${prefix}`);

  // Find and delete test documents
  const docs = await client.documents.findV0({});
  const testDocs = docs.documents?.filter((d) =>
    d.title?.startsWith(prefix)
  ) ?? [];

  for (const doc of testDocs) {
    try {
      await client.documents.deleteV0({ documentId: doc.id! });
      console.log(`Deleted: ${doc.title}`);
    } catch (error) {
      console.warn(`Failed to delete: ${doc.title}`);
    }
  }

  console.log(`Cleanup complete. Deleted ${testDocs.length} documents.`);
}

cleanup().catch(console.error);
```

## GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy

variables:
  NODE_VERSION: "20"

.node-setup:
  image: node:${NODE_VERSION}
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/

lint:
  extends: .node-setup
  stage: lint
  script:
    - npm ci
    - npm run lint
    - npm run typecheck

unit-tests:
  extends: .node-setup
  stage: test
  script:
    - npm ci
    - npm run test:unit
  coverage: '/Lines\s*:\s*(\d+.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-tests:
  extends: .node-setup
  stage: test
  needs: [lint, unit-tests]
  variables:
    DOCUMENSO_API_KEY: ${DOCUMENSO_STAGING_API_KEY}
    DOCUMENSO_BASE_URL: https://stg-app.documenso.com/api/v2/
  script:
    - npm ci
    - npm run test:integration
  after_script:
    - npm run test:cleanup
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

deploy-staging:
  extends: .node-setup
  stage: deploy
  environment:
    name: staging
  variables:
    DOCUMENSO_API_KEY: ${DOCUMENSO_STAGING_API_KEY}
  script:
    - npm ci
    - npm run build
    - npm run deploy:staging
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy-production:
  extends: .node-setup
  stage: deploy
  environment:
    name: production
  variables:
    DOCUMENSO_API_KEY: ${DOCUMENSO_PRODUCTION_API_KEY}
  script:
    - npm ci
    - npm run build
    - npm run deploy:production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: manual
```

## Pre-commit Hooks

```json
// package.json
{
  "scripts": {
    "prepare": "husky install"
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
npm run typecheck
```
