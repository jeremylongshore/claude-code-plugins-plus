# MaintainX SDK Patterns - Implementation Guide

> Full implementation details and code examples for the `maintainx-sdk-patterns` skill.

# MaintainX SDK Patterns

## Overview

Production-grade patterns for building robust MaintainX API integrations with proper error handling, pagination, and type safety.

## Prerequisites

- Completed `maintainx-install-auth` setup
- Understanding of REST API principles
- TypeScript/Node.js familiarity

## Core API Endpoints

### Available Endpoints

| Resource | Endpoint | Methods | Description |
|----------|----------|---------|-------------|
| Work Orders | `/workorders` | GET, POST | Maintenance tasks |
| Work Requests | `/workrequests` | GET, POST | Maintenance requests |
| Assets | `/assets` | GET | Equipment tracking |
| Locations | `/locations` | GET | Facility/area hierarchy |
| Users | `/users` | GET | Team members |
| Parts | `/parts` | GET | Inventory items |
| Procedures | `/procedures` | GET | Standard checklists |

## Instructions

### Step 1: Type-Safe API Client

```typescript
// src/api/maintainx-client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Base types
interface PaginatedResponse<T> {
  [key: string]: T[];
  nextCursor: string | null;
}

interface WorkOrder {
  id: string;
  title: string;
  description?: string;
  status: WorkOrderStatus;
  priority: WorkOrderPriority;
  assignees?: User[];
  asset?: Asset;
  location?: Location;
  dueDate?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

type WorkOrderStatus = 'OPEN' | 'IN_PROGRESS' | 'ON_HOLD' | 'DONE';
type WorkOrderPriority = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';

interface Asset {
  id: string;
  name: string;
  serialNumber?: string;
  model?: string;
  manufacturer?: string;
  location?: Location;
  status: 'OPERATIONAL' | 'NON_OPERATIONAL' | 'DECOMMISSIONED';
}

interface Location {
  id: string;
  name: string;
  address?: string;
  parentId?: string;
}

interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
}

// Query parameters
interface QueryParams {
  cursor?: string;
  limit?: number;
}

interface WorkOrderQueryParams extends QueryParams {
  status?: WorkOrderStatus;
  priority?: WorkOrderPriority;
  assigneeId?: string;
  assetId?: string;
  locationId?: string;
  createdAfter?: string;
  createdBefore?: string;
}

interface AssetQueryParams extends QueryParams {
  locationId?: string;
  status?: Asset['status'];
}

// Main client class
export class MaintainXClient {
  private client: AxiosInstance;

  constructor(config?: { apiKey?: string; baseUrl?: string; timeout?: number }) {
    const apiKey = config?.apiKey || process.env.MAINTAINX_API_KEY;
    if (!apiKey) {
      throw new Error('MAINTAINX_API_KEY is required');
    }

    this.client = axios.create({
      baseURL: config?.baseUrl || 'https://api.getmaintainx.com/v1',
      timeout: config?.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request logging
    this.client.interceptors.request.use(config => {
      console.debug(`[MaintainX] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    // Response error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        if (error.response) {
          const { status, data } = error.response;
          const message = data?.message || data?.error || 'Unknown error';
          console.error(`[MaintainX] Error ${status}: ${message}`);
        }
        throw error;
      }
    );
  }

  // Work Orders
  async getWorkOrders(params?: WorkOrderQueryParams): Promise<PaginatedResponse<WorkOrder>> {
    const response = await this.client.get('/workorders', { params });
    return response.data;
  }

  async getWorkOrder(id: string): Promise<WorkOrder> {
    const response = await this.client.get(`/workorders/${id}`);
    return response.data;
  }

  async createWorkOrder(data: Partial<WorkOrder>): Promise<WorkOrder> {
    const response = await this.client.post('/workorders', data);
    return response.data;
  }

  // Assets
  async getAssets(params?: AssetQueryParams): Promise<PaginatedResponse<Asset>> {
    const response = await this.client.get('/assets', { params });
    return response.data;
  }

  async getAsset(id: string): Promise<Asset> {
    const response = await this.client.get(`/assets/${id}`);
    return response.data;
  }

  // Locations
  async getLocations(params?: QueryParams): Promise<PaginatedResponse<Location>> {
    const response = await this.client.get('/locations', { params });
    return response.data;
  }

  async getLocation(id: string): Promise<Location> {
    const response = await this.client.get(`/locations/${id}`);
    return response.data;
  }

  // Users
  async getUsers(params?: QueryParams): Promise<PaginatedResponse<User>> {
    const response = await this.client.get('/users', { params });
    return response.data;
  }

  async getUser(id: string): Promise<User> {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }
}
```

### Step 2: Cursor-Based Pagination

```typescript
// src/utils/pagination.ts
import { MaintainXClient } from '../api/maintainx-client';

interface PaginationOptions {
  limit?: number;
  maxPages?: number;
  delayMs?: number;
}

