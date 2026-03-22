---
name: linear-sdk-patterns
description: |
  TypeScript/JavaScript SDK patterns and best practices for Linear.
  Use when learning SDK idioms, implementing pagination,
  filtering, relation loading, or custom GraphQL queries.
  Trigger: "linear SDK patterns", "linear best practices",
  "linear typescript", "linear API patterns", "linear pagination".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, typescript]

---
# Linear SDK Patterns

## Overview
Production patterns for `@linear/sdk`. The SDK wraps Linear's GraphQL API with strongly-typed models, cursor-based pagination (`fetchNext()`/`fetchPrevious()`), lazy-loaded relations, and typed error classes. Understanding these patterns avoids N+1 queries and rate limit waste.

## Prerequisites
- `@linear/sdk` installed
- TypeScript project with `strict: true`
- Understanding of async/await and GraphQL concepts

## Instructions

### Pattern 1: Client Singleton
```typescript
import { LinearClient } from "@linear/sdk";

let _client: LinearClient | null = null;

export function getLinearClient(): LinearClient {
  if (!_client) {
    const apiKey = process.env.LINEAR_API_KEY;
    if (!apiKey) throw new Error("LINEAR_API_KEY is required");
    _client = new LinearClient({ apiKey });
  }
  return _client;
}

// For multi-user OAuth apps — one client per user
const clientCache = new Map<string, LinearClient>();

export function getClientForUser(userId: string, accessToken: string): LinearClient {
  if (!clientCache.has(userId)) {
    clientCache.set(userId, new LinearClient({ accessToken }));
  }
  return clientCache.get(userId)!;
}
```

### Pattern 2: Cursor-Based Pagination
Linear uses Relay-style cursor pagination. The SDK provides `fetchNext()` and `fetchPrevious()` helpers, plus raw `pageInfo` for manual control.

```typescript
// SDK built-in pagination helpers
const firstPage = await client.issues({ first: 50 });
console.log(`Page 1: ${firstPage.nodes.length} issues`);

if (firstPage.pageInfo.hasNextPage) {
  const secondPage = await firstPage.fetchNext();
  console.log(`Page 2: ${secondPage.nodes.length} issues`);
}

// Manual pagination with cursor — good for streaming all data
async function* paginateAll<T>(
  fetchPage: (cursor?: string) => Promise<{
    nodes: T[];
    pageInfo: { hasNextPage: boolean; endCursor: string };
  }>
): AsyncGenerator<T> {
  let cursor: string | undefined;
  let hasNext = true;

  while (hasNext) {
    const page = await fetchPage(cursor);
    for (const node of page.nodes) yield node;
    hasNext = page.pageInfo.hasNextPage;
    cursor = page.pageInfo.endCursor;
  }
}

// Stream all issues without loading everything into memory
for await (const issue of paginateAll(c => client.issues({ first: 50, after: c }))) {
  console.log(`${issue.identifier}: ${issue.title}`);
}
```

### Pattern 3: Relation Loading (Avoiding N+1)
SDK models lazy-load relations. Accessing `.assignee` triggers a separate API call. Use raw GraphQL to batch-fetch relations in one request.

```typescript
// LAZY (N+1 problem) — each .assignee is a separate API call
const issues = await client.issues({ first: 50 });
for (const issue of issues.nodes) {
  const assignee = await issue.assignee; // API call per issue!
  console.log(`${issue.identifier}: ${assignee?.name}`);
}

// BATCH (1 request) — use rawRequest for precise field selection
const response = await client.client.rawRequest(`
  query TeamIssues($teamKey: String!) {
    issues(first: 50, filter: { team: { key: { eq: $teamKey } } }) {
      nodes {
        id identifier title priority
        assignee { name email }
        state { name type }
        labels { nodes { name color } }
        project { name }
      }
    }
  }
`, { teamKey: "ENG" });

// PRE-RESOLVE — parallel resolution for a single issue
async function enrichIssue(issue: any) {
  const [assignee, state, team, labels] = await Promise.all([
    issue.assignee,
    issue.state,
    issue.team,
    issue.labels(),
  ]);
  return { ...issue, _assignee: assignee, _state: state, _team: team, _labels: labels.nodes };
}
```

### Pattern 4: Filtering with Comparators
Linear supports `eq`, `neq`, `in`, `nin`, `lt`, `lte`, `gt`, `gte`, `startsWith`, `contains`, and logical `and`/`or` operators.

