---
name: salesforce-ci-integration
description: |
  Configure Salesforce CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Salesforce tests into your build process.
  Trigger with phrases like "salesforce CI", "salesforce GitHub Actions",
  "salesforce automated tests", "CI salesforce".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce CI Integration

## Overview
Set up CI/CD pipelines for Salesforce integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Salesforce test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/salesforce-integration.yml`:

```yaml
name: Salesforce Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  SALESFORCE_API_KEY: ${{ secrets.SALESFORCE_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      SALESFORCE_API_KEY: ${{ secrets.SALESFORCE_API_KEY }}
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
gh secret set SALESFORCE_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Salesforce Integration', () => {
  it.skipIf(!process.env.SALESFORCE_API_KEY)('should connect', async () => {
    const client = getSalesforceClient();
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
      SALESFORCE_API_KEY: ${{ secrets.SALESFORCE_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Salesforce production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "salesforce-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Salesforce CI Guide](https://docs.salesforce.com/ci)

## Next Steps
For deployment patterns, see `salesforce-deploy-integration`.