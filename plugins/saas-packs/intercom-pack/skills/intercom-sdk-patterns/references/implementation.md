# Intercom SDK — Full Implementation Patterns

Deep-dive implementations for the `intercom-client` TypeScript SDK. These are the
full versions of the patterns summarized in `SKILL.md`. Copy them into your
project and adapt the names/paths to your codebase.

## Error Handling with IntercomError

Wrap every API call so a thrown `IntercomError` is normalized into a
`{ data, error }` result and status-specific guidance is logged. Non-Intercom
errors are re-thrown untouched.

```typescript
import { IntercomError } from "intercom-client";

async function safeIntercomCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ data: T | null; error: IntercomError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof IntercomError) {
      console.error(`[Intercom:${context}] ${err.statusCode}: ${err.message}`, {
        requestId: err.body?.request_id,
        errors: err.body?.errors,
      });

      // Specific error handling
      switch (err.statusCode) {
        case 401:
          console.error("Token invalid or expired. Regenerate access token.");
          break;
        case 404:
          console.error("Resource not found. Verify the ID.");
          break;
        case 409:
          console.error("Conflict: resource already exists.");
          break;
        case 422:
          console.error("Validation failed:", err.body?.errors);
          break;
        case 429:
          console.error("Rate limited. Back off and retry.");
          break;
      }

      return { data: null, error: err };
    }
    throw err; // Re-throw non-Intercom errors
  }
}

// Usage
const { data: contact, error } = await safeIntercomCall(
  () => client.contacts.find({ contactId: "abc123" }),
  "findContact"
);
```

## Retry with Exponential Backoff

Retry only transient failures — rate limits (429) and server errors (5xx).
Client errors (4xx other than 429) fail fast. Honor a `Retry-After` header when
present; otherwise back off exponentially with jitter.

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (err instanceof IntercomError) {
        // Only retry on rate limits and server errors
        if (err.statusCode !== 429 && (err.statusCode ?? 0) < 500) {
          throw err;
        }

        if (attempt === config.maxRetries) throw err;

        // Use Retry-After header if available, otherwise exponential backoff
        const retryAfter = err.headers?.["retry-after"];
        const delay = retryAfter
          ? parseInt(retryAfter) * 1000
          : config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;

        console.log(`Retry ${attempt + 1}/${config.maxRetries} in ${delay}ms`);
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw err;
      }
    }
  }
  throw new Error("Unreachable");
}
```

## Multi-Tenant Client Factory

For apps serving multiple Intercom workspaces, cache one client per workspace
token so each tenant stays isolated and connections are reused.

```typescript
const clientCache = new Map<string, IntercomClient>();

export function getClientForWorkspace(
  workspaceToken: string
): IntercomClient {
  if (!clientCache.has(workspaceToken)) {
    clientCache.set(
      workspaceToken,
      new IntercomClient({ token: workspaceToken })
    );
  }
  return clientCache.get(workspaceToken)!;
}
```

## Intercom Search Operators

The search API accepts these operators inside `query.value` conditions.

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `email = "test@example.com"` |
| `!=` | Not equals | `role != "lead"` |
| `~` | Contains | `email ~ "@acme.com"` |
| `!~` | Not contains | `name !~ "test"` |
| `>` | Greater than | `created_at > 1700000000` |
| `<` | Less than | `last_seen_at < 1700000000` |
| `IN` | In list | `tag_id IN ["tag1", "tag2"]` |
| `NIN` | Not in list | `segment_id NIN ["seg1"]` |
