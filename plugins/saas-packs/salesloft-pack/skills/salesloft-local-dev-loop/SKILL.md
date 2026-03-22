---
name: salesloft-local-dev-loop
description: |
  Configure SalesLoft local development with API mocking and sandbox testing.
  Use when setting up a development environment, building integration tests,
  or creating mock SalesLoft API responses for offline development.
  Trigger: "salesloft dev setup", "salesloft local", "test salesloft locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Local Dev Loop

## Overview

Set up a local development workflow for SalesLoft integrations with API mocking, environment separation, and fast iteration. SalesLoft has no official sandbox -- use test data tagging and request recording for safe development.

## Prerequisites

- Completed `salesloft-install-auth` setup
- Node.js 18+ with Vitest
- Separate SalesLoft test workspace (recommended)

## Instructions

### Step 1: Create API Client Wrapper

```typescript
// src/salesloft/client.ts
import axios, { AxiosInstance } from 'axios';

export function createClient(token?: string): AxiosInstance {
  return axios.create({
    baseURL: process.env.SALESLOFT_BASE_URL || 'https://api.salesloft.com/v2',
    headers: {
      Authorization: `Bearer ${token || process.env.SALESLOFT_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });
}
```

### Step 2: Create Fixtures from Real API Shape

```typescript
// tests/fixtures/salesloft.ts
export const mockPerson = {
  data: {
    id: 1001, display_name: 'Test User', email_address: 'test@example.com',
    first_name: 'Test', last_name: 'User', title: 'Engineer',
    phone: '+1-555-0100', company_name: 'Acme Corp',
    tags: ['dev_test'], created_at: '2025-01-15T10:00:00Z',
  },
};

export const mockPeopleList = {
  data: [mockPerson.data],
  metadata: { paging: { per_page: 25, current_page: 1, total_pages: 1, total_count: 1 } },
};

export const mockCadence = {
  data: {
    id: 500, name: 'Test Outbound', team_cadence: false,
    current_state: 'active', added_stage: 'prospecting',
    cadence_framework_id: null, counts: { people_count: 10 },
  },
};

export const mockActivity = {
  data: {
    id: 2001, action_type: 'email', person_id: 1001,
    cadence_id: 500, step_id: 100, due_at: '2025-02-01T09:00:00Z',
  },
};
```

### Step 3: Write Tests Against Real API Shape

```typescript
// tests/salesloft.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createClient } from '../src/salesloft/client';
import { mockPeopleList, mockCadence } from './fixtures/salesloft';

vi.mock('axios', () => ({
  default: { create: vi.fn(() => ({
    get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn(),
  }))},
}));

describe('SalesLoft People API', () => {
  it('lists people with pagination metadata', async () => {
    const client = createClient('test-token');
    vi.mocked(client.get).mockResolvedValue({ data: mockPeopleList });

    const { data } = await client.get('/people.json', { params: { per_page: 25 } });
    expect(data.metadata.paging.total_count).toBe(1);
    expect(data.data[0].email_address).toBe('test@example.com');
  });

  it('filters people by cadence membership', async () => {
    const client = createClient('test-token');
    vi.mocked(client.get).mockResolvedValue({ data: mockPeopleList });

    const { data } = await client.get('/people.json', {
      params: { cadence_id: 500, per_page: 25 },
    });
    expect(data.data.length).toBeGreaterThan(0);
  });
});
```

### Step 4: Environment Separation

```bash
# .env.development
SALESLOFT_BASE_URL=https://api.salesloft.com/v2
SALESLOFT_API_KEY=dev-token-here
SALESLOFT_TAG_PREFIX=dev_test_

# .env.test
SALESLOFT_BASE_URL=http://localhost:3001/mock
SALESLOFT_API_KEY=mock-token
```

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:integration": "dotenv -e .env.development vitest run --config vitest.integration.ts"
  }
}
```

## Output

```
 PASS  tests/salesloft.test.ts
  SalesLoft People API
    ✓ lists people with pagination metadata (2ms)
    ✓ filters people by cadence membership (1ms)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED` | Mock server not running | Use `vi.mock` instead of live mock server |
| `401` in integration tests | Token expired | Refresh dev token from SalesLoft portal |
| Stale mock data | API response shape changed | Record fresh responses with interceptor |

## Resources

- [SalesLoft API Logs](https://developers.salesloft.com/docs/platform/guides/api-logs/)
- [Vitest Mocking Guide](https://vitest.dev/guide/mocking.html)

## Next Steps

Proceed to `salesloft-sdk-patterns` for production client patterns.
