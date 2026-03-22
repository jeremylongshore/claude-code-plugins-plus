---
name: hubspot-local-dev-loop
description: |
  Configure HubSpot local development with testing and sandbox accounts.
  Use when setting up a development environment, mocking HubSpot APIs,
  or establishing a fast iteration cycle for HubSpot integrations.
  Trigger with phrases like "hubspot dev setup", "hubspot local development",
  "hubspot test sandbox", "develop with hubspot", "mock hubspot".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Local Dev Loop

## Overview

Set up a fast local development workflow for HubSpot integrations with sandbox accounts, mocking, and test utilities.

## Prerequisites

- Completed `hubspot-install-auth` setup
- Node.js 18+ with npm/pnpm
- HubSpot developer test account (free at developers.hubspot.com)

## Instructions

### Step 1: Create Project Structure

```
my-hubspot-project/
├── src/
│   ├── hubspot/
│   │   ├── client.ts       # Singleton @hubspot/api-client wrapper
│   │   ├── contacts.ts     # Contact operations
│   │   ├── deals.ts        # Deal operations
│   │   └── types.ts        # HubSpot type definitions
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── hubspot.ts      # Shared mock factory
│   ├── contacts.test.ts
│   └── deals.test.ts
├── .env.local               # Local secrets (git-ignored)
├── .env.example             # Template for team
├── tsconfig.json
└── package.json
```

### Step 2: Create Client Singleton

```typescript
// src/hubspot/client.ts
import * as hubspot from '@hubspot/api-client';

let instance: hubspot.Client | null = null;

export function getHubSpotClient(): hubspot.Client {
  if (!instance) {
    if (!process.env.HUBSPOT_ACCESS_TOKEN) {
      throw new Error('HUBSPOT_ACCESS_TOKEN environment variable is required');
    }
    instance = new hubspot.Client({
      accessToken: process.env.HUBSPOT_ACCESS_TOKEN,
      numberOfApiCallRetries: 3,
    });
  }
  return instance;
}

// Reset client (useful for tests)
export function resetHubSpotClient(): void {
  instance = null;
}
```

### Step 3: Configure Testing with Vitest

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "HUBSPOT_TEST=true vitest --config vitest.integration.config.ts"
  },
  "devDependencies": {
    "@hubspot/api-client": "^13.0.0",
    "vitest": "^2.0.0",
    "tsx": "^4.0.0"
  }
}
```

### Step 4: Mock HubSpot API for Unit Tests

```typescript
// tests/mocks/hubspot.ts
import { vi } from 'vitest';

export function createMockHubSpotClient() {
  return {
    crm: {
      contacts: {
        basicApi: {
          create: vi.fn().mockResolvedValue({
            id: '101',
            properties: { firstname: 'Jane', lastname: 'Doe', email: 'jane@test.com' },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            archived: false,
          }),
          getById: vi.fn().mockResolvedValue({
            id: '101',
            properties: { firstname: 'Jane', lastname: 'Doe', email: 'jane@test.com' },
          }),
          getPage: vi.fn().mockResolvedValue({
            results: [],
            paging: undefined,
          }),
          update: vi.fn().mockResolvedValue({ id: '101', properties: {} }),
          archive: vi.fn().mockResolvedValue(undefined),
        },
        searchApi: {
          doSearch: vi.fn().mockResolvedValue({ total: 0, results: [] }),
        },
        batchApi: {
          create: vi.fn().mockResolvedValue({ status: 'COMPLETE', results: [] }),
          read: vi.fn().mockResolvedValue({ status: 'COMPLETE', results: [] }),
          update: vi.fn().mockResolvedValue({ status: 'COMPLETE', results: [] }),
        },
      },
      deals: {
        basicApi: {
          create: vi.fn().mockResolvedValue({
            id: '201',
            properties: { dealname: 'Test Deal', amount: '1000' },
          }),
          getById: vi.fn(),
          update: vi.fn(),
        },
      },
      companies: {
        basicApi: {
          create: vi.fn().mockResolvedValue({
            id: '301',
            properties: { name: 'Test Co', domain: 'test.com' },
          }),
        },
      },
    },
  };
}

// tests/contacts.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMockHubSpotClient } from './mocks/hubspot';

vi.mock('../src/hubspot/client', () => ({
  getHubSpotClient: vi.fn(),
}));

describe('Contact operations', () => {
  const mockClient = createMockHubSpotClient();

  beforeEach(() => {
    vi.mocked(getHubSpotClient).mockReturnValue(mockClient as any);
  });

  it('should create a contact with required properties', async () => {
    const result = await mockClient.crm.contacts.basicApi.create({
      properties: { firstname: 'Jane', lastname: 'Doe', email: 'jane@test.com' },
      associations: [],
    });
    expect(result.id).toBe('101');
    expect(result.properties.email).toBe('jane@test.com');
  });
});
```

### Step 5: Developer Test Account

```bash
# Create a free developer test account at:
# https://developers.hubspot.com/get-started

# Use test account token for integration tests
# .env.local
HUBSPOT_ACCESS_TOKEN=pat-na1-test-xxxx  # test account token
HUBSPOT_PORTAL_ID=12345678              # test portal ID
```

## Output

- Client singleton with reset capability for tests
- Mock factory covering contacts, deals, companies
- Unit tests running without API calls
- Integration tests using developer test account
- Hot-reload dev loop with `tsx watch`

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `HUBSPOT_ACCESS_TOKEN is required` | Missing env var | Copy `.env.example` to `.env.local` |
| Mock type mismatch | SDK version change | Update mock factory to match SDK types |
| Test timeout | Real API call leaked | Verify mocks are wired correctly |
| `429` in integration tests | Rate limited on test account | Add delay between test runs |

## Examples

### Integration Test with Real API

```typescript
// tests/integration/contacts.integration.test.ts
import { describe, it, expect } from 'vitest';
import * as hubspot from '@hubspot/api-client';

const shouldRun = process.env.HUBSPOT_TEST === 'true';

describe.skipIf(!shouldRun)('HubSpot Integration', () => {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  });

  it('should create and archive a test contact', async () => {
    const contact = await client.crm.contacts.basicApi.create({
      properties: {
        firstname: 'Integration',
        lastname: `Test-${Date.now()}`,
        email: `test-${Date.now()}@example.com`,
      },
      associations: [],
    });
    expect(contact.id).toBeDefined();

    // Clean up
    await client.crm.contacts.basicApi.archive(contact.id);
  });
});
```

## Resources

- [HubSpot Developer Test Accounts](https://developers.hubspot.com/docs/guides/apps/developer-test-accounts)
- [Vitest Documentation](https://vitest.dev/)
- [@hubspot/api-client GitHub](https://github.com/HubSpot/hubspot-api-nodejs)

## Next Steps

See `hubspot-sdk-patterns` for production-ready code patterns.
