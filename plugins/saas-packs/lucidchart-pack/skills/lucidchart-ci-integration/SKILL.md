---
name: lucidchart-ci-integration
description: 'Ci Integration for Lucidchart.

  Trigger: "lucidchart ci integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart CI Integration

## Overview

Configure CI pipelines that validate Lucidchart diagramming API integrations using a two-tier testing strategy. Unit tests mock the Lucidchart REST client to verify document creation, shape manipulation, and export logic without requiring OAuth2 credentials. Integration tests run on main-branch merges with a real OAuth2 token to confirm document CRUD, versioned API header handling, and export rendering against the live Lucidchart API. This separation keeps PR cycles fast while catching OAuth flow regressions and API version changes before they reach production.

## GitHub Actions Workflow

```yaml
# .github/workflows/lucidchart-tests.yml
name: Lucidchart API Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint && npm run typecheck
      - run: npm test -- --testPathPattern=unit  # No OAuth credentials needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --testPathPattern=integration
        env:
          LUCID_API_KEY: ${{ secrets.LUCID_API_KEY }}
          LUCID_CLIENT_SECRET: ${{ secrets.LUCID_CLIENT_SECRET }}
```

## Mock-Based Unit Tests

```typescript
// tests/unit/document-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { createDiagram } from '../../src/services/document-service';
import * as lucidClient from '../../src/lib/lucid-client';

vi.mock('../../src/lib/lucid-client');

describe('DocumentService', () => {
  it('creates a flowchart document with initial shapes', async () => {
    vi.mocked(lucidClient.post).mockResolvedValue({
      documentId: 'doc-7742',
      title: 'CI Pipeline Diagram',
      pageCount: 1,
      editUrl: 'https://lucid.app/documents/edit/doc-7742',
    });

    const result = await createDiagram('CI Pipeline Diagram', 'flowchart');
    expect(result.documentId).toBe('doc-7742');
    expect(lucidClient.post).toHaveBeenCalledWith(
      '/documents',
      { title: 'CI Pipeline Diagram', template: 'flowchart' },
      { headers: { 'Lucid-Api-Version': '1' } }
    );
  });
});
```

## Integration Tests

```typescript
// tests/integration/document-export.test.ts
import { describe, it, expect } from 'vitest';
import { LucidClient } from '../../src/lib/lucid-client';

const canRun = process.env.LUCID_API_KEY && process.env.LUCID_CLIENT_SECRET;

describe.skipIf(!canRun)('Lucidchart Document Export (live API)', () => {
  const client = new LucidClient({
    apiKey: process.env.LUCID_API_KEY!,
    clientSecret: process.env.LUCID_CLIENT_SECRET!,
  });

  it('exports a document as PNG', async () => {
    const docs = await client.get('/documents', { limit: 1 });
    expect(docs.length).toBeGreaterThan(0);

    const exported = await client.get(`/documents/${docs[0].documentId}/export`, {
      format: 'png', page: 1,
    });
    expect(exported.contentType).toBe('image/png');
    expect(exported.data.length).toBeGreaterThan(0);
  });
});
```

## CI Cost Management

```typescript
// tests/helpers/api-budget.ts
let callCount = 0;
const MAX_CALLS_PER_RUN = 20; // Lucidchart API: OAuth token refresh + tight rate limits

export function trackApiCall(): void {
  callCount++;
  if (callCount > MAX_CALLS_PER_RUN) {
    throw new Error(
      `CI API budget exceeded: ${callCount}/${MAX_CALLS_PER_RUN} calls. ` +
      'Lucidchart enforces per-app rate limits — reduce export tests or batch requests.'
    );
  }
}

export function getCallCount(): number { return callCount; }
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| 401 Unauthorized | OAuth2 token expired or client secret rotated | Re-run OAuth flow, update `LUCID_API_KEY` and `LUCID_CLIENT_SECRET` in GitHub Secrets |
| 400 Bad Request on export | Missing `Lucid-Api-Version` header | Ensure all requests include `{ 'Lucid-Api-Version': '1' }` header |
| Document not found (404) | Test document deleted or workspace changed | Create a dedicated CI workspace with persistent test documents |
| Rate limit (429) on export | PNG/PDF exports are expensive API calls | Cache export results, limit to 1 export test per CI run |
| Integration tests skipped | Missing both `LUCID_API_KEY` and `LUCID_CLIENT_SECRET` secrets | Add both secrets in repo Settings > Secrets and variables |

## Resources

- [Lucidchart Developer API Reference](https://developer.lucid.co/reference/overview)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `lucidchart-deploy-integration`.
