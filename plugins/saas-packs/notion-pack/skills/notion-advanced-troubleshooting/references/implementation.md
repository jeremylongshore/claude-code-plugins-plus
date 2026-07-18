# Notion Advanced Troubleshooting — Full Implementation

Complete, runnable implementations for each debugging step. SKILL.md shows the
skeleton and the entry point; this file carries the full TypeScript and Python
code, verbatim.

## Step 1: API Response Inspection with Request ID Tracking

Every Notion API response includes an `x-request-id` header. Capture it for
debugging and support tickets.

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

## Step 2: Permission Chain Tracing

When you get `object_not_found` (404), the page exists but your integration
lacks access. Trace the permission chain up the page hierarchy.

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

## Step 3: Property Type Mismatch Detection and Pagination Edge Cases

The most common `validation_error` comes from sending the wrong property type.
Validate against the live schema before creating/updating.

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
