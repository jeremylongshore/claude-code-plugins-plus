---
name: notion-advanced-troubleshooting
description: |
  Deep debugging for Notion API: response inspection, permission chain tracing,
  property type mismatches, pagination edge cases, and block nesting limits.
  Use when standard troubleshooting fails or investigating intermittent errors.
  Trigger with phrases like "notion deep debug", "notion permission trace",
  "notion property mismatch", "notion pagination bug", "notion nesting limit".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Advanced Troubleshooting

## Overview

Deep debugging techniques for Notion API issues that resist standard fixes. Covers API response inspection with request IDs, permission chain tracing through page hierarchies, property type mismatch detection against database schemas, pagination edge cases with cursor validation, and block nesting limit violations (max depth of 3 levels via API). Uses `Client` from `@notionhq/client` and raw `curl` for comparison testing.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `curl` available for raw API testing
- `NOTION_TOKEN` environment variable set (internal integration token starting with `ntn_`)
- Pages/databases shared with your integration via Notion UI

## Instructions

### Step 1: API Response Inspection with Request ID Tracking

Every Notion API response includes an `x-request-id` header. Capture it for debugging and support tickets.

```typescript
import { Client, LogLevel, isNotionClientError, APIErrorCode } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  logLevel: LogLevel.DEBUG, // Logs full request/response to stderr
});

// Wrapper that captures request ID and timing for every call
async function tracedCall<T>(
  label: string,
  fn: () => Promise<T>
): Promise<{ result: T; durationMs: number }> {
  const start = Date.now();
  try {
    const result = await fn();
    const durationMs = Date.now() - start;
    console.log(`[${label}] OK ${durationMs}ms`);
    return { result, durationMs };
  } catch (error) {
    const durationMs = Date.now() - start;
    if (isNotionClientError(error)) {
      console.error(`[${label}] FAILED ${durationMs}ms`, {
        code: error.code,
        status: error.status,
        message: error.message,
        body: error.body,
      });
    }
    throw error;
  }
}

// Compare SDK vs raw curl to isolate SDK issues
// Run in bash alongside:
// curl -v https://api.notion.com/v1/pages/PAGE_ID \
//   -H "Authorization: Bearer $NOTION_TOKEN" \
//   -H "Notion-Version: 2022-06-28" 2>&1 | grep x-request-id
```

```python
from notion_client import Client
import logging

# Enable debug logging for full request/response visibility
logging.basicConfig(level=logging.DEBUG)
notion = Client(auth=os.environ["NOTION_TOKEN"], log_level=logging.DEBUG)

# Traced wrapper for Python
import time

def traced_call(label: str, fn):
    start = time.time()
    try:
        result = fn()
        duration = (time.time() - start) * 1000
        print(f"[{label}] OK {duration:.0f}ms")
        return result
    except Exception as e:
        duration = (time.time() - start) * 1000
        print(f"[{label}] FAILED {duration:.0f}ms: {e}")
        raise
```

### Step 2: Permission Chain Tracing

When you get `object_not_found` (404), the page exists but your integration lacks access. Trace the permission chain up the page hierarchy.

```typescript
async function tracePermissionChain(pageId: string): Promise<void> {
  console.log(`\n=== Permission Chain Trace for ${pageId} ===`);
  let currentId = pageId;
  let depth = 0;

  while (currentId && depth < 10) {
    try {
      const page = await notion.pages.retrieve({ page_id: currentId });
      const parent = (page as any).parent;
      console.log(`  ${'  '.repeat(depth)}[${depth}] Page ${currentId} - ACCESSIBLE`);
      console.log(`  ${'  '.repeat(depth)}    Parent type: ${parent.type}`);

      if (parent.type === 'database_id') {
        // Check database access too
        try {
          await notion.databases.retrieve({ database_id: parent.database_id });
          console.log(`  ${'  '.repeat(depth)}    Database ${parent.database_id} - ACCESSIBLE`);
        } catch {
          console.log(`  ${'  '.repeat(depth)}    Database ${parent.database_id} - NO ACCESS`);
        }
        break;
      } else if (parent.type === 'page_id') {
        currentId = parent.page_id;
      } else if (parent.type === 'workspace') {
        console.log(`  ${'  '.repeat(depth)}    Root: workspace`);
        break;
      } else {
        break;
      }
      depth++;
    } catch (error) {
      if (isNotionClientError(error) && error.code === APIErrorCode.ObjectNotFound) {
        console.log(`  ${'  '.repeat(depth)}[${depth}] Page ${currentId} - NO ACCESS (object_not_found)`);
        console.log(`  ${'  '.repeat(depth)}    Fix: Open this page in Notion → ··· → Connections → Add your integration`);
      } else {
        console.log(`  ${'  '.repeat(depth)}[${depth}] Page ${currentId} - ERROR: ${(error as Error).message}`);
      }
      break;
    }
  }
}

// Also verify bot identity and capabilities
const me = await notion.users.me({});
console.log('Bot user:', me.name, '| Type:', me.type);
// If me.type !== 'bot', your token is wrong
```

