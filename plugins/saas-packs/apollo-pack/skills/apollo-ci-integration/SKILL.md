---
name: apollo-ci-integration
description: |
  Configure Apollo CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Apollo tests into your build process.
  Trigger with phrases like "apollo CI", "apollo GitHub Actions",
  "apollo automated tests", "CI apollo".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo CI Integration

## Overview
Set up CI/CD pipelines for Apollo integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Apollo test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/apollo-integration.yml`:

```yaml
name: Apollo Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - run: npm run test:integration
```

### Step 2: Configure Secrets
```bash
gh secret set APOLLO_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Apollo Integration', () => {
  it.skipIf(!process.env.APOLLO_API_KEY)('should connect', async () => {
    const client = getApolloClient();
    const result = await client.healthCheck();
    expect(result.status).toBe('ok');
  });
});
```

## Output
- Automated test pipeline
- PR checks configured
- Coverage reports uploaded
- Release workflow ready

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via `gh secret set` |
| Tests timeout | Network issues | Increase timeout or mock |
| Auth failures | Invalid key | Check secret value |

## Examples

### Release Workflow
```yaml
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Apollo production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "apollo-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apollo CI Guide](https://docs.apollo.com/ci)

## Next Steps
For deployment patterns, see `apollo-deploy-integration`.