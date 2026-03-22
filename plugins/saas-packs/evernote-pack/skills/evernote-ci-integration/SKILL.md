---
name: evernote-ci-integration
description: |
  Configure Evernote CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Evernote tests into your build process.
  Trigger with phrases like "evernote CI", "evernote GitHub Actions",
  "evernote automated tests", "CI evernote".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, evernote]
---

# Evernote CI Integration

## Overview
Set up CI/CD pipelines for Evernote integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Evernote test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/evernote-integration.yml`:

```yaml
name: Evernote Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  EVERNOTE_API_KEY: ${{ secrets.EVERNOTE_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      EVERNOTE_API_KEY: ${{ secrets.EVERNOTE_API_KEY }}
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
gh secret set EVERNOTE_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Evernote Integration', () => {
  it.skipIf(!process.env.EVERNOTE_API_KEY)('should connect', async () => {
    const client = getEvernoteClient();
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
      EVERNOTE_API_KEY: ${{ secrets.EVERNOTE_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Evernote production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "evernote-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Evernote CI Guide](https://docs.evernote.com/ci)

## Next Steps
For deployment patterns, see `evernote-deploy-integration`.