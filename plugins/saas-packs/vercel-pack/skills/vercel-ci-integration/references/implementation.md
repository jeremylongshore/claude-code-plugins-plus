## Implementation Guide

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
    env:
      VERCEL_API_KEY: ${{ secrets.VERCEL_API_KEY }}
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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
