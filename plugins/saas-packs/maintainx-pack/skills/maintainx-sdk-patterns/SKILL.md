---
name: maintainx-sdk-patterns
description: |
  Learn MaintainX REST API patterns, pagination, filtering, and client architecture.
  Use when building robust API integrations, implementing pagination,
  or creating reusable SDK patterns for MaintainX.
  Trigger with phrases like "maintainx sdk", "maintainx api patterns",
  "maintainx pagination", "maintainx filtering", "maintainx client design".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX SDK Patterns

## Overview
Production-grade patterns for building robust MaintainX API integrations with proper error handling, cursor-based pagination, retry logic, and type safety.

## Prerequisites
- Completed `maintainx-install-auth` setup
- TypeScript/Node.js familiarity
- Understanding of REST API principles

## Instructions

### Step 1: Type-Safe Client with Generics

```typescript
// src/maintainx/typed-client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

interface PaginatedResponse<T> {
  cursor: string | null;
}

interface WorkOrder {
  id: number;
  title: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CLOSED';
  priority: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  description?: string;
  assignees: Array<{ type: 'USER' | 'TEAM'; id: number }>;
  assetId?: number;
  locationId?: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  dueDate?: string;
  categories: string[];
}

interface Asset {
  id: number;
  name: string;
  serialNumber?: string;
  model?: string;
  manufacturer?: string;
  locationId?: number;
  createdAt: string;
}

interface WorkOrdersResponse extends PaginatedResponse<WorkOrder> {
  workOrders: WorkOrder[];
}

interface AssetsResponse extends PaginatedResponse<Asset> {
  assets: Asset[];
}

export class MaintainXClient {
  private http: AxiosInstance;

  constructor(apiKey?: string) {
    const key = apiKey || process.env.MAINTAINX_API_KEY;
    if (!key) throw new Error('MAINTAINX_API_KEY required');

    this.http = axios.create({
      baseURL: 'https://api.getmaintainx.com/v1',
      headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
      timeout: 30_000,
    });
  }

  async getWorkOrders(params?: Record<string, any>): Promise<WorkOrdersResponse> {
    const { data } = await this.http.get<WorkOrdersResponse>('/workorders', { params });
    return data;
  }

  async getWorkOrder(id: number): Promise<WorkOrder> {
    const { data } = await this.http.get<WorkOrder>(`/workorders/${id}`);
    return data;
  }

  async createWorkOrder(input: Partial<WorkOrder>): Promise<WorkOrder> {
    const { data } = await this.http.post<WorkOrder>('/workorders', input);
    return data;
  }

  async updateWorkOrder(id: number, input: Partial<WorkOrder>): Promise<WorkOrder> {
    const { data } = await this.http.patch<WorkOrder>(`/workorders/${id}`, input);
    return data;
  }

  async getAssets(params?: Record<string, any>): Promise<AssetsResponse> {
    const { data } = await this.http.get<AssetsResponse>('/assets', { params });
    return data;
  }

  async request<T = any>(method: string, path: string, body?: any): Promise<T> {
    const config: AxiosRequestConfig = { method, url: path, data: body };
    const { data } = await this.http.request<T>(config);
    return data;
  }
}
```

### Step 2: Cursor-Based Pagination

MaintainX uses cursor-based pagination. The response includes a `cursor` field; pass it as a query parameter to get the next page.

```typescript
async function paginate<T>(
  fetcher: (cursor?: string) => Promise<{ cursor: string | null } & Record<string, T[]>>,
  key: string,
): Promise<T[]> {
  const all: T[] = [];
  let cursor: string | undefined;

  do {
    const response = await fetcher(cursor);
    const items = (response as any)[key] as T[];
    all.push(...items);
    cursor = response.cursor ?? undefined;
  } while (cursor);

  return all;
}

// Usage
const allWorkOrders = await paginate(
  (cursor) => client.getWorkOrders({ limit: 100, cursor, status: 'OPEN' }),
  'workOrders',
);
console.log(`Total open work orders: ${allWorkOrders.length}`);

const allAssets = await paginate(
  (cursor) => client.getAssets({ limit: 100, cursor }),
  'assets',
);
console.log(`Total assets: ${allAssets.length}`);
```