// Generic paginator
export async function* paginate<T>(
  fetchFn: (cursor?: string) => Promise<{ items: T[]; nextCursor: string | null }>,
  options: PaginationOptions = {}
): AsyncGenerator<T[], void, unknown> {
  const { limit = 100, maxPages = Infinity, delayMs = 0 } = options;
  let cursor: string | undefined;
  let pageCount = 0;

  do {
    const response = await fetchFn(cursor);
    yield response.items;

    cursor = response.nextCursor || undefined;
    pageCount++;

    if (delayMs > 0 && cursor) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  } while (cursor && pageCount < maxPages);
}

// Work order specific paginator
export async function getAllWorkOrders(
  client: MaintainXClient,
  params: Parameters<typeof client.getWorkOrders>[0] = {},
  options: PaginationOptions = {}
): Promise<WorkOrder[]> {
  const allWorkOrders: WorkOrder[] = [];

  for await (const batch of paginate(
    async (cursor) => {
      const response = await client.getWorkOrders({ ...params, cursor, limit: options.limit || 100 });
      return { items: response.workOrders, nextCursor: response.nextCursor };
    },
    options
  )) {
    allWorkOrders.push(...batch);
  }

  return allWorkOrders;
}

// Usage example
async function fetchAllOpenWorkOrders(client: MaintainXClient) {
  const workOrders = await getAllWorkOrders(
    client,
    { status: 'OPEN' },
    { limit: 100, maxPages: 10 }
  );
  console.log(`Fetched ${workOrders.length} open work orders`);
  return workOrders;
}
```

### Step 3: Retry with Exponential Backoff

```typescript
// src/utils/retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableStatuses: number[];
}

const defaultConfig: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
  retryableStatuses: [429, 500, 502, 503, 504],
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, retryableStatuses } = {
    ...defaultConfig,
    ...config,
  };

  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;
      const status = error.response?.status;

      // Don't retry non-retryable errors
      if (status && !retryableStatuses.includes(status)) {
        throw error;
      }

      if (attempt === maxRetries) {
        throw error;
      }

      // Calculate delay with exponential backoff + jitter
      const exponentialDelay = baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * 500;
      const delay = Math.min(exponentialDelay + jitter, maxDelayMs);

      console.log(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw lastError!;
}

// Usage
async function resilientApiCall(client: MaintainXClient) {
  return withRetry(
    () => client.getWorkOrders({ limit: 100 }),
    { maxRetries: 5 }
  );
}
```

### Step 4: Batch Operations

```typescript
// src/utils/batch.ts
interface BatchConfig {
  batchSize: number;
  concurrency: number;
  delayBetweenBatches: number;
}

export async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  config: Partial<BatchConfig> = {}
): Promise<R[]> {
  const { batchSize = 10, concurrency = 5, delayBetweenBatches = 100 } = config;
  const results: R[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);

    // Process batch with limited concurrency
    const batchResults = await Promise.all(
      batch.map(item => processor(item))
    );

    results.push(...batchResults);

    // Delay between batches to avoid rate limiting
    if (i + batchSize < items.length) {
      await new Promise(r => setTimeout(r, delayBetweenBatches));
    }
  }

  return results;
}

// Create multiple work orders
async function createWorkOrders(
  client: MaintainXClient,
  workOrderData: Partial<WorkOrder>[]
): Promise<WorkOrder[]> {
  return processBatch(
    workOrderData,
    data => client.createWorkOrder(data),
    { batchSize: 5, delayBetweenBatches: 200 }
  );
}
```

### Step 5: Query Builder Pattern

```typescript
// src/utils/query-builder.ts
class WorkOrderQueryBuilder {
  private params: WorkOrderQueryParams = {};

  status(status: WorkOrderStatus): this {
    this.params.status = status;
    return this;
  }

  priority(priority: WorkOrderPriority): this {
    this.params.priority = priority;
    return this;
  }

  assignedTo(userId: string): this {
    this.params.assigneeId = userId;
    return this;
  }

  forAsset(assetId: string): this {
    this.params.assetId = assetId;
    return this;
  }

  atLocation(locationId: string): this {
    this.params.locationId = locationId;
    return this;
  }

  createdBetween(start: Date, end: Date): this {
    this.params.createdAfter = start.toISOString();
    this.params.createdBefore = end.toISOString();
    return this;
  }

  limit(count: number): this {
    this.params.limit = count;
    return this;
  }

  build(): WorkOrderQueryParams {
    return { ...this.params };
  }

  async execute(client: MaintainXClient) {
    return client.getWorkOrders(this.build());
  }
}

// Fluent API usage
async function queryExample(client: MaintainXClient) {
  const query = new WorkOrderQueryBuilder()
    .status('OPEN')
    .priority('HIGH')
    .limit(50);

  const results = await query.execute(client);
  return results;
}
```

## Output

- Type-safe MaintainX client with full TypeScript support
- Cursor-based pagination utilities
- Retry logic with exponential backoff
- Batch processing helpers
- Fluent query builder

## Error Handling

| Pattern | Use Case |
|---------|----------|
| Retry with backoff | Transient errors (429, 5xx) |
| Pagination | Large result sets |
| Batch processing | Bulk operations |
| Query builder | Complex filtering |

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [REST API Best Practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)

## Next Steps

For core workflows, see `maintainx-core-workflow-a` (Work Orders) and `maintainx-core-workflow-b` (Assets).
