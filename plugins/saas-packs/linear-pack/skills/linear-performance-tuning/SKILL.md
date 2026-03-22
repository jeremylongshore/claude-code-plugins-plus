---
name: linear-performance-tuning
description: |
  Optimize Linear API queries, caching, and batching for performance.
  Use when improving response times, reducing API calls,
  or implementing caching strategies for Linear data.
  Trigger: "linear performance", "optimize linear", "linear caching",
  "linear slow queries", "speed up linear", "linear N+1".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, performance]

---
# Linear Performance Tuning

## Overview
Optimize Linear API usage for minimal latency and efficient resource consumption. The three main levers are: (1) query flattening to avoid N+1 and reduce complexity, (2) caching static data with webhook-driven invalidation, and (3) batching mutations into single GraphQL requests.

**Key numbers:**
- Query complexity budget: 250,000 pts/hour, max 10,000 per query
- Each property: 0.1 pt, each object: 1 pt, connections: multiply by `first`
- Best practice: sort by `updatedAt` to get fresh data first

## Prerequisites
- Working Linear integration with `@linear/sdk`
- Understanding of GraphQL query structure
- Optional: Redis for distributed caching

## Instructions

### Step 1: Eliminate N+1 Queries
The SDK lazy-loads relations. Accessing `.assignee` on 50 issues makes 50 separate API calls.