```python
def trace_permission_chain(page_id: str):
    """Walk up the page hierarchy to find where access breaks."""
    current_id = page_id
    depth = 0

    while current_id and depth < 10:
        try:
            page = notion.pages.retrieve(page_id=current_id)
            parent = page["parent"]
            print(f"  [depth={depth}] {current_id} - ACCESSIBLE (parent: {parent['type']})")

            if parent["type"] == "database_id":
                try:
                    notion.databases.retrieve(database_id=parent["database_id"])
                    print(f"  [depth={depth}] Database {parent['database_id']} - ACCESSIBLE")
                except Exception:
                    print(f"  [depth={depth}] Database {parent['database_id']} - NO ACCESS")
                break
            elif parent["type"] == "page_id":
                current_id = parent["page_id"]
            else:
                break
            depth += 1
        except Exception as e:
            print(f"  [depth={depth}] {current_id} - NO ACCESS: {e}")
            print(f"  Fix: Share this page with your integration in Notion UI")
            break
```

### Step 3: Property Type Mismatch Detection and Pagination Edge Cases

The most common `validation_error` comes from sending the wrong property type. Validate against the live schema before creating/updating.

```typescript
// Detect property type mismatches against live database schema
async function detectPropertyMismatches(
  databaseId: string,
  properties: Record<string, unknown>
): Promise<string[]> {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const schema = db.properties;
  const issues: string[] = [];

  // Check each property you're trying to set
  for (const [name, value] of Object.entries(properties)) {
    if (!schema[name]) {
      issues.push(
        `Property "${name}" not found. Available: ${Object.keys(schema).join(', ')}`
      );
      continue;
    }

    const expectedType = schema[name].type;
    const sentType = Object.keys(value as object).find(k =>
      ['title', 'rich_text', 'number', 'select', 'multi_select',
       'date', 'checkbox', 'url', 'email', 'phone_number',
       'people', 'relation', 'files', 'status'].includes(k)
    );

    if (sentType && sentType !== expectedType) {
      issues.push(
        `"${name}": schema type is "${expectedType}" but you sent "${sentType}"`
      );
    }
  }

  // Check for missing title property (required for page creation)
  const titleProp = Object.entries(schema).find(([, v]) => v.type === 'title');
  if (titleProp && !properties[titleProp[0]]) {
    issues.push(`Missing required title property "${titleProp[0]}"`);
  }

  return issues;
}

// Pagination edge cases: cursor validation and empty page handling
async function safeFullPagination(databaseId: string, filter?: any) {
  const allResults: any[] = [];
  let cursor: string | undefined;
  let pageCount = 0;
  const MAX_PAGES = 1000; // Safety valve: 100K records max

  do {
    if (pageCount >= MAX_PAGES) {
      console.warn(`Pagination safety limit reached (${MAX_PAGES} pages, ${allResults.length} results)`);
      break;
    }

    const response = await notion.databases.query({
      database_id: databaseId,
      filter,
      page_size: 100,
      start_cursor: cursor,
    });

    allResults.push(...response.results);
    pageCount++;

    // Edge case: has_more is true but next_cursor is null (API bug, rare)
    if (response.has_more && !response.next_cursor) {
      console.warn('Pagination anomaly: has_more=true but next_cursor is null');
      break;
    }

    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;

    // Rate limit compliance: ~3 req/s
    await new Promise(r => setTimeout(r, 350));
  } while (cursor);

  console.log(`Paginated ${pageCount} pages, ${allResults.length} total results`);
  return allResults;
}

// Block nesting limit detection
// Notion API allows max 3 levels of nested blocks (API limitation)
// UI supports deeper nesting, but API cannot create/read beyond depth 3
async function checkBlockNesting(blockId: string, depth = 0): Promise<number> {
  if (depth >= 3) {
    console.warn(`Block nesting limit reached at depth ${depth} (API max is 3)`);
    return depth;
  }

  const children = await notion.blocks.children.list({ block_id: blockId });
  let maxDepth = depth;

  for (const block of children.results) {
    if ((block as any).has_children) {
      const childDepth = await checkBlockNesting((block as any).id, depth + 1);
      maxDepth = Math.max(maxDepth, childDepth);
    }
  }

  return maxDepth;
}
```

