---
name: klaviyo-local-dev-loop
description: 'Configure Klaviyo local development with hot reload, mocking, and testing.

  Use when setting up a development environment, configuring test workflows,

  or establishing a fast iteration cycle with the Klaviyo API.

  Trigger with phrases like "klaviyo dev setup", "klaviyo local development",

  "klaviyo dev environment", "develop with klaviyo", "klaviyo testing".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Klaviyo integrations with hot reload, SDK mocking, and integration tests. The loop keeps three concerns separate: a lazily-instantiated SDK client singleton, mocked unit tests that never hit the network, and live integration tests gated behind an opt-in flag so they only run in CI.

## Prerequisites

- Completed `klaviyo-install-auth` setup (provides your private API key)
- Node.js 18+ with `npm` or `pnpm` on the PATH
- `klaviyo-api` package installed as a project dependency
- `tsx` and `vitest` installed as dev dependencies for hot reload and tests

## Instructions

Follow six steps to stand up the loop. The full file contents for each step —
project layout, `.env` templates, `package.json` scripts, and the client
singleton — live in [full walkthrough](references/implementation.md). The
complete test files live in [test examples](references/examples.md).

1. **Project structure** — create `src/klaviyo/` for SDK modules and `tests/{unit,integration}/`. Keep secrets in a git-ignored `.env.local`, ship a committed `.env.example`.
2. **Environment configuration** — define `KLAVIYO_PRIVATE_KEY` / `KLAVIYO_PUBLIC_KEY` and wire the `dev`, `test`, `test:watch`, `test:integration`, and `typecheck` scripts.
3. **SDK client singleton** — read the key once, cache the `ApiKeySession`, and export lazy per-API accessors so you only instantiate what you use:

   ```typescript
   // src/klaviyo/client.ts
   import { ApiKeySession, ProfilesApi } from 'klaviyo-api';

   let session: ApiKeySession | null = null;
   function getSession(): ApiKeySession {
     if (!session) {
       const key = process.env.KLAVIYO_PRIVATE_KEY;
       if (!key) throw new Error('KLAVIYO_PRIVATE_KEY not set');
       session = new ApiKeySession(key);
     }
     return session;
   }
   export const profiles = () => new ProfilesApi(getSession());
   ```

4. **Unit testing with mocks** — `vi.mock('klaviyo-api', ...)` the whole SDK so unit tests are deterministic and offline. See [test examples](references/examples.md).
5. **Integration test** — a `describe.skipIf(!process.env.KLAVIYO_TEST)` suite that exercises the live account. See [test examples](references/examples.md).
6. **Hot reload development** — run `npm run dev` (`tsx watch`) in one terminal and `npm run test:watch` in another for a tight edit-test cycle.

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

## Examples

A minimal mocked unit test — no network, fully deterministic. The full unit and
integration suites are in [test examples](references/examples.md).

```typescript
// tests/unit/profiles.test.ts
import { describe, it, expect, vi } from 'vitest';

vi.mock('klaviyo-api', () => ({
  ApiKeySession: vi.fn(),
  ProfilesApi: vi.fn().mockImplementation(() => ({
    createProfile: vi.fn().mockResolvedValue({
      body: { data: { id: '01JMOCKPROFILEID', attributes: { email: 'test@example.com' } } },
    }),
  })),
}));

import { ProfilesApi, ApiKeySession } from 'klaviyo-api';

describe('Profile operations', () => {
  it('creates a profile with email', async () => {
    const api = new ProfilesApi(new ApiKeySession('pk_test_key'));
    const result = await api.createProfile({
      data: { type: 'profile' as any, attributes: { email: 'test@example.com' } },
    });
    expect(result.body.data.id).toBe('01JMOCKPROFILEID');
  });
});
```

Run it with `npm run test`, or `npm run test:watch` for the hot loop. To exercise
the live API instead, set `KLAVIYO_TEST=1` and run `npm run test:integration`.

## Resources

- [klaviyo-api-node SDK](https://github.com/klaviyo/klaviyo-api-node)
- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)
- [Full implementation walkthrough](references/implementation.md)
- [Complete test examples](references/examples.md)

## Next Steps

See `klaviyo-sdk-patterns` for production-ready code patterns, and
`klaviyo-install-auth` if you still need to provision an API key. Once the loop
is green locally, wire `npm run test:integration` into CI behind the
`KLAVIYO_TEST` gate so live checks run only where a sandbox key is available.
