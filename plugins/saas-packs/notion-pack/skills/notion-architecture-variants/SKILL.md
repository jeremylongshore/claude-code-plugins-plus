---
name: notion-architecture-variants
description: |
  Choose and implement Notion integration architectures for different scales.
  Use when designing new Notion integrations, choosing between simple vs service
  architectures, or planning migration paths for Notion applications.
  Trigger with phrases like "notion architecture", "notion blueprint",
  "how to structure notion", "notion project layout", "notion design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Architecture Variants

## Overview
Three validated architecture patterns for Notion integrations at different scales, using real `@notionhq/client` patterns and Notion's actual API constraints.

## Prerequisites
- Understanding of your scale requirements
- `@notionhq/client` installed
- Notion API familiarity (see `notion-core-workflow-a`)

## Instructions

### Variant A: Direct Integration (Script/Small App)
**Best for:** Scripts, small tools, internal dashboards, < 1,000 API calls/day.

```
my-notion-tool/
├── src/
│   ├── index.ts               # Entry point
│   └── notion.ts              # All Notion logic in one file
├── .env
└── package.json
```

```typescript
// src/notion.ts — Everything in one file
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const DB_ID = process.env.NOTION_DB_ID!;

export async function getTasks(status?: string) {
  const filter = status
    ? { property: 'Status', select: { equals: status } }
    : undefined;

  return notion.databases.query({ database_id: DB_ID, filter });
}

export async function createTask(title: string, status: string) {
  return notion.pages.create({
    parent: { database_id: DB_ID },
    properties: {
      Name: { title: [{ text: { content: title } }] },
      Status: { select: { name: status } },
    },
  });
}

export async function updateTaskStatus(pageId: string, status: string) {
  return notion.pages.update({
    page_id: pageId,
    properties: { Status: { select: { name: status } } },
  });
}
```

**Characteristics:**
- Single file, no abstraction layers
- Direct `@notionhq/client` calls
- SDK handles rate limiting and retries
- No caching (acceptable at low volume)

---

### Variant B: Service Layer (Medium App)
**Best for:** Web apps, APIs, team tools, 1,000-50,000 API calls/day.

```
my-notion-app/
├── src/
│   ├── notion/
│   │   ├── client.ts           # Singleton client
│   │   ├── extractors.ts       # Property value helpers
│   │   └── errors.ts           # Error classification
│   ├── services/
│   │   ├── task.service.ts     # Business logic
│   │   └── sync.service.ts     # Background sync
│   ├── cache/
│   │   └── notion-cache.ts     # LRU cache layer
│   ├── api/
│   │   ├── routes.ts           # HTTP endpoints
│   │   └── webhooks.ts         # Webhook handler
│   └── index.ts
├── tests/
│   ├── task.service.test.ts
│   └── integration.test.ts
└── package.json
```

```typescript
// src/services/task.service.ts
import { getNotionClient } from '../notion/client';
import { extractTitle, extractSelect } from '../notion/extractors';
import { notionCache } from '../cache/notion-cache';
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

export class TaskService {
  private notion = getNotionClient();
  private dbId: string;

  constructor(dbId: string) {
    this.dbId = dbId;
  }

  async list(statusFilter?: string) {
    const cacheKey = `tasks:${this.dbId}:${statusFilter ?? 'all'}`;
    const cached = notionCache.get(cacheKey);
    if (cached) return { data: cached, source: 'cache' as const };

    const response = await queue.add(() =>
      this.notion.databases.query({
        database_id: this.dbId,
        filter: statusFilter
          ? { property: 'Status', select: { equals: statusFilter } }
          : undefined,
        sorts: [{ property: 'Created', direction: 'descending' }],
        page_size: 100,
      })
    );

    const tasks = response!.results
      .filter((p: any) => 'properties' in p)
      .map((page: any) => ({
        id: page.id,
        title: extractTitle(page, 'Name'),
        status: extractSelect(page, 'Status'),
        url: page.url,
      }));

    notionCache.set(cacheKey, tasks);
    return { data: tasks, source: 'live' as const };
  }

  async create(title: string, status?: string) {
    const properties: any = {
      Name: { title: [{ text: { content: title } }] },
    };
    if (status) properties.Status = { select: { name: status } };

    const result = await queue.add(() =>
      this.notion.pages.create({
        parent: { database_id: this.dbId },
        properties,
      })
    );

    // Invalidate cache
    notionCache.clear(`tasks:${this.dbId}:`);
    return result;
  }
}
```

