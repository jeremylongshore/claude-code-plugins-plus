---
name: linear-rate-limits
description: |
  Handle Linear API rate limiting and quotas effectively.
  Use when dealing with rate limit errors, implementing throttling,
  or optimizing API usage patterns.
  Trigger with phrases like "linear rate limit", "linear throttling",
  "linear API quota", "linear 429 error", "linear request limits".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Rate Limits

## Overview
Handle Linear API rate limits for reliable integrations. Linear uses complexity-based rate limiting for its GraphQL API — each query has a complexity score based on nesting depth and page sizes. When the budget is exceeded, the API returns HTTP 429.

## Prerequisites
- Linear SDK installed (`npm install @linear/sdk`)
- Understanding of HTTP response headers
- Familiarity with async/await patterns

## Instructions

### Step 1: Understand Rate Limit Headers
Linear returns rate limit information in response headers.

```typescript
// Check rate limit status via raw HTTP
const response = await fetch("https://api.linear.app/graphql", {
  method: "POST",
  headers: {
    "Authorization": process.env.LINEAR_API_KEY!,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: "{ viewer { id } }" }),
});

console.log("Status:", response.status);
console.log("X-RateLimit-Requests-Limit:", response.headers.get("x-ratelimit-requests-limit"));
console.log("X-RateLimit-Requests-Remaining:", response.headers.get("x-ratelimit-requests-remaining"));
console.log("X-RateLimit-Requests-Reset:", response.headers.get("x-ratelimit-requests-reset"));
console.log("X-Complexity:", response.headers.get("x-complexity"));
```

### Step 2: Implement Exponential Backoff
```typescript
import { LinearClient } from "@linear/sdk";

class RateLimitedLinear {
  private client: LinearClient;

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  async withRetry<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        const isRateLimited = error.status === 429 || error.message?.includes("rate");
        if (!isRateLimited || attempt === maxRetries - 1) throw error;

        const baseDelay = 1000;
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 500;
        console.warn(`Rate limited (attempt ${attempt + 1}/${maxRetries}), waiting ${Math.round(delay)}ms`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
    throw new Error("Unreachable");
  }

  async getIssues(filter?: any) {
    return this.withRetry(() => this.client.issues(filter));
  }

  async createIssue(input: any) {
    return this.withRetry(() => this.client.createIssue(input));
  }
}
```

### Step 3: Request Queue with Throttling
Prevent bursts by spacing requests with a token-bucket pattern.

```typescript
class RequestQueue {
  private queue: Array<{ fn: () => Promise<any>; resolve: Function; reject: Function }> = [];
  private processing = false;
  private intervalMs: number;

  constructor(requestsPerSecond = 10) {
    this.intervalMs = 1000 / requestsPerSecond;
  }

  async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      if (!this.processing) this.processQueue();
    });
  }

  private async processQueue() {
    this.processing = true;
    while (this.queue.length > 0) {
      const { fn, resolve, reject } = this.queue.shift()!;
      try {
        resolve(await fn());
      } catch (error) {
        reject(error);
      }
      if (this.queue.length > 0) {
        await new Promise(r => setTimeout(r, this.intervalMs));
      }
    }
    this.processing = false;
  }
}

// Usage
const queue = new RequestQueue(8);  // 8 requests per second
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// These execute serially with 125ms spacing
const results = await Promise.all(
  teamIds.map(id => queue.enqueue(() => client.team(id)))
);
```

### Step 4: Reduce Query Complexity
```typescript
// HIGH COMPLEXITY: deep nesting + large page
// Complexity ≈ first × nested_fields
const heavy = await client.issues({
  first: 250,  // Large page
  // Plus each issue fetches assignee, project, labels...
});

// LOW COMPLEXITY: flat query, small page
const light = await client.issues({
  first: 50,
  filter: { team: { id: { eq: teamId } } },
  // Access relations lazily only when needed
});
for (const issue of light.nodes) {
  // Only fetch assignee for assigned issues
  if (issue.assigneeId) {
    const assignee = await queue.enqueue(() => issue.assignee);
  }
}
```

### Step 5: Batch Operations
Combine multiple mutations into one request to stay within limits.

```typescript
// Instead of 100 separate issueUpdate calls:
async function batchArchive(client: LinearClient, issueIds: string[]) {
  const chunks = [];
  for (let i = 0; i < issueIds.length; i += 20) {
    chunks.push(issueIds.slice(i, i + 20));
  }

  for (const chunk of chunks) {
    const mutations = chunk.map((id, i) =>
      `a${i}: issueArchive(id: "${id}") { success }`
    ).join("\n");

    await queue.enqueue(() =>
      client.client.rawRequest(`mutation { ${mutations} }`)
    );
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| HTTP `429 Too Many Requests` | Rate limit exceeded | Parse `Retry-After` header, back off exponentially |
| `Query complexity too high` | Query exceeds complexity budget | Reduce `first` param, remove nested relations, split into multiple queries |
| `Timeout` on SDK call | Server slow under load | Add 30s timeout, retry once |
| Burst of `429`s on startup | Initialization fetches too much | Stagger startup queries, cache static data |

## Examples

### Rate Limit Monitor
```typescript
async function checkRateLimitStatus(): Promise<void> {
  const resp = await fetch("https://api.linear.app/graphql", {
    method: "POST",
    headers: {
      "Authorization": process.env.LINEAR_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: "{ viewer { id } }" }),
  });

  const remaining = resp.headers.get("x-ratelimit-requests-remaining");
  const limit = resp.headers.get("x-ratelimit-requests-limit");
  const reset = resp.headers.get("x-ratelimit-requests-reset");
  console.log(`Rate limit: ${remaining}/${limit} remaining, resets at ${reset}`);
}
```

### Safe Bulk Import
```typescript
const rateLimited = new RateLimitedLinear(process.env.LINEAR_API_KEY!);
const importData = [/* array of issues to import */];

let created = 0;
for (const item of importData) {
  await rateLimited.createIssue({ teamId: "team-uuid", title: item.title });
  created++;
  if (created % 50 === 0) console.log(`Created ${created}/${importData.length}`);
}
```

## Output
- Rate limit header monitoring for proactive throttling
- Retry wrapper with exponential backoff and jitter
- Token-bucket request queue spacing API calls
- Query complexity reduction patterns
- Batch mutation builder for bulk operations

## Resources
- [Linear Rate Limiting](https://developers.linear.app/docs/graphql/rate-limiting)
- [GraphQL Complexity](https://developers.linear.app/docs/graphql/complexity)
- [Best Practices](https://developers.linear.app/docs/graphql/best-practices)

## Next Steps
Learn security best practices with `linear-security-basics`.
