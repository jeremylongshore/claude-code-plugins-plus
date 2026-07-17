---
name: notion-known-pitfalls
description: |
  Use when debugging or reviewing Notion API code that fails with
  object_not_found, validation_error, rate_limited, or returns incomplete
  data. Covers the twelve most common mistakes: wrong page ID format
  (dashes), rich text array structure, block children not returned with page,
  pagination required for all lists, 3 req/sec shared across endpoints, and
  not sharing pages with the integration. Trigger with phrases like "notion
  mistakes", "notion pitfalls", "notion common errors", "notion gotchas",
  "notion debugging".
allowed-tools: Read, Grep
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Known Pitfalls

## Overview

The twelve most common mistakes when building Notion API integrations, each with the wrong pattern, why it fails, and the correct fix. These pitfalls account for the majority of developer support questions.

The lean flow lives here; the full wrong-vs-right code for every pitfall (TypeScript and Python) is in [references/implementation.md](references/implementation.md).

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set
- Familiarity with Notion API concepts (databases, pages, blocks, properties)

## Authentication

All calls authenticate with an internal integration token passed to the client
constructor (`new Client({ auth: process.env.NOTION_TOKEN })` /
`Client(auth=os.environ["NOTION_TOKEN"])`). The token alone is not enough —
every page and database must also be explicitly shared with the integration in
the Notion UI (Pitfall #1). Never hardcode the token; read it from the
environment.

## Instructions

Work the pitfalls in order of frequency. Pitfall #1 is the single most common error, so it is worked in full below; #2–#12 follow the same wrong-vs-right shape and the complete code is in [references/implementation.md](references/implementation.md).

### Step 1: Not Sharing Pages with the Integration (Pitfall #1)

The single most common Notion API error. Every page/database must be explicitly shared with your integration. A `404 object_not_found` does NOT mean the page is missing — it means your integration lacks access.

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// This returns 404 even though the page EXISTS in your workspace
try {
  const page = await notion.pages.retrieve({ page_id: 'some-page-id' });
} catch (error) {
  if (isNotionClientError(error) && error.code === APIErrorCode.ObjectNotFound) {
    // "object_not_found" does NOT mean the page doesn't exist
    // It means your integration doesn't have access
    console.error('Page exists but integration lacks access.');
    console.error('Fix: In Notion UI, open page -> ... menu -> Connections -> Add your integration');
    console.error('Tip: Share a parent page to grant access to ALL child pages');
  }
}

// Always verify access at startup
async function verifyAccess(databaseId: string): Promise<boolean> {
  try {
    await notion.databases.retrieve({ database_id: databaseId });
    return true;
  } catch {
    console.error(`Cannot access database ${databaseId}. Share it with your integration.`);
    return false;
  }
}
```

### Step 2: Extract IDs and Read Properties Safely (Pitfalls #2–#3)

Notion IDs work with or without dashes — always extract the last 32 hex chars from a URL. Rich text is ALWAYS an array (even for a single value), so accessing `rich_text[0]` on an empty property throws. Use the `extractPageId` and `extractProperty` helpers in [references/implementation.md](references/implementation.md).

### Step 3: Fetch Content, Paginate, and Throttle (Pitfalls #4–#6)

`pages.retrieve()` returns properties, NOT content blocks — call `blocks.children.list()` separately. Every list endpoint caps at 100 results, so loop on `has_more`/`next_cursor`. The 3 req/sec rate limit is SHARED across all endpoints, so route every call through ONE shared queue, not one queue per operation type. Full `getAllBlocks`, `queryAll`, and shared-`PQueue` patterns are in [references/implementation.md](references/implementation.md).

### Step 4: Filters, Creation, and Config (Pitfalls #7–#12)

Match each filter to its property type; property names are case-sensitive; batch block appends (max 100/call) instead of looping; import from `@notionhq/client`; always include the title property on page creation; and read database IDs from the environment, never hardcode them. Complete code for each is in [references/implementation.md](references/implementation.md), with Python equivalents at the bottom of that file.

## Output

- 12 pitfalls identified with wrong pattern, explanation, and correct code
- Safe property extraction helpers for all property types
- Full pagination pattern that never misses data
- Block retrieval pattern (separate from page retrieval)
- Rate limit queue shared across all endpoints
- Codebase scanning commands to detect pitfalls

## Error Handling

| Pitfall | Error You See | Real Cause |
| --------- | -------------- | ------------ |
| #1 Not shared | `object_not_found` (404) | Page not shared with integration |
| #2 ID format | `validation_error` (400) | Wrong ID extracted from URL |
| #3 Empty rich_text | `TypeError: Cannot read property` | Array is empty, not checked |
| #4 No blocks | Missing page content | Need `blocks.children.list()` |
| #5 No pagination | Incomplete data | Only got first 100 results |
| #6 Split rate limit | `rate_limited` (429) | Separate queues = 2x rate |
| #7 Wrong filter | `validation_error` (400) | Filter type doesn't match property |
| #8 Wrong case | `validation_error` (400) | Property names are case-sensitive |
| #9 Single append | Slow performance | N calls instead of 1 batched call |
| #10 Wrong import | `Module not found` | Use `@notionhq/client` |
| #11 No title | `validation_error` (400) | Title property is required |
| #12 Hardcoded ID | Works locally, fails in CI | Use environment variables |

## Examples

A copy-paste bash scan that greps a codebase for the four most detectable pitfalls (wrong import, unsafe array access, hardcoded UUIDs, missing pagination) — plus a table for reading its output — is in [references/examples.md](references/examples.md).

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Property Value Types](https://developers.notion.com/reference/property-value-object)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Request Limits](https://developers.notion.com/reference/request-limits)
- [GitHub: notion-sdk-js](https://github.com/makenotion/notion-sdk-js)

## Next Steps

For debugging hard issues, see `notion-advanced-troubleshooting`.
For scaling beyond these basics, see `notion-load-scale`.
