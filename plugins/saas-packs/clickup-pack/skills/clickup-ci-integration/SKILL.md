---
name: clickup-ci-integration
description: |
  Set up CI/CD pipelines for ClickUp API integrations with GitHub Actions,
  automated testing, and task status sync.
  Trigger: "clickup CI", "clickup GitHub Actions", "clickup automated tests",
  "CI clickup integration", "clickup pipeline", "clickup CI/CD".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp CI Integration

## Overview

Automate ClickUp integration testing in CI and sync task statuses from your pipeline. Uses GitHub Actions with live API testing against ClickUp API v2.

## GitHub Actions Workflow

```yaml
# .github/workflows/clickup-integration.yml
name: ClickUp Integration Tests

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

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    env:
      CLICKUP_API_TOKEN: ${{ secrets.CLICKUP_API_TOKEN }}
      CLICKUP_TEST_LIST_ID: ${{ secrets.CLICKUP_TEST_LIST_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: ClickUp API health check
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            https://api.clickup.com/api/v2/user \
            -H "Authorization: $CLICKUP_API_TOKEN")
          if [ "$STATUS" != "200" ]; then
            echo "::warning::ClickUp API returned $STATUS, skipping integration tests"
            exit 0
          fi
      - name: Run integration tests
        run: CLICKUP_LIVE=1 npm run test:integration
```

## Configure Secrets

```bash
# Store ClickUp token in GitHub Secrets
gh secret set CLICKUP_API_TOKEN --body "pk_12345678_YOUR_TOKEN"

# Store test list ID (for integration tests to create/delete test tasks)
gh secret set CLICKUP_TEST_LIST_ID --body "900100200300"
```

## Integration Test Suite

```typescript
// tests/integration/clickup-ci.test.ts
import { describe, it, expect, afterAll } from 'vitest';

const TOKEN = process.env.CLICKUP_API_TOKEN!;
const TEST_LIST = process.env.CLICKUP_TEST_LIST_ID!;
const BASE = 'https://api.clickup.com/api/v2';
const createdTaskIds: string[] = [];

async function api(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Authorization': TOKEN, 'Content-Type': 'application/json', ...options?.headers },
  });
  return { status: res.status, data: await res.json() };
}

describe('ClickUp API Integration', () => {
  it('authenticates successfully', async () => {
    const { status, data } = await api('/user');
    expect(status).toBe(200);
    expect(data.user.id).toBeDefined();
  });

  it('creates a task in test list', async () => {
    const { status, data } = await api(`/list/${TEST_LIST}/task`, {
      method: 'POST',
      body: JSON.stringify({
        name: `CI Test Task - ${new Date().toISOString()}`,
        description: 'Created by CI pipeline, safe to delete',
        priority: 4,
      }),
    });
    expect(status).toBe(200);
    expect(data.id).toBeDefined();
    createdTaskIds.push(data.id);
  });

  it('reads the created task', async () => {
    const { status, data } = await api(`/task/${createdTaskIds[0]}`);
    expect(status).toBe(200);
    expect(data.name).toContain('CI Test Task');
  });

  afterAll(async () => {
    // Cleanup: delete test tasks
    for (const id of createdTaskIds) {
      await api(`/task/${id}`, { method: 'DELETE' });
    }
  });
});
```

## Sync CI Status to ClickUp Task

```typescript
// scripts/update-clickup-task.ts
// Run after deploy: npx tsx scripts/update-clickup-task.ts TASK_ID "deployed"
async function updateTaskFromCI(taskId: string, newStatus: string) {
  const response = await fetch(
    `https://api.clickup.com/api/v2/task/${taskId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': process.env.CLICKUP_API_TOKEN!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: newStatus }),
    }
  );

  if (!response.ok) {
    console.error(`Failed to update task ${taskId}:`, await response.text());
    process.exit(1);
  }
  console.log(`Task ${taskId} status updated to "${newStatus}"`);
}

const [taskId, status] = process.argv.slice(2);
updateTaskFromCI(taskId, status);
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing GitHub secret | `gh secret set CLICKUP_API_TOKEN` |
| 401 in CI | Token expired/rotated | Update secret value |
| Rate limited in CI | Too many test runs | Add pre-flight rate check |
| Integration test cleanup fails | Task already deleted | Ignore 404 on cleanup |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [ClickUp API Reference](https://developer.clickup.com/)

## Next Steps

For deployment patterns, see `clickup-deploy-integration`.
