---
name: linktree-ci-integration
description: |
  Configure Linktree CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Linktree tests into your build process.
  Trigger with phrases like "linktree CI", "linktree GitHub Actions",
  "linktree automated tests", "CI linktree".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree CI Integration

## Overview
Set up CI/CD pipelines for Linktree integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Linktree test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/linktree-integration.yml`:

```yaml
name: Linktree Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  LINKTREE_API_KEY: ${{ secrets.LINKTREE_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      LINKTREE_API_KEY: ${{ secrets.LINKTREE_API_KEY }}
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
gh secret set LINKTREE_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Linktree Integration', () => {
  it.skipIf(!process.env.LINKTREE_API_KEY)('should connect', async () => {
    const client = getLinktreeClient();
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
      LINKTREE_API_KEY: ${{ secrets.LINKTREE_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Linktree production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "linktree-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Linktree CI Guide](https://docs.linktree.com/ci)

## Next Steps
For deployment patterns, see `linktree-deploy-integration`.