---
name: onenote-local-dev-loop
description: 'Set up a local development loop for OneNote integrations with mock Graph
  API responses.

  Use when developing OneNote features without Azure credentials or to avoid rate
  limits during development.

  Trigger with "onenote local dev", "onenote mock", "onenote testing setup".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Local Dev Loop

## Overview

Testing OneNote integrations typically requires Azure AD credentials and live Graph API calls, which means authentication friction on every dev session and risk of hitting the 600 req/60s rate limit during rapid iteration. This skill sets up a local development loop with mock Graph responses so you can develop and test OneNote features without Azure credentials, without rate limits, and with instant feedback.

The mock layer intercepts HTTP calls to `graph.microsoft.com` and returns realistic fixture data, including the XHTML output format that differs from input format. You can switch between mock and live Graph with a single environment variable.

## Prerequisites

- Node.js 18+ or Python 3.10+
- Familiarity with your project's test framework (vitest/jest for Node, pytest for Python)
- Optional: completed `onenote-install-auth` for live mode switching

## Instructions

### Step 1: Project Structure

```
my-onenote-app/
├── .env                          # GRAPH_MODE=mock or GRAPH_MODE=live
├── .env.example                  # Template (commit this, not .env)
├── src/
│   ├── client.ts                 # Graph client factory (mock/live switching)
│   ├── onenote.ts                # Business logic (testable)
│   └── types.ts                  # OneNote type definitions
├── tests/
│   ├── fixtures/
│   │   ├── notebooks.json        # Mock notebook list response
│   │   ├── sections.json         # Mock section list response
│   │   ├── pages.json            # Mock page list response
│   │   ├── page-content.html     # Mock page HTML (output format)
│   │   └── error-responses.json  # Mock error responses for testing
│   ├── mocks/
│   │   └── graph-handlers.ts     # MSW request handlers
│   └── onenote.test.ts           # Unit tests
├── package.json
└── tsconfig.json
```

### Step 2: Mock Graph API Server (TypeScript with MSW)

