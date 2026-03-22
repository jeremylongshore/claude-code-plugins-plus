---
name: linear-cost-tuning
description: |
  Optimize Linear API usage, reduce unnecessary calls, and maximize
  efficiency within rate limit budgets.
  Trigger: "linear cost", "reduce linear API calls", "linear efficiency",
  "linear API usage", "optimize linear costs", "linear budget".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, api, cost-optimization]

---
# Linear Cost Tuning

## Overview
Optimize Linear API usage to stay within rate budgets and minimize infrastructure costs. Linear's API is free (no per-request billing), but rate limits (5,000 requests/hour, 250,000 complexity/hour) constrain throughput. Efficient patterns let you do more within these limits.

## Cost Factors

| Factor | Budget Impact | Optimization |
|--------|--------------|-------------|
| Request count | 5,000/hr limit | Batch operations, coalesce requests |
| Query complexity | 250,000/hr limit | Flat queries, small page sizes |
| Payload size | Bandwidth + latency | Select only needed fields |
| Polling frequency | Wastes budget | Replace with webhooks |
| Webhook volume | Processing costs | Filter by event type and team |

## Instructions

### Step 1: Audit Current Usage
```typescript
import { LinearClient } from "@linear/sdk";

class UsageTracker {
  private requests = 0;
  private totalComplexity = 0;
  private startTime = Date.now();

  track(complexity: number) {
    this.requests++;
    this.totalComplexity += complexity;
  }

  report() {
    const elapsedHours = (Date.now() - this.startTime) / 3600000;
    return {
      requests: this.requests,
      requestsPerHour: Math.round(this.requests / elapsedHours),
      totalComplexity: this.totalComplexity,
      complexityPerHour: Math.round(this.totalComplexity / elapsedHours),
      budgetUsed: {
        requests: `${Math.round((this.requests / elapsedHours / 5000) * 100)}%`,
        complexity: `${Math.round((this.totalComplexity / elapsedHours / 250000) * 100)}%`,
      },
    };
  }
}

const tracker = new UsageTracker();
```

### Step 2: Replace Polling with Webhooks
The single biggest optimization. A polling loop checking every minute uses 1,440 requests/day. A webhook uses zero.

```typescript
// BAD: Polling every 60 seconds (1,440 req/day, ~60 req/hr)
setInterval(async () => {
  const issues = await client.issues({
    first: 100,
    filter: { updatedAt: { gte: lastCheck } },
  });
  await syncIssues(issues.nodes);
  lastCheck = new Date().toISOString();
}, 60000);

// GOOD: Webhook receives updates in real-time (0 requests for monitoring)
app.post("/webhooks/linear", express.raw({ type: "*/*" }), (req, res) => {
  // Verify signature, process event
  const event = JSON.parse(req.body.toString());
  if (event.type === "Issue") {
    syncSingleIssue(event.data);
  }
  res.json({ ok: true });
});
```

### Step 3: Minimize Query Complexity
```typescript
// BAD: ~12,500 pts — deeply nested with large page
// issues(50) * (labels(50 default) * fields + comments(50) * user)
const expensive = `query {
  issues(first: 50) {
    nodes {
      id title
      assignee { name }
      labels { nodes { name } }
      comments(first: 10) { nodes { body user { name } } }
    }
  }
}`;

// GOOD: ~55 pts — flat fields only
const cheap = `query {
  issues(first: 50) {
    nodes { id identifier title priority estimate }
  }
}`;

// Fetch relations separately only when needed
const issueDetail = `query($id: String!) {
  issue(id: $id) {
    id identifier title description priority
    assignee { name email }
    state { name type }
    labels { nodes { name color } }
  }
}`;
```

### Step 4: Request Coalescing
Deduplicate concurrent identical requests.

```typescript
const inflight = new Map<string, Promise<any>>();

async function coalesce<T>(key: string, fn: () => Promise<T>): Promise<T> {
  if (inflight.has(key)) return inflight.get(key)!;
  const promise = fn().finally(() => inflight.delete(key));
  inflight.set(key, promise);
  return promise;
}

// 10 concurrent requests for same team = 1 actual API call
async function getTeam(teamKey: string) {
  return coalesce(`team:${teamKey}`, async () => {
    const result = await client.teams({ filter: { key: { eq: teamKey } } });
    return result.nodes[0];
  });
}
```

### Step 5: Cache with Smart TTLs
```typescript
const CACHE_TTLS = {
  teams: 600,        // 10 min — teams almost never change
  workflowStates: 1800, // 30 min — states rarely change
  labels: 600,       // 10 min — labels rarely change
  issues: 60,        // 1 min — issues change frequently
  viewer: 3600,      // 1 hr — your identity doesn't change
};

// Combined with webhook invalidation, even short TTLs
// dramatically reduce redundant requests
```

### Step 6: Filter Webhook Events
Skip irrelevant events to reduce processing costs.

```typescript
async function processEvent(event: any): Promise<void> {
  // Skip bot/automation events to avoid loops
  if (event.actor?.type === "application") return;

  // Skip trivial field updates (e.g., sortOrder changes)
  if (event.type === "Issue" && event.action === "update") {
    const significantFields = ["stateId", "assigneeId", "priority", "title"];
    const changedFields = Object.keys(event.updatedFrom ?? {});
    if (!changedFields.some(f => significantFields.includes(f))) return;
  }

  // Skip specific teams if not relevant
  const relevantTeamKeys = ["ENG", "PRODUCT"];
  if (event.data?.team?.key && !relevantTeamKeys.includes(event.data.team.key)) return;

  // Process significant event
  await handleEvent(event);
}
```

### Step 7: Incremental Sync Pattern
```typescript
// Instead of fetching ALL issues every sync:
// Sort by updatedAt, stop when you reach already-synced data

async function incrementalSync(client: LinearClient, lastSyncTime: string) {
  let cursor: string | undefined;
  let synced = 0;

  while (true) {
    const issues = await client.issues({
      first: 100,
      after: cursor,
      filter: { updatedAt: { gte: lastSyncTime } },
      orderBy: "updatedAt",
    });

    for (const issue of issues.nodes) {
      await upsertLocally(issue);
      synced++;
    }

    if (!issues.pageInfo.hasNextPage) break;
    cursor = issues.pageInfo.endCursor;
  }

  console.log(`Synced ${synced} issues since ${lastSyncTime}`);
  return synced;
}
```

## Optimization Checklist
- [ ] Replace all polling with webhooks
- [ ] Implement request caching (static data: 10-30 min TTL)
- [ ] Add request coalescing for concurrent identical calls
- [ ] Filter webhook events (skip bots, trivial updates, irrelevant teams)
- [ ] Keep query complexity under 500 pts per query
- [ ] Use `rawRequest()` for exact field selection
- [ ] Sort by `updatedAt` for incremental sync
- [ ] Batch mutations (20 per GraphQL request)
- [ ] Cache teams/states/labels with webhook invalidation

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limit hit frequently | Too many requests | Implement coalescing + caching |
| Stale cache data | TTL too long | Use webhook-driven invalidation |
| High complexity queries | Nested relations | Flatten with `rawRequest()`, fetch relations lazily |
| Webhook processing overload | Unfiltered events | Add type/team/field filtering |

## Resources
- [Linear Rate Limiting](https://linear.app/developers/rate-limiting)
- [Linear Best Practices](https://linear.app/developers/graphql)
- [Webhooks](https://linear.app/developers/webhooks)
