---
name: glean-ci-integration
description: |
  Configure Glean CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Glean tests into your build process.
  Trigger with phrases like "glean CI", "glean GitHub Actions",
  "glean automated tests", "CI glean".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, glean]
---

# Glean CI Integration

## Overview
Set up CI/CD pipelines for Glean integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Glean test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/glean-integration.yml`:

```yaml
name: Glean Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  GLEAN_API_KEY: ${{ secrets.GLEAN_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      GLEAN_API_KEY: ${{ secrets.GLEAN_API_KEY }}
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
gh secret set GLEAN_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Glean Integration', () => {
  it.skipIf(!process.env.GLEAN_API_KEY)('should connect', async () => {
    const client = getGleanClient();
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
      GLEAN_API_KEY: ${{ secrets.GLEAN_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Glean production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "glean-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Glean CI Guide](https://docs.glean.com/ci)

## Next Steps
For deployment patterns, see `glean-deploy-integration`.