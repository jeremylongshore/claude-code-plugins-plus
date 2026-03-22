---
name: clickup-local-dev-loop
description: |
  Set up local development for ClickUp API integrations with testing,
  mocking, and hot reload.
  Trigger: "clickup dev setup", "clickup local development", "clickup dev environment",
  "develop with clickup", "clickup testing setup", "mock clickup API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Local Dev Loop

## Overview

Set up a fast local development workflow for ClickUp API v2 integrations with hot reload, mocking, and integration testing.

## Project Setup

```bash
mkdir my-clickup-integration && cd $_
npm init -y
npm install -D typescript tsx vitest @types/node dotenv
npx tsc --init --target ES2022 --module nodenext --outDir dist
```

```
my-clickup-integration/
├── src/
│   ├── clickup/
│   │   ├── client.ts       # ClickUp API client (see clickup-sdk-patterns)
│   │   ├── types.ts         # TypeScript interfaces
│   │   └── tasks.ts         # Task operations
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── clickup.ts       # Mock ClickUp API responses
│   ├── unit/
│   │   └── tasks.test.ts
│   └── integration/
│       └── clickup.test.ts
├── .env.local                # Local secrets (git-ignored)
├── .env.example              # Template for team
└── package.json
```

## Environment Configuration

```bash
# .env.example (commit this)
CLICKUP_API_TOKEN=pk_your_token_here
CLICKUP_TEAM_ID=your_team_id
CLICKUP_TEST_LIST_ID=your_test_list_id

# .env.local (git-ignored, copy from .env.example)
cp .env.example .env.local
```

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "CLICKUP_LIVE=1 vitest --run tests/integration/",
    "build": "tsc",
    "typecheck": "tsc --noEmit"
  }
}
```

## Mock ClickUp API for Unit Tests

```typescript
// tests/mocks/clickup.ts
export const mockTask = {
  id: 'test_task_001',
  name: 'Test Task',
  status: { status: 'to do', color: '#d3d3d3', type: 'open' },
  priority: { id: '3', priority: 'normal', color: '#6fddff' },
  date_created: '1695000000000',
  date_updated: '1695000000000',
  due_date: null,
  assignees: [],
  tags: [],
  url: 'https://app.clickup.com/t/test_task_001',
  list: { id: '900100200300', name: 'Test List' },
  folder: { id: '456', name: 'Test Folder' },
  space: { id: '789' },
  custom_fields: [],
};

export const mockTeam = {
  teams: [{
    id: '1234567',
    name: 'Test Workspace',
    members: [{ user: { id: 183, username: 'testuser', email: 'test@example.com' } }],
  }],
};

// Mock fetch for ClickUp API calls
export function mockClickUpFetch() {
  return vi.fn(async (url: string, options?: RequestInit) => {
    const path = new URL(url).pathname.replace('/api/v2', '');

    const routes: Record<string, any> = {
      '/team': mockTeam,
      '/user': { user: { id: 183, username: 'testuser' } },
    };

    // Match dynamic routes
    if (path.match(/^\/task\/.+/)) return jsonResponse(mockTask);
    if (path.match(/^\/list\/.+\/task$/) && options?.method === 'POST') {
      return jsonResponse({ ...mockTask, ...JSON.parse(options.body as string) });
    }

    return jsonResponse(routes[path] ?? {}, routes[path] ? 200 : 404);
  });
}

function jsonResponse(data: any, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'X-RateLimit-Remaining': '95',
      'X-RateLimit-Limit': '100',
      'X-RateLimit-Reset': String(Math.floor(Date.now() / 1000) + 60),
    },
  });
}
```

## Unit Test Example

```typescript
// tests/unit/tasks.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mockClickUpFetch, mockTask } from '../mocks/clickup';

describe('ClickUp Task Operations', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockClickUpFetch());
    vi.stubEnv('CLICKUP_API_TOKEN', 'pk_test_token');
  });

  it('creates a task with required fields', async () => {
    const { createTask } = await import('../../src/clickup/tasks');
    const task = await createTask('list123', { name: 'New Task' });
    expect(task.name).toBe('New Task');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/list/list123/task'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('gets a task by ID', async () => {
    const { getTask } = await import('../../src/clickup/tasks');
    const task = await getTask('test_task_001');
    expect(task.id).toBe(mockTask.id);
  });
});
```

## Integration Test (Live API)

```typescript
// tests/integration/clickup.test.ts
import { describe, it, expect } from 'vitest';
import 'dotenv/config';

const LIVE = process.env.CLICKUP_LIVE === '1';

describe.skipIf(!LIVE)('ClickUp Live API', () => {
  it('authenticates and lists workspaces', async () => {
    const response = await fetch('https://api.clickup.com/api/v2/team', {
      headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! },
    });
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.teams.length).toBeGreaterThan(0);
  });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `CLICKUP_API_TOKEN` undefined | Missing .env.local | Copy from .env.example |
| Integration tests fail | No live token | Set `CLICKUP_LIVE=1` and valid token |
| Mock not matching | Route pattern wrong | Check URL path in mock router |

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)
- [ClickUp API Reference](https://developer.clickup.com/)

## Next Steps

See `clickup-sdk-patterns` for production-ready client patterns.
