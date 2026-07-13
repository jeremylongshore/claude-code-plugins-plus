# CI Configuration Examples

## GitHub Actions Workflow

```yaml
# .github/workflows/retellai-integration.yml
name: Retell AI Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  RETELLAI_API_KEY: ${{ secrets.RETELLAI_API_KEY }}

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      RETELLAI_API_KEY: ${{ secrets.RETELLAI_API_KEY }}
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

## Integration Tests

```typescript
describe('Retell AI Integration', () => {
  it.skipIf(!process.env.RETELLAI_API_KEY)('should connect', async () => {
    const client = getRetellAIClient();
    const result = await client.healthCheck();
    expect(result.status).toBe('ok');
  });
});
```

## Release Workflow

```yaml
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      RETELLAI_API_KEY: ${{ secrets.RETELLAI_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Verify Retell AI production readiness
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

## Branch Protection

```yaml
required_status_checks:
  - "test"
  - "retellai-integration"
```
