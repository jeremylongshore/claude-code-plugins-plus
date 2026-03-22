---
name: linear-rate-limits
description: |
  Handle Linear API rate limiting, complexity budgets, and quotas.
  Use when dealing with 429 errors, implementing throttling,
  or optimizing request patterns to stay within limits.
  Trigger: "linear rate limit", "linear throttling", "linear 429",
  "linear API quota", "linear complexity", "linear request limits".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api]

---
# Linear Rate Limits

## Overview
Linear uses the **leaky bucket algorithm** with two rate limiting dimensions. Understanding both is critical for reliable integrations:

| Budget | Limit | Refill Rate |
|--------|-------|-------------|
| **Requests** | 5,000/hour per API key | ~83/min constant refill |
| **Complexity** | 250,000 points/hour | ~4,167/min constant refill |
| **Max single query** | 10,000 points | Hard reject if exceeded |

**Complexity scoring:** Each property = 0.1 pt, each object = 1 pt, connections multiply children by `first` arg (default 50), then round up.

## Prerequisites
- `@linear/sdk` installed
- Understanding of HTTP response headers
- Familiarity with async/await patterns

## Instructions

### Step 1: Read Rate Limit Headers
Linear returns rate limit info on every response.

```typescript
const response = await fetch("https://api.linear.app/graphql", {
  method: "POST",
  headers: {
    Authorization: process.env.LINEAR_API_KEY!,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: "{ viewer { id } }" }),
});

// Key headers
const headers = {
  requestsRemaining: response.headers.get("x-ratelimit-requests-remaining"),
  requestsLimit: response.headers.get("x-ratelimit-requests-limit"),
  requestsReset: response.headers.get("x-ratelimit-requests-reset"),
  complexityRemaining: response.headers.get("x-ratelimit-complexity-remaining"),
  complexityLimit: response.headers.get("x-ratelimit-complexity-limit"),
  queryComplexity: response.headers.get("x-complexity"),
};

console.log(`Requests: ${headers.requestsRemaining}/${headers.requestsLimit}`);
console.log(`Complexity: ${headers.complexityRemaining}/${headers.complexityLimit}`);
console.log(`This query cost: ${headers.queryComplexity} points`);
```

### Step 2: Exponential Backoff with Jitter
```typescript
import { LinearClient } from "@linear/sdk";

class RateLimitedClient {
  private client: LinearClient;

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  async withRetry<T>(fn: () => Promise<T>, maxRetries = 5): Promise<T> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        const isRateLimited = error.status === 429 ||
          error.message?.includes("rate") ||
          error.type === "ratelimited";

        if (!isRateLimited || attempt === maxRetries - 1) throw error;

        // Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter
        const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
        console.warn(`Rate limited (attempt ${attempt + 1}/${maxRetries}), waiting ${Math.round(delay)}ms`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
    throw new Error("Unreachable");
  }

  get sdk() { return this.client; }
}
```

### Step 3: Request Queue with Token Bucket
Prevent bursts by spacing requests evenly.

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

// Usage: 8 requests/second max
const queue = new RequestQueue(8);
const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

const teamResults = await Promise.all(
  teamIds.map(id => queue.enqueue(() => client.team(id)))
);
```

### Step 4: Reduce Query Complexity
```typescript
// HIGH COMPLEXITY (~12,500 pts):
// 250 issues * (1 issue + 50 labels * 0.1 per field) = expensive
// const heavy = await client.issues({ first: 250 });

// LOW COMPLEXITY (~55 pts):
// 50 issues * (5 fields * 0.1 + 1 object) = cheap
const light = await client.issues({
  first: 50,
  filter: { team: { id: { eq: teamId } } },
});

// Use rawRequest for minimal field selection
const minimal = await client.client.rawRequest(`
  query { issues(first: 50) { nodes { id identifier title priority } } }
`);

// Sort by updatedAt to get fresh data first, avoid paginating everything
const fresh = await client.issues({
  first: 50,
  orderBy: "updatedAt",
  filter: { updatedAt: { gte: lastSyncTime } },
});
```

### Step 5: Batch Mutations
Combine multiple mutations into one GraphQL request.

```typescript
// Instead of 100 separate issueUpdate calls (~100 requests):
async function batchUpdatePriority(client: LinearClient, issueIds: string[], priority: number) {
  const chunkSize = 20; // Keep each batch under complexity limit
  for (let i = 0; i < issueIds.length; i += chunkSize) {
    const chunk = issueIds.slice(i, i + chunkSize);
    const mutations = chunk.map((id, j) =>
      `u${j}: issueUpdate(id: "${id}", input: { priority: ${priority} }) { success }`
    ).join("\n");

    await queue.enqueue(() =>
      client.client.rawRequest(`mutation BatchUpdate { ${mutations} }`)
    );
  }
}

// Batch archive
async function batchArchive(client: LinearClient, issueIds: string[]) {
  for (let i = 0; i < issueIds.length; i += 20) {
    const chunk = issueIds.slice(i, i + 20);
    const mutations = chunk.map((id, j) =>
      `a${j}: issueArchive(id: "${id}") { success }`
    ).join("\n");

    await client.client.rawRequest(`mutation { ${mutations} }`);
  }
}
```

### Step 6: Rate Limit Monitor
```typescript
class RateLimitMonitor {
  private remaining = { requests: 5000, complexity: 250000 };

  update(headers: Headers) {
    const reqRemaining = headers.get("x-ratelimit-requests-remaining");
    const cxRemaining = headers.get("x-ratelimit-complexity-remaining");
    if (reqRemaining) this.remaining.requests = parseInt(reqRemaining);
    if (cxRemaining) this.remaining.complexity = parseInt(cxRemaining);
  }

  isLow(): boolean {
    return this.remaining.requests < 100 || this.remaining.complexity < 5000;
  }

  getStatus() {
    return {
      requests: this.remaining.requests,
      complexity: this.remaining.complexity,
      healthy: !this.isLow(),
    };
  }
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| HTTP 429 | Request or complexity budget exceeded | Parse headers, back off exponentially |
| `Query complexity too high` | Single query > 10,000 pts | Reduce `first` to 50, remove nested relations |
| Burst of 429s on startup | Init fetches too much data | Stagger startup queries, cache static data |
| Timeout on SDK call | Server under load | Add 30s timeout, retry once |

## Examples

### Rate Limit Status Check
```bash
curl -s -I -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id } }"}' 2>&1 | grep -i ratelimit
```

### Safe Bulk Import
```typescript
const rlClient = new RateLimitedClient(process.env.LINEAR_API_KEY!);
const items = [/* issues to import */];

for (let i = 0; i < items.length; i++) {
  await rlClient.withRetry(() =>
    rlClient.sdk.createIssue({ teamId: "team-uuid", title: items[i].title })
  );
  if ((i + 1) % 50 === 0) console.log(`Imported ${i + 1}/${items.length}`);
}
```

## Resources
- [Linear Rate Limiting](https://linear.app/developers/rate-limiting)
- [Query Complexity](https://linear.app/developers/rate-limiting)
- [Best Practices](https://linear.app/developers/graphql)
