---
name: linear-common-errors
description: |
  Diagnose and fix common Linear API errors.
  Use when encountering Linear API errors, debugging integration issues,
  or troubleshooting authentication problems.
  Trigger with phrases like "linear error", "linear API error",
  "debug linear", "linear not working", "linear authentication error".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Common Errors

## Overview
Quick reference for diagnosing and resolving common Linear API and SDK errors. Linear's GraphQL API returns errors in `response.errors[]` with `extensions.type` and `extensions.userPresentableMessage` fields.

## Prerequisites
- Linear SDK or API access configured
- Access to application logs
- Understanding of GraphQL error responses

## Instructions

### Step 1: Understand Error Response Structure
Linear GraphQL errors follow this pattern — note that HTTP 200 responses can still contain errors:

```typescript
// Linear error response shape
interface LinearErrorResponse {
  data: Record<string, any> | null;
  errors?: Array<{
    message: string;
    path?: string[];
    extensions: {
      type: string;  // "authentication_error", "forbidden", etc.
      userPresentableMessage?: string;
    };
  }>;
}
```

### Step 2: Authentication Errors
```typescript
// Error: "Authentication required" / extensions.type: "authentication_error"
// Cause: Missing, invalid, or expired API key or OAuth token

// Diagnostic check
import { LinearClient } from "@linear/sdk";

async function testAuth(): Promise<void> {
  try {
    const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    const viewer = await client.viewer;
    console.log(`Authenticated as: ${viewer.name} (${viewer.email})`);
  } catch (error: any) {
    if (error.message?.includes("Authentication")) {
      console.error("API key is invalid or expired. Generate a new key at:");
      console.error("  Settings > Account > API > Personal API keys");
    }
    throw error;
  }
}
```

### Step 3: Rate Limit Errors
```typescript
// Error: HTTP 429 or extensions.type: "ratelimited"
// Linear uses complexity-based rate limiting for GraphQL

async function safeQuery<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error.status === 429 || error.type === "ratelimited") {
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(`Rate limited, retrying in ${delay}ms (attempt ${attempt + 1}/${retries})`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error("Max retries exceeded");
}
```

### Step 4: Query Complexity Errors
```typescript
// Error: "Query complexity is too high"
// Linear enforces query complexity limits to prevent expensive queries

// BAD: fetching too many nested relations
const issues = await client.issues({
  first: 250,
  // Deep nesting increases complexity
  // include: { project: true, assignee: true, labels: true, comments: true }
});

// GOOD: reduce page size and nest minimally
const issues = await client.issues({ first: 50 });
for (const issue of issues.nodes) {
  // Fetch related data only when needed
  const assignee = await issue.assignee;
}
```

### Step 5: Common SDK Errors
```typescript
// Error: "Cannot read properties of null"
// Cause: Accessing nullable fields without checking
const issue = await client.issue("issue-id");
// BAD: issue.assignee might be null
// const name = (await issue.assignee).name;
// GOOD:
const assignee = await issue.assignee;
const name = assignee?.name ?? "Unassigned";

// Error: "Entity not found"
// Cause: Deleted issue, wrong workspace, or insufficient permissions
try {
  const issue = await client.issue("nonexistent-id");
} catch (error: any) {
  if (error.message?.includes("Entity not found")) {
    console.error("Issue may be deleted, archived, or in another workspace");
  }
}
```

## Error Handling
| Error | Type | Cause | Solution |
|-------|------|-------|----------|
| `Authentication required` | `authentication_error` | Invalid or expired API key | Regenerate key in Linear Settings > API |
| `Forbidden` | `forbidden` | Insufficient permissions | Check OAuth scopes or team membership |
| HTTP 429 | `ratelimited` | Too many requests | Implement exponential backoff, reduce query complexity |
| `Query complexity too high` | `query_error` | Deep nesting or large page sizes | Reduce `first` param, flatten query |
| `Entity not found` | `not_found` | Deleted, archived, or wrong workspace | Verify ID and add `includeArchived: true` if needed |
| `Validation error` | `invalid_input` | Invalid field values in mutation | Check field constraints (e.g., title length, valid state ID) |
| `Webhook signature mismatch` | N/A (local check) | Wrong signing secret | Verify `LINEAR_WEBHOOK_SECRET` matches Linear settings |

## Examples

### Quick Diagnostic Script
```bash
# Test API connectivity
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name email } }"}' | jq .
```

### Catch-All Error Handler
```typescript
import { LinearClient, LinearError } from "@linear/sdk";

async function withLinearErrorHandling<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof LinearError) {
      console.error(`Linear API error [${error.type}]: ${error.message}`);
      if (error.type === "authentication_error") {
        // Trigger re-auth flow
      } else if (error.type === "ratelimited") {
        // Back off and retry
      }
    }
    throw error;
  }
}
```

## Output
- Diagnostic script confirming API connectivity and auth status
- Error handler wrapping all Linear SDK calls with typed error routing
- Rate limit retry logic with exponential backoff
- Null-safe patterns for accessing optional Linear entity fields

## Resources
- [Linear API Error Reference](https://developers.linear.app/docs/graphql/errors)
- [Rate Limiting Guide](https://developers.linear.app/docs/graphql/rate-limiting)
- [Authentication Guide](https://developers.linear.app/docs/graphql/authentication)

## Next Steps
Set up comprehensive debugging with `linear-debug-bundle`.
