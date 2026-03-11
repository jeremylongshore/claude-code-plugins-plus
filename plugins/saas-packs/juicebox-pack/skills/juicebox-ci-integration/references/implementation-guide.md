# Juicebox CI Integration - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Configure GitHub Secrets
```bash
# Add secrets via GitHub CLI
gh secret set JUICEBOX_API_KEY --body "jb_test_xxxx"
gh secret set JUICEBOX_API_KEY_PROD --body "jb_prod_xxxx"
```

### Step 2: Create Test Workflow
```yaml
# .github/workflows/juicebox-tests.yml
name: Juicebox Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  JUICEBOX_API_KEY: ${{ secrets.JUICEBOX_API_KEY }}

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

      - name: Run Juicebox tests
        run: npm run test:juicebox

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: coverage/
```

### Step 3: Add Integration Tests
```typescript
// tests/juicebox.integration.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { JuiceboxClient } from '@juicebox/sdk';

describe('Juicebox Integration', () => {
  let client: JuiceboxClient;

  beforeAll(() => {
    if (!process.env.JUICEBOX_API_KEY) {
      throw new Error('JUICEBOX_API_KEY required for integration tests');
    }
    client = new JuiceboxClient({
      apiKey: process.env.JUICEBOX_API_KEY
    });
  });

  it('authenticates with valid API key', async () => {
    const user = await client.auth.me();
    expect(user.id).toBeDefined();
  });

  it('performs basic search', async () => {
    const results = await client.search.people({
      query: 'engineer',
      limit: 5
    });
    expect(results.profiles).toBeDefined();
  });

  it('handles invalid queries gracefully', async () => {
    await expect(
      client.search.people({ query: '', limit: 5 })
    ).rejects.toThrow();
  });
});
```

### Step 4: Configure Branch Protection
```yaml
# .github/workflows/required-checks.yml
name: Required Checks

on:
  pull_request:
    branches: [main]

jobs:
  juicebox-smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run test:juicebox:smoke
        env:
          JUICEBOX_API_KEY: ${{ secrets.JUICEBOX_API_KEY }}
```

### Step 5: Add Deployment Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Validate Juicebox config
        run: |
          curl -f -H "Authorization: Bearer ${{ secrets.JUICEBOX_API_KEY_PROD }}" \
            https://api.juicebox.ai/v1/auth/me

      - name: Deploy application
        run: npm run deploy
        env:
          JUICEBOX_API_KEY: ${{ secrets.JUICEBOX_API_KEY_PROD }}
```
