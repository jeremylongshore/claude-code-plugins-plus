---
name: webflow-reference-architecture
description: |
  Implement Webflow reference architecture — layered project structure, client wrapper,
  CMS sync service, webhook handlers, and caching layer for production integrations.
  Trigger with phrases like "webflow architecture", "webflow project structure",
  "how to organize webflow", "webflow integration design", "webflow best practices".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Reference Architecture

## Overview

Production-ready architecture for Webflow Data API v2 integrations. Layered design
separating API access, business logic, caching, and webhook handling.

## Prerequisites

- TypeScript 5+ project
- `webflow-api` SDK (v3.x)
- Understanding of service-oriented architecture
- Redis (optional, for distributed caching)

## Project Structure

```
my-webflow-project/
├── src/
│   ├── webflow/                     # Webflow API layer
│   │   ├── client.ts                # WebflowClient singleton
│   │   ├── types.ts                 # TypeScript types for Webflow resources
│   │   ├── errors.ts                # Custom error classes
│   │   └── cache.ts                 # Response caching (LRU/Redis)
│   ├── services/                    # Business logic layer
│   │   ├── cms.service.ts           # CMS content management
│   │   ├── ecommerce.service.ts     # Products, orders, inventory
│   │   ├── forms.service.ts         # Form submission processing
│   │   └── sync.service.ts          # External data sync
│   ├── webhooks/                    # Event handling layer
│   │   ├── router.ts                # Event type routing
│   │   ├── handlers/
│   │   │   ├── form-submission.ts
│   │   │   ├── cms-item-changed.ts
│   │   │   └── ecomm-new-order.ts
│   │   └── middleware.ts            # Signature verification
│   ├── api/                         # HTTP endpoints
│   │   ├── health.ts
│   │   ├── webhooks.ts
│   │   └── content.ts
│   └── config/
│       └── webflow.ts               # Environment-aware config
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── webhooks/
│   └── integration/
│       └── webflow.integration.test.ts
├── .env.example
├── tsconfig.json
└── package.json
```

## Layer Architecture

```
┌──────────────────────────────────────────────────┐
│                  API Layer                        │
│   Express routes, webhook endpoints, health      │
├──────────────────────────────────────────────────┤
│               Service Layer                       │
│   CMS sync, ecommerce, form processing           │
│   (Business logic, orchestration)                 │
├──────────────────────────────────────────────────┤
│             Webflow Client Layer                  │
│   WebflowClient wrapper, error handling, types    │
├──────────────────────────────────────────────────┤
│           Infrastructure Layer                    │
│   Cache (LRU/Redis), queue (p-queue), monitoring  │
└──────────────────────────────────────────────────┘
```

## Instructions

### Layer 1: Webflow Client

```typescript
// src/webflow/client.ts
import { WebflowClient } from "webflow-api";
import { getConfig } from "../config/webflow.js";

let client: WebflowClient | null = null;

export function getClient(): WebflowClient {
  if (!client) {
    const config = getConfig();
    client = new WebflowClient({
      accessToken: config.accessToken,
      maxRetries: config.maxRetries,
    });
  }
  return client;
}

export function resetClient(): void {
  client = null;
}
```

```typescript
// src/webflow/errors.ts
export class WebflowServiceError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly originalError?: unknown
  ) {
    super(message);
    this.name = "WebflowServiceError";
  }

  static fromApiError(error: any): WebflowServiceError {
    const status = error.statusCode || error.status || 500;
    const retryable = status === 429 || status >= 500;

    return new WebflowServiceError(
      error.message || "Unknown Webflow error",
      status,
      retryable,
      error
    );
  }
}
```

```typescript
// src/webflow/types.ts
export interface WebflowSite {
  id: string;
  displayName: string;
  shortName: string;
  lastPublished: string | null;
  customDomains?: Array<{ url: string }>;
}

export interface WebflowCollection {
  id: string;
  displayName: string;
  slug: string;
  itemCount: number;
  fields: WebflowField[];
}

export interface WebflowField {
  slug: string;
  displayName: string;
  type: string;
  isRequired: boolean;
}

export interface WebflowItem {
  id: string;
  isDraft: boolean;
  isArchived: boolean;
  createdOn: string;
  lastUpdated: string;
  fieldData: Record<string, any>;
}
```

### Layer 2: Service Layer

```typescript
// src/services/cms.service.ts
import { getClient } from "../webflow/client.js";
import { WebflowServiceError } from "../webflow/errors.js";
import { cachedFetch, invalidateCache } from "../webflow/cache.js";
import type { WebflowItem } from "../webflow/types.js";

export class CmsService {
  private webflow = getClient();

  async getCollections(siteId: string) {
    return cachedFetch(
      `collections:${siteId}`,
      () => this.webflow.collections.list(siteId).then(r => r.collections!),
      30 * 60 * 1000 // 30 min — schemas change rarely
    );
  }

  async getPublishedItems(collectionId: string): Promise<WebflowItem[]> {
    // CDN-cached — no rate limit
    return cachedFetch(
      `items:live:${collectionId}`,
      () => this.webflow.collections.items.listItemsLive(collectionId, { limit: 100 })
        .then(r => r.items as WebflowItem[]),
      60 * 1000 // 1 min
    );
  }

  async createItems(
    collectionId: string,
    items: Array<{ fieldData: Record<string, any> }>
  ): Promise<string[]> {
    try {
      const result = await this.webflow.collections.items.createItemsBulk(
        collectionId,
        { items: items.map(i => ({ ...i, isDraft: false })) }
      );
      // Invalidate cache after write
      invalidateCache(`items:live:${collectionId}`);
      return result.items!.map(i => i.id!);
    } catch (error) {
      throw WebflowServiceError.fromApiError(error);
    }
  }

  async publishItems(collectionId: string, itemIds: string[]): Promise<void> {
    await this.webflow.collections.items.publishItem(collectionId, { itemIds });
    invalidateCache(`items:live:${collectionId}`);
  }
}
```

