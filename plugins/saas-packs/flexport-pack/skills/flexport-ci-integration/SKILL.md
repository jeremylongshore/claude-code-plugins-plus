---
name: flexport-ci-integration
description: |
  Configure CI/CD pipelines for Flexport logistics integrations with GitHub Actions,
  automated API contract testing, and deployment workflows.
  Trigger: "flexport CI", "flexport GitHub Actions", "flexport CI/CD pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport CI Integration

## Overview

Set up CI/CD for Flexport integrations: unit tests with mocked responses on every PR, integration tests against sandbox on merge, and API contract validation.

## Instructions

### GitHub Actions Workflow

```yaml
# .github/workflows/flexport-ci.yml
name: Flexport CI
on:
  pull_request:
    paths: ['src/flexport/**', 'tests/**']
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --reporter=verbose

  integration-tests:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          FLEXPORT_API_KEY: ${{ secrets.FLEXPORT_API_KEY_STAGING }}
          FLEXPORT_LIVE: '1'

  api-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check API contract
        run: |
          curl -sf https://logistics-api.flexport.com/logistics/api/2024-04/documentation/raw \
            -o openapi-latest.json
          npx @openapitools/openapi-diff openapi-baseline.json openapi-latest.json \
            --fail-on-breaking || echo "::warning::API contract changes detected"
```

### Integration Test Pattern

```typescript
// tests/integration.test.ts
const isLive = process.env.FLEXPORT_API_KEY && process.env.FLEXPORT_LIVE;

describe.skipIf(!isLive)('Flexport Live API', () => {
  const headers = {
    'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
    'Flexport-Version': '2',
  };

  it('lists shipments successfully', async () => {
    const res = await fetch('https://api.flexport.com/shipments?per=1', { headers });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveProperty('total_count');
  });
});
```

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions)

## Next Steps

For deployment strategies, see `flexport-deploy-integration`.
