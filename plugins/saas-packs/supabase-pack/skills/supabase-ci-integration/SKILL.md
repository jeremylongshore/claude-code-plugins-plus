---
name: supabase-ci-integration
description: |
  Supabase CI/CD integration with GitHub Actions and testing.
  Trigger phrases: "supabase CI", "supabase GitHub Actions",
  "supabase automated tests", "CI supabase".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase CI Integration

## Overview
Set up CI/CD pipelines for Supabase integrations with automated testing.

## GitHub Actions Workflow

```yaml
# .github/workflows/supabase-integration.yml
name: Supabase Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Run Supabase integration tests
        run: npm run test:integration
        env:
          SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
```

## Secrets Configuration

```bash
# Add secrets to GitHub repository
gh secret set SUPABASE_API_KEY --body "sk_test_***"

# For staging/production, use environment-specific secrets
gh secret set SUPABASE_API_KEY_STAGING -e staging
gh secret set SUPABASE_API_KEY_PROD -e production
```

## Integration Test Pattern

```typescript
// tests/integration/supabase.test.ts
import { describe, it, expect, beforeAll } from 'vitest';

describe('Supabase Integration', () => {
  const isCI = process.env.CI === 'true';
  const hasApiKey = !!process.env.SUPABASE_API_KEY;

  beforeAll(() => {
    if (isCI && !hasApiKey) {
      console.warn('Skipping integration tests: no API key');
    }
  });

  it.skipIf(!hasApiKey)('should connect to Supabase API', async () => {
    const client = getSupabaseClient();
    const result = await client.healthCheck();
    expect(result.status).toBe('ok');
  });
});
```

## Release Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Verify Supabase production readiness
        run: npm run verify:supabase
        env:
          SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY_PROD }}

      - name: Build and publish
        run: |
          npm ci
          npm run build
          npm publish
```

## PR Checks

```yaml
# Branch protection rule requirements
# Settings → Branches → Add rule
required_status_checks:
  - "test"
  - "supabase-integration"
```

## Next Steps
For deployment patterns, see `supabase-deploy-integration`.