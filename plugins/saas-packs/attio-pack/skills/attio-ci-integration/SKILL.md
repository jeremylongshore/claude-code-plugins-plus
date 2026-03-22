---
name: attio-ci-integration
description: |
  Configure CI/CD pipelines for Attio integrations with GitHub Actions,
  mock-based unit tests, and live API integration tests.
  Trigger: "attio CI", "attio GitHub Actions", "attio automated tests",
  "CI attio", "attio pipeline", "test attio in CI".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio CI Integration

## Overview

Set up CI/CD pipelines that validate Attio integrations without burning API quota on every push. Uses MSW mocks for unit tests and gated live API tests for pre-release validation.

## Prerequisites

- GitHub repository with Actions enabled
- Attio test workspace token (separate from production)
- Node.js project with vitest

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/attio-integration.yml
name: Attio Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    name: Unit Tests (mocked API)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
      - run: npm ci
      - run: npm run typecheck
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    name: Integration Tests (live API)
    runs-on: ubuntu-latest
    # Only run on main branch pushes and manual triggers
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: unit-tests
    env:
      ATTIO_API_KEY: ${{ secrets.ATTIO_API_KEY_TEST }}
      ATTIO_LIVE: "1"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
      - run: npm ci
      - name: Verify Attio connectivity
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer ${ATTIO_API_KEY}" \
            https://api.attio.com/v2/objects)
          if [ "$STATUS" != "200" ]; then
            echo "Attio API unreachable (HTTP $STATUS). Skipping live tests."
            exit 0
          fi
      - run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Configure GitHub Secrets

```bash
# Use a dedicated test workspace token with minimal scopes
gh secret set ATTIO_API_KEY_TEST --body "sk_test_workspace_token"

# Optional: webhook secret for webhook handler tests
gh secret set ATTIO_WEBHOOK_SECRET_TEST --body "whsec_test_secret"
```

### Step 3: Unit Tests with MSW Mocks

```typescript
// tests/unit/attio-service.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const BASE = "https://api.attio.com/v2";

const server = setupServer(
  http.get(`${BASE}/objects`, () =>
    HttpResponse.json({
      data: [
        { api_slug: "people", singular_noun: "Person" },
        { api_slug: "companies", singular_noun: "Company" },
      ],
    })
  ),
  http.post(`${BASE}/objects/people/records/query`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const limit = (body as any).limit || 10;
    return HttpResponse.json({
      data: Array.from({ length: Math.min(limit as number, 3) }, (_, i) => ({
        id: { object_id: "obj_people", record_id: `rec_${i}` },
        values: {
          name: [{ full_name: `Person ${i}` }],
          email_addresses: [{ email_address: `person${i}@test.com` }],
        },
      })),
    });
  }),
  // Simulate rate limiting
  http.post(`${BASE}/objects/companies/records`, () =>
    HttpResponse.json(
      { status_code: 429, type: "rate_limit_error", code: "rate_limit_exceeded", message: "Rate limited" },
      {
        status: 429,
        headers: { "Retry-After": new Date(Date.now() + 1000).toUTCString() },
      }
    )
  )
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("Attio Service", () => {
  it("lists workspace objects", async () => {
    const res = await fetch(`${BASE}/objects`, {
      headers: { Authorization: "Bearer sk_test" },
    });
    const data = await res.json();
    expect(data.data).toHaveLength(2);
    expect(data.data[0].api_slug).toBe("people");
  });

  it("handles rate limit responses", async () => {
    const res = await fetch(`${BASE}/objects/companies/records`, {
      method: "POST",
      headers: { Authorization: "Bearer sk_test", "Content-Type": "application/json" },
      body: JSON.stringify({ data: { values: {} } }),
    });
    expect(res.status).toBe(429);
    expect(res.headers.get("Retry-After")).toBeTruthy();
  });
});
```

### Step 4: Integration Tests (Live API)

```typescript
// tests/integration/attio-live.test.ts
import { describe, it, expect } from "vitest";
import { AttioClient } from "../../src/attio/client";

const LIVE = process.env.ATTIO_LIVE === "1" && !!process.env.ATTIO_API_KEY;
const client = LIVE ? new AttioClient(process.env.ATTIO_API_KEY!) : null;

describe.skipIf(!LIVE)("Attio Live API", () => {
  it("lists objects", async () => {
    const res = await client!.get<{ data: Array<{ api_slug: string }> }>("/objects");
    expect(res.data.map((o) => o.api_slug)).toContain("people");
  });

  it("queries people with filter", async () => {
    const res = await client!.post<{ data: any[] }>(
      "/objects/people/records/query",
      { limit: 1 }
    );
    expect(Array.isArray(res.data)).toBe(true);
  });

  it("lists attributes on people object", async () => {
    const res = await client!.get<{ data: Array<{ api_slug: string; type: string }> }>(
      "/objects/people/attributes"
    );
    const slugs = res.data.map((a) => a.api_slug);
    expect(slugs).toContain("name");
    expect(slugs).toContain("email_addresses");
  });
});
```

### Step 5: Release Workflow with Attio Smoke Test

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ["v*"]

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      ATTIO_API_KEY: ${{ secrets.ATTIO_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
      - name: Attio smoke test
        run: |
          curl -sf https://api.attio.com/v2/objects \
            -H "Authorization: Bearer ${ATTIO_API_KEY}" \
            | jq '.data | length' | xargs -I{} echo "Attio: {} objects accessible"
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| Integration tests flaky | Attio rate limits in CI | Run live tests only on main, not PRs |
| Secret not found | Missing GitHub secret | `gh secret set ATTIO_API_KEY_TEST` |
| Live tests timeout | Slow API or network | Add `timeout-minutes: 5` and connectivity check |
| MSW not intercepting | Version mismatch | Match MSW v2 imports (`msw/node`) |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [MSW Documentation](https://mswjs.io/docs/getting-started)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

For deployment patterns, see `attio-deploy-integration`.