### Step 3: Retry with Exponential Backoff

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const status = err?.response?.status;
      const isRetryable = status === 429 || (status >= 500 && status < 600);

      if (!isRetryable || attempt === maxRetries) throw err;

      // Honor Retry-After header if present
      const retryAfter = err.response?.headers?.['retry-after'];
      const delayMs = retryAfter
        ? parseInt(retryAfter) * 1000
        : baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;

      console.warn(`Retry ${attempt + 1}/${maxRetries} after ${delayMs}ms (HTTP ${status})`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error('Unreachable');
}

// Usage
const wo = await withRetry(() => client.getWorkOrder(12345));
```

### Step 4: Batch Operations

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 10 });

async function batchCreateWorkOrders(items: Array<Partial<WorkOrder>>): Promise<WorkOrder[]> {
  const results = await Promise.all(
    items.map((item) =>
      queue.add(() => withRetry(() => client.createWorkOrder(item)))
    ),
  );
  return results as WorkOrder[];
}

// Create 50 PMs in controlled batches
const pms = Array.from({ length: 50 }, (_, i) => ({
  title: `Weekly Inspection - Zone ${i + 1}`,
  priority: 'LOW' as const,
  categories: ['PREVENTIVE'],
}));

const created = await batchCreateWorkOrders(pms);
console.log(`Created ${created.length} preventive maintenance orders`);
```

### Step 5: Fluent Query Builder

```typescript
class WorkOrderQuery {
  private params: Record<string, any> = {};

  status(s: WorkOrder['status']) { this.params.status = s; return this; }
  priority(p: WorkOrder['priority']) { this.params.priority = p; return this; }
  assignee(userId: number) { this.params.assigneeId = userId; return this; }
  asset(assetId: number) { this.params.assetId = assetId; return this; }
  location(locationId: number) { this.params.locationId = locationId; return this; }
  createdAfter(date: string) { this.params.createdAtGte = date; return this; }
  createdBefore(date: string) { this.params.createdAtLte = date; return this; }
  limit(n: number) { this.params.limit = n; return this; }

  async execute(client: MaintainXClient) {
    return client.getWorkOrders(this.params);
  }
}

// Usage
const results = await new WorkOrderQuery()
  .status('OPEN')
  .priority('HIGH')
  .location(2345)
  .createdAfter('2026-01-01T00:00:00Z')
  .limit(25)
  .execute(client);
```

## Output
- Type-safe MaintainX client with full TypeScript interfaces
- Cursor-based pagination utility that works across all list endpoints
- Retry logic with exponential backoff and `Retry-After` header support
- Rate-limited batch processor using `p-queue`
- Fluent query builder for readable work order filters

## Error Handling
| Pattern | Use Case |
|---------|----------|
| `withRetry()` | Transient errors (429, 5xx) with exponential backoff |
| `paginate()` | Collecting all items from cursor-based endpoints |
| `PQueue` | Controlled concurrency to avoid rate limits |
| `WorkOrderQuery` | Type-safe filtering to prevent invalid API calls |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [p-queue](https://github.com/sindresorhus/p-queue) -- Promise queue with concurrency control

## Next Steps
For core workflows, see `maintainx-core-workflow-a` (Work Orders) and `maintainx-core-workflow-b` (Assets).

## Examples

**Stream large datasets with async iterators**:

```typescript
async function* streamWorkOrders(client: MaintainXClient, params?: Record<string, any>) {
  let cursor: string | undefined;
  do {
    const response = await client.getWorkOrders({ ...params, limit: 100, cursor });
    for (const wo of response.workOrders) {
      yield wo;
    }
    cursor = response.cursor ?? undefined;
  } while (cursor);
}

for await (const wo of streamWorkOrders(client, { status: 'COMPLETED' })) {
  console.log(`Processing completed WO #${wo.id}`);
}
```
