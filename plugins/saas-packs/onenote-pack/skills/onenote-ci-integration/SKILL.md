---
name: onenote-ci-integration
description: 'Set up CI/CD pipelines for OneNote integrations with Graph API testing
  and mock strategies.

  Use when configuring GitHub Actions, setting up test credentials, or building mock-based
  CI tests.

  Trigger with "onenote ci", "onenote github actions", "onenote test pipeline", "graph
  api ci".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote CI Integration

## Overview

Testing OneNote integrations in CI requires Azure AD app registration, credential management, and mock strategies for Graph API responses. This skill provides two proven CI strategies: mock-only PR checks (zero Azure credentials required) and nightly live integration tests with proper credential isolation and rate limit awareness.

## Prerequisites

- GitHub Actions or equivalent CI platform
- Node.js 18+ or Python 3.10+
- For mock-only CI: no Azure credentials needed
- For live integration tests: Azure AD test tenant with app registration
- GitHub repository secrets configured (live tests only)

## Instructions

### Strategy 1: Mock-Only CI (PR Checks)

Use `msw` (Mock Service Worker) to intercept Graph API calls with zero Azure dependency:

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";
const GRAPH = "https://graph.microsoft.com/v1.0";

export const handlers = [
  http.get(`${GRAPH}/me/onenote/notebooks`, () =>
    HttpResponse.json({ value: [
      { id: "nb-001", displayName: "Work Notes", createdDateTime: "2026-01-15T10:00:00Z" },
    ]})),

  http.get(`${GRAPH}/me/onenote/sections/:sectionId/pages`, () =>
    HttpResponse.json({ value: [
      { id: "page-001", title: "Sprint Review", createdDateTime: "2026-03-10T14:00:00Z" },
    ]})),

  http.post(`${GRAPH}/me/onenote/sections/:sectionId/pages`, async ({ request }) => {
    const body = await request.text();
    if (!body.includes("<html")) {
      return new HttpResponse(JSON.stringify({
        error: { code: "InvalidArgument", message: "Page content must be valid XHTML" }
      }), { status: 400 });
    }
    return HttpResponse.json({ id: "page-new", title: "Created Page" }, { status: 201 });
  }),
];
```

```typescript
// tests/setup.ts
import { setupServer } from "msw/node";
import { handlers } from "./mocks/handlers";
export const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Strategy 2: Live Integration Tests (Nightly)

Required GitHub Secrets: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`.

**Warning:** `ClientSecretCredential` (app-only auth) was deprecated March 31, 2025 for OneNote APIs. CI test environments may still use it for automation, but production code must use delegated auth. Monitor Microsoft deprecation notices.

### GitHub Actions Workflows

```yaml
# .github/workflows/onenote-pr.yml — Mock-only, every PR
name: OneNote PR Checks
on: [push, pull_request]
jobs:
  mock-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci && npm test -- --reporter=verbose
        env: { ONENOTE_TEST_MODE: mock }
```

```yaml
# .github/workflows/onenote-nightly.yml — Live tests, daily 3AM UTC
name: OneNote Integration Tests
on:
  schedule: [{ cron: "0 3 * * *" }]
  workflow_dispatch:
jobs:
  integration:
    runs-on: ubuntu-latest
    concurrency: { group: onenote-live-tests, cancel-in-progress: false }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci && npm test -- --testPathPattern="integration"
        env:
          ONENOTE_TEST_MODE: live
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
      - name: Cleanup test notebooks
        if: always()
        run: node scripts/cleanup-test-notebooks.js
        env:
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
```

### Test Isolation

Each test creates resources with a unique prefix. Note: OneNote notebooks cannot be deleted via Graph API — use a disposable test tenant or archive-based cleanup.

```typescript
// tests/helpers/test-context.ts
import { randomUUID } from "crypto";
export function createTestContext() {
  const prefix = `ci-test-${randomUUID().slice(0, 8)}`;
  return {
    notebookName: `${prefix}-notebook`,
    sectionName: `${prefix}-section`,
    prefix,
  };
}
```

### Rate Limit Awareness

Stay under 600 req/60s per user across parallel test jobs:

```typescript
export async function withRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  await new Promise((r) => setTimeout(r, 200));
  try { return await fn(); }
  catch (err: any) {
    if (err?.statusCode === 429) {
      const retry = parseInt(err.headers?.["retry-after"] ?? "5", 10);
      await new Promise((r) => setTimeout(r, retry * 1000));
      return fn();
    }
    throw err;
  }
}
```

## Output

- `.github/workflows/onenote-pr.yml` — mock-based PR check workflow
- `.github/workflows/onenote-nightly.yml` — live integration test workflow
- `tests/mocks/handlers.ts` — MSW handlers for Graph API endpoints
- `tests/setup.ts` — mock server lifecycle management
- `tests/helpers/test-context.ts` — test isolation with unique prefixes

## Error Handling

| CI Error | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` in nightly | Expired client secret | Rotate `AZURE_CLIENT_SECRET` in GitHub Settings > Secrets |
| `403 Forbidden` in live tests | Missing `Notes.ReadWrite` scope | Update app registration API permissions in Azure portal |
| Mock handler mismatch | `onUnhandledRequest: "error"` caught unknown URL | Add missing endpoint to `handlers.ts` |
| Rate limit in parallel jobs | Multiple CI runs hitting same tenant | Use `concurrency` group to serialize nightly runs |
| Orphaned test notebooks | Cleanup step skipped | OneNote notebooks cannot be API-deleted; archive manually |

## Examples

```bash
# Run mock tests locally
ONENOTE_TEST_MODE=mock npm test

# Run single integration test against live API
ONENOTE_TEST_MODE=live AZURE_TENANT_ID=xxx AZURE_CLIENT_ID=yyy \
  AZURE_CLIENT_SECRET=zzz npx vitest run tests/integration/notebooks.test.ts
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Azure App Registration](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
- [Graph API Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [MSW Documentation](https://mswjs.io/docs/)

## Next Steps

- Deploy tested integrations with `onenote-deploy-integration`
- Debug CI failures with `onenote-debug-bundle`
- Monitor rate limits in CI with `onenote-rate-limits`
