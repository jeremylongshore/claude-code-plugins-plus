---
name: notion-ci-integration
description: |
  Configure CI/CD pipelines for Notion integrations with GitHub Actions and automated testing.
  Use when setting up automated testing against the Notion API,
  or integrating Notion validation into your build process.
  Trigger with phrases like "notion CI", "notion GitHub Actions",
  "notion automated tests", "CI notion", "notion pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion CI Integration

## Overview
Set up CI/CD pipelines for Notion integrations with GitHub Actions, including unit tests with mocks, optional integration tests against live API, and deployment gates.

## Prerequisites
- GitHub repository with Actions enabled
- `@notionhq/client` in project dependencies
- Vitest or Jest configured
- Notion test integration token (for integration tests)

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/notion-ci.yml
name: Notion Integration CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

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
      - run: npm run typecheck
      - run: npm test -- --coverage
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    # Only run on main branch (not PRs) to avoid rate limits
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    env:
      NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
      NOTION_TEST_DATABASE_ID: ${{ secrets.NOTION_TEST_DATABASE_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Run integration tests
        run: INTEGRATION=true npm test -- tests/integration.test.ts
        timeout-minutes: 5
```

### Step 2: Configure Secrets
```bash
# Store Notion test token as GitHub secret
gh secret set NOTION_TOKEN

# Store test database ID
gh secret set NOTION_TEST_DATABASE_ID

# Verify secrets are set
gh secret list
```

### Step 3: Unit Tests (Mocked, Run on Every PR)
```typescript
// tests/notion-service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Client } from '@notionhq/client';

vi.mock('@notionhq/client');

describe('NotionService', () => {
  let mockNotion: any;

  beforeEach(() => {
    mockNotion = {
      databases: {
        query: vi.fn().mockResolvedValue({
          results: [{
            id: 'page-1',
            properties: {
              Name: { type: 'title', title: [{ plain_text: 'Test' }] },
              Status: { type: 'select', select: { name: 'Done' } },
            },
          }],
          has_more: false,
          next_cursor: null,
        }),
        retrieve: vi.fn(),
      },
      pages: {
        create: vi.fn().mockResolvedValue({ id: 'new-page-id' }),
        update: vi.fn().mockResolvedValue({ id: 'page-1' }),
      },
    };
    vi.mocked(Client).mockImplementation(() => mockNotion);
  });

  it('should query database with correct filter', async () => {
    const notion = new Client({ auth: 'test' });
    await notion.databases.query({
      database_id: 'db-id',
      filter: { property: 'Status', select: { equals: 'Done' } },
    });

    expect(mockNotion.databases.query).toHaveBeenCalledWith(
      expect.objectContaining({
        filter: { property: 'Status', select: { equals: 'Done' } },
      })
    );
  });

  it('should create page with required title', async () => {
    const notion = new Client({ auth: 'test' });
    const result = await notion.pages.create({
      parent: { database_id: 'db-id' },
      properties: {
        Name: { title: [{ text: { content: 'New Task' } }] },
      },
    });

    expect(result.id).toBe('new-page-id');
  });
});
```

### Step 4: Integration Tests (Live API, Main Branch Only)
```typescript
// tests/integration.test.ts
import { describe, it, expect } from 'vitest';
import { Client } from '@notionhq/client';

const SKIP = !process.env.INTEGRATION;

describe.skipIf(SKIP)('Notion Live API', () => {
  const notion = new Client({ auth: process.env.NOTION_TOKEN! });
  const dbId = process.env.NOTION_TEST_DATABASE_ID!;

  it('should authenticate successfully', async () => {
    const me = await notion.users.me({});
    expect(me.type).toBe('bot');
  });

  it('should query test database', async () => {
    const { results } = await notion.databases.query({
      database_id: dbId,
      page_size: 1,
    });
    expect(results).toBeDefined();
  });

  it('should create, verify, and clean up test page', async () => {
    const testName = `CI Test ${Date.now()}`;

    // Create
    const page = await notion.pages.create({
      parent: { database_id: dbId },
      properties: {
        Name: { title: [{ text: { content: testName } }] },
      },
    });
    expect(page.id).toBeTruthy();

    // Verify
    const retrieved = await notion.pages.retrieve({ page_id: page.id });
    expect(retrieved.id).toBe(page.id);

    // Clean up — archive the test page
    await notion.pages.update({ page_id: page.id, archived: true });
  });
});
```

### Step 5: PR Status Check
```yaml
# Add to branch protection rules
# Settings → Branches → Branch protection → Require status checks
# Required: "unit-tests"
# Optional: "integration-tests" (can be flaky due to API)
```

## Output
- Unit test pipeline running on every PR
- Integration tests on main branch merges
- Coverage reports uploaded as artifacts
- Secrets securely managed via `gh secret`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing `gh secret set` | Add secret and re-run |
| Integration test timeout | API latency | Set `timeout-minutes: 5` |
| Rate limit in CI | Too many test runs | Run integration tests only on main |
| Flaky tests | Notion API variance | Add retry logic or mock |

## Examples

### Quick Secret Verification
```bash
# Verify token works in CI context
gh run view --log | grep "Connected"
```

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
For deployment patterns, see `notion-deploy-integration`.
