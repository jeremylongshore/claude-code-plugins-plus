---
name: klaviyo-local-dev-loop
description: |
  Configure Klaviyo local development with hot reload, mocking, and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with the Klaviyo API.
  Trigger with phrases like "klaviyo dev setup", "klaviyo local development",
  "klaviyo dev environment", "develop with klaviyo", "klaviyo testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Klaviyo integrations with hot reload, SDK mocking, and integration tests.

## Prerequisites

- Completed `klaviyo-install-auth` setup
- Node.js 18+ with npm/pnpm
- `klaviyo-api` package installed

## Instructions

### Step 1: Project Structure

```
my-klaviyo-project/
├── src/
│   ├── klaviyo/
│   │   ├── client.ts          # ApiKeySession + API class singletons
│   │   ├── profiles.ts        # Profile operations
│   │   ├── events.ts          # Event tracking
│   │   └── lists.ts           # List management
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── profiles.test.ts   # Mocked SDK tests
│   └── integration/
│       └── klaviyo.test.ts    # Live API tests (CI only)
├── .env.local                 # Local secrets (git-ignored)
├── .env.example               # Template for team
├── .env.test                  # Test environment (sandbox key)
└── package.json
```

### Step 2: Environment Configuration

```bash
# .env.example (commit this)
KLAVIYO_PRIVATE_KEY=pk_your_test_key_here
KLAVIYO_PUBLIC_KEY=YourPublicKey
NODE_ENV=development

# .env.local (git-ignored, actual secrets)
KLAVIYO_PRIVATE_KEY=pk_********************************
```

```json
// package.json scripts
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "KLAVIYO_TEST=1 vitest --config vitest.integration.config.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

### Step 3: SDK Client Singleton

```typescript
// src/klaviyo/client.ts
import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ListsApi,
  SegmentsApi,
  CampaignsApi,
  MetricsApi,
} from 'klaviyo-api';

let session: ApiKeySession | null = null;

function getSession(): ApiKeySession {
  if (!session) {
    const key = process.env.KLAVIYO_PRIVATE_KEY;
    if (!key) throw new Error('KLAVIYO_PRIVATE_KEY not set');
    session = new ApiKeySession(key);
  }
  return session;
}

// Lazy singletons -- only instantiate what you use
export const profiles = () => new ProfilesApi(getSession());
export const events = () => new EventsApi(getSession());
export const lists = () => new ListsApi(getSession());
export const segments = () => new SegmentsApi(getSession());
export const campaigns = () => new CampaignsApi(getSession());
export const metrics = () => new MetricsApi(getSession());
```

### Step 4: Unit Testing with Mocks

```typescript
// tests/unit/profiles.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the entire klaviyo-api module
vi.mock('klaviyo-api', () => ({
  ApiKeySession: vi.fn(),
  ProfilesApi: vi.fn().mockImplementation(() => ({
    createProfile: vi.fn().mockResolvedValue({
      body: {
        data: {
          id: '01JMOCKPROFILEID',
          type: 'profile',
          attributes: { email: 'test@example.com', firstName: 'Test' },
        },
      },
    }),
    getProfiles: vi.fn().mockResolvedValue({
      body: {
        data: [{ id: '01JMOCKPROFILEID', attributes: { email: 'test@example.com' } }],
        links: { next: null },
      },
    }),
  })),
  ProfileEnum: { Profile: 'profile' },
}));

import { ProfilesApi, ApiKeySession } from 'klaviyo-api';

describe('Profile operations', () => {
  let profilesApi: ProfilesApi;

  beforeEach(() => {
    const session = new ApiKeySession('pk_test_key');
    profilesApi = new ProfilesApi(session);
  });

  it('creates a profile with email', async () => {
    const result = await profilesApi.createProfile({
      data: {
        type: 'profile' as any,
        attributes: { email: 'test@example.com', firstName: 'Test' },
      },
    });
    expect(result.body.data.id).toBe('01JMOCKPROFILEID');
  });
});
```

### Step 5: Integration Test (runs against live API)

```typescript
// tests/integration/klaviyo.test.ts
import { describe, it, expect } from 'vitest';
import { ApiKeySession, ProfilesApi, AccountsApi } from 'klaviyo-api';

const SKIP = !process.env.KLAVIYO_TEST;

describe.skipIf(SKIP)('Klaviyo Integration', () => {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

  it('connects to Klaviyo account', async () => {
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();
    expect(result.body.data).toHaveLength(1);
    expect(result.body.data[0].id).toBeTruthy();
  });

  it('creates and retrieves a test profile', async () => {
    const profilesApi = new ProfilesApi(session);
    const testEmail = `test-${Date.now()}@example.com`;

    await profilesApi.createProfile({
      data: {
        type: 'profile' as any,
        attributes: { email: testEmail, firstName: 'IntegrationTest' },
      },
    });

    const profiles = await profilesApi.getProfiles({
      filter: `equals(email,"${testEmail}")`,
    });
    expect(profiles.body.data[0].attributes.firstName).toBe('IntegrationTest');
  });
});
```

### Step 6: Hot Reload Development

```bash
# Start dev server with file watching
npm run dev

# In another terminal, run tests on change
npm run test:watch
```

## Output

- Working dev environment with hot reload via `tsx watch`
- Unit tests with mocked `klaviyo-api` SDK
- Integration tests gated behind `KLAVIYO_TEST=1`
- Client singleton pattern for consistent SDK usage

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `KLAVIYO_PRIVATE_KEY not set` | Missing .env.local | Copy from .env.example |
| Mock type errors | SDK type mismatches | Use `as any` for mock enum values |
| Integration test 429 | Rate limited in CI | Add delays between tests or use test key |
| `tsx` not found | Missing dependency | `npm install -D tsx` |

## Resources

- [klaviyo-api-node SDK](https://github.com/klaviyo/klaviyo-api-node)
- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)

## Next Steps

See `klaviyo-sdk-patterns` for production-ready code patterns.
