---
name: intercom-local-dev-loop
description: |
  Configure Intercom local development with testing, mocking, and hot reload.
  Use when setting up a development environment, writing tests against the
  Intercom API, or establishing a fast iteration cycle against a dev workspace.
  Trigger with phrases like "intercom dev setup", "intercom local development",
  "intercom dev environment", "develop with intercom", "test intercom locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Local Dev Loop

## Overview

Set up a fast local development workflow for Intercom integrations with proper
test isolation, mocking strategies, and webhook tunneling. The loop has two
lanes: a mocked unit lane that runs offline with no token, and an integration
lane that talks to a real dev workspace and is skipped automatically when no
token is present.

## Prerequisites

- Completed `intercom-install-auth` setup
- Node.js 18+ with npm/pnpm
- A test/development Intercom workspace (separate from production)

## Authentication

The client authenticates with a single Intercom bearer access token, issued per
workspace by the `intercom-install-auth` step. Read it from
`process.env.INTERCOM_ACCESS_TOKEN` (loaded from git-ignored `.env.development`);
never hardcode it. The mocked unit lane needs no token at all — pointing the loop
at a different dev workspace is only a matter of swapping the `.env.development`
value.

## Instructions

Work through these steps to stand up the loop. The full, copy-paste-ready code
for every step lives in [the implementation walkthrough](references/implementation.md).

1. **Scaffold the project structure** — an `src/intercom/` module (singleton
   `client.ts`, plus `contacts.ts` / `conversations.ts` / `types.ts`), a `tests/`
   tree with a `mocks/` factory, and three env files (`.env.example` committed,
   `.env.development` and `.env.test` git-ignored). Use **Write** to create each
   file. See [implementation.md](references/implementation.md).

2. **Configure environments** — commit `.env.example` as the template and keep
   real tokens in the git-ignored `.env.development`. See
   [implementation.md](references/implementation.md).

3. **Write an environment-aware client singleton** that reads the token, throws a
   clear error when it is missing, and exposes a `resetClient()` for tests. The
   skeleton:

   ```typescript
   // src/intercom/client.ts
   import { IntercomClient } from "intercom-client";

   let instance: IntercomClient | null = null;

   export function getClient(): IntercomClient {
     if (!instance) {
       const token = process.env.INTERCOM_ACCESS_TOKEN;
       if (!token) {
         throw new Error(
           "INTERCOM_ACCESS_TOKEN not set. Copy .env.example to .env.development"
         );
       }
       instance = new IntercomClient({ token });
     }
     return instance;
   }

   export function resetClient(): void {
     instance = null;
   }
   ```

4. **Build a mock client factory** (`tests/mocks/intercom.ts`) covering contacts,
   conversations, messages, admins, and tags with `vi.fn()` resolved values, so
   the unit lane never touches the network. Full factory in
   [implementation.md](references/implementation.md).

5. **Write mocked unit tests** against the factory, asserting call arguments and
   returned shapes. See [implementation.md](references/implementation.md).

6. **Tunnel webhooks with ngrok** — run the local server, `ngrok http 3000`, and
   register the HTTPS URL in Intercom Developer Hub. Use **Bash(npx:*)** for
   ngrok. See [implementation.md](references/implementation.md).

7. **Wire package scripts** (`dev`, `test`, `test:watch`, `test:integration`,
   `typecheck`) — use **Edit** to add them to `package.json`, then drive the loop
   with **Bash(npm:*)**. See [implementation.md](references/implementation.md).

## Output

Following this skill produces a working local Intercom development loop:

- A scaffolded `src/intercom/` client module and `tests/` tree with a reusable
  mock factory.
- Three environment files — a committed `.env.example` template plus git-ignored
  `.env.development` / `.env.test`.
- An offline mocked unit test lane (`npm run test` / `test:watch`) that runs with
  no token and no network.
- A token-gated integration lane (`npm run test:integration`) that is skipped
  automatically when `INTERCOM_ACCESS_TOKEN` is absent.
- An ngrok webhook tunnel exposing the local server to Intercom's Developer Hub.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INTERCOM_ACCESS_TOKEN not set` | Missing .env file | Copy `.env.example` to `.env.development` |
| Port 3000 in use | Another process | `lsof -i :3000` and kill, or change port |
| ngrok tunnel expired | Free tier 2h limit | Restart ngrok or use paid plan |
| Mock type mismatch | SDK updated | Regenerate mocks from SDK types |
| `rate_limit_exceeded` in dev | Dev workspace limits | Add delays between integration tests |

## Examples

A minimal mocked unit test (from
[implementation.md](references/implementation.md)):

```typescript
it("should create a user contact", async () => {
  const contact = await mockClient.contacts.create({
    role: "user",
    externalId: "user-123",
    email: "test@example.com",
  });

  expect(contact.id).toBe("mock-contact-id");
  expect(mockClient.contacts.create).toHaveBeenCalledOnce();
});
```

For the token-gated integration test pattern (`describe.skipIf`, live create +
cleanup) and the commands that drive each lane, see
[the examples reference](references/examples.md).

## Resources

- [Full implementation walkthrough](references/implementation.md) — every step's complete code
- [Integration examples](references/examples.md) — live-workspace test pattern and run commands
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)
- [Vitest Documentation](https://vitest.dev/)
- [ngrok](https://ngrok.com/)
- See `intercom-sdk-patterns` for production-ready code patterns.
