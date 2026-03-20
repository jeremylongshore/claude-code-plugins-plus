---
name: apollo-local-dev-loop
description: |
  Configure Apollo.io local development workflow.
  Use when setting up development environment, testing API calls locally,
  or establishing team development practices.
  Trigger with phrases like "apollo local dev", "apollo development setup",
  "apollo dev environment", "apollo testing locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Local Dev Loop

## Overview
Set up an efficient local development workflow for Apollo.io integrations with environment management, mock servers for offline testing, request logging, and npm scripts for daily development.

## Prerequisites
- Completed `apollo-install-auth` setup
- Node.js 18+ or Python 3.10+
- Git repository initialized

## Instructions

### Step 1: Set Up Environment Files
```bash
# .env.example (commit this)
APOLLO_API_KEY=your-api-key-here
APOLLO_BASE_URL=https://api.apollo.io/v1
APOLLO_MOCK_ENABLED=false

# .env (gitignored, copy from example)
cp .env.example .env
# Then fill in your real API key
```

```bash
# Ensure .env is gitignored
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 2: Create a Dev Client with Request Logging
```typescript
// src/apollo/dev-client.ts
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

export const devClient = axios.create({
  baseURL: process.env.APOLLO_BASE_URL ?? 'https://api.apollo.io/v1',
  headers: { 'Content-Type': 'application/json' },
  params: { api_key: process.env.APOLLO_API_KEY },
});

// Log all requests in development
devClient.interceptors.request.use((config) => {
  console.log(`[Apollo] ${config.method?.toUpperCase()} ${config.url}`);
  if (config.data) {
    console.log('[Apollo] Body:', JSON.stringify(config.data, null, 2));
  }
  return config;
});

devClient.interceptors.response.use(
  (res) => {
    console.log(`[Apollo] ${res.status} (${res.config.url}) — ${res.headers['x-rate-limit-remaining']} requests remaining`);
    return res;
  },
  (err) => {
    console.error(`[Apollo] ERROR ${err.response?.status}: ${err.response?.data?.message ?? err.message}`);
    return Promise.reject(err);
  },
);
```

### Step 3: Set Up MSW Mock Server for Testing
```typescript
// src/mocks/apollo-handlers.ts
import { http, HttpResponse } from 'msw';

const BASE = 'https://api.apollo.io/v1';

export const apolloHandlers = [
  http.post(`${BASE}/people/search`, () =>
    HttpResponse.json({
      people: [
        { id: 'mock-1', name: 'Jane Doe', title: 'VP Sales', email: 'jane@example.com' },
        { id: 'mock-2', name: 'John Smith', title: 'Director', email: 'john@example.com' },
      ],
      pagination: { page: 1, per_page: 25, total_entries: 2 },
    }),
  ),

  http.post(`${BASE}/people/match`, () =>
    HttpResponse.json({
      person: {
        id: 'mock-enriched',
        name: 'Jane Doe',
        email: 'jane@example.com',
        title: 'VP Sales',
        organization: { name: 'Example Corp' },
      },
    }),
  ),

  http.get(`${BASE}/organizations/enrich`, ({ request }) => {
    const url = new URL(request.url);
    const domain = url.searchParams.get('domain');
    return HttpResponse.json({
      organization: {
        id: 'mock-org',
        name: domain?.replace('.com', '') ?? 'Mock Org',
        industry: 'Technology',
        estimated_num_employees: 250,
      },
    });
  }),

  http.get(`${BASE}/emailer_campaigns`, () =>
    HttpResponse.json({
      emailer_campaigns: [
        { id: 'seq-1', name: 'Q1 Outbound', active: true, num_contacts_with_status: 50 },
      ],
    }),
  ),
];
```

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node';
import { apolloHandlers } from './apollo-handlers';

export const mockServer = setupServer(...apolloHandlers);
```

### Step 4: Configure Vitest for Apollo Tests
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    setupFiles: ['./src/mocks/setup.ts'],
    environment: 'node',
  },
});
```

```typescript
// src/mocks/setup.ts
import { mockServer } from './server';
import { beforeAll, afterAll, afterEach } from 'vitest';

beforeAll(() => mockServer.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => mockServer.resetHandlers());
afterAll(() => mockServer.close());
```

```typescript
// src/__tests__/people-search.test.ts
import { describe, it, expect } from 'vitest';
import { devClient } from '../apollo/dev-client';

describe('Apollo People Search', () => {
  it('returns mock people data', async () => {
    const { data } = await devClient.post('/people/search', {
      q_organization_domains: ['example.com'],
      per_page: 10,
    });

    expect(data.people).toHaveLength(2);
    expect(data.people[0].name).toBe('Jane Doe');
    expect(data.pagination.total_entries).toBe(2);
  });
});
```

### Step 5: Add npm Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:live": "APOLLO_MOCK_ENABLED=false vitest --run",
    "apollo:check": "tsx src/scripts/check-credentials.ts",
    "apollo:quota": "tsx src/scripts/check-quota.ts"
  }
}
```

```typescript
// src/scripts/check-credentials.ts
import { devClient } from '../apollo/dev-client';

async function checkCredentials() {
  try {
    const { data } = await devClient.post('/people/search', {
      q_organization_domains: ['apollo.io'],
      per_page: 1,
    });
    console.log('API key valid. Found', data.pagination.total_entries, 'results');
  } catch (err: any) {
    console.error('API key check failed:', err.response?.status, err.response?.data?.message);
    process.exit(1);
  }
}

checkCredentials();
```

## Output
- `.env.example` template and `.env` gitignore rules
- Dev client with request/response logging and rate-limit display
- MSW mock handlers for people search, enrichment, org enrichment, and sequences
- Vitest config with mock server setup/teardown
- npm scripts: `dev`, `test`, `test:live`, `apollo:check`, `apollo:quota`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing API Key | `.env` not loaded | Run `cp .env.example .env` and fill in your key |
| Mock Not Working | MSW not configured | Ensure `setupFiles` points to mock setup |
| Rate Limited in Dev | Too many live API calls | Use `npm test` (mocked) instead of `test:live` |
| Stale Credentials | Key rotated in dashboard | Run `npm run apollo:check` to verify |

## Examples

### Quick Start for New Team Members
```bash
git clone <repo> && cd <repo>
npm install
cp .env.example .env
# Edit .env with your Apollo API key
npm run apollo:check   # Verify credentials
npm test               # Run tests with mocks
npm run dev            # Start development
```

## Resources
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Testing Framework](https://vitest.dev/)
- [dotenv Configuration](https://github.com/motdotla/dotenv)

## Next Steps
Proceed to `apollo-sdk-patterns` for production-ready code patterns.