[MSW (Mock Service Worker)](https://mswjs.io/) intercepts HTTP requests at the network level, so your production code does not need any changes to work with mocks.

```typescript
// tests/mocks/graph-handlers.ts
import { http, HttpResponse } from "msw";

const BASE = "https://graph.microsoft.com/v1.0";

// Import fixture data
import notebooksFixture from "../fixtures/notebooks.json";
import sectionsFixture from "../fixtures/sections.json";
import pagesFixture from "../fixtures/pages.json";
import { readFileSync } from "fs";
import { join } from "path";

const pageContentFixture = readFileSync(
  join(__dirname, "../fixtures/page-content.html"),
  "utf-8"
);

export const graphHandlers = [
  // List notebooks
  http.get(`${BASE}/me/onenote/notebooks`, () => {
    return HttpResponse.json(notebooksFixture);
  }),

  // Create notebook
  http.post(`${BASE}/me/onenote/notebooks`, async ({ request }) => {
    const body = (await request.json()) as { displayName: string };
    return HttpResponse.json(
      {
        id: `notebook-${Date.now()}`,
        displayName: body.displayName,
        createdDateTime: new Date().toISOString(),
        lastModifiedDateTime: new Date().toISOString(),
        isDefault: false,
        isShared: false,
        sectionsUrl: `${BASE}/me/onenote/notebooks/notebook-${Date.now()}/sections`,
        self: `${BASE}/me/onenote/notebooks/notebook-${Date.now()}`,
      },
      { status: 201 }
    );
  }),

  // List sections in a notebook
  http.get(`${BASE}/me/onenote/notebooks/:notebookId/sections`, () => {
    return HttpResponse.json(sectionsFixture);
  }),

  // Create section
  http.post(
    `${BASE}/me/onenote/notebooks/:notebookId/sections`,
    async ({ request }) => {
      const body = (await request.json()) as { displayName: string };
      return HttpResponse.json(
        {
          id: `section-${Date.now()}`,
          displayName: body.displayName,
          createdDateTime: new Date().toISOString(),
          pagesUrl: `${BASE}/me/onenote/sections/section-${Date.now()}/pages`,
        },
        { status: 201 }
      );
    }
  ),

  // List pages in a section
  http.get(`${BASE}/me/onenote/sections/:sectionId/pages`, () => {
    return HttpResponse.json(pagesFixture);
  }),

  // Create page (accepts HTML body)
  http.post(`${BASE}/me/onenote/sections/:sectionId/pages`, async ({ request }) => {
    const html = await request.text();
    const titleMatch = html.match(/<title>(.*?)<\/title>/);
    return HttpResponse.json(
      {
        id: `page-${Date.now()}`,
        title: titleMatch?.[1] ?? "Untitled",
        createdDateTime: new Date().toISOString(),
        contentUrl: `${BASE}/me/onenote/pages/page-${Date.now()}/content`,
      },
      { status: 201 }
    );
  }),

  // Get page content (returns HTML, not JSON)
  http.get(`${BASE}/me/onenote/pages/:pageId/content`, () => {
    return new HttpResponse(pageContentFixture, {
      headers: { "Content-Type": "text/html" },
    });
  }),

  // PATCH page content
  http.patch(`${BASE}/me/onenote/pages/:pageId/content`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Simulate 429 rate limit (use special notebook ID to trigger)
  http.get(`${BASE}/me/onenote/notebooks/trigger-429/sections`, () => {
    return new HttpResponse(
      JSON.stringify({ error: { code: "429", message: "Too many requests" } }),
      {
        status: 429,
        headers: { "Retry-After": "5", "Content-Type": "application/json" },
      }
    );
  }),
];
```

### Step 3: MSW Setup for Tests

```typescript
// tests/setup.ts
import { setupServer } from "msw/node";
import { graphHandlers } from "./mocks/graph-handlers";

export const mockServer = setupServer(...graphHandlers);

// Start before all tests, reset between tests, close after
beforeAll(() => mockServer.listen({ onUnhandledRequest: "warn" }));
afterEach(() => mockServer.resetHandlers());
afterAll(() => mockServer.close());
```

```json
// vitest.config.ts addition
{
  "test": {
    "setupFiles": ["./tests/setup.ts"]
  }
}
```

### Step 4: Realistic Fixture Data

Use [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) to capture real responses, then save them as fixtures.

```json
// tests/fixtures/notebooks.json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('user-id')/onenote/notebooks",
  "value": [
    {
      "id": "notebook-abc-123",
      "displayName": "Work Notes",
      "createdDateTime": "2026-01-15T10:00:00Z",
      "lastModifiedDateTime": "2026-03-22T14:30:00Z",
      "isDefault": true,
      "isShared": false,
      "sectionsUrl": "https://graph.microsoft.com/v1.0/me/onenote/notebooks/notebook-abc-123/sections",
      "self": "https://graph.microsoft.com/v1.0/me/onenote/notebooks/notebook-abc-123"
    },
    {
      "id": "notebook-def-456",
      "displayName": "Project Alpha",
      "createdDateTime": "2026-02-01T09:00:00Z",
      "lastModifiedDateTime": "2026-03-20T16:45:00Z",
      "isDefault": false,
      "isShared": true,
      "sectionsUrl": "https://graph.microsoft.com/v1.0/me/onenote/notebooks/notebook-def-456/sections",
      "self": "https://graph.microsoft.com/v1.0/me/onenote/notebooks/notebook-def-456"
    }
  ]
}
```

```html
<!-- tests/fixtures/page-content.html -->
<!-- NOTE: This is OUTPUT format — Graph normalizes your input HTML -->
<!-- Output includes data-id attributes, absolute positioning, div wrappers -->
<html lang="en-US">
  <head>
    <title>Sprint Planning Notes</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  </head>
  <body data-absolute-enabled="true" style="font-family:Calibri;font-size:11pt">
    <div id="div-{guid}" data-id="div1" style="position:absolute;left:48px;top:115px;width:624px">
      <h1 style="font-size:16pt;color:#1e4e79;margin-top:11pt;margin-bottom:11pt">
        Sprint Planning Notes
      </h1>
      <p data-id="p1">Attendees: Alice, Bob, Charlie</p>
      <h2 style="font-size:14pt;color:#2e74b5;margin-top:11pt;margin-bottom:11pt">
        Action Items
      </h2>
      <ul>
        <li data-id="li1" data-tag="to-do" style="--tag-state:unchecked">Deploy feature X by Friday</li>
        <li data-id="li2" data-tag="to-do" style="--tag-state:unchecked">Review PR #488</li>
      </ul>
    </div>
  </body>
</html>
```

### Step 5: Environment Switching (Mock vs Live)

```typescript
// src/client.ts
import { Client } from "@microsoft/microsoft-graph-client";
import { TokenCredentialAuthenticationProvider } from
  "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials";
import { DeviceCodeCredential } from "@azure/identity";

export function createGraphClient(): Client {
  const mode = process.env.GRAPH_MODE ?? "mock";

  if (mode === "live") {
    const credential = new DeviceCodeCredential({
      clientId: process.env.AZURE_CLIENT_ID!,
      tenantId: process.env.AZURE_TENANT_ID!,
    });
    const authProvider = new TokenCredentialAuthenticationProvider(credential, {
      scopes: ["Notes.ReadWrite"],
    });
    return Client.initWithMiddleware({ authProvider });
  }

  // In mock mode, MSW intercepts all requests — no auth needed
  // Use a dummy auth provider that returns a fake token
  return Client.init({
    authProvider: (done) => done(null, "mock-token-for-dev"),
  });
}
```

```bash
# .env.example (commit this file)
# Set GRAPH_MODE=mock for local development (no Azure credentials needed)
# Set GRAPH_MODE=live to use real Graph API (requires AZURE_CLIENT_ID and AZURE_TENANT_ID)
GRAPH_MODE=mock
AZURE_CLIENT_ID=
AZURE_TENANT_ID=
```

### Step 6: Python Mock Setup (responses library)

```python
# tests/conftest.py — Python mock setup using responses library
import json, pytest, responses
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://graph.microsoft.com/v1.0"

@pytest.fixture
def mock_graph():
    """Activate mock Graph API responses for all tests."""
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{BASE}/me/onenote/notebooks",
                 json=json.loads((FIXTURES / "notebooks.json").read_text()), status=200)
        rsps.add_callback(responses.POST, f"{BASE}/me/onenote/notebooks",
            callback=lambda req: (201, {}, json.dumps({
                "id": f"nb-{hash(req.body) % 10000}",
                "displayName": json.loads(req.body)["displayName"]})))
        yield rsps
```

### Step 7: Test Isolation Patterns

```typescript
// tests/onenote.test.ts
import { describe, it, expect } from "vitest";
import { createGraphClient } from "../src/client";
import { mockServer } from "./setup";
import { http, HttpResponse } from "msw";

describe("OneNote integration", () => {
  const client = createGraphClient();

  it("lists notebooks", async () => {
    const response = await client.api("/me/onenote/notebooks").get();
    expect(response.value).toHaveLength(2);
    expect(response.value[0].displayName).toBe("Work Notes");
  });

  it("creates a page with valid XHTML", async () => {
    const xhtml = `<!DOCTYPE html>
      <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>Test Page</title></head>
        <body><p>Hello World</p></body>
      </html>`;

    const page = await client
      .api("/me/onenote/sections/section-abc/pages")
      .header("Content-Type", "text/html")
      .post(xhtml);

    expect(page.id).toBeDefined();
    expect(page.title).toBe("Test Page");
  });

  it("handles 429 rate limit", async () => {
    // Override handler for this test only
    mockServer.use(
      http.get(
        "https://graph.microsoft.com/v1.0/me/onenote/notebooks",
        () => {
          return new HttpResponse(
            JSON.stringify({ error: { code: "429", message: "Throttled" } }),
            { status: 429, headers: { "Retry-After": "1" } }
          );
        },
        { once: true } // Only intercept once, then fall through to default
      )
    );

    // Your retry logic should handle this and succeed on second attempt
  });

  it("detects silent upload failure", async () => {
    // Override to return empty body (simulates >4MB upload)
    mockServer.use(
      http.post(
        "https://graph.microsoft.com/v1.0/me/onenote/sections/:sectionId/pages",
        () => {
          return HttpResponse.json(null, { status: 200 });
        },
        { once: true }
      )
    );

    const response = await client
      .api("/me/onenote/sections/section-abc/pages")
      .header("Content-Type", "text/html")
      .post("<html><head><title>Big</title></head><body>...</body></html>");

    // This is the silent failure — 200 but no id
    expect(response?.id).toBeUndefined();
  });
});
```

### Step 8: Hot Reload Configuration

```json
// package.json scripts
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:live": "GRAPH_MODE=live vitest --run",
    "fixtures:refresh": "GRAPH_MODE=live tsx scripts/capture-fixtures.ts"
  }
}
```

```typescript
// scripts/capture-fixtures.ts — Capture fresh fixtures from live Graph API
import { createGraphClient } from "../src/client";
import { writeFileSync } from "fs";
import { join } from "path";

const client = createGraphClient(); // GRAPH_MODE=live required
const FIXTURES_DIR = join(__dirname, "../tests/fixtures");

async function captureFixtures() {
  console.log("Capturing live fixtures from Graph API...");

  const notebooks = await client.api("/me/onenote/notebooks").get();
  writeFileSync(
    join(FIXTURES_DIR, "notebooks.json"),
    JSON.stringify(notebooks, null, 2)
  );
  console.log(`Saved ${notebooks.value.length} notebooks`);

  if (notebooks.value.length > 0) {
    const nb = notebooks.value[0];
    const sections = await client
      .api(`/me/onenote/notebooks/${nb.id}/sections`)
      .get();
    writeFileSync(
      join(FIXTURES_DIR, "sections.json"),
      JSON.stringify(sections, null, 2)
    );
    console.log(`Saved ${sections.value.length} sections from "${nb.displayName}"`);
  }

  console.log("Fixtures captured. Run tests with GRAPH_MODE=mock.");
}

captureFixtures().catch(console.error);
```

## Output

After completing this setup you will have:
- Mock Graph API server that intercepts all OneNote requests without Azure credentials
- Realistic fixture data matching actual Graph API response format (including output HTML)
- Environment variable toggle between mock and live Graph API
- Test patterns for rate limits, silent failures, and error responses
- A fixture capture script to refresh mocks from live data
- Hot reload for rapid development iteration

## Error Handling

| Scenario | Detection | Resolution |
|----------|-----------|------------|
| MSW not intercepting requests | `onUnhandledRequest: "warn"` logs to console | Add missing handler to `graphHandlers` array |
| Fixture data stale | Tests pass locally but fail against live API | Run `npm run fixtures:refresh` with live credentials |
| Mock returns wrong content type | Page content tests fail | Ensure HTML fixtures use `text/html` content type, not `application/json` |
| GRAPH_MODE not set | Client uses wrong auth | Default to `mock` in `createGraphClient()` |

## Examples

**Quick start — run tests without any Azure setup:**
```bash
echo "GRAPH_MODE=mock" > .env
npm install
npm test
# All tests pass — no Azure credentials needed
```

**Switch to live for integration testing:**
```bash
echo "GRAPH_MODE=live" > .env
echo "AZURE_CLIENT_ID=your-id" >> .env
echo "AZURE_TENANT_ID=your-tenant" >> .env
npm run test:live
```

## Resources

- [Graph Explorer (capture fixture data)](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [MSW Documentation](https://mswjs.io/)
- [OneNote Input/Output HTML](https://learn.microsoft.com/en-us/graph/onenote-input-output-html)
- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [OneNote Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [OneNote Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)

## Next Steps

- See `onenote-hello-world` to understand what real Graph API responses look like
- Use `onenote-sdk-patterns` to add retry middleware that works in both mock and live modes
- See `onenote-common-errors` to add error response fixtures for each status code