**Characteristics:**
- Separated concerns (client, service, cache, API)
- Request queuing at 3/s with p-queue
- LRU caching for reads
- Cache invalidation on writes
- Mockable services for testing

---

### Variant C: Event-Driven (High Scale)
**Best for:** Multi-workspace integrations, >50,000 API calls/day, SaaS products.

```
notion-platform/
├── services/
│   ├── api-gateway/            # User-facing API
│   ├── notion-worker/          # Processes Notion API calls
│   ├── webhook-receiver/       # Handles incoming webhooks
│   └── sync-scheduler/         # Schedules periodic syncs
├── shared/
│   ├── notion-client/          # Shared client library
│   ├── queue/                  # Message queue adapter
│   └── cache/                  # Distributed cache
└── infrastructure/
    ├── docker-compose.yml
    └── k8s/
```

```typescript
// services/notion-worker/worker.ts
// Processes Notion API calls from a message queue

import { Client } from '@notionhq/client';
import PQueue from 'p-queue';

interface NotionJob {
  id: string;
  workspaceToken: string; // Each workspace has its own rate limit
  operation: 'query' | 'create' | 'update';
  payload: any;
  priority: 'high' | 'normal' | 'low';
}

// Per-workspace rate limiting
const workspaceQueues = new Map<string, PQueue>();

function getQueue(workspaceId: string): PQueue {
  if (!workspaceQueues.has(workspaceId)) {
    workspaceQueues.set(workspaceId, new PQueue({
      concurrency: 3,
      interval: 1000,
      intervalCap: 3,
    }));
  }
  return workspaceQueues.get(workspaceId)!;
}

async function processJob(job: NotionJob) {
  const notion = new Client({ auth: job.workspaceToken });
  const queue = getQueue(job.workspaceToken);

  return queue.add(async () => {
    switch (job.operation) {
      case 'query':
        return notion.databases.query(job.payload);
      case 'create':
        return notion.pages.create(job.payload);
      case 'update':
        return notion.pages.update(job.payload);
    }
  }, { priority: job.priority === 'high' ? 0 : job.priority === 'normal' ? 1 : 2 });
}
```

**Characteristics:**
- Per-workspace rate limiting (each OAuth token = its own 3 req/s)
- Message queue decouples API calls from user requests
- Horizontal scaling of workers
- Webhook-driven instead of polling
- Distributed caching (Redis)
- Priority queuing (critical reads before bulk syncs)

---

### Decision Matrix

| Factor | Direct (A) | Service Layer (B) | Event-Driven (C) |
|--------|-----------|-------------------|-------------------|
| API calls/day | < 1,000 | 1,000-50,000 | 50,000+ |
| Workspaces | 1 | 1 | Many (OAuth) |
| Team size | 1-2 | 2-10 | 5+ |
| Caching | None | LRU | Redis |
| Rate limiting | SDK built-in | p-queue | Per-workspace queues |
| Complexity | Minimal | Moderate | High |
| Time to build | Hours | Days | Weeks |

### Migration Path
```
Direct → Service Layer:
1. Extract Notion calls to services/
2. Add LRU cache
3. Add p-queue for rate limiting
4. Add error classification
5. Write unit tests with mocked client

Service Layer → Event-Driven:
1. Add message queue (Bull, SQS, Pub/Sub)
2. Move Notion calls to worker process
3. Switch to Redis for distributed cache
4. Implement per-workspace rate limiting
5. Add webhook receiver service
```

## Output
- Architecture variant selected based on scale requirements
- Project structure implemented
- Appropriate caching and rate limiting in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Over-engineering | Wrong variant | Start with A, graduate to B when needed |
| Rate limits in production | Missing queue | Add p-queue (B) or worker queue (C) |
| Stale data | No cache invalidation | Invalidate on writes or use webhooks |
| Multi-workspace rate limits | Shared queue | Per-workspace queues (C) |

## Examples

### Quick Variant Check
```typescript
function recommendVariant(dailyCalls: number, workspaces: number): string {
  if (workspaces > 1) return 'C: Event-Driven (multi-workspace requires per-workspace limits)';
  if (dailyCalls > 50_000) return 'C: Event-Driven';
  if (dailyCalls > 1_000) return 'B: Service Layer';
  return 'A: Direct Integration';
}
```

## Resources
- [Notion API Introduction](https://developers.notion.com/reference/intro)
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [Notion OAuth Authorization](https://developers.notion.com/docs/authorization)

## Next Steps
For common anti-patterns, see `notion-known-pitfalls`.
