---
name: linear-performance-tuning
description: |
  Optimize Linear API queries and caching for better performance.
  Use when improving response times, reducing API calls,
  or implementing caching strategies.
  Trigger with phrases like "linear performance", "optimize linear",
  "linear caching", "linear slow queries", "speed up linear".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Performance Tuning

## Overview
Optimize Linear API usage for minimal latency and efficient resource consumption. Linear uses complexity-based rate limiting for GraphQL — deeply nested queries with large page sizes consume more budget. Caching, batching, and query flattening are the main levers.

## Prerequisites
- Working Linear integration
- Understanding of GraphQL query structure
- Caching infrastructure (Redis or in-memory) recommended

## Instructions

### Step 1: Query Optimization
Fetch only the fields you need. Every nested relation adds to query complexity.

```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// BAD: fetching all issues with deep nesting
// const issues = await client.issues({ first: 250 });
// for (const i of issues.nodes) {
//   const assignee = await i.assignee;      // N+1 query
//   const project = await i.project;        // N+1 query
//   const labels = await i.labels();        // N+1 query
// }

// GOOD: use GraphQL directly for precise field selection
const response = await client.client.rawRequest(`
  query RecentIssues($teamId: String!) {
    team(id: $teamId) {
      issues(first: 50, orderBy: updatedAt) {
        nodes {
          id
          identifier
          title
          state { name type }
          assignee { name }
          priority
          updatedAt
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
`, { teamId: "team-uuid" });
```

### Step 2: Implement Caching Layer
Cache frequently accessed data that changes infrequently (teams, workflow states, labels).

```typescript
interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

class LinearCache {
  private store = new Map<string, CacheEntry<any>>();

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry || Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data;
  }

  set<T>(key: string, data: T, ttlSeconds: number): void {
    this.store.set(key, { data, expiresAt: Date.now() + ttlSeconds * 1000 });
  }
}

const cache = new LinearCache();

// Cache team data for 10 minutes (rarely changes)
async function getTeams(client: LinearClient) {
  const cached = cache.get<any[]>("teams");
  if (cached) return cached;

  const teams = await client.teams();
  const data = teams.nodes;
  cache.set("teams", data, 600);
  return data;
}

// Cache workflow states for 30 minutes (almost never changes)
async function getWorkflowStates(client: LinearClient, teamId: string) {
  const key = `states:${teamId}`;
  const cached = cache.get<any[]>(key);
  if (cached) return cached;

  const team = await client.team(teamId);
  const states = await team.states();
  cache.set(key, states.nodes, 1800);
  return states.nodes;
}

// Cache labels for 10 minutes
async function getLabels(client: LinearClient) {
  const cached = cache.get<any[]>("labels");
  if (cached) return cached;

  const labels = await client.issueLabels();
  cache.set("labels", labels.nodes, 600);
  return labels.nodes;
}
```

### Step 3: Request Batching
Batch multiple operations into single GraphQL requests.

```typescript
// Instead of N separate mutations for bulk updates:
async function batchUpdatePriority(issueIds: string[], priority: number) {
  // Build a single GraphQL request with multiple mutations
  const mutations = issueIds.map((id, i) =>
    `update${i}: issueUpdate(id: "${id}", input: { priority: ${priority} }) { success }`
  ).join("\n");

  const query = `mutation BatchUpdate { ${mutations} }`;
  await client.client.rawRequest(query);
}

// Batch create issues
async function batchCreateIssues(
  teamId: string,
  issues: Array<{ title: string; description?: string; priority?: number }>
) {
  const mutations = issues.map((issue, i) =>
    `create${i}: issueCreate(input: {
      teamId: "${teamId}"
      title: "${issue.title.replace(/"/g, '\\"')}"
      ${issue.description ? `description: "${issue.description.replace(/"/g, '\\"')}"` : ""}
      ${issue.priority !== undefined ? `priority: ${issue.priority}` : ""}
    }) { success issue { id identifier } }`
  ).join("\n");

  return client.client.rawRequest(`mutation BatchCreate { ${mutations} }`);
}
```

### Step 4: Pagination with Cursor Caching
```typescript
async function* paginateIssues(client: LinearClient, teamId: string, pageSize = 50) {
  let hasNextPage = true;
  let cursor: string | undefined;

  while (hasNextPage) {
    const result = await client.issues({
      first: pageSize,
      after: cursor,
      filter: { team: { id: { eq: teamId } } },
    });

    yield result.nodes;

    hasNextPage = result.pageInfo.hasNextPage;
    cursor = result.pageInfo.endCursor;
  }
}

// Usage: process all issues without loading everything into memory
for await (const batch of paginateIssues(client, "team-uuid")) {
  console.log(`Processing batch of ${batch.length} issues`);
  // Process batch...
}
```

### Step 5: Webhook-Driven Cache Invalidation
Instead of polling, use webhooks to invalidate cached data when changes occur.

```typescript
// Webhook handler that invalidates relevant cache keys
function handleWebhookEvent(event: { type: string; action: string; data: any }) {
  switch (event.type) {
    case "Issue":
      cache.set(`issue:${event.data.id}`, null, 0);  // Invalidate
      break;
    case "WorkflowState":
      cache.set(`states:${event.data.teamId}`, null, 0);
      break;
    case "IssueLabel":
      cache.set("labels", null, 0);
      break;
  }
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Query complexity too high` | Deep nesting or large `first` value | Reduce page size to 50, flatten nested queries |
| `429 Too Many Requests` | Burst of requests exceeding rate limit | Add request queue with 100ms spacing between calls |
| Stale cache data | TTL too long for volatile data | Shorten TTL or use webhook-driven invalidation |
| `Timeout` on large queries | Query spanning too many records | Paginate with `first: 50` and cursor-based iteration |

## Examples

### Performance Benchmark Script
```typescript
async function benchmark(label: string, fn: () => Promise<any>): Promise<void> {
  const start = Date.now();
  await fn();
  console.log(`${label}: ${Date.now() - start}ms`);
}

await benchmark("Cold fetch teams", () => client.teams());
await benchmark("Cached fetch teams", () => getTeams(client));
await benchmark("50 issues", () => client.issues({ first: 50 }));
await benchmark("250 issues (paginated)", async () => {
  for await (const _ of paginateIssues(client, "team-id")) {}
});
```

## Output
- Optimized GraphQL queries fetching only required fields
- In-memory cache for teams, workflow states, and labels with TTL
- Batch mutations reducing N API calls to 1
- Async generator for memory-efficient pagination
- Webhook-driven cache invalidation eliminating polling

## Resources
- [Linear GraphQL Best Practices](https://developers.linear.app/docs/graphql/best-practices)
- [Query Complexity](https://developers.linear.app/docs/graphql/complexity)
- [Pagination Guide](https://developers.linear.app/docs/graphql/pagination)

## Next Steps
Optimize costs with `linear-cost-tuning`.