```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// BAD: N+1 — 1 query for issues + 50 for assignees + 50 for states = 101 requests
const issues = await client.issues({ first: 50 });
for (const i of issues.nodes) {
  const assignee = await i.assignee;  // API call!
  const state = await i.state;        // API call!
  console.log(`${i.identifier}: ${assignee?.name} [${state?.name}]`);
}

// GOOD: 1 request — use rawRequest with exact field selection
const response = await client.client.rawRequest(`
  query TeamDashboard($teamId: String!) {
    team(id: $teamId) {
      issues(first: 50, orderBy: updatedAt) {
        nodes {
          id identifier title priority estimate updatedAt
          assignee { name email }
          state { name type }
          labels { nodes { name color } }
          project { name }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
`, { teamId: "team-uuid" });
// Complexity: ~50 * (10 fields * 0.1 + 4 objects) = ~275 pts
```

### Step 2: Cache Static Data
Teams, workflow states, and labels change rarely. Cache them with appropriate TTLs.

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

  invalidate(key: string): void {
    this.store.delete(key);
  }
}

const cache = new LinearCache();

// Teams: 10 minute TTL (almost never change)
async function getTeams(client: LinearClient) {
  const cached = cache.get<any[]>("teams");
  if (cached) return cached;
  const teams = await client.teams();
  cache.set("teams", teams.nodes, 600);
  return teams.nodes;
}

// Workflow states: 30 minute TTL (rarely change)
async function getStates(client: LinearClient, teamId: string) {
  const key = `states:${teamId}`;
  const cached = cache.get<any[]>(key);
  if (cached) return cached;
  const team = await client.team(teamId);
  const states = await team.states();
  cache.set(key, states.nodes, 1800);
  return states.nodes;
}

// Labels: 10 minute TTL
async function getLabels(client: LinearClient) {
  const cached = cache.get<any[]>("labels");
  if (cached) return cached;
  const labels = await client.issueLabels();
  cache.set("labels", labels.nodes, 600);
  return labels.nodes;
}
```

### Step 3: Webhook-Driven Cache Invalidation
Replace polling with webhooks. Invalidate cache when relevant entities change.

```typescript
function handleCacheInvalidation(event: { type: string; action: string; data: any }) {
  switch (event.type) {
    case "Issue":
      cache.invalidate(`issue:${event.data.id}`);
      break;
    case "WorkflowState":
      cache.invalidate(`states:${event.data.teamId}`);
      break;
    case "IssueLabel":
      cache.invalidate("labels");
      break;
    case "Team":
      cache.invalidate("teams");
      break;
  }
}
```

### Step 4: Batch Mutations
Combine multiple mutations into one GraphQL request.

```typescript
// Instead of 100 separate updateIssue calls:
async function batchUpdatePriority(
  client: LinearClient,
  issueUpdates: Array<{ id: string; priority: number }>
) {
  const chunkSize = 20; // Keep complexity manageable
  for (let i = 0; i < issueUpdates.length; i += chunkSize) {
    const chunk = issueUpdates.slice(i, i + chunkSize);
    const mutations = chunk.map((u, j) =>
      `u${j}: issueUpdate(id: "${u.id}", input: { priority: ${u.priority} }) { success }`
    ).join("\n");

    await client.client.rawRequest(`mutation { ${mutations} }`);
  }
}

// Batch issue creation
async function batchCreate(
  client: LinearClient,
  teamId: string,
  issues: Array<{ title: string; priority?: number }>
) {
  const mutations = issues.map((issue, i) =>
    `c${i}: issueCreate(input: {
      teamId: "${teamId}",
      title: "${issue.title.replace(/"/g, '\\"')}",
      priority: ${issue.priority ?? 3}
    }) { success issue { id identifier } }`
  ).join("\n");

  return client.client.rawRequest(`mutation { ${mutations} }`);
}
```

### Step 5: Efficient Pagination
```typescript
// Stream all issues without loading everything into memory
async function* paginateIssues(
  client: LinearClient,
  teamId: string,
  pageSize = 50
) {
  let cursor: string | undefined;
  let hasNext = true;

  while (hasNext) {
    const result = await client.issues({
      first: pageSize,
      after: cursor,
      filter: { team: { id: { eq: teamId } } },
      orderBy: "updatedAt", // Fresh data first
    });

    yield result.nodes;
    hasNext = result.pageInfo.hasNextPage;
    cursor = result.pageInfo.endCursor;
  }
}

// Process in batches
for await (const batch of paginateIssues(client, "team-uuid")) {
  console.log(`Processing ${batch.length} issues`);
}

// Incremental sync: only fetch issues updated since last sync
const lastSync = "2026-03-20T00:00:00Z";
const updated = await client.issues({
  first: 100,
  filter: { updatedAt: { gte: lastSync } },
  orderBy: "updatedAt",
});
```

### Step 6: Request Coalescing
Deduplicate concurrent identical requests.

```typescript
const inflight = new Map<string, Promise<any>>();

async function coalesce<T>(key: string, fn: () => Promise<T>): Promise<T> {
  if (inflight.has(key)) return inflight.get(key)!;
  const promise = fn().finally(() => inflight.delete(key));
  inflight.set(key, promise);
  return promise;
}

// Multiple components requesting same team data simultaneously = 1 API call
const team = await coalesce("team:ENG", () =>
  client.teams({ filter: { key: { eq: "ENG" } } }).then(r => r.nodes[0])
);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Query complexity too high` | Deep nesting + large `first` | Use `rawRequest()` with flat fields, `first: 50` |
| HTTP 429 | Burst exceeding rate budget | Add request queue with 100ms spacing |
| Stale cache | TTL too long | Shorten TTL or use webhook invalidation |
| Timeout | Query spanning too many records | Paginate with `first: 50` + cursor |

## Examples

### Performance Benchmark
```typescript
async function benchmark(label: string, fn: () => Promise<any>) {
  const start = Date.now();
  await fn();
  console.log(`${label}: ${Date.now() - start}ms`);
}

await benchmark("Cold teams", () => client.teams());
await benchmark("Cached teams", () => getTeams(client));
await benchmark("50 issues (SDK)", () => client.issues({ first: 50 }));
await benchmark("50 issues (raw)", () => client.client.rawRequest(
  `query { issues(first: 50) { nodes { id identifier title priority } } }`
));
```

## Resources
- [Linear Best Practices](https://linear.app/developers/graphql)
- [Rate Limiting](https://linear.app/developers/rate-limiting)
- [Pagination](https://linear.app/developers/pagination)
- [Filtering](https://linear.app/developers/filtering)
