---
name: flexport-ci-integration
description: 'Configure CI/CD pipelines for Flexport logistics integrations with GitHub
  Actions,

  automated API contract testing, and deployment workflows.

  Trigger: "flexport CI", "flexport GitHub Actions", "flexport CI/CD pipeline".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- logistics
- flexport
compatibility: Designed for Claude Code
---
# Flexport CI Integration

## Overview

Set up CI/CD for Flexport logistics integrations: run unit tests with mocked shipment and tracking responses on every PR, execute live API contract validation against the Flexport sandbox on merge to main. Flexport's API covers shipments, booking, customs documentation, and real-time tracking, so CI pipelines verify data transforms for shipment lifecycle events and ensure API contract compatibility across versions.

## GitHub Actions Workflow

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
    needs: unit-tests
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          FLEXPORT_API_KEY: ${{ secrets.FLEXPORT_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/flexport-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { getShipmentStatus } from '../src/flexport-service';

vi.mock('../src/flexport-client', () => ({
  FlexportClient: vi.fn().mockImplementation(() => ({
    getShipment: vi.fn().mockResolvedValue({
      id: 'shp_abc123',
      status: 'in_transit',
      origin: { port: 'CNSHA', country: 'CN' },
      destination: { port: 'USLAX', country: 'US' },
      containers: [{ id: 'MSKU1234567', type: '40ft_hc' }],
      estimated_arrival: '2026-04-15T00:00:00Z',
    }),
    listShipments: vi.fn().mockResolvedValue({ data: [], total_count: 0 }),
  })),
}));

describe('Flexport Service', () => {
  it('returns shipment tracking status', async () => {
    const status = await getShipmentStatus('shp_abc123');
    expect(status.status).toBe('in_transit');
    expect(status.origin.port).toBe('CNSHA');
  });
});
```

## Integration Tests

```typescript
// tests/integration/flexport.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.FLEXPORT_API_KEY;

describe.skipIf(!hasKey)('Flexport Live API', () => {
  it('lists shipments from sandbox', async () => {
    const res = await fetch('https://api.flexport.com/shipments?per=1', {
      headers: {
        'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
        'Flexport-Version': '2',
      },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveProperty('total_count');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid API key or wrong environment | Verify key at portal.flexport.com |
| `Flexport-Version` header missing | API version not set | Add `Flexport-Version: 2` to all requests |
| Shipment not found (404) | Test shipment ID expired | Use `listShipments` to get a valid ID dynamically |
| Rate limit (429) | Too many parallel test requests | Add request throttling between test cases |
| Customs data empty | Sandbox doesn't populate customs | Mock customs fields in unit tests, skip in integration |

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment strategies, see `flexport-deploy-integration`.
