---
name: linear-common-errors
description: |
  Diagnose and fix common Linear API and SDK errors.
  Use when encountering Linear API errors, debugging integration issues,
  or troubleshooting authentication, rate limits, or query problems.
  Trigger: "linear error", "linear API error", "debug linear",
  "linear not working", "linear 429", "linear authentication error".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, debugging, authentication]

---
# Linear Common Errors

## Overview
Quick reference for diagnosing and resolving common Linear API and SDK errors. Linear's GraphQL API returns errors in `response.errors[]` with `extensions.type` and `extensions.userPresentableMessage` fields. HTTP 200 responses can still contain partial errors -- always check the `errors` array.

## Prerequisites
- Linear SDK or raw API access configured
- Access to application logs
- Understanding of GraphQL error response format

## Instructions

### Error Response Structure
```typescript
// Linear GraphQL error shape
interface LinearGraphQLResponse {
  data: Record<string, any> | null;
  errors?: Array<{
    message: string;
    path?: string[];
    extensions: {
      type: string;  // "authentication_error", "forbidden", "ratelimited", etc.
      userPresentableMessage?: string;
    };
  }>;
}

// SDK throws these typed errors
import { LinearError, InvalidInputLinearError } from "@linear/sdk";
// LinearError includes: .status, .message, .type, .query, .variables
// InvalidInputLinearError extends LinearError for mutation input errors
```

### Error 1: Authentication Failures
```typescript
// extensions.type: "authentication_error"
// HTTP 401 or error in response.errors

// Diagnostic check
async function testAuth(): Promise<void> {
  try {
    const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    const viewer = await client.viewer;
    console.log(`OK: ${viewer.name} (${viewer.email})`);
  } catch (error: any) {
    if (error.message?.includes("Authentication")) {
      console.error("API key is invalid or expired.");
      console.error("Fix: Settings > Account > API > Personal API keys");
    }
    throw error;
  }
}
```

**Quick curl diagnostic:**
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name email } }"}' | jq .
```

### Error 2: Rate Limiting (HTTP 429)
Linear uses the **leaky bucket algorithm** with two budgets:
- **Request limit**: 5,000 requests/hour per API key
- **Complexity limit**: 250,000 complexity points/hour per API key
- **Max single query complexity**: 10,000 points

```typescript
// extensions.type: "ratelimited"
// HTTP 429 with rate limit headers

async function withRetry<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const isRateLimited = error.status === 429 ||
        error.message?.includes("rate") ||
        error.type === "ratelimited";
      if (!isRateLimited || attempt === maxRetries - 1) throw error;

      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      console.warn(`Rate limited (attempt ${attempt + 1}), waiting ${Math.round(delay)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

**Check rate limit status via headers:**
```typescript
const resp = await fetch("https://api.linear.app/graphql", {
  method: "POST",
  headers: {
    Authorization: process.env.LINEAR_API_KEY!,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: "{ viewer { id } }" }),
});

console.log("Requests remaining:", resp.headers.get("x-ratelimit-requests-remaining"));
console.log("Requests limit:", resp.headers.get("x-ratelimit-requests-limit"));
console.log("Requests reset:", resp.headers.get("x-ratelimit-requests-reset"));
console.log("Complexity:", resp.headers.get("x-complexity"));
```

### Error 3: Query Complexity Too High
Each property = 0.1 pt, each object = 1 pt, connections multiply children by the `first` argument (default 50). Max 10,000 pts per query.

```typescript
// BAD: ~12,500 complexity (250 * 50 labels)
const heavy = await client.issues({ first: 250 });

// GOOD: reduce page size and fetch relations separately
const light = await client.issues({ first: 50 });
```

### Error 4: Entity Not Found
```typescript
// extensions.type: "not_found"
// Cause: deleted, archived, wrong workspace, or insufficient permissions

try {
  const issue = await client.issue("nonexistent-uuid");
} catch (error: any) {
  if (error.message?.includes("Entity not found")) {
    console.error("Issue may be deleted, archived, or in another workspace.");
    console.error("Try: client.issues({ includeArchived: true })");
  }
}
```

### Error 5: Invalid Input on Mutations
```typescript
import { InvalidInputLinearError } from "@linear/sdk";

try {
  await client.createIssue({
    teamId: "invalid-uuid",
    title: "", // Empty title
  });
} catch (error) {
  if (error instanceof InvalidInputLinearError) {
    console.error("Invalid input:", error.message);
    // error.query and error.variables contain request details
  }
}
```

### Error 6: Null Reference on Relations
```typescript
// SDK models lazy-load relations -- they can be null
const issue = await client.issue("uuid");

// BAD: crashes if unassigned
// const name = (await issue.assignee).name;

// GOOD: optional chaining
const name = (await issue.assignee)?.name ?? "Unassigned";
const projectName = (await issue.project)?.name ?? "No project";
```

### Error 7: Webhook Signature Mismatch
```typescript
// Happens when LINEAR_WEBHOOK_SECRET doesn't match the webhook config
import crypto from "crypto";

function verifyWebhook(payload: string, signature: string, secret: string): boolean {
  const expected = crypto.createHmac("sha256", secret).update(payload).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
  } catch {
    return false; // Length mismatch
  }
}
```

## Error Reference Table

| Error | extensions.type | HTTP | Cause | Fix |
|-------|----------------|------|-------|-----|
| Authentication required | `authentication_error` | 401 | Invalid/expired key | Regenerate at Settings > API |
| Forbidden | `forbidden` | 403 | Missing OAuth scope | Re-authorize with correct scopes |
| Rate limited | `ratelimited` | 429 | Budget exceeded | Exponential backoff, reduce complexity |
| Query complexity too high | `query_error` | 400 | Deep nesting or large pages | Reduce `first`, flatten query |
| Entity not found | `not_found` | 200 | Deleted/archived/wrong workspace | Verify ID, try `includeArchived` |
| Validation error | `invalid_input` | 200 | Bad mutation input | Check field constraints |
| Webhook sig mismatch | N/A (local) | N/A | Wrong signing secret | Match `LINEAR_WEBHOOK_SECRET` |

## Examples

### Catch-All Error Handler
```typescript
import { LinearError, InvalidInputLinearError } from "@linear/sdk";

async function handleLinearOp<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof InvalidInputLinearError) {
      console.error(`Input error: ${error.message}`);
    } else if (error instanceof LinearError) {
      console.error(`Linear error [${error.status}]: ${error.message}`);
      if (error.status === 429) {
        console.error("Rate limited — implement backoff");
      }
    } else {
      console.error("Unexpected error:", error);
    }
    throw error;
  }
}
```

## Resources
- [SDK Error Handling](https://linear.app/developers/sdk-errors)
- [Rate Limiting](https://linear.app/developers/rate-limiting)
- [GraphQL API](https://linear.app/developers/graphql)
