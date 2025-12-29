---
name: supabase-ci-integration
description: |
  Configure Supabase CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing or continuous integration.
  Trigger with phrases like "supabase CI", "supabase GitHub Actions",
  "supabase automated tests", "CI supabase".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase CI Integration

## Overview
Set up CI/CD pipelines for Supabase integrations with automated testing.

## Prerequisites
- GitHub repository with actions enabled
- supabase-install-auth completed
- Test suite configured
- Access to GitHub repository settings

## Instructions

### Step 1: Add Secrets to GitHub
```bash
gh secret set SUPABASE_API_KEY --body "sk_test_***"
gh secret set SUPABASE_API_KEY_STAGING -e staging
gh secret set SUPABASE_API_KEY_PROD -e production
```

### Step 2: Create Workflow File
Create `.github/workflows/supabase-integration.yml`:

```yaml
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
```

### Step 3: Configure Integration Tests
```typescript
// tests/integration/supabase.test.ts
import { describe, it, expect, beforeAll } from 'vitest';

describe('Supabase Integration', () => {
  const hasApiKey = !!process.env.SUPABASE_API_KEY;

  it.skipIf(!hasApiKey)('should connect to Supabase API', async () => {
    const client = getSupabaseClient();
    const result = await client.healthCheck();
    expect(result.status).toBe('ok');
  });
});
```

## Output
- GitHub Actions workflow running on push/PR
- Integration tests validating Supabase connectivity
- Coverage reports uploaded to Codecov
- Branch protection rules enforcing tests

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | Add secret with `gh secret set` |
| Integration test skipped | No API key in CI | Configure repository secrets |
| Workflow failed | Test failure | Check test output and fix |
| Rate limit in CI | Too many test runs | Use test API key with higher limits |

## Examples

### Release Workflow
```yaml
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
        run: npm ci && npm run build && npm publish
```

### PR Check Configuration
```yaml
# Branch protection rule requirements
required_status_checks:
  - "test"
  - "supabase-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Supabase CI Guide](https://supabase.com/docs/ci)
- [Codecov Documentation](https://docs.codecov.com/)

## Next Steps
For deployment patterns, see `supabase-deploy-integration`.