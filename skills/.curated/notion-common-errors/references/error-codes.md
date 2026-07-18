# Notion API Error Codes — Detailed Reference

Every Notion API error with its exact HTTP status, error body, root cause, and fix.
Match the HTTP status and `code` field from the JSON error body to the section below.

---

## 401 — `unauthorized`

```json
{"object": "error", "status": 401, "code": "unauthorized", "message": "API token is invalid."}
```

**Cause:** Token is missing, malformed, expired, or revoked.

**Fix:**

```bash
# Verify token is set
echo ${NOTION_TOKEN:+SET}

# Test directly
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq .
```

If the response shows your integration bot user, the token is valid. Otherwise regenerate at [notion.so/my-integrations](https://www.notion.so/my-integrations). Tokens starting with `secret_` are legacy format — new integrations use `ntn_` prefix.

---

## 403 — `restricted_resource`

```json
{"object": "error", "status": 403, "code": "restricted_resource", "message": "Insufficient permissions for this resource."}
```

**Cause:** The integration exists and the page is shared, but the integration lacks the required capability (read content, update content, insert content, read comments).

**Fix:** Go to [notion.so/my-integrations](https://www.notion.so/my-integrations), select your integration, and enable the needed capabilities under "Capabilities." Common missing capability: "Read comments" when querying comments, or "Insert content" when creating pages.

---

## 404 — `object_not_found`

```json
{"object": "error", "status": 404, "code": "object_not_found", "message": "Could not find page with ID: abc123..."}
```

**Cause:** The page, database, or block either does not exist or has not been shared with your integration. This is the single most common Notion API error.

**Fix:**

1. Open the target page in Notion
2. Click the `...` menu at top right
3. Select **Connections** and add your integration
4. Parent pages must also be shared — sharing only a child page is not enough

```typescript
// Defensive retrieval pattern
try {
  const page = await notion.pages.retrieve({ page_id: pageId });
} catch (error) {
  if (isNotionClientError(error) && error.code === APIErrorCode.ObjectNotFound) {
    console.error('Page not shared with integration. Add via Connections menu.');
  }
}
```

**Page ID gotcha:** Notion URLs use 32-character hex IDs without dashes (`https://notion.so/Page-abc123def456...`). The API accepts both dashed (`abc123de-f456-...`) and undashed formats. If you're extracting IDs from URLs, strip the page title prefix and use the last 32 characters.

---

## 400 — `validation_error`

```json
{"object": "error", "status": 400, "code": "validation_error", "message": "..."}
```

**Message varies.** This is the broadest error category. Common sub-cases:

| Message Pattern | Cause | Fix |
| ---------------- | ------- | ----- |
| `Title is not a property that exists` | Wrong property name | Use exact name from database schema (case-sensitive) |
| `... should be an array` | Rich text passed as string | Wrap in `[{ text: { content: "value" } }]` |
| `body.parent.database_id should be defined` | Missing parent in page create | Include `parent: { database_id: "..." }` |
| `... should be a string, instead was ...` | Wrong property type for filter | Match filter type to property type (see below) |
| `Could not find property with name or id` | Property renamed in Notion UI | Retrieve schema with `databases.retrieve()` to get current names |

**Filter type mismatches** — the most common validation error:

```typescript
// WRONG: Status is a status property, not text
{ property: 'Status', text: { equals: 'Done' } }
// RIGHT: Use the matching filter type
{ property: 'Status', status: { equals: 'Done' } }

// WRONG: Passing plain string for title
{ Name: { title: 'My Page' } }
// RIGHT: Title requires rich text array
{ Name: { title: [{ text: { content: 'My Page' } }] } }
```

**Debug tip:** Always retrieve the database schema first to avoid property name/type errors:

```typescript
const db = await notion.databases.retrieve({ database_id: dbId });
console.log(Object.entries(db.properties).map(([name, prop]) => `${name}: ${prop.type}`));
// Output: "Name: title", "Status: status", "Tags: multi_select", ...
```

---

## 429 — `rate_limited`

```json
{"object": "error", "status": 429, "code": "rate_limited", "message": "Rate limited"}
```

**Cause:** Exceeded Notion's average rate limit of 3 requests per second per integration.

**Fix:**

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
        const wait = Math.pow(2, attempt) * 1000; // exponential backoff
        console.log(`Rate limited. Waiting ${wait}ms (attempt ${attempt + 1}/${maxRetries})...`);
        await new Promise(r => setTimeout(r, wait));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

The `@notionhq/client` SDK has built-in retry with exponential backoff. If you hit rate limits frequently, batch operations and add delays between sequential calls. For bulk operations, see `notion-rate-limits`.

---

## 409 — `conflict_error`

```json
{"object": "error", "status": 409, "code": "conflict_error", "message": "Transaction has an existing lock on the object."}
```

**Cause:** Concurrent modifications to the same page, block, or database. Common in parallel scripts or multi-user workflows.

**Fix:** Retry the operation. The SDK handles this automatically. If writing your own retry logic, a simple retry after 1-2 seconds resolves most conflicts. Avoid parallelizing writes to the same page.

---

## 500 — `internal_server_error`

```json
{"object": "error", "status": 500, "code": "internal_server_error", "message": "Internal Server Error"}
```

**Cause:** Bug or transient failure on Notion's servers.

**Fix:** Retry with exponential backoff. If persistent (>5 minutes), check [status.notion.so](https://status.notion.so) for ongoing incidents. Consider filing a bug report at [developers.notion.com](https://developers.notion.com) with the request ID from the response headers (`x-request-id`).

---

## 502/503 — `service_unavailable`

```json
{"object": "error", "status": 503, "code": "service_unavailable", "message": "Notion is unavailable. Try again later."}
```

**Cause:** Notion's servers are down or under maintenance.

**Fix:**

```bash
# Check Notion status
curl -s https://status.notion.so/api/v2/status.json | jq '.status.description'
```

Wait and retry. Monitor [status.notion.so](https://status.notion.so) for incident updates.
