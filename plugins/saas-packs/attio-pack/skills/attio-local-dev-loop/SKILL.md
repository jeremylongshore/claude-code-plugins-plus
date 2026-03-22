---
name: attio-local-dev-loop
description: |
  Set up a fast local development loop for Attio integrations with
  hot reload, mock server, and integration tests.
  Trigger: "attio dev setup", "attio local development",
  "attio dev environment", "develop with attio", "attio project setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Attio REST API integrations. Includes project structure, typed client, mock server for offline work, and integration test harness.

## Prerequisites

- Completed `attio-install-auth` setup
- Node.js 18+ with npm or pnpm
- TypeScript 5+

## Instructions

### Step 1: Project Structure

```
my-attio-integration/
├── src/
│   ├── attio/
│   │   ├── client.ts          # Typed fetch wrapper (see attio-install-auth)
│   │   ├── types.ts           # Attio response types
│   │   └── config.ts          # Env-based configuration
│   ├── services/
│   │   ├── people.ts          # People record operations
│   │   ├── companies.ts       # Company record operations
│   │   └── lists.ts           # List entry operations
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── attio-fixtures.ts  # Realistic API response fixtures
│   ├── unit/
│   │   └── people.test.ts
│   └── integration/
│       └── attio-live.test.ts # Runs against real API (CI only)
├── .env.example
├── .env.local                 # Git-ignored, real credentials
├── tsconfig.json
└── package.json
```

### Step 2: Type the Attio Response Model

```typescript
// src/attio/types.ts

/** Attio record identifier */
export interface AttioRecordId {
  object_id: string;
  record_id: string;
}

/** Attio attribute value wrapper */
export interface AttioValue<T = unknown> {
  active_from: string;
  active_until: string | null;
  created_by_actor: { type: string; id: string };
  attribute_type: string;
  [key: string]: T | unknown;
}

/** Generic Attio record */
export interface AttioRecord {
  id: AttioRecordId;
  created_at: string;
  values: Record<string, AttioValue[]>;
}

/** Paginated list response */
export interface AttioListResponse<T> {
  data: T[];
  pagination?: {
    next_cursor?: string;
    has_more?: boolean;
  };
}

/** Attio API error response */
export interface AttioError {
  status_code: number;
  type: string;
  code: string;
  message: string;
}
```

### Step 3: Environment Configuration

```typescript
// src/attio/config.ts
export interface AttioConfig {
  apiKey: string;
  baseUrl: string;
  timeout: number;
  environment: "development" | "staging" | "production";
}

export function loadConfig(): AttioConfig {
  const env = process.env.NODE_ENV || "development";
  return {
    apiKey: process.env.ATTIO_API_KEY || "",
    baseUrl: process.env.ATTIO_BASE_URL || "https://api.attio.com/v2",
    timeout: parseInt(process.env.ATTIO_TIMEOUT || "30000", 10),
    environment: env as AttioConfig["environment"],
  };
}
```

### Step 4: Package Scripts for Dev Loop

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest run",
    "test:watch": "vitest --watch",
    "test:integration": "ATTIO_LIVE=1 vitest run tests/integration/",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/ tests/"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0",
    "typescript": "^5.5.0",
    "msw": "^2.0.0"
  }
}
```

### Step 5: Mock Attio API with MSW

```typescript
// tests/mocks/attio-fixtures.ts
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const BASE = "https://api.attio.com/v2";

export const handlers = [
  // List objects
  http.get(`${BASE}/objects`, () =>
    HttpResponse.json({
      data: [
        { api_slug: "people", singular_noun: "Person", plural_noun: "People" },
        { api_slug: "companies", singular_noun: "Company", plural_noun: "Companies" },
      ],
    })
  ),

  // Query people records
  http.post(`${BASE}/objects/people/records/query`, () =>
    HttpResponse.json({
      data: [
        {
          id: { object_id: "obj_people", record_id: "rec_abc123" },
          created_at: "2025-01-15T10:00:00.000Z",
          values: {
            name: [{ first_name: "Ada", last_name: "Lovelace", full_name: "Ada Lovelace" }],
            email_addresses: [{ email_address: "ada@example.com" }],
          },
        },
      ],
    })
  ),

  // Create person
  http.post(`${BASE}/objects/people/records`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      data: {
        id: { object_id: "obj_people", record_id: `rec_${Date.now()}` },
        created_at: new Date().toISOString(),
        values: (body as any).data?.values || {},
      },
    }, { status: 200 });
  }),
];

export const mockServer = setupServer(...handlers);
```

### Step 6: Write Tests Against Mocks

```typescript
// tests/unit/people.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { mockServer } from "../mocks/attio-fixtures";
import { attioFetch } from "../../src/attio/client";

beforeAll(() => mockServer.listen());
afterAll(() => mockServer.close());

describe("People Service", () => {
  it("queries people records", async () => {
    const res = await attioFetch<{ data: any[] }>({
      method: "POST",
      path: "/objects/people/records/query",
      body: { limit: 10 },
    });
    expect(res.data).toHaveLength(1);
    expect(res.data[0].values.name[0].full_name).toBe("Ada Lovelace");
  });

  it("creates a person", async () => {
    const res = await attioFetch<{ data: { id: { record_id: string } } }>({
      method: "POST",
      path: "/objects/people/records",
      body: {
        data: { values: { email_addresses: ["test@example.com"] } },
      },
    });
    expect(res.data.id.record_id).toBeTruthy();
  });
});
```

### Step 7: Integration Test (Live API)

```typescript
// tests/integration/attio-live.test.ts
import { describe, it, expect } from "vitest";
import { attioFetch } from "../../src/attio/client";

const LIVE = process.env.ATTIO_LIVE === "1";

describe.skipIf(!LIVE)("Attio Live API", () => {
  it("lists objects from real workspace", async () => {
    const res = await attioFetch<{ data: Array<{ api_slug: string }> }>({
      path: "/objects",
    });
    expect(res.data.map((o) => o.api_slug)).toContain("people");
  });
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `fetch is not defined` | Node < 18 | Upgrade Node.js or add `undici` |
| MSW not intercepting | Wrong base URL | Match `ATTIO_BASE_URL` in mock handlers |
| Integration test fails | Missing/invalid token | Set `ATTIO_API_KEY` in `.env.local` |
| TypeScript errors on values | Attio multiselect arrays | Values are always arrays -- type as `T[]` |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [MSW Documentation](https://mswjs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)

## Next Steps

See `attio-sdk-patterns` for production-ready client patterns.