```typescript
// High-priority open bugs
const bugs = await client.issues({
  first: 50,
  filter: {
    priority: { lte: 2 },
    state: { type: { nin: ["completed", "canceled"] } },
    labels: { name: { eq: "Bug" } },
    team: { key: { eq: "ENG" } },
  },
});

// OR logic — issues assigned to Alice or Bob
const filtered = await client.issues({
  filter: {
    or: [
      { assignee: { email: { eq: "alice@company.com" } } },
      { assignee: { email: { eq: "bob@company.com" } } },
    ],
    state: { type: { eq: "started" } },
  },
});

// Full-text search
const results = await client.issueSearch("authentication bug");

// Issues updated in the last 24 hours
const recent = await client.issues({
  filter: {
    updatedAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() },
  },
  orderBy: "updatedAt",
  first: 100,
});
```

### Pattern 5: Type-Safe Error Handling
```typescript
import { LinearError, InvalidInputLinearError } from "@linear/sdk";

type Result<T> = { ok: true; data: T } | { ok: false; error: string; retryable: boolean };

async function safeCall<T>(fn: () => Promise<T>): Promise<Result<T>> {
  try {
    return { ok: true, data: await fn() };
  } catch (error) {
    if (error instanceof InvalidInputLinearError) {
      return { ok: false, error: `Invalid input: ${error.message}`, retryable: false };
    }
    if (error instanceof LinearError) {
      const retryable = error.status === 429 || error.status === 503;
      return { ok: false, error: `[${error.status}] ${error.message}`, retryable };
    }
    return { ok: false, error: String(error), retryable: false };
  }
}

// Usage
const result = await safeCall(() => client.issue("issue-uuid"));
if (result.ok) {
  console.log(result.data.title);
} else if (result.retryable) {
  console.warn("Transient error, retry:", result.error);
}
```

### Pattern 6: Custom GraphQL Client
Access the underlying `LinearGraphQLClient` for full control.

```typescript
const graphQLClient = client.client;

// Set custom headers
graphQLClient.setHeader("X-Request-Id", crypto.randomUUID());

// Raw query with variables
const data = await graphQLClient.rawRequest(`
  query Cycle($id: String!) {
    cycle(id: $id) {
      id name startsAt endsAt
      issues { nodes { identifier title state { name } } }
    }
  }
`, { id: "cycle-uuid" });

// Batch mutations
const batchResult = await graphQLClient.rawRequest(`
  mutation BatchUpdate {
    a: issueUpdate(id: "id1", input: { priority: 1 }) { success }
    b: issueUpdate(id: "id2", input: { priority: 1 }) { success }
    c: issueUpdate(id: "id3", input: { priority: 1 }) { success }
  }
`);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot read properties of null` | Nullable relation not checked | Use `(await issue.assignee)?.name` |
| `Type is not assignable` | SDK/TypeScript version mismatch | Update `@linear/sdk` to latest |
| `Promise rejection unhandled` | Missing try/catch on async | Wrap in `safeCall()` or `.catch()` |
| `Query complexity too high` | Too many nested relations | Use `rawRequest()` with flat field selection |

## Examples

### Create Issue with Full Metadata
```typescript
const teams = await client.teams();
const eng = teams.nodes.find(t => t.key === "ENG")!;
const states = await eng.states();
const todo = states.nodes.find(s => s.type === "unstarted")!;
const labels = await client.issueLabels({ filter: { name: { eq: "Bug" } } });

await client.createIssue({
  teamId: eng.id,
  title: "Login page crashes on Safari",
  description: "## Steps to reproduce\n1. Open login in Safari 17\n2. Click Sign in\n3. Crash",
  stateId: todo.id,
  priority: 1,
  labelIds: [labels.nodes[0].id],
  estimate: 3,
});
```

## Resources
- [SDK Getting Started](https://linear.app/developers/sdk)
- [SDK Data Fetching](https://linear.app/developers/sdk-fetching-and-modifying-data)
- [SDK Error Handling](https://linear.app/developers/sdk-errors)
- [Advanced Usage](https://linear.app/developers/advanced-usage)
- [GraphQL Filtering](https://linear.app/developers/filtering)
- [Pagination](https://linear.app/developers/pagination)
