---
name: miro-reference-architecture
description: 'Implement a production-ready reference architecture for Miro REST API
  v2

  integrations with layered design, caching, and event processing.

  Trigger with phrases like "miro architecture", "miro project structure",

  "how to organize miro integration", "miro design patterns".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- miro
- architecture
- design
compatibility: Designed for Claude Code
---
# Miro Reference Architecture

## Overview

Production-ready architecture for Miro REST API v2 integrations. Layered design with a board service, item factory, webhook event processor, and caching layer.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    API / UI Layer                         │
│   Express routes, Next.js API routes, CLI commands       │
├──────────────────────────────────────────────────────────┤
│                   Service Layer                          │
│   BoardService, ItemService, SyncService                 │
│   (business logic, orchestration, validation)            │
├──────────────────────────────────────────────────────────┤
│                  Miro Client Layer                        │
│   MiroApiClient (REST v2), TokenManager (OAuth 2.0)      │
│   ItemFactory (typed creation), ConnectorBuilder          │
├──────────────────────────────────────────────────────────┤
│                Infrastructure Layer                       │
│   Cache (LRU/Redis), Queue (PQueue), Monitor (metrics)   │
│   WebhookProcessor (signature + idempotency)             │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
            https://api.miro.com/v2/
```

## Project Structure

```
src/
├── miro/
│   ├── client.ts              # MiroApiClient — wraps fetch with auth, retries, monitoring
│   ├── token-manager.ts       # OAuth 2.0 token lifecycle (refresh, storage)
│   ├── item-factory.ts        # Typed item creation (sticky notes, shapes, cards, etc.)
│   ├── connector-builder.ts   # Fluent API for creating connectors
│   ├── types.ts               # TypeScript types for all Miro v2 responses
│   └── errors.ts              # MiroApiError, MiroAuthError, MiroRateLimitError
├── services/
│   ├── board-service.ts       # Board CRUD + member management
│   ├── item-service.ts        # Item CRUD + tag operations
│   ├── sync-service.ts        # Two-way sync between Miro and your database
│   └── search-service.ts      # Find items by content, type, or tag
├── webhooks/
│   ├── handler.ts             # Express/serverless webhook endpoint
│   ├── processor.ts           # Event routing and processing
│   └── idempotency.ts         # Duplicate event prevention
├── cache/
│   ├── board-cache.ts         # Board metadata cache
│   └── item-cache.ts          # Item data cache with webhook invalidation
├── config/
│   ├── miro.ts                # Environment-based Miro configuration
│   └── index.ts               # Config loader
└── monitoring/
    ├── metrics.ts             # Prometheus counters/histograms for Miro API
    └── health.ts              # Health check endpoint
```

## Core Components

### MiroApiClient

```typescript
// src/miro/client.ts
export class MiroApiClient {
  constructor(
    private tokenManager: TokenManager,
    private cache: ItemCache,
    private monitor: MiroMetrics,
  ) {}

  async fetch<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const token = await this.tokenManager.getValidToken();
    const start = performance.now();

