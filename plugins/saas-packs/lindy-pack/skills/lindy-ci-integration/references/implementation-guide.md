# Lindy Ci Integration - Implementation Guide

# Lindy CI Integration

## Overview
Configure CI/CD pipelines for Lindy AI agent testing and deployment.

## Prerequisites
- GitHub repository with Actions enabled
- Lindy test API key
- npm/pnpm project configured

## Instructions

### Step 1: Create GitHub Actions Workflow
```yaml
# .github/workflows/lindy-ci.yml
name: Lindy CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  LINDY_API_KEY: ${{ secrets.LINDY_API_KEY }}
  LINDY_ENVIRONMENT: test

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run type check
        run: npm run typecheck

      - name: Run unit tests
        run: npm test

      - name: Run Lindy integration tests
        run: npm run test:integration
        env:
          LINDY_API_KEY: ${{ secrets.LINDY_TEST_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

### Step 2: Configure Test API Key
```bash
# Add secret to GitHub repository
gh secret set LINDY_TEST_API_KEY --body "lnd_test_xxx"

# Verify secret is set
gh secret list
```

### Step 3: Create Integration Tests
```typescript
// tests/integration/lindy.test.ts
import { Lindy } from '@lindy-ai/sdk';

describe('Lindy Integration', () => {
  let lindy: Lindy;
  let testAgentId: string;

  beforeAll(async () => {
    lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

    // Create test agent
    const agent = await lindy.agents.create({
      name: 'CI Test Agent',
      instructions: 'Respond with "OK" to any input.',
    });
    testAgentId = agent.id;
  });

  afterAll(async () => {
    // Cleanup test agent
    await lindy.agents.delete(testAgentId);
  });

  test('agent responds correctly', async () => {
    const result = await lindy.agents.run(testAgentId, {
      input: 'Test message',
    });
    expect(result.output).toContain('OK');
  });

  test('handles rate limits gracefully', async () => {
    const promises = Array(5).fill(null).map(() =>
      lindy.agents.run(testAgentId, { input: 'Test' })
    );
    const results = await Promise.allSettled(promises);
    const successful = results.filter(r => r.status === 'fulfilled');
    expect(successful.length).toBeGreaterThan(0);
  });
});
```

### Step 4: Add PR Checks
```yaml
# .github/workflows/lindy-pr-check.yml
name: Lindy PR Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate-agents:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Validate agent configurations
        run: npm run validate:agents

      - name: Check for sensitive data
        run: |
          if grep -r "lnd_" --include="*.ts" --include="*.js" .; then
            echo "Found hardcoded API keys!"
            exit 1
          fi
```

## Output
- Automated test pipeline
- PR checks configured
- Coverage reports uploaded
- Integration test suite

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Not configured | Add via `gh secret set` |
| Tests timeout | Agent slow | Increase jest timeout |
| Rate limited | Too many tests | Add delays or use test key |

## Examples

### Matrix Testing
```yaml
jobs:
  test:
    strategy:
      matrix:
        node: [18, 20, 22]
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Lindy CI Guide](https://docs.lindy.ai/ci)
- [Jest Configuration](https://jestjs.io/docs/configuration)

## Next Steps
Proceed to `lindy-deploy-integration` for deployment automation.
