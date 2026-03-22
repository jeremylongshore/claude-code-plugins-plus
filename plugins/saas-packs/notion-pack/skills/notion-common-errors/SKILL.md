---
name: notion-common-errors
description: |
  Diagnose and fix common Notion API errors and exceptions.
  Use when encountering Notion errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "notion error", "fix notion",
  "notion not working", "debug notion", "notion 400", "notion 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Common Errors

## Overview
Quick reference for Notion API error codes, their causes, and solutions. All errors return a JSON body with `status`, `code`, and `message` fields.

## Prerequisites
- `@notionhq/client` installed
- `NOTION_TOKEN` configured
- Access to application logs

## Instructions

### Step 1: Identify the Error Code
Notion API errors follow a consistent structure:
```json
{
  "object": "error",
  "status": 400,
  "code": "validation_error",
  "message": "Title is not a property that exists."
}
```

### Step 2: Match Error and Apply Fix

---

### 401 — `unauthorized`
**Message:** `API token is invalid.`

**Cause:** Token is missing, malformed, or revoked.

**Solution:**
```bash
# Verify token is set
echo ${NOTION_TOKEN:+SET}

# Test directly
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq .
```
Regenerate at https://www.notion.so/my-integrations if needed.

---

### 403 — `restricted_resource`
**Message:** `Insufficient permissions for this resource.`

**Cause:** Integration lacks required capabilities (read/update/insert content, read comments, etc.).

**Solution:** Edit integration capabilities at notion.so/my-integrations. Ensure the integration has the needed capability enabled.

---

### 404 — `object_not_found`
**Message:** `Could not find [object type] with ID: ...`

**Cause:** The page/database either does not exist OR is not shared with your integration. This is the most common Notion API error.

**Solution:**
1. Open the page in Notion
2. Click `...` menu -> **Connections** -> Add your integration
3. Parent pages must also be shared — sharing a child page alone is not enough

```typescript
// Defensive pattern
const { data, error } = await safeNotionCall(() =>
  notion.pages.retrieve({ page_id: pageId })
);
if (error?.includes('not found')) {
  console.log('Page not shared with integration. Add via Connections menu.');
}
```

---

### 400 — `validation_error`
**Message varies:** Property name/type mismatches, invalid filter syntax, malformed requests.

**Common causes and fixes:**

```typescript
// Wrong: Property name doesn't match database schema
{ property: 'title', title: { contains: 'x' } }
// Right: Use the exact property name from the database
{ property: 'Name', title: { contains: 'x' } }

// Wrong: Using wrong filter type for property
{ property: 'Status', text: { equals: 'Done' } }
// Right: Status is a select, not text
{ property: 'Status', select: { equals: 'Done' } }

// Wrong: Creating page without required title property
notion.pages.create({
  parent: { database_id: dbId },
  properties: { Status: { select: { name: 'New' } } },  // Missing title!
});
// Right: Always include the title property
notion.pages.create({
  parent: { database_id: dbId },
  properties: {
    Name: { title: [{ text: { content: 'New item' } }] },  // Title required
    Status: { select: { name: 'New' } },
  },
});
```

**Debug tip:** Retrieve the database schema first:
```typescript
const db = await notion.databases.retrieve({ database_id: dbId });
console.log(Object.entries(db.properties).map(([k, v]) => `${k}: ${v.type}`));
```

---

### 429 — `rate_limited`
**Message:** `Rate limited`

**Cause:** Exceeded average of 3 requests per second.

**Solution:**
```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
        const retryAfter = parseInt(error.headers?.['retry-after'] ?? '1');
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

Note: `@notionhq/client` has built-in retry (default 2 retries with backoff).

---

### 409 — `conflict_error`
**Message:** `Resource was updated by another request.`

**Cause:** Concurrent updates to the same page/block.

**Solution:** Retry the operation. The SDK's built-in retry handles this automatically.

---

### 502/503 — `service_unavailable`
**Message:** `Notion encountered an internal error.`

**Cause:** Notion's servers are temporarily unavailable.

**Solution:**
```bash
# Check Notion status
curl -s https://status.notion.com/api/v2/status.json | jq '.status.description'
```
Wait and retry. Check https://status.notion.com for ongoing incidents.

---

### Step 3: Common Non-HTTP Errors

```typescript
// "Could not find property with name or id: ..."
// → Property was renamed in Notion UI. Update your code to match.

// "body failed validation: ... should be a string"
// → You passed a number or object where a string was expected.
// Common with rich_text — must be an array of rich text objects.

// "body.properties.Name.title should be defined"
// → Every database page requires its title property.

// Timeout errors
// → Increase timeoutMs on the Client constructor (default is 60s).
```

## Output
- Identified error cause from code and message
- Applied targeted fix
- Verified resolution with test API call

## Error Handling
| Code | HTTP | Retryable | Action |
|------|------|-----------|--------|
| `unauthorized` | 401 | No | Fix token |
| `restricted_resource` | 403 | No | Add capability |
| `object_not_found` | 404 | No | Share page |
| `validation_error` | 400 | No | Fix request |
| `rate_limited` | 429 | Yes | Respect Retry-After |
| `conflict_error` | 409 | Yes | Retry |
| `internal_server_error` | 500 | Yes | Retry |
| `service_unavailable` | 503 | Yes | Wait + retry |

## Examples

### Diagnostic One-Liner
```bash
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '{id, type, name}'
```

## Resources
- [Notion API Error Codes](https://developers.notion.com/reference/request-limits)
- [Notion Status Page](https://status.notion.com)
- [API Introduction](https://developers.notion.com/reference/intro)

## Next Steps
For comprehensive debugging, see `notion-debug-bundle`.