```python
def detect_property_mismatches(database_id: str, properties: dict) -> list[str]:
    """Validate properties against live database schema."""
    db = notion.databases.retrieve(database_id=database_id)
    schema = db["properties"]
    issues = []

    for name, value in properties.items():
        if name not in schema:
            available = ", ".join(schema.keys())
            issues.append(f'Property "{name}" not found. Available: {available}')
            continue

        expected_type = schema[name]["type"]
        sent_types = [k for k in value.keys() if k in
            ("title", "rich_text", "number", "select", "multi_select",
             "date", "checkbox", "url", "email", "status")]
        if sent_types and sent_types[0] != expected_type:
            issues.append(f'"{name}": expected "{expected_type}", got "{sent_types[0]}"')

    # Check for missing title
    title_props = [k for k, v in schema.items() if v["type"] == "title"]
    if title_props and title_props[0] not in properties:
        issues.append(f'Missing required title property "{title_props[0]}"')

    return issues
```

## Output

- Request IDs captured for every API call with timing data
- Permission chain traced from target page up to workspace root
- Property type mismatches detected before they cause validation errors
- Pagination edge cases handled (null cursors, safety limits)
- Block nesting depth verified against API 3-level limit

## Error Handling

| Symptom | Root Cause | Debug Approach |
|---------|-----------|----------------|
| `object_not_found` on valid page | Page not shared with integration | Run `tracePermissionChain()` |
| `validation_error` on create/update | Property type mismatch | Run `detectPropertyMismatches()` |
| Missing data from query | Not paginating (max 100/request) | Use `safeFullPagination()` |
| `could not find block` at depth 4+ | API nesting limit (3 levels) | Flatten block structure |
| Works in curl, fails in SDK | SDK header or payload difference | Enable `LogLevel.DEBUG`, compare |
| Intermittent 500 errors | Notion server issues | Capture `x-request-id`, retry with backoff |
| `rate_limited` (429) | Exceeding 3 req/s | Add 350ms delay between calls |
| `conflict_error` | Concurrent page update | Retry with fresh page read |

## Examples

### Minimal Reproduction Script

```typescript
// Strip to bare minimum to isolate the issue
async function minimalRepro() {
  const notion = new Client({
    auth: process.env.NOTION_TOKEN,
    logLevel: LogLevel.DEBUG,
  });

  // 1. Auth check
  const me = await notion.users.me({});
  console.log('Auth OK:', me.name);

  // 2. Search check (proves token works)
  const search = await notion.search({ page_size: 1 });
  console.log('Search OK:', search.results.length, 'results');

  // 3. Specific resource check
  const db = await notion.databases.retrieve({
    database_id: process.env.NOTION_DB_ID!,
  });
  console.log('DB OK:', Object.keys(db.properties).join(', '));

  // 4. The failing operation — insert exact failing call here
}

minimalRepro().catch(console.error);
```

### Support Escalation Template

```
Subject: [Request ID: abc123] validation_error on pages.create
Environment: Node.js 20, @notionhq/client 2.2.15, API 2022-06-28
Integration ID: [from notion.so/profile/integrations]
Request ID: [from x-request-id header or error body]
Timestamp: 2026-03-22T14:30:00Z

Steps: POST /v1/pages with body: { ... }
Expected: 200 with page object
Actual: 400 validation_error "..."
Frequency: Every time / Intermittent since [date]
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
