---
name: customerio-ci-integration
description: |
  Configure Customer.io CI/CD integration with automated testing.
  Use when setting up GitHub Actions, integration test suites,
  or pre-commit validation for Customer.io code.
  Trigger: "customer.io ci", "customer.io github actions",
  "customer.io pipeline", "customer.io automated testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gh:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, ci-cd, testing, github-actions]

---
# Customer.io CI Integration

## Overview

Set up CI/CD pipelines for Customer.io integrations: GitHub Actions workflow with unit + integration tests, test fixtures with automatic cleanup, pre-commit hooks, and environment-specific credential management.

## Prerequisites

- GitHub repository with Node.js project
- Separate Customer.io workspace for CI testing (do NOT use production)
- GitHub Actions secrets configured

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/customerio-tests.yml
name: Customer.io Integration Tests
on:
  push:
    paths:
      - "lib/customerio-*.ts"
      - "services/customerio-*.ts"
      - "tests/customerio*"
  pull_request:
    paths:
      - "lib/customerio-*.ts"
      - "services/customerio-*.ts"

env:
  CUSTOMERIO_SITE_ID: ${{ secrets.CIO_TEST_SITE_ID }}
  CUSTOMERIO_TRACK_API_KEY: ${{ secrets.CIO_TEST_TRACK_API_KEY }}
  CUSTOMERIO_APP_API_KEY: ${{ secrets.CIO_TEST_APP_API_KEY }}
  CUSTOMERIO_REGION: us

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npx vitest run tests/customerio --reporter=verbose
        env:
          CUSTOMERIO_DRY_RUN: "true"  # Unit tests use mocks

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests  # Only run if unit tests pass
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - name: Validate credentials
        run: |
          if [ -z "$CUSTOMERIO_SITE_ID" ]; then
            echo "::warning::CIO credentials not configured — skipping integration tests"
            exit 0
          fi
      - name: Run integration tests
        run: npx vitest run tests/customerio.integration --reporter=verbose
      - name: Cleanup test users
        if: always()
        run: npx tsx scripts/cio-cleanup-test-users.ts
```

### Step 2: Test Fixtures and Helpers

```typescript
// tests/helpers/cio-test-utils.ts
import { TrackClient, RegionUS } from "customerio-node";

const TEST_RUN_ID = `ci-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
const createdUsers: string[] = [];

export function getCioTestClient(): TrackClient {
  return new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );
}

export function testUserId(label: string): string {
  const id = `${TEST_RUN_ID}-${label}`;
  createdUsers.push(id);
  return id;
}

export async function cleanupTestUsers(client: TrackClient): Promise<void> {
  console.log(`Cleaning up ${createdUsers.length} test users...`);
  for (const userId of createdUsers) {
    try {
      await client.suppress(userId);
      await client.destroy(userId);
    } catch {
      // Ignore cleanup errors
    }
  }
  createdUsers.length = 0;
}
```

### Step 3: Integration Test Suite

```typescript
// tests/customerio.integration.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { getCioTestClient, testUserId, cleanupTestUsers } from "./helpers/cio-test-utils";

const cio = getCioTestClient();

describe("Customer.io Integration", () => {
  afterAll(async () => {
    await cleanupTestUsers(cio);
  });

  it("should identify a new user", async () => {
    const userId = testUserId("identify-new");
    await expect(
      cio.identify(userId, {
        email: `${userId}@test.example.com`,
        created_at: Math.floor(Date.now() / 1000),
      })
    ).resolves.not.toThrow();
  });

  it("should update an existing user", async () => {
    const userId = testUserId("identify-update");
    await cio.identify(userId, { email: `${userId}@test.example.com` });
    await expect(
      cio.identify(userId, { plan: "pro", updated: true })
    ).resolves.not.toThrow();
  });

  it("should track an event on a user", async () => {
    const userId = testUserId("track-event");
    await cio.identify(userId, { email: `${userId}@test.example.com` });
    await expect(
      cio.track(userId, {
        name: "ci_test_event",
        data: { test_run: true, timestamp: Date.now() },
      })
    ).resolves.not.toThrow();
  });

  it("should track an anonymous event", async () => {
    await expect(
      cio.trackAnonymous({
        anonymous_id: testUserId("anon"),
        name: "ci_anonymous_test",
        data: { page: "/test" },
      })
    ).resolves.not.toThrow();
  });

  it("should suppress a user", async () => {
    const userId = testUserId("suppress");
    await cio.identify(userId, { email: `${userId}@test.example.com` });
    await expect(cio.suppress(userId)).resolves.not.toThrow();
  });

  it("should reject invalid credentials", async () => {
    const badClient = new (await import("customerio-node")).TrackClient(
      "invalid", "invalid", { region: (await import("customerio-node")).RegionUS }
    );
    await expect(
      badClient.identify("x", { email: "x@test.com" })
    ).rejects.toThrow();
  });
});
```

### Step 4: Test User Cleanup Script

```typescript
// scripts/cio-cleanup-test-users.ts
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Clean up any test users from failed CI runs
// This uses the ci- prefix convention from testUserId()
async function cleanup() {
  console.log("Cleaning up CI test users...");
  console.log("Note: Customer.io doesn't have a list/search API via Track API.");
  console.log("Cleanup relies on suppress+destroy for known test user IDs.");
  console.log("For bulk cleanup, use the Customer.io dashboard People filter.");
}

cleanup();
```

### Step 5: GitHub Secrets Setup

```bash
# Set up CI secrets (use a dedicated test workspace — NEVER production)
gh secret set CIO_TEST_SITE_ID --body "your-test-site-id"
gh secret set CIO_TEST_TRACK_API_KEY --body "your-test-track-key"
gh secret set CIO_TEST_APP_API_KEY --body "your-test-app-key"
```

### Step 6: Pre-commit Hook

```bash
# .husky/pre-commit (or lint-staged config)
npx lint-staged
```

```json
// package.json
{
  "lint-staged": {
    "lib/customerio-*.ts": ["eslint --fix", "vitest related --run"],
    "services/customerio-*.ts": ["eslint --fix", "vitest related --run"]
  }
}
```

## CI Best Practices

| Practice | Rationale |
|----------|-----------|
| Dedicated test workspace | Prevents CI from polluting dev/staging data |
| Unique test user IDs | Prevents collisions between parallel CI runs |
| Always cleanup in `afterAll` | Prevents accumulating stale test profiles |
| Rate limit awareness | Add small delays between batched API calls in CI |
| Skip integration tests if no creds | PRs from forks won't have secrets |

## Error Handling

| Issue | Solution |
|-------|----------|
| Secrets not available in PR | Fork PRs don't get secrets — skip integration tests gracefully |
| Test user pollution | Use `${TEST_RUN_ID}` prefix, cleanup in `afterAll` |
| Rate limiting in CI | Keep integration test count under 50 API calls |
| Flaky network failures | Add retry logic to integration tests |

## Resources

- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [vitest Documentation](https://vitest.dev/)

## Next Steps

After CI setup, proceed to `customerio-deploy-pipeline` for production deployment.
