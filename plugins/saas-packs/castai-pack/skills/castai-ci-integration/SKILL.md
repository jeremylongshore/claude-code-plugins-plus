---
name: castai-ci-integration
description: |
  Configure Cast AI CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Cast AI tests into your build process.
  Trigger with phrases like "castai CI", "castai GitHub Actions",
  "castai automated tests", "CI castai".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI CI Integration

## Overview
Set up CI/CD pipelines for Cast AI integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Cast AI test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/castai-integration.yml`:

```yaml
name: Cast AI Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  CASTAI_API_KEY: ${{ secrets.CASTAI_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      CASTAI_API_KEY: ${{ secrets.CASTAI_API_KEY }}
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
gh secret set CASTAI_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Cast AI Integration', () => {
  it.skipIf(!process.env.CASTAI_API_KEY)('should connect', async () => {
    const client = getCast AIClient();
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
      CASTAI_API_KEY: ${{ secrets.CASTAI_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Cast AI production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "castai-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cast AI CI Guide](https://docs.castai.com/ci)

## Next Steps
For deployment patterns, see `castai-deploy-integration`.