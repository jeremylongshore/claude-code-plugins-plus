---
name: maintainx-ci-integration
description: |
  Configure MaintainX CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating MaintainX tests into your build process.
  Trigger with phrases like "maintainx CI", "maintainx GitHub Actions",
  "maintainx automated tests", "CI maintainx".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX CI Integration

## Overview
Set up CI/CD pipelines for MaintainX integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- MaintainX test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/maintainx-integration.yml`:

```yaml
name: MaintainX Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  MAINTAINX_API_KEY: ${{ secrets.MAINTAINX_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      MAINTAINX_API_KEY: ${{ secrets.MAINTAINX_API_KEY }}
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
gh secret set MAINTAINX_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('MaintainX Integration', () => {
  it.skipIf(!process.env.MAINTAINX_API_KEY)('should connect', async () => {
    const client = getMaintainXClient();
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
      MAINTAINX_API_KEY: ${{ secrets.MAINTAINX_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify MaintainX production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "maintainx-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [MaintainX CI Guide](https://docs.maintainx.com/ci)

## Next Steps
For deployment patterns, see `maintainx-deploy-integration`.