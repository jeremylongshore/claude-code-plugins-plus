---
name: notion-advanced-troubleshooting
description: |
  Use when standard Notion troubleshooting fails or you are chasing intermittent
  API errors — deep debugging for response inspection, permission chain tracing,
  property type mismatches, pagination edge cases, and block nesting limits.
  Trigger with phrases like "notion deep debug", "notion permission trace",
  "notion property mismatch", "notion pagination bug", "notion nesting limit".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Advanced Troubleshooting

## Overview

Deep debugging techniques for Notion API issues that resist standard fixes —
API response inspection with request IDs, permission chain tracing, property
type mismatch detection, pagination edge cases, and block nesting limit
violations (max depth of 3 levels via API). Full runnable TypeScript and Python
for every step lives in [references/implementation.md](references/implementation.md).

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `curl` available for raw API testing
- `NOTION_TOKEN` environment variable set (internal integration token starting with `ntn_`)
- Pages/databases shared with your integration via Notion UI

## Authentication

All calls authenticate with a single internal integration token in the
`NOTION_TOKEN` environment variable — the SDK reads it via `auth:
process.env.NOTION_TOKEN`, and raw `curl` sends it as
`Authorization: Bearer $NOTION_TOKEN` plus the `Notion-Version: 2022-06-28`
header. Never hardcode the token; keep it in the environment. Confirm the token
is a bot token with `notion.users.me()` — if the returned `type` is not `bot`,
the token is wrong. A `401 unauthorized` means a bad/expired token; a `404
object_not_found` on a valid page means the token is fine but the resource
was never shared with the integration (see Step 2).

## Instructions

Work the steps in order — each narrows where the failure lives. Read the
[full walkthrough](references/implementation.md) for the complete function
bodies; the skeletons below show the entry point of each.

### Step 1: API Response Inspection with Request ID Tracking

Every Notion API response carries an `x-request-id` header. Enable
`LogLevel.DEBUG` and wrap calls so every request logs its ID and timing —
capture that ID for support tickets. Use `Grep` over the debug log to find a
specific request's ID after the fact.

```typescript
const notion = new Client({ auth: process.env.NOTION_TOKEN, logLevel: LogLevel.DEBUG });

async function tracedCall<T>(label: string, fn: () => Promise<T>) {
  const start = Date.now();
  try {
    const result = await fn();
    console.log(`[${label}] OK ${Date.now() - start}ms`);
    return result;
  } catch (error) {
    if (isNotionClientError(error)) console.error(`[${label}] FAILED`, error.code, error.body);
    throw error;
  }
}
```

To isolate SDK-vs-transport bugs, replay the same call with raw `curl` and
compare — full curl recipe and the Python `traced_call` equivalent are in
[references/implementation.md](references/implementation.md) under Step 1.

### Step 2: Permission Chain Tracing

An `object_not_found` (404) on a page that clearly exists means your
integration lacks access somewhere up the hierarchy. Walk from the target page
toward the workspace root, reporting the first inaccessible ancestor.

```typescript
async function tracePermissionChain(pageId: string) {
  let currentId = pageId, depth = 0;
  while (currentId && depth < 10) {
    try {
      const page = await notion.pages.retrieve({ page_id: currentId });
      const parent = (page as any).parent;
      // ...ascend via parent.page_id / parent.database_id until workspace root
    } catch (error) {
      // object_not_found here = the ancestor to share with your integration
      break;
    }
  }
}
```

Full ascent logic, database-access check, and the Python port:
[references/implementation.md](references/implementation.md) under Step 2.

### Step 3: Property Type Mismatch Detection and Pagination Edge Cases

Most `validation_error`s come from sending the wrong property type. Retrieve
the live database schema and compare each property you send against it before
the write. The same step covers safe full pagination (null-cursor handling,
rate-limit delay, a page-count safety valve) and block-nesting checks against
the API's 3-level limit.

```typescript
async function detectPropertyMismatches(databaseId: string, properties: Record<string, unknown>) {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const schema = db.properties;                       // live truth
  // for each sent property: flag unknown names + type != schema[name].type
  // flag a missing required title property
  return issues; // string[]
}
```

Complete `detectPropertyMismatches`, `safeFullPagination`, `checkBlockNesting`,
and the Python schema validator:
[references/implementation.md](references/implementation.md) under Step 3.

## Output

- Request IDs captured for every API call with timing data
- Permission chain traced from target page up to workspace root
- Property type mismatches detected before they cause validation errors
- Pagination edge cases handled (null cursors, safety limits)
- Block nesting depth verified against API 3-level limit

## Error Handling

| Symptom | Root Cause | Debug Approach |
| --------- | ----------- | ---------------- |
| `object_not_found` on valid page | Page not shared with integration | Run `tracePermissionChain()` |
| `validation_error` on create/update | Property type mismatch | Run `detectPropertyMismatches()` |
| Missing data from query | Not paginating (max 100/request) | Use `safeFullPagination()` |
| `could not find block` at depth 4+ | API nesting limit (3 levels) | Flatten block structure |
| Works in curl, fails in SDK | SDK header or payload difference | Enable `LogLevel.DEBUG`, compare |
| Intermittent 500 errors | Notion server issues | Capture `x-request-id`, retry with backoff |
| `rate_limited` (429) | Exceeding 3 req/s | Add 350ms delay between calls |
| `conflict_error` | Concurrent page update | Retry with fresh page read |

## Examples

Two ready-to-run starting points live in
[references/examples.md](references/examples.md):

- **Minimal reproduction script** — walks auth → search → resource retrieve →
  the failing call, isolating which layer breaks.
- **Support escalation template** — the exact ticket format (with `x-request-id`)
  Notion support can trace fastest.

```typescript
// Minimal repro skeleton — full version in references/examples.md
const me = await notion.users.me({});          // 1. auth
const search = await notion.search({ page_size: 1 }); // 2. token works
const db = await notion.databases.retrieve({ database_id: process.env.NOTION_DB_ID! }); // 3. resource
// 4. insert the exact failing call here
```

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro)
- [Notion Status Page](https://status.notion.com)
- [Property Value Types](https://developers.notion.com/reference/property-value-object)
- [Block Types](https://developers.notion.com/reference/block)
- [GitHub: notion-sdk-js Issues](https://github.com/makenotion/notion-sdk-js/issues)

## Next Steps

For load testing and scaling, see `notion-load-scale`.
For reliability patterns, see `notion-reliability-patterns`.
