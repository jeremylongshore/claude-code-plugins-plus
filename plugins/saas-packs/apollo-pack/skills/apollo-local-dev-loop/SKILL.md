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
tags: [saas, apollo, api, testing, workflow]

---
# Apollo Local Dev Loop

## Overview
Set up an efficient local development workflow for Apollo.io integrations. Includes sandbox API key support, MSW mock server for offline testing, request logging, and npm scripts for daily development. Apollo provides a **sandbox API token** that returns dummy data without consuming credits.

## Prerequisites
- Completed `apollo-install-auth` setup
- Node.js 18+
- Git repository initialized

## Instructions

### Step 1: Set Up Environment Files
Apollo offers a sandbox token for testing. Generate one at Settings > Integrations > API Keys > Sandbox.

```bash
# .env.example (commit this — team reference)
APOLLO_API_KEY=your-api-key-here
APOLLO_SANDBOX_KEY=your-sandbox-key-here
APOLLO_USE_SANDBOX=false

# .env (gitignored — copy from example)
cp .env.example .env
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

### Step 2: Create a Dev Client with Request Logging
```typescript
// src/apollo/dev-client.ts
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const apiKey = process.env.APOLLO_USE_SANDBOX === 'true'
  ? process.env.APOLLO_SANDBOX_KEY
  : process.env.APOLLO_API_KEY;

export const devClient = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': apiKey!,
  },
  timeout: 30_000,
});

// Log all requests in development
devClient.interceptors.request.use((config) => {
  console.log(`[Apollo] ${config.method?.toUpperCase()} ${config.url}`);
  if (config.data) console.log('[Apollo] Body:', JSON.stringify(config.data, null, 2));
  return config;
});

devClient.interceptors.response.use(
  (res) => {
    const remaining = res.headers['x-rate-limit-remaining'];
    console.log(`[Apollo] ${res.status} ${res.config.url}${remaining ? ` — ${remaining} req remaining` : ''}`);
    return res;
  },
  (err) => {
    console.error(`[Apollo] ERROR ${err.response?.status}: ${err.response?.data?.message ?? err.message}`);
    return Promise.reject(err);
  },
);
```

### Step 3: Set Up MSW Mock Server for Offline Testing
```typescript
// src/mocks/apollo-handlers.ts
import { http, HttpResponse } from 'msw';

const BASE = 'https://api.apollo.io/api/v1';

export const apolloHandlers = [
  // People Search (free endpoint)
  http.post(`${BASE}/mixed_people/api_search`, () =>
    HttpResponse.json({
      people: [
        { id: 'mock-1', name: 'Jane Doe', title: 'VP Sales', organization: { name: 'Acme Corp' } },
        { id: 'mock-2', name: 'John Smith', title: 'Director Engineering', organization: { name: 'Acme Corp' } },
      ],
      pagination: { page: 1, per_page: 25, total_entries: 2, total_pages: 1 },
    }),
  ),

  // People Enrichment
  http.post(`${BASE}/people/match`, () =>
    HttpResponse.json({
      person: {
        id: 'mock-enriched', name: 'Jane Doe', email: 'jane@acme.com',
        title: 'VP Sales', organization: { name: 'Acme Corp' },
        phone_numbers: [{ sanitized_number: '+14155551234' }],
        linkedin_url: 'https://www.linkedin.com/in/janedoe',
      },
    }),
  ),

  // Organization Enrichment
  http.get(`${BASE}/organizations/enrich`, ({ request }) => {
    const url = new URL(request.url);
    return HttpResponse.json({
      organization: {
        id: 'mock-org', name: 'Acme Corp', industry: 'Technology',
        estimated_num_employees: 250, annual_revenue_printed: '$25M',
        primary_domain: url.searchParams.get('domain') ?? 'acme.com',
      },
    });
  }),

  // Search for Sequences
  http.post(`${BASE}/emailer_campaigns/search`, () =>
    HttpResponse.json({
      emailer_campaigns: [
        { id: 'seq-1', name: 'Q1 Outbound', active: true, num_steps: 4 },
      ],
    }),
  ),

  // Auth Health
  http.get(`${BASE}/auth/health`, () =>
    HttpResponse.json({ is_logged_in: true }),
  ),
];
```

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node';
import { apolloHandlers } from './apollo-handlers';
export const mockServer = setupServer(...apolloHandlers);
```

### Step 4: Configure Vitest
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: { setupFiles: ['./src/mocks/setup.ts'], environment: 'node' },
});

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
  it('returns contacts from mock server', async () => {
    const { data } = await devClient.post('/mixed_people/api_search', {
      q_organization_domains_list: ['acme.com'],
      per_page: 10,
    });
    expect(data.people).toHaveLength(2);
    expect(data.people[0].name).toBe('Jane Doe');
  });
});
```

### Step 5: Add Development Scripts
```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:live": "APOLLO_USE_SANDBOX=false vitest --run",
    "test:sandbox": "APOLLO_USE_SANDBOX=true vitest --run",
    "apollo:check": "tsx src/scripts/verify-auth.ts",
    "apollo:search": "tsx src/scripts/quick-search.ts"
  }
}
```

## Output
- `.env.example` template with sandbox key support
- Dev client with request/response logging and rate-limit display
- MSW mock handlers for people search, enrichment, org enrichment, and sequences
- Vitest config with mock server setup/teardown
- npm scripts for dev, test, sandbox testing, and credential checks

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Missing API Key | `.env` not loaded | Run `cp .env.example .env` and add your key |
| Mock Not Working | MSW not configured | Ensure `setupFiles` includes mock setup |
| Unexpected credits used | Sandbox mode off | Set `APOLLO_USE_SANDBOX=true` in `.env` |
| Stale Credentials | Key rotated in dashboard | Run `npm run apollo:check` to verify |

## Resources
- [Apollo Sandbox Testing](https://docs.apollo.io/docs/test-api-key)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Vitest Testing Framework](https://vitest.dev/)

## Next Steps
Proceed to `apollo-sdk-patterns` for production-ready code patterns.
