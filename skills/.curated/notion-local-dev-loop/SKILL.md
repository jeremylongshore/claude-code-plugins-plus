---
name: notion-local-dev-loop
description: |
  Configure Notion local development with a dedicated dev integration, test
  mocking, and hot reload. Use when setting up a Notion development
  environment, writing tests for Notion code, or establishing a fast
  iteration cycle against the Notion API without risking production data.
  Trigger with "notion dev setup", "notion local development", "mock notion",
  "notion test environment".
allowed-tools: Read, Write, Bash(npm:*), Bash(pnpm:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Notion integrations. This skill creates a
dedicated dev integration with its own token, structures the project for testability, mocks the
Notion SDK in unit tests, and runs gated integration tests against a sandboxed dev workspace — so
production data stays safe while you iterate quickly.

## Prerequisites

- Completed `notion-install-auth` setup (you have a working Notion integration)
- Node.js 18+ with npm/pnpm, or Python 3.10+
- A Notion workspace where you can create test pages and databases

## Authentication

This workflow uses a **separate dev integration token**, never the production token. The Notion SDK
reads `NOTION_TOKEN` from the environment automatically. Store the dev token (prefix `ntn_`) in a
git-ignored `.env.development` and commit a `.env.example` template so teammates know which variables
to fill in. Token creation is covered by the `notion-install-auth` skill; Step 1 below wires it into
the dev sandbox.

## Instructions

### Step 1: Create a Dev Integration and Workspace Sandbox

Create a separate integration exclusively for development so writes can never touch production data.

1. Go to **Settings & Members > Connections > Develop or manage integrations** (or visit [developers.notion.com](https://developers.notion.com))
2. Click **New integration** and name it `My App — Dev`
3. Copy the token (starts with `ntn_`) into `.env.development`
4. Create a dedicated **Dev Workspace** page (or a top-level "Dev Testing" page) and share it with the dev integration
5. Inside that page, create test databases that mirror your production schema

```bash
# .env.development — git-ignored, dev only
NOTION_TOKEN=ntn_dev_xxxxxxxxxxxxxxxxxxxx
NOTION_TEST_DATABASE_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
NOTION_TEST_PAGE_ID=ffffffff-0000-1111-2222-333333333333

# .env.example — commit this as a template
NOTION_TOKEN=ntn_your_dev_token_here
NOTION_TEST_DATABASE_ID=your_test_db_id
NOTION_TEST_PAGE_ID=your_test_page_id
```

Recommended project layout — a `notion/` module the app imports, and split unit/integration tests:

```
my-notion-project/
├── src/
│   ├── notion/
│   │   ├── client.ts          # Singleton with retry + rate-limit awareness
│   │   ├── queries.ts         # Database query wrappers
│   │   └── helpers.ts         # Property extractors, rich text builders
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── notion.test.ts     # Mocked SDK tests
│   └── integration/
│       └── notion.test.ts     # Live API tests (gated)
├── .env.development            # Dev token (git-ignored)
├── .env.example                # Template for team
├── .gitignore
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

### Step 2: Configure the Client with Retry and Rate-Limit Handling

The Notion API enforces a hard limit of **3 requests per second** across all pricing tiers, so build
retry logic into a shared singleton client from day one. The essential shape:

```typescript
// src/notion/client.ts — singleton + exponential-backoff retry on HTTP 429
export function getNotionClient(): Client { /* cache one Client instance */ }
export async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> { /* backoff */ }
```

For the complete `client.ts` (backoff math, `retry-after` header parsing, debug logging) plus the
`package.json` scripts (`dev` hot reload, `test`, `test:integration`, `typecheck`) and dev
dependencies, see [client and config reference](references/client-and-config.md).

### Step 3: Write Unit Tests with a Mocked SDK, plus Gated Integration Tests

**Unit tests** mock the entire `@notionhq/client` module so they run instantly with no network
calls. **Integration tests** hit the real API but are gated behind an environment variable and
target only the dev workspace:

```typescript
// tests/unit/notion.test.ts — mock the SDK so tests run offline
vi.mock('@notionhq/client', () => ({ Client: vi.fn().mockImplementation(() => ({ /* stubbed API */ })) }));

// tests/integration/notion.test.ts — only run when INTEGRATION=true, against the dev workspace
describe.skipIf(!process.env.INTEGRATION)('Notion Integration (live API)', () => { /* live calls */ });
```

Run units with `npm test` (or `pnpm test`) and the gated live suite with `npm run test:integration`.
For the full mocked query/pagination tests, the live connect/query/create-and-archive cleanup tests,
and the `vitest.config.ts`, see [testing reference](references/testing.md).

## Output

After completing these steps you will have:

- A **dedicated dev integration** with its own token, isolated from production
- A **singleton client** with built-in retry logic for the 3 req/s rate limit
- **Unit tests** that run instantly using mocked `@notionhq/client`
- **Integration tests** gated behind `INTEGRATION=true`, targeting dev-only pages
- **Hot reload** via `tsx watch` for rapid iteration
- **Type checking** via `tsc --noEmit`

## Error Handling

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `NOTION_TOKEN undefined` | Missing `.env.development` or not loaded | Run `cp .env.example .env.development` and fill in dev token |
| `401 Unauthorized` | Token invalid or integration not connected to page | Re-share the dev page with the dev integration |
| `404 Not found` (database/page) | Test DB not shared with dev integration | Open DB in Notion > `...` > Connections > add your dev integration |
| Mock not intercepting calls | `vi.mock()` not at file top level | Move `vi.mock('@notionhq/client', ...)` above all imports |
| `429 Rate Limited` | Exceeded 3 req/s | Use `withRetry` wrapper; add delay between batch operations |
| Integration tests timeout | Slow API under rate limits | Increase `testTimeout` in vitest config; reduce test data volume |
| `baseUrl` connection refused | Proxy or mock server not running | Verify proxy is up; remove `baseUrl` override for direct API access |

## Examples

Minimal TypeScript smoke test to confirm the dev token and database access are wired correctly:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const { results } = await notion.users.list({});
console.log(`Connected. ${results.length} user(s) in workspace.`);
```

For the full TypeScript smoke test (with dev-database verification) and the Python equivalent using
`notion-client` plus a pytest mocking example, see [examples reference](references/examples.md).

## Resources

- [@notionhq/client (npm)](https://www.npmjs.com/package/@notionhq/client) — official Node.js SDK
- [notion-sdk-py (PyPI)](https://pypi.org/project/notion-client/) — official Python SDK
- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/s across all tiers
- [Notion API Errors](https://developers.notion.com/reference/errors) — status codes and retry guidance
- [Vitest Mocking Guide](https://vitest.dev/guide/mocking.html) — `vi.mock` patterns for SDK mocking
- [Client and config reference](references/client-and-config.md) — full singleton client, retry, and `package.json`
- [Testing reference](references/testing.md) — complete unit, integration, and vitest setup
- [Examples reference](references/examples.md) — TypeScript and Python smoke tests

## Next Steps

Once the dev loop is green, see the `notion-sdk-patterns` skill for production-ready query helpers,
pagination utilities, and property extraction functions to build on this foundation.