    const response = await fetch(`https://api.miro.com${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });

    const duration = performance.now() - start;
    this.monitor.recordRequest(method, path, response.status, duration);
    this.monitor.updateRateLimit(response);

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') ?? '5', 10);
      throw new MiroRateLimitError(retryAfter);
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new MiroApiError(response.status, error.message, error.code);
    }

    if (response.status === 204) return null as T;
    return response.json() as T;
  }

  // Paginated fetch — returns all pages
  async fetchAll<T>(path: string, limit = 50): Promise<T[]> {
    const items: T[] = [];
    let cursor: string | undefined;

    do {
      const params = new URLSearchParams({ limit: String(limit) });
      if (cursor) params.set('cursor', cursor);

      const result = await this.fetch<PaginatedResponse<T>>(
        `${path}?${params}`
      );
      items.push(...result.data);
      cursor = result.cursor;
    } while (cursor);

    return items;
  }
}
```

### Board Service

```typescript
// src/services/board-service.ts
export class BoardService {
  constructor(
    private api: MiroApiClient,
    private cache: BoardCache,
  ) {}

  async getBoard(boardId: string): Promise<MiroBoard> {
    const cached = await this.cache.get(boardId);
    if (cached) return cached;

    const board = await this.api.fetch<MiroBoard>(`/v2/boards/${boardId}`);
    await this.cache.set(boardId, board, 120);  // 2 min TTL
    return board;
  }

  async createBoard(params: CreateBoardParams): Promise<MiroBoard> {
    return this.api.fetch<MiroBoard>('/v2/boards', 'POST', {
      name: params.name,
      description: params.description,
      teamId: params.teamId,
      policy: {
        sharingPolicy: { access: params.access ?? 'private' },
        permissionsPolicy: { sharingAccess: 'team_members_and_collaborators' },
      },
    });
  }

  async shareBoard(boardId: string, emails: string[], role: BoardRole): Promise<void> {
    await this.api.fetch(`/v2/boards/${boardId}/members`, 'POST', {
      emails,
      role,  // 'viewer' | 'commenter' | 'editor' | 'coowner'
    });
  }

  async getMembers(boardId: string): Promise<BoardMember[]> {
    return this.api.fetchAll(`/v2/boards/${boardId}/members`);
  }
}
```

### Webhook Processor

```typescript
// src/webhooks/processor.ts
export class WebhookProcessor {
  private handlers = new Map<string, EventHandler[]>();

  on(eventType: string, handler: EventHandler): void {
    const existing = this.handlers.get(eventType) ?? [];
    existing.push(handler);
    this.handlers.set(eventType, existing);
  }

  async process(event: MiroBoardEvent): Promise<void> {
    // Type-based routing
    const key = `${event.item.type}:${event.type}`;  // e.g., 'sticky_note:create'
    const handlers = [
      ...(this.handlers.get(key) ?? []),
      ...(this.handlers.get(`*:${event.type}`) ?? []),  // Wildcard item type
      ...(this.handlers.get('*:*') ?? []),               // Catch-all
    ];

    for (const handler of handlers) {
      await handler(event);
    }
  }
}

// Usage
const processor = new WebhookProcessor();

processor.on('sticky_note:create', async (event) => {
  console.log(`New sticky note on board ${event.boardId}: ${event.item.id}`);
  await syncService.syncItem(event.boardId, event.item.id);
});

processor.on('*:delete', async (event) => {
  console.log(`Item deleted from board ${event.boardId}: ${event.item.id}`);
  await database.deleteItem(event.item.id);
});
```

### Connector Builder (Fluent API)

```typescript
// src/miro/connector-builder.ts
export class ConnectorBuilder {
  private config: any = { style: {} };

  constructor(private api: MiroApiClient, private boardId: string) {}

  from(itemId: string, snapTo?: SnapPosition): this {
    this.config.startItem = { id: itemId, ...(snapTo ? { snapTo } : {}) };
    return this;
  }

  to(itemId: string, snapTo?: SnapPosition): this {
    this.config.endItem = { id: itemId, ...(snapTo ? { snapTo } : {}) };
    return this;
  }

  caption(text: string, position = 0.5): this {
    this.config.captions = [{ content: text, position }];
    return this;
  }

  dashed(): this { this.config.style.strokeStyle = 'dashed'; return this; }
  curved(): this { this.config.shape = 'curved'; return this; }
  arrow(): this { this.config.style.endStrokeCap = 'stealth'; return this; }

  async build(): Promise<MiroConnector> {
    return this.api.fetch(`/v2/boards/${this.boardId}/connectors`, 'POST', this.config);
  }
}

// Usage
const connector = await new ConnectorBuilder(api, boardId)
  .from(taskId, 'right')
  .to(dependencyId, 'left')
  .caption('depends on')
  .dashed()
  .arrow()
  .build();
```

## Data Flow

```
User Action (or cron job)
     │
     ▼
┌─────────────┐
│   Service   │  ←── Business logic
│   Layer     │
└──────┬──────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
┌──────┐ ┌──────┐
│Cache │ │ Miro │  ←── api.miro.com/v2
│Layer │ │Client│
└──────┘ └──────┘

Miro Board Change
     │
     ▼
┌─────────────┐
│  Webhook    │  ←── Signature verification
│  Handler    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Processor   │  ←── Idempotency + routing
└──────┬──────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
┌──────┐ ┌──────┐
│Cache │ │  DB  │  ←── Sync + invalidation
│Inval │ │Sync  │
└──────┘ └──────┘
```

## Configuration

```typescript
// src/config/miro.ts
export interface MiroConfig {
  clientId: string;
  clientSecret: string;
  accessToken?: string;
  environment: 'development' | 'staging' | 'production';
  cache: { enabled: boolean; ttlSeconds: number };
  rateLimit: { maxConcurrency: number; requestsPerSecond: number };
  webhook: { secret: string; callbackUrl: string };
}

export function loadMiroConfig(): MiroConfig {
  return {
    clientId: requireEnv('MIRO_CLIENT_ID'),
    clientSecret: requireEnv('MIRO_CLIENT_SECRET'),
    accessToken: process.env.MIRO_ACCESS_TOKEN,
    environment: (process.env.NODE_ENV ?? 'development') as MiroConfig['environment'],
    cache: {
      enabled: process.env.MIRO_CACHE_ENABLED !== 'false',
      ttlSeconds: parseInt(process.env.MIRO_CACHE_TTL ?? '120'),
    },
    rateLimit: {
      maxConcurrency: parseInt(process.env.MIRO_MAX_CONCURRENCY ?? '5'),
      requestsPerSecond: parseInt(process.env.MIRO_RPS ?? '10'),
    },
    webhook: {
      secret: process.env.MIRO_WEBHOOK_SECRET ?? '',
      callbackUrl: process.env.MIRO_WEBHOOK_URL ?? '',
    },
  };
}
```

## Error Handling

| Layer | Error Type | Handling |
|-------|-----------|----------|
| Client | 429 Rate Limited | Exponential backoff with `Retry-After` |
| Client | 401 Token Expired | Auto-refresh via TokenManager |
| Service | Item Not Found | Return null, log, continue |
| Webhook | Invalid Signature | Return 401, do not process |
| Webhook | Duplicate Event | Skip via idempotency check |
| Cache | Redis Down | Fall through to API directly |

## Resources

- [Miro REST API Reference](https://developers.miro.com/docs/rest-api-reference-guide)
- [Miro Node.js Client](https://developers.miro.com/docs/miro-nodejs-api-client)
- [Miro App Examples (GitHub)](https://github.com/miroapp/app-examples)

## Next Steps

For multi-environment setup, see `miro-multi-env-setup`.
