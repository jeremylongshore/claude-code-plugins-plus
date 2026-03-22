---
name: documenso-ci-integration
description: |
  Configure CI/CD pipelines for Documenso integrations.
  Use when setting up automated testing, deployment pipelines,
  or continuous integration for Documenso projects.
  Trigger with phrases like "documenso CI", "documenso GitHub Actions",
  "documenso pipeline", "documenso automated testing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, deployment, testing, ci-cd]

---
# Documenso CI Integration

## Overview

Configure CI/CD pipelines for Documenso integrations with GitHub Actions. Covers unit testing with mocks, integration testing against staging, and deployment workflows with secret management.

## Prerequisites

- GitHub repository with Actions enabled
- Documenso staging API key
- Test environment configured (see `documenso-local-dev-loop`)

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/documenso-ci.yml
name: Documenso CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_ENV: test

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test
        # Unit tests use mocks — no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'  # Only on push to main/develop
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
      - run: npm run test:cleanup  # Remove test documents
        env:
          DOCUMENSO_API_KEY: ${{ secrets.DOCUMENSO_STAGING_API_KEY }}
        if: always()
```

### Step 2: Unit Tests with Mocked SDK

```typescript
// tests/unit/document-service.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMockClient } from "../mocks/documenso";
import { DocumentService } from "../../src/services/document-service";

describe("DocumentService", () => {
  let service: DocumentService;
  let mockClient: ReturnType<typeof createMockClient>;

  beforeEach(() => {
    mockClient = createMockClient();
    service = new DocumentService(mockClient as any);
  });

  it("creates document with recipients and sends", async () => {
    const result = await service.createAndSend({
      title: "Test Contract",
      pdfPath: "./fixtures/test.pdf",
      signers: [{ email: "test@example.com", name: "Test User" }],
    });

    expect(mockClient.documents.createV0).toHaveBeenCalledWith({ title: "Test Contract" });
    expect(mockClient.documentsRecipients.createV0).toHaveBeenCalled();
    expect(mockClient.documents.sendV0).toHaveBeenCalled();
    expect(result.documentId).toBe(1);
  });

  it("handles API errors gracefully", async () => {
    mockClient.documents.createV0.mockRejectedValue(
      Object.assign(new Error("Unauthorized"), { statusCode: 401 })
    );

    await expect(service.createAndSend({
      title: "Test",
      pdfPath: "./fixtures/test.pdf",
      signers: [],
    })).rejects.toThrow("Unauthorized");
  });
});
```

### Step 3: Integration Tests Against Staging

```typescript
// tests/integration/document-lifecycle.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { Documenso } from "@documenso/sdk-typescript";

const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
const testDocIds: number[] = [];

describe("Document Lifecycle (Integration)", () => {
  it("creates a document", async () => {
    const doc = await client.documents.createV0({
      title: "[CI-TEST] Integration Test",
    });
    testDocIds.push(doc.documentId);
    expect(doc.documentId).toBeGreaterThan(0);
  }, 30000);

  it("lists documents", async () => {
    const { documents } = await client.documents.findV0({ page: 1, perPage: 5 });
    expect(documents.length).toBeGreaterThan(0);
  }, 15000);

  afterAll(async () => {
    // Cleanup: delete test documents
    for (const id of testDocIds) {
      try {
        await client.documents.deleteV0(id);
      } catch {
        console.warn(`Cleanup: could not delete document ${id}`);
      }
    }
  });
});
```

### Step 4: Add Secrets to GitHub

```bash
# Using GitHub CLI
gh secret set DOCUMENSO_STAGING_API_KEY --body "api_stg_xxxxxxxxxxxx"
gh secret set DOCUMENSO_WEBHOOK_SECRET --body "whsec_xxxxxxxxxxxx"

# Verify secrets exist
gh secret list
```

### Step 5: Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest run tests/unit/",
    "test:integration": "vitest run tests/integration/ --timeout 60000",
    "test:cleanup": "tsx scripts/cleanup-test-docs.ts",
    "test:all": "npm test && npm run test:integration"
  }
}
```

### Step 6: Pre-commit Hook (Optional)

```bash
# .husky/pre-commit
npm test -- --run
```

This runs unit tests (with mocks) before every commit, catching issues early without needing API access.

## CI Strategy Summary

| Test Type | Runs On | API Key Needed? | Speed |
|-----------|---------|-----------------|-------|
| Unit tests (mocks) | Every push + PR | No | Fast (~5s) |
| Integration tests | Push to main/develop only | Yes (staging) | Slow (~30s) |
| Cleanup | After integration tests | Yes (staging) | Fast |

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| Integration test timeout | Slow API | Increase vitest `timeout` to 60s |
| Rate limit in CI | Too many test runs | Use mocks for PRs, live API only on main |
| Secret not found | Missing GitHub secret | Add via `gh secret set` |
| Stale test data | Cleanup didn't run | Run `npm run test:cleanup` manually |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)
- [Documenso SDK Testing](https://github.com/documenso/sdk-typescript)

## Next Steps

For deployment strategies, see `documenso-deploy-integration`.
