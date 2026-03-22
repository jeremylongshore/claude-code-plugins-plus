---
name: flexport-ci-integration
description: |
  Configure Flexport CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Flexport tests into your build process.
  Trigger with phrases like "flexport CI", "flexport GitHub Actions",
  "flexport automated tests", "CI flexport".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flexport]
---

# Flexport CI Integration

## Overview
Set up CI/CD pipelines for Flexport integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Flexport test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/flexport-integration.yml`:

```yaml
name: Flexport Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  FLEXPORT_API_KEY: ${{ secrets.FLEXPORT_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      FLEXPORT_API_KEY: ${{ secrets.FLEXPORT_API_KEY }}
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
gh secret set FLEXPORT_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Flexport Integration', () => {
  it.skipIf(!process.env.FLEXPORT_API_KEY)('should connect', async () => {
    const client = getFlexportClient();
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
      FLEXPORT_API_KEY: ${{ secrets.FLEXPORT_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Flexport production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "flexport-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Flexport CI Guide](https://docs.flexport.com/ci)

## Next Steps
For deployment patterns, see `flexport-deploy-integration`.