---
name: bamboohr-local-dev-loop
description: |
  Configure BambooHR local development with hot reload, mocking, and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with BambooHR API.
  Trigger with phrases like "bamboohr dev setup", "bamboohr local development",
  "bamboohr dev environment", "develop with bamboohr", "bamboohr mock".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, development]
compatible-with: claude-code
---

# BambooHR Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for BambooHR integrations with request mocking, hot reload, and integration testing against the real API.

## Prerequisites

- Completed `bamboohr-install-auth` setup
- Node.js 18+ with npm or pnpm
- `BAMBOOHR_API_KEY` and `BAMBOOHR_COMPANY_DOMAIN` set in `.env`

## Instructions

### Step 1: Project Structure

```
my-bamboohr-project/
├── src/
│   ├── bamboohr/
│   │   ├── client.ts       # Reusable API client
│   │   ├── types.ts         # BambooHR response types
│   │   └── employees.ts     # Employee operations
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── bamboohr.ts      # API response fixtures
│   ├── unit/
│   │   └── employees.test.ts
│   └── integration/
│       └── bamboohr.test.ts
├── .env.local               # Real API key (git-ignored)
├── .env.example              # Template for team
├── .env.test                 # Test config (sandbox key)
└── package.json
```

### Step 2: Create Reusable API Client

```typescript
// src/bamboohr/client.ts
import 'dotenv/config';

export class BambooHRClient {
  private baseUrl: string;
  private authHeader: string;

  constructor(companyDomain?: string, apiKey?: string) {
    const domain = companyDomain || process.env.BAMBOOHR_COMPANY_DOMAIN!;
    const key = apiKey || process.env.BAMBOOHR_API_KEY!;
    this.baseUrl = `https://api.bamboohr.com/api/gateway.php/${domain}/v1`;
    this.authHeader = `Basic ${Buffer.from(`${key}:x`).toString('base64')}`;
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        Authorization: this.authHeader,
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!res.ok) {
      const errMsg = res.headers.get('X-BambooHR-Error-Message') || res.statusText;
      throw new BambooHRError(res.status, errMsg, path);
    }

    return res.json() as Promise<T>;
  }

  async getEmployee(id: number | string, fields: string[]): Promise<Record<string, string>> {
    return this.request(`/employees/${id}/?fields=${fields.join(',')}`);
  }

  async getDirectory(): Promise<{ employees: BambooEmployee[] }> {
    return this.request('/employees/directory');
  }
}

export class BambooHRError extends Error {
  constructor(public status: number, message: string, public path: string) {
    super(`BambooHR ${status}: ${message} [${path}]`);
    this.name = 'BambooHRError';
  }
}
```

### Step 3: Setup Hot Reload and Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "DOTENV_CONFIG_PATH=.env.test vitest run tests/integration/",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0",
    "typescript": "^5.5.0",
    "msw": "^2.0.0"
  }
}
```

### Step 4: Mock BambooHR API with MSW

```typescript
// tests/mocks/bamboohr.ts
import { http, HttpResponse } from 'msw';

const MOCK_COMPANY = 'testcompany';
const BASE = `https://api.bamboohr.com/api/gateway.php/${MOCK_COMPANY}/v1`;

export const bamboohrHandlers = [
  // Employee directory
  http.get(`${BASE}/employees/directory`, () => {
    return HttpResponse.json({
      fields: [{ id: 'displayName', type: 'text', name: 'Display Name' }],
      employees: [
        {
          id: '1', displayName: 'Jane Smith', firstName: 'Jane',
          lastName: 'Smith', jobTitle: 'Engineer', department: 'Engineering',
          workEmail: 'jane@test.com', location: 'Remote',
        },
        {
          id: '2', displayName: 'Bob Jones', firstName: 'Bob',
          lastName: 'Jones', jobTitle: 'Designer', department: 'Design',
          workEmail: 'bob@test.com', location: 'NYC',
        },
      ],
    });
  }),

  // Single employee
  http.get(`${BASE}/employees/:id/`, ({ params }) => {
    return HttpResponse.json({
      id: params.id, firstName: 'Jane', lastName: 'Smith',
      jobTitle: 'Engineer', department: 'Engineering',
      hireDate: '2023-01-15', workEmail: 'jane@test.com',
      status: 'Active',
    });
  }),

  // Custom report
  http.post(`${BASE}/reports/custom`, () => {
    return HttpResponse.json({
      title: 'Test Report', employees: [
        { firstName: 'Jane', lastName: 'Smith', department: 'Engineering' },
      ],
    });
  }),
];
```

### Step 5: Write Unit Tests

```typescript
// tests/unit/employees.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { bamboohrHandlers } from '../mocks/bamboohr';
import { BambooHRClient } from '../../src/bamboohr/client';

const server = setupServer(...bamboohrHandlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('BambooHRClient', () => {
  const client = new BambooHRClient('testcompany', 'fake-key');

  it('fetches the employee directory', async () => {
    const dir = await client.getDirectory();
    expect(dir.employees).toHaveLength(2);
    expect(dir.employees[0].displayName).toBe('Jane Smith');
  });

  it('fetches a single employee', async () => {
    const emp = await client.getEmployee(1, ['firstName', 'lastName', 'jobTitle']);
    expect(emp.firstName).toBe('Jane');
    expect(emp.jobTitle).toBe('Engineer');
  });
});
```

### Step 6: Integration Test Against Real API

```typescript
// tests/integration/bamboohr.test.ts
import { describe, it, expect } from 'vitest';
import { BambooHRClient } from '../../src/bamboohr/client';

const HAS_KEY = !!process.env.BAMBOOHR_API_KEY;

describe.skipIf(!HAS_KEY)('BambooHR Integration', () => {
  const client = new BambooHRClient();

  it('should fetch the real employee directory', async () => {
    const dir = await client.getDirectory();
    expect(dir.employees.length).toBeGreaterThan(0);
    expect(dir.employees[0]).toHaveProperty('displayName');
  }, 15_000);
});
```

## Output

- Reusable `BambooHRClient` with typed methods
- MSW mocks for offline development
- Unit tests with mocked API
- Integration tests gated on `BAMBOOHR_API_KEY` presence
- Hot-reload dev server via `tsx watch`

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `BambooHRError 401` | Wrong key in `.env.local` | Re-copy from BambooHR dashboard |
| MSW `onUnhandledRequest` | Unmocked endpoint hit | Add handler to `bamboohrHandlers` |
| `ECONNREFUSED` in tests | MSW server not started | Ensure `beforeAll(() => server.listen())` |
| Slow integration tests | Real API latency | Increase vitest timeout to 15s |

## Resources

- [MSW Documentation](https://mswjs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)

## Next Steps

See `bamboohr-sdk-patterns` for production-ready code patterns.
