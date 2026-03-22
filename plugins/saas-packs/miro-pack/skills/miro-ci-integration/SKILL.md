---
name: miro-ci-integration
description: |
  Configure CI/CD pipelines for Miro REST API v2 integrations with GitHub Actions,
  test board isolation, and automated validation.
  Trigger with phrases like "miro CI", "miro GitHub Actions",
  "miro automated tests", "CI miro", "miro pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, ci-cd, github-actions]
compatible-with: claude-code
---

# Miro CI Integration

## Overview

Set up CI/CD pipelines for Miro REST API v2 integrations with isolated test boards, proper secret handling, and API validation in GitHub Actions.

## Prerequisites

- GitHub repository with Actions enabled
- Miro app with test credentials (separate from production)
- A dedicated test board ID for integration tests

## GitHub Actions Workflow

```yaml
# .github/workflows/miro-integration.yml
name: Miro Integration Tests

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
      - run: npm test -- --coverage
      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    # Only run on main branch or when explicitly requested
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'run-integration')
    env:
      MIRO_ACCESS_TOKEN: ${{ secrets.MIRO_ACCESS_TOKEN_TEST }}
      MIRO_TEST_BOARD_ID: ${{ secrets.MIRO_TEST_BOARD_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Verify Miro API connectivity
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" \
            "https://api.miro.com/v2/boards?limit=1")
          if [ "$STATUS" != "200" ]; then
            echo "::error::Miro API returned $STATUS — check MIRO_ACCESS_TOKEN_TEST secret"
            exit 1
          fi
          echo "Miro API connectivity verified (HTTP $STATUS)"

      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5

      - name: Cleanup test board items
        if: always()
        run: |
          # Delete items created during test run
          curl -s "https://api.miro.com/v2/boards/$MIRO_TEST_BOARD_ID/items?limit=50" \
            -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" | \
            jq -r '.data[].id' | \
            while read -r ITEM_ID; do
              curl -s -X DELETE \
                "https://api.miro.com/v2/boards/$MIRO_TEST_BOARD_ID/items/$ITEM_ID" \
                -H "Authorization: Bearer $MIRO_ACCESS_TOKEN"
            done
          echo "Test board cleaned"
```

## Configuring Secrets

```bash
# Store test credentials as GitHub secrets
gh secret set MIRO_ACCESS_TOKEN_TEST --body "your_test_access_token"
gh secret set MIRO_TEST_BOARD_ID --body "uXjVN1234567890"

# For OAuth refresh in CI (long-lived tokens)
gh secret set MIRO_CLIENT_ID --body "your_client_id"
gh secret set MIRO_CLIENT_SECRET --body "your_client_secret"
gh secret set MIRO_REFRESH_TOKEN --body "your_refresh_token"
```

## Integration Test Examples

```typescript
// tests/integration/miro-boards.test.ts
import { describe, it, expect, afterAll } from 'vitest';

const TOKEN = process.env.MIRO_ACCESS_TOKEN!;
const BOARD_ID = process.env.MIRO_TEST_BOARD_ID!;
const BASE = 'https://api.miro.com/v2';
const createdIds: string[] = [];

const miroFetch = async (path: string, method = 'GET', body?: unknown) => {
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  return { status: response.status, data: await response.json() };
};

describe('Miro REST API v2 Integration', () => {
  it.skipIf(!TOKEN)('should read test board', async () => {
    const { status, data } = await miroFetch(`/boards/${BOARD_ID}`);
    expect(status).toBe(200);
    expect(data.type).toBe('board');
    expect(data.id).toBe(BOARD_ID);
  });

  it.skipIf(!TOKEN)('should create and delete a sticky note', async () => {
    // Create
    const { status: createStatus, data: note } = await miroFetch(
      `/boards/${BOARD_ID}/sticky_notes`, 'POST',
      {
        data: { content: `CI test: ${Date.now()}`, shape: 'square' },
        style: { fillColor: 'light_yellow' },
        position: { x: 0, y: 0 },
      }
    );
    expect(createStatus).toBe(201);
    expect(note.type).toBe('sticky_note');
    createdIds.push(note.id);

    // Delete
    const { status: deleteStatus } = await miroFetch(
      `/boards/${BOARD_ID}/items/${note.id}`, 'DELETE'
    );
    expect(deleteStatus).toBe(204);
  });

  it.skipIf(!TOKEN)('should list items with pagination', async () => {
    const { status, data } = await miroFetch(
      `/boards/${BOARD_ID}/items?limit=10`
    );
    expect(status).toBe(200);
    expect(Array.isArray(data.data)).toBe(true);
  });

  afterAll(async () => {
    // Clean up any items that weren't deleted in tests
    for (const id of createdIds) {
      await miroFetch(`/boards/${BOARD_ID}/items/${id}`, 'DELETE').catch(() => {});
    }
  });
});
```

## Token Refresh in CI

Miro access tokens expire in ~1 hour. For CI pipelines that run infrequently, automate refresh:

```yaml
  refresh-token:
    runs-on: ubuntu-latest
    steps:
      - name: Refresh Miro access token
        run: |
          RESPONSE=$(curl -s -X POST https://api.miro.com/v1/oauth/token \
            -d "grant_type=refresh_token" \
            -d "client_id=${{ secrets.MIRO_CLIENT_ID }}" \
            -d "client_secret=${{ secrets.MIRO_CLIENT_SECRET }}" \
            -d "refresh_token=${{ secrets.MIRO_REFRESH_TOKEN }}")

          NEW_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')
          if [ "$NEW_TOKEN" = "null" ] || [ -z "$NEW_TOKEN" ]; then
            echo "::error::Token refresh failed"
            exit 1
          fi

          echo "::add-mask::$NEW_TOKEN"
          echo "MIRO_ACCESS_TOKEN=$NEW_TOKEN" >> "$GITHUB_ENV"
```

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| Token expired in CI | Long time between runs | Add token refresh step |
| Rate limited in CI | Parallel test runs | Run integration tests serially |
| Test board full | No cleanup | Add `afterAll` cleanup step |
| Flaky tests | Miro API latency | Add retries + increase timeout |
| Secret not found | Missing GitHub secret | Run `gh secret set` commands above |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Miro OAuth Token](https://developers.miro.com/docs/getting-started-with-oauth)
- [Vitest Configuration](https://vitest.dev/config/)

## Next Steps

For deployment patterns, see `miro-deploy-integration`.
