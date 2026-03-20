---
name: linear-sdk-patterns
description: |
  TypeScript/JavaScript SDK patterns and best practices for Linear.
  Use when learning SDK idioms, implementing common patterns,
  or optimizing Linear API usage.
  Trigger with phrases like "linear SDK patterns", "linear best practices",
  "linear typescript", "linear API patterns", "linear SDK idioms".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear SDK Patterns

## Overview
Production patterns for the `@linear/sdk` TypeScript package. The SDK wraps Linear's GraphQL API with strongly-typed models, automatic pagination, and lazy-loading of relations.

## Prerequisites
- `@linear/sdk` installed (`npm install @linear/sdk`)
- TypeScript project with `strict: true`
- Understanding of async/await and GraphQL concepts

## Instructions

### Step 1: Client Singleton
Create one `LinearClient` instance and reuse it. Each instance holds an HTTP session.

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

// For OAuth-based multi-user apps:
const clientCache = new Map<string, LinearClient>();

export function getClientForUser(userId: string, accessToken: string): LinearClient {
  if (!clientCache.has(userId)) {
    clientCache.set(userId, new LinearClient({ accessToken }));
  }
  return clientCache.get(userId)!;
}
```

### Step 2: Type-Safe Error Handling
The SDK throws typed errors that can be caught and handled per-type.

```typescript
import { LinearError } from "@linear/sdk";

type Result<T> = { ok: true; data: T } | { ok: false; error: string; retryable: boolean };

async function safeCall<T>(fn: () => Promise<T>): Promise<Result<T>> {
  try {
    return { ok: true, data: await fn() };
  } catch (error) {
    if (error instanceof LinearError) {
      const retryable = error.status === 429 || error.status === 503;
      return { ok: false, error: `[${error.status}] ${error.message}`, retryable };
    }
    return { ok: false, error: String(error), retryable: false };
  }
}

// Usage
const client = getLinearClient();
const result = await safeCall(() => client.issue("issue-uuid"));
if (result.ok) {
  console.log(result.data.title);
} else if (result.retryable) {
  console.warn("Transient error, retry:", result.error);
} else {
  console.error("Permanent failure:", result.error);
}
```

### Step 3: Pagination Iterator
The SDK returns paginated connections with `nodes` and `pageInfo`. Build a generic async iterator.

```typescript
async function* paginate<T>(
  fetchPage: (cursor?: string) => Promise<{ nodes: T[]; pageInfo: { hasNextPage: boolean; endCursor: string } }>
): AsyncGenerator<T> {
  let cursor: string | undefined;
  let hasNext = true;

  while (hasNext) {
    const page = await fetchPage(cursor);
    for (const node of page.nodes) {
      yield node;
    }
    hasNext = page.pageInfo.hasNextPage;
    cursor = page.pageInfo.endCursor;
  }
}

// Usage: iterate all issues without loading everything into memory
const client = getLinearClient();
for await (const issue of paginate(cursor => client.issues({ first: 50, after: cursor }))) {
  console.log(`${issue.identifier}: ${issue.title}`);
}
```

### Step 4: Relation Loading Patterns
SDK models use lazy-loading for relations — accessing `.assignee` triggers a separate API call. Be intentional about when to resolve.

```typescript
// Pattern A: Resolve only when needed (lazy)
const issue = await client.issue("uuid");
const title = issue.title;  // No API call — already fetched
const assignee = await issue.assignee;  // API call happens here

// Pattern B: Batch resolve with raw GraphQL
const response = await client.client.rawRequest(`
  query {
    issues(first: 50, filter: { team: { key: { eq: "ENG" } } }) {
      nodes {
        id identifier title priority
        assignee { name email }
        state { name type }
        labels { nodes { name color } }
      }
    }
  }
`);
// All data fetched in one request — no lazy-loading overhead

// Pattern C: Pre-resolve in utility function
async function enrichIssue(issue: any) {
  const [assignee, state, team] = await Promise.all([
    issue.assignee,
    issue.state,
    issue.team,
  ]);
  return { ...issue, _assignee: assignee, _state: state, _team: team };
}
```

### Step 5: Filtering and Searching
```typescript
// Filter with comparators
const highPriority = await client.issues({
  first: 50,
  filter: {
    priority: { lte: 2 },  // Urgent (1) or High (2)
    state: { type: { nin: ["completed", "canceled"] } },
    team: { key: { eq: "ENG" } },
  },
});

// Full-text search
const results = await client.issueSearch("authentication bug");
for (const issue of results.nodes) {
  console.log(`${issue.identifier}: ${issue.title}`);
}

// Complex filter with OR logic
const filtered = await client.issues({
  filter: {
    or: [
      { assignee: { email: { eq: "alice@co.com" } } },
      { assignee: { email: { eq: "bob@co.com" } } },
    ],
    state: { type: { eq: "started" } },
  },
});
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot read properties of null` | Accessing unresolved nullable relation | Use optional chaining: `(await issue.assignee)?.name` |
| `Type is not assignable` | SDK version vs TypeScript mismatch | Update `@linear/sdk` and check `tsconfig` strict settings |
| `Promise rejection unhandled` | Missing try/catch on async call | Wrap in `safeCall()` or add `.catch()` |
| `Module not found: @linear/sdk` | Package not installed | Run `npm install @linear/sdk` |

## Examples

### Find Issues Across Teams
```typescript
const allTeams = await client.teams();
for (const team of allTeams.nodes) {
  const openCount = (await client.issues({
    filter: { team: { id: { eq: team.id } }, state: { type: { nin: ["completed", "canceled"] } } },
  })).nodes.length;
  console.log(`${team.name} (${team.key}): ${openCount} open issues`);
}
```

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
  description: "Steps to reproduce:\n1. Open login page in Safari 17\n2. Click 'Sign in with Google'\n3. Page crashes",
  stateId: todo.id,
  priority: 1,
  labelIds: [labels.nodes[0].id],
  estimate: 3,
});
```

## Output
- Thread-safe client singleton with multi-user OAuth support
- Type-safe `Result` wrapper for structured error handling
- Generic async pagination iterator for any Linear collection
- Relation loading patterns (lazy, batch, pre-resolve)
- Filter and search patterns with comparators and OR logic

## Resources
- [Linear SDK Getting Started](https://developers.linear.app/docs/sdk/getting-started)
- [GraphQL Schema Reference](https://developers.linear.app/docs/graphql/schema)
- [Filtering Guide](https://developers.linear.app/docs/graphql/filtering)

## Next Steps
Apply these patterns in `linear-core-workflow-a` for issue management.