```typescript
// src/services/sync.service.ts
import { CmsService } from "./cms.service.js";

export class SyncService {
  constructor(private cms: CmsService) {}

  async syncFromExternal(
    collectionId: string,
    externalData: Array<{ title: string; body: string; slug: string }>
  ) {
    // Get existing items to avoid duplicates
    const existing = await this.cms.getPublishedItems(collectionId);
    const existingSlugs = new Set(existing.map(i => i.fieldData?.slug));

    // Filter new items
    const newItems = externalData
      .filter(d => !existingSlugs.has(d.slug))
      .map(d => ({
        fieldData: {
          name: d.title,
          slug: d.slug,
          "post-body": d.body,
        },
      }));

    if (newItems.length === 0) return { synced: 0 };

    // Bulk create (100 at a time)
    const createdIds = await this.cms.createItems(collectionId, newItems.slice(0, 100));

    // Publish new items
    await this.cms.publishItems(collectionId, createdIds);

    return { synced: createdIds.length };
  }
}
```

### Layer 3: Webhook Handling

```typescript
// src/webhooks/router.ts
import { handleFormSubmission } from "./handlers/form-submission.js";
import { handleCmsItemChanged } from "./handlers/cms-item-changed.js";
import { handleNewOrder } from "./handlers/ecomm-new-order.js";

type Handler = (payload: any) => Promise<void>;

const handlers: Record<string, Handler> = {
  form_submission: handleFormSubmission,
  collection_item_created: handleCmsItemChanged,
  collection_item_changed: handleCmsItemChanged,
  ecomm_new_order: handleNewOrder,
};

export async function routeWebhookEvent(
  triggerType: string,
  payload: any
): Promise<void> {
  const handler = handlers[triggerType];
  if (!handler) {
    console.log(`No handler for: ${triggerType}`);
    return;
  }
  await handler(payload);
}
```

```typescript
// src/webhooks/handlers/cms-item-changed.ts
import { invalidateCache } from "../../webflow/cache.js";

export async function handleCmsItemChanged(payload: any): Promise<void> {
  const { collectionId, itemId } = payload;

  // Invalidate cache for this collection
  invalidateCache(`items:live:${collectionId}`);
  invalidateCache(`items:staged:${collectionId}`);

  // Trigger downstream updates (search index, external DB, etc.)
  console.log(`CMS item changed: ${itemId} in collection ${collectionId}`);
}
```

### Layer 4: Configuration

```typescript
// src/config/webflow.ts
interface WebflowConfig {
  accessToken: string;
  siteId: string;
  maxRetries: number;
  environment: "development" | "staging" | "production";
  webhookSecret: string;
}

export function getConfig(): WebflowConfig {
  const env = (process.env.NODE_ENV || "development") as WebflowConfig["environment"];

  return {
    accessToken: requireEnv("WEBFLOW_API_TOKEN"),
    siteId: requireEnv("WEBFLOW_SITE_ID"),
    maxRetries: env === "production" ? 3 : 1,
    environment: env,
    webhookSecret: process.env.WEBFLOW_WEBHOOK_SECRET || "",
  };
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} environment variable required`);
  return value;
}
```

## Data Flow

```
External Data Source
       │
       ▼
┌─────────────────┐     ┌─────────────┐
│  Sync Service   │────▶│  CMS Service │
│  (orchestration)│     │  (CRUD ops)  │
└─────────────────┘     └──────┬───────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌──────────────┐    ┌────────────────┐
            │ Cache (LRU)  │    │ Webflow Client │
            │ or Redis     │    │ (webflow-api)  │
            └──────────────┘    └───────┬────────┘
                                        │
                                        ▼
                               ┌────────────────┐
                               │ Webflow API v2 │
                               │ api.webflow.com│
                               └────────────────┘
```

## Output

- Layered project structure with clear boundaries
- WebflowClient wrapper with singleton and error handling
- CMS service with caching and bulk operations
- Webhook event router with typed handlers
- Environment-aware configuration
- Sync service for external data integration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular imports | Wrong layer dependencies | Services depend on client, not reverse |
| Cache inconsistency | Missing invalidation | Invalidate on writes and webhook events |
| Config missing | Environment not set | `requireEnv()` fails fast with clear message |
| Type mismatches | API shape changes | Update `types.ts` from collection schema |

## Resources

- [Webflow API Reference](https://developers.webflow.com/data/reference/rest-introduction)
- [CMS API](https://developers.webflow.com/data/reference/cms)
- [SDK GitHub](https://github.com/webflow/js-webflow-api)

## Next Steps

For multi-environment setup, see `webflow-multi-env-setup`.
