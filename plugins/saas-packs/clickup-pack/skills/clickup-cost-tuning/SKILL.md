---
name: clickup-cost-tuning
description: |
  Optimize ClickUp API usage costs through plan selection, request reduction,
  caching, and usage monitoring.
  Trigger: "clickup cost", "clickup billing", "reduce clickup usage",
  "clickup pricing", "clickup plan comparison", "clickup API usage".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Cost Tuning

## Overview

ClickUp charges per-seat, not per-API-call. However, rate limits constrain throughput per plan tier. Optimizing API usage means reducing request count to stay within rate limits and avoid needing plan upgrades.

## ClickUp Pricing (Per Member/Month)

| Plan | Price | Rate Limit | Key API Features |
|------|-------|-----------|------------------|
| Free Forever | $0 | 100 req/min | Full API access, 100 uses of automations |
| Unlimited | $7/member | 100 req/min | Unlimited storage, integrations |
| Business | $12/member | 100 req/min | Custom fields, time tracking, goals |
| Business Plus | $19/member | 1,000 req/min | Custom role creation, admin training |
| Enterprise | Custom | 10,000 req/min | SSO/SAML, advanced permissions, dedicated support |

## Request Reduction Strategies

### 1. Cache Workspace Structure

Spaces, folders, and lists change rarely. Cache them aggressively.

```typescript
import { LRUCache } from 'lru-cache';

const structureCache = new LRUCache<string, any>({
  max: 500,
  ttl: 300000, // 5 minutes for hierarchy data
});

async function getCachedSpaces(teamId: string) {
  const key = `spaces:${teamId}`;
  let spaces = structureCache.get(key);
  if (!spaces) {
    const data = await clickupRequest(`/team/${teamId}/space?archived=false`);
    spaces = data.spaces;
    structureCache.set(key, spaces);
  }
  return spaces;
}
```

### 2. Use Pagination Efficiently

Get Tasks returns max 100 per page. Fetch only what you need.

```typescript
// Bad: fetch all pages when you only need recent tasks
// Good: use filters to minimize pages
async function getRecentTasks(listId: string, limit = 25) {
  return clickupRequest(`/list/${listId}/task?${new URLSearchParams({
    page: '0',
    order_by: 'updated',
    reverse: 'true',
    subtasks: 'true',
    include_closed: 'false',
  })}`);
}
```

### 3. Batch with Custom Fields

Set custom fields during task creation instead of separate calls.

```typescript
// Bad: 3 API calls (create + 2 custom field updates)
const task = await createTask(listId, { name: 'Task' });
await setCustomField(task.id, field1Id, value1);
await setCustomField(task.id, field2Id, value2);

// Good: 1 API call (custom fields in create body)
await createTask(listId, {
  name: 'Task',
  custom_fields: [
    { id: field1Id, value: value1 },
    { id: field2Id, value: value2 },
  ],
});
```

### 4. Use Webhooks Instead of Polling

```typescript
// Bad: poll every 30 seconds (2 req/min wasted)
setInterval(() => checkForUpdates(), 30000);

// Good: register webhook, process events on-demand (0 polling requests)
await clickupRequest(`/team/${teamId}/webhook`, {
  method: 'POST',
  body: JSON.stringify({
    endpoint: 'https://myapp.com/webhooks/clickup',
    events: ['taskUpdated', 'taskCreated'],
  }),
});
```

## Usage Monitoring

```typescript
class ClickUpUsageTracker {
  private requestLog: Array<{ timestamp: number; endpoint: string }> = [];

  track(endpoint: string): void {
    this.requestLog.push({ timestamp: Date.now(), endpoint });

    // Keep only last hour
    const cutoff = Date.now() - 3600000;
    this.requestLog = this.requestLog.filter(r => r.timestamp > cutoff);
  }

  getRequestsPerMinute(): number {
    const oneMinAgo = Date.now() - 60000;
    return this.requestLog.filter(r => r.timestamp > oneMinAgo).length;
  }

  getTopEndpoints(n = 5): Array<{ endpoint: string; count: number }> {
    const counts = new Map<string, number>();
    for (const r of this.requestLog) {
      counts.set(r.endpoint, (counts.get(r.endpoint) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
      .map(([endpoint, count]) => ({ endpoint, count }));
  }

  needsUpgrade(): boolean {
    return this.getRequestsPerMinute() > 80; // 80% of Free tier limit
  }
}
```

## Cost Decision Matrix

| Monthly Requests | Recommended Plan | Rationale |
|-----------------|-----------------|-----------|
| < 144,000 | Free Forever | 100/min * 60min * 24h = 144K/day max |
| 100-1000 req/min sustained | Business Plus | 10x rate limit increase |
| > 1000 req/min sustained | Enterprise | 10,000 req/min + dedicated support |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Constant 429 errors | Hit rate ceiling | Implement queuing or upgrade |
| Cache stale data | TTL too long | Invalidate via webhooks |
| Redundant API calls | No deduplication | Use DataLoader batching |
| Polling overhead | No webhook setup | Switch to event-driven |

## Resources

- [ClickUp Pricing](https://clickup.com/pricing)
- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)

## Next Steps

For architecture patterns, see `clickup-reference-architecture`.
