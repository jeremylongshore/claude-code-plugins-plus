---
name: customerio-ci-integration
description: |
  Configure Customer.io CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Customer.io tests into your build process.
  Trigger with phrases like "customerio CI", "customerio GitHub Actions",
  "customerio automated tests", "CI customerio".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io CI Integration

## Overview
Set up CI/CD pipelines for Customer.io integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Customer.io test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/customerio-integration.yml`:

```yaml
name: Customer.io Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  CUSTOMERIO_API_KEY: ${{ secrets.CUSTOMERIO_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      CUSTOMERIO_API_KEY: ${{ secrets.CUSTOMERIO_API_KEY }}
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
gh secret set CUSTOMERIO_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Customer.io Integration', () => {
  it.skipIf(!process.env.CUSTOMERIO_API_KEY)('should connect', async () => {
    const client = getCustomer.ioClient();
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
      CUSTOMERIO_API_KEY: ${{ secrets.CUSTOMERIO_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Customer.io production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "customerio-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Customer.io CI Guide](https://docs.customerio.com/ci)

## Next Steps
For deployment patterns, see `customerio-deploy-integration`.