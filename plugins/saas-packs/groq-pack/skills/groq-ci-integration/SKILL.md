---
name: groq-ci-integration
description: |
  Configure Groq CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Groq tests into your build process.
  Trigger with phrases like "groq CI", "groq GitHub Actions",
  "groq automated tests", "CI groq".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq CI Integration

## Overview
Set up CI/CD pipelines for Groq integrations with automated testing.

## Prerequisites
- GitHub repository with Actions enabled
- Groq test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/groq-integration.yml`:

```yaml
name: Groq Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
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
gh secret set GROQ_API_KEY --body "sk_test_***"
```

### Step 3: Add Integration Tests
```typescript
describe('Groq Integration', () => {
  it.skipIf(!process.env.GROQ_API_KEY)('should connect', async () => {
    const client = getGroqClient();
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
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Groq production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

### Branch Protection
```yaml
required_status_checks:
  - "test"
  - "groq-integration"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Groq CI Guide](https://docs.groq.com/ci)

## Next Steps
For deployment patterns, see `groq-deploy-integration`.