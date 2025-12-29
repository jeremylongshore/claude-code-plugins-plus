---
name: vercel-ci-integration
description: |
  Configure Vercel CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Vercel tests into your build process.
  Trigger with phrases like "vercel CI", "vercel GitHub Actions",
  "vercel automated tests", "CI vercel".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel CI Integration

## Overview
Set up CI/CD pipelines for Vercel integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Vercel test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/vercel-integration.yml`:

```yaml
name: Vercel Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  VERCEL_API_KEY: ${{ secrets.VERCEL_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
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
gh secret set VERCEL_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Vercel Integration', () => {
  it.skipIf(!process.env.VERCEL_API_KEY)('should connect', async () => {
    const client = getVercelClient();
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
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build && npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "vercel-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel CI Guide](https://vercel.com/docs/ci)

## Next Steps
For deployment patterns, see `vercel-deploy-integration`.