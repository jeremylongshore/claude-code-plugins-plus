# Notion Error Handling — Full Examples

Copy-paste-ready handlers and diagnostics that go deeper than the SKILL.md skeleton.

## Common Non-HTTP Gotchas

Errors that surface as `validation_error` but stem from client-side shape mistakes:

```typescript
// "body failed validation: body.children should be an array"
// → Block children must always be an array, even for a single child.

// Rich text structure — the #1 source of frustration
// WRONG: "Hello"
// RIGHT: [{ type: "text", text: { content: "Hello" } }]
// Rich text is ALWAYS an array of rich text objects.

// Block type mismatch when appending children
// → Each block type has its own structure. A paragraph block needs:
//   { type: "paragraph", paragraph: { rich_text: [{ text: { content: "..." } }] } }

// Timeout errors (default 60s)
// → Increase via Client constructor:
//   new Client({ auth: token, timeoutMs: 120_000 })

// Pagination: missing results
// → Always check has_more and pass start_cursor for next page.
//   Notion returns max 100 items per request.
```

## Full SDK Error Handler

A single `catch` block that branches on every documented Notion error code:

```typescript
import { Client, isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

try {
  const page = await notion.pages.retrieve({ page_id: pageId });
} catch (error) {
  if (isNotionClientError(error)) {
    switch (error.code) {
      case APIErrorCode.ObjectNotFound:
        console.error('Page not found or not shared with integration');
        break;
      case APIErrorCode.Unauthorized:
        console.error('Invalid API token');
        break;
      case APIErrorCode.RestrictedResource:
        console.error('Integration lacks required capability');
        break;
      case APIErrorCode.RateLimited:
        console.error('Rate limited — retry with backoff');
        break;
      case APIErrorCode.ValidationError:
        console.error(`Validation error: ${error.message}`);
        break;
      case ClientErrorCode.RequestTimeout:
        console.error('Request timed out');
        break;
      default:
        console.error(`Notion error: ${error.code} — ${error.message}`);
    }
  } else {
    throw error; // Non-Notion error
  }
}
```

## Quick Diagnostic Script

Three curl probes to isolate whether the problem is Notion's status, your token, or resource access:

```bash
# 1. Check Notion status
curl -s https://status.notion.so/api/v2/status.json | jq '.status.description'

# 2. Verify token
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '{id, type, name}'

# 3. Test database access (replace DB_ID)
curl -s "https://api.notion.com/v1/databases/${DB_ID}" \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '{id, title: .title[0].plain_text}'
```
