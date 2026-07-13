# MaintainX Cost Tuning - Implementation Guide

> Full implementation details and code examples for the `maintainx-cost-tuning` skill.

# MaintainX Cost Tuning

## Overview

Optimize your MaintainX API usage for cost efficiency while maintaining functionality.

## Prerequisites

- MaintainX integration deployed
- API usage monitoring in place
- Understanding of pricing tiers

## Cost Optimization Strategies

| Strategy | Savings Potential | Implementation Effort |
|----------|------------------|----------------------|
| Caching | 40-60% | Low |
| Batch operations | 20-30% | Medium |
| Webhook over polling | 50-70% | Medium |
| Smart pagination | 10-20% | Low |
| Request deduplication | 15-25% | Low |

## Instructions

### Step 1: API Usage Tracking

```typescript
// src/monitoring/api-usage.ts

interface UsageMetric {
  endpoint: string;
  method: string;
  timestamp: Date;
  responseSize: number;
  cached: boolean;
}

class ApiUsageTracker {
  private metrics: UsageMetric[] = [];
  private dailyUsage: Map<string, number> = new Map();

  track(metric: Omit<UsageMetric, 'timestamp'>): void {
    this.metrics.push({
      ...metric,
      timestamp: new Date(),
    });

    // Update daily counter
    const today = new Date().toISOString().split('T')[0];
    const key = `${today}:${metric.endpoint}`;
    this.dailyUsage.set(key, (this.dailyUsage.get(key) || 0) + 1);
  }

  getUsageReport(days = 7): any {
    const now = Date.now();
    const cutoff = now - days * 24 * 60 * 60 * 1000;

    const recentMetrics = this.metrics.filter(
      m => m.timestamp.getTime() > cutoff
    );

    // Group by endpoint
    const byEndpoint: Record<string, number> = {};
    recentMetrics.forEach(m => {
      byEndpoint[m.endpoint] = (byEndpoint[m.endpoint] || 0) + 1;
    });

    // Calculate cache hit rate
    const cacheHits = recentMetrics.filter(m => m.cached).length;
    const cacheHitRate = recentMetrics.length > 0
      ? cacheHits / recentMetrics.length
      : 0;

    // Identify optimization opportunities
    const opportunities = this.identifyOpportunities(byEndpoint, cacheHitRate);

    return {
      period: `${days} days`,
      totalRequests: recentMetrics.length,
      byEndpoint,
      cacheHitRate: `${(cacheHitRate * 100).toFixed(1)}%`,
      estimatedSavings: this.calculateSavings(recentMetrics),
      opportunities,
    };
  }

  private identifyOpportunities(
    byEndpoint: Record<string, number>,
    cacheHitRate: number
  ): string[] {
    const opportunities: string[] = [];

    // High-frequency endpoints that could be cached
    Object.entries(byEndpoint).forEach(([endpoint, count]) => {
      if (count > 1000 && !endpoint.includes('create')) {
        opportunities.push(
          `High volume on ${endpoint} (${count} requests) - consider caching`
        );
      }
    });

    // Low cache hit rate
    if (cacheHitRate < 0.3) {
      opportunities.push(
        `Low cache hit rate (${(cacheHitRate * 100).toFixed(1)}%) - improve caching strategy`
      );
    }

    return opportunities;
  }

  private calculateSavings(metrics: UsageMetric[]): string {
    const totalRequests = metrics.length;
    const cachedRequests = metrics.filter(m => m.cached).length;

    // Estimate cost per request (varies by plan)
    const costPerRequest = 0.001;  // Example: $0.001 per request

    const savedRequests = cachedRequests;
    const savings = savedRequests * costPerRequest;

    return `$${savings.toFixed(2)} saved from ${savedRequests} cached requests`;
  }
}

export const usageTracker = new ApiUsageTracker();
```

### Step 2: Smart Caching Strategy

```typescript
// src/cache/smart-cache.ts

interface CacheStrategy {
  ttlSeconds: number;
  staleWhileRevalidate: boolean;
  priority: 'high' | 'medium' | 'low';
}

const cacheStrategies: Record<string, CacheStrategy> = {
  // Static data - cache longer
  'locations': { ttlSeconds: 3600, staleWhileRevalidate: true, priority: 'low' },
  'users': { ttlSeconds: 1800, staleWhileRevalidate: true, priority: 'low' },
  'assets': { ttlSeconds: 900, staleWhileRevalidate: true, priority: 'medium' },

  // Dynamic data - cache shorter
  'workorders:list': { ttlSeconds: 60, staleWhileRevalidate: true, priority: 'high' },
  'workorders:single': { ttlSeconds: 300, staleWhileRevalidate: true, priority: 'medium' },
};

class SmartCache {
  private cache: CacheManager;

  async getOrFetch<T>(
    key: string,
    fetchFn: () => Promise<T>,
    strategyKey: string
  ): Promise<T> {
    const strategy = cacheStrategies[strategyKey] || {
      ttlSeconds: 300,
      staleWhileRevalidate: false,
      priority: 'medium',
    };

    // Try cache first
    const cached = await this.cache.get<T>(key);

    if (cached) {
      usageTracker.track({
        endpoint: strategyKey,
        method: 'GET',
        responseSize: 0,
        cached: true,
      });

      // Stale-while-revalidate: return cached, refresh in background
      if (strategy.staleWhileRevalidate) {
        this.revalidateInBackground(key, fetchFn, strategy);
      }

      return cached;
    }

    // Fetch fresh data
    const data = await fetchFn();

    usageTracker.track({
      endpoint: strategyKey,
      method: 'GET',
      responseSize: JSON.stringify(data).length,
      cached: false,
    });

    // Cache the result
    await this.cache.set(key, data, strategy.ttlSeconds);

    return data;
  }

  private async revalidateInBackground<T>(
    key: string,
    fetchFn: () => Promise<T>,
    strategy: CacheStrategy
  ): Promise<void> {
    // Don't await - runs in background
    fetchFn()
      .then(data => this.cache.set(key, data, strategy.ttlSeconds))
      .catch(err => console.error('Background revalidation failed:', err));
  }
}
```

### Step 3: Webhook-Based Updates

```typescript
// src/sync/webhook-sync.ts

// Instead of polling, use webhooks to stay in sync
class WebhookBasedSync {
  private localCache: Map<string, any> = new Map();

  constructor() {
    // Initialize cache from MaintainX on startup
    this.initializeCache();

    // Register webhook handlers
    this.registerWebhookHandlers();
  }

  private async initializeCache(): Promise<void> {
    console.log('Initializing local cache from MaintainX...');

    // One-time full sync
    const workOrders = await getAllWorkOrders(client, { status: 'OPEN' });
    workOrders.forEach(wo => this.localCache.set(`workorder:${wo.id}`, wo));

    console.log(`Cached ${workOrders.length} work orders`);
  }

  private registerWebhookHandlers(): void {
    // Update cache from webhooks instead of polling
    on('workorder.created', async (event) => {
      this.localCache.set(`workorder:${event.data.id}`, event.data);
    });

    on('workorder.updated', async (event) => {
      this.localCache.set(`workorder:${event.data.id}`, event.data);
    });

    on('workorder.deleted', async (event) => {
      this.localCache.delete(`workorder:${event.data.id}`);
    });
  }

  // Get data from cache - no API call needed
  getWorkOrder(id: string): WorkOrder | undefined {
    return this.localCache.get(`workorder:${id}`);
  }

  // Only call API when data doesn't exist locally
  async getWorkOrderWithFallback(id: string): Promise<WorkOrder> {
    const cached = this.localCache.get(`workorder:${id}`);
    if (cached) return cached;

    // Fallback to API
    const workOrder = await client.getWorkOrder(id);
    this.localCache.set(`workorder:${id}`, workOrder);
    return workOrder;
  }
}

// Cost comparison:
// Polling every 30 seconds = 2,880 requests/day = $2.88/day (at $0.001/request)
// Webhooks = ~100 events/day = $0.10/day (at $0.001/request)
// Savings = 96.5%
```

### Step 4: Request Batching

```typescript
// src/optimization/batch-requests.ts

// Instead of individual requests, batch where possible
class BatchRequestManager {
  private pendingWorkOrderIds: Set<string> = new Set();
  private batchTimeout: NodeJS.Timeout | null = null;
  private batchResolvers: Map<string, (wo: WorkOrder) => void> = new Map();

  async getWorkOrder(id: string): Promise<WorkOrder> {
    return new Promise((resolve) => {
      this.pendingWorkOrderIds.add(id);
      this.batchResolvers.set(id, resolve);

      // Schedule batch execution
      if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => this.executeBatch(), 50);
      }
    });
  }

  private async executeBatch(): Promise<void> {
    const ids = Array.from(this.pendingWorkOrderIds);
    this.pendingWorkOrderIds.clear();
    this.batchTimeout = null;

    if (ids.length === 0) return;

    console.log(`Batching ${ids.length} work order requests`);

    // Fetch all at once (if API supports batch endpoint)
    // Otherwise, parallel fetch with rate limiting
    const workOrders = await Promise.all(
      ids.map(id => client.getWorkOrder(id))
    );

    // Resolve individual promises
    workOrders.forEach((wo, i) => {
      const resolver = this.batchResolvers.get(ids[i]);
      if (resolver) {
        resolver(wo);
        this.batchResolvers.delete(ids[i]);
      }
    });

    // Cost savings: 10 individual requests -> 1 batch = 90% reduction
  }
}
```

### Step 5: Efficient Data Fetching

```typescript
// src/optimization/efficient-fetch.ts

// Only fetch what you need
async function fetchMinimalWorkOrderData(
  client: MaintainXClient,
  params: WorkOrderQueryParams
): Promise<WorkOrderSummary[]> {
  const response = await client.getWorkOrders({
    ...params,
    // Request only necessary fields if API supports field selection
    // fields: ['id', 'title', 'status', 'priority', 'dueDate'],
    limit: params.limit || 50,  // Don't over-fetch
  });

  // Transform to minimal objects
  return response.workOrders.map(wo => ({
    id: wo.id,
    title: wo.title,
    status: wo.status,
    priority: wo.priority,
    dueDate: wo.dueDate,
  }));
}

// Pagination with early termination
async function fetchUntilCondition(
  client: MaintainXClient,
  condition: (wo: WorkOrder) => boolean,
  params: WorkOrderQueryParams = {}
): Promise<WorkOrder[]> {
  const results: WorkOrder[] = [];
  let cursor: string | undefined;

  do {
    const response = await client.getWorkOrders({ ...params, cursor, limit: 100 });

    for (const wo of response.workOrders) {
      if (condition(wo)) {
        results.push(wo);
      } else {
        // Early termination - don't fetch more pages
        return results;
      }
    }

    cursor = response.nextCursor || undefined;
  } while (cursor && results.length < 1000);  // Safety limit

  return results;
}
```

### Step 6: Cost Dashboard

```typescript
// src/monitoring/cost-dashboard.ts

interface CostReport {
  period: string;
  totalRequests: number;
  estimatedCost: number;
  byEndpoint: Record<string, { count: number; cost: number }>;
  recommendations: string[];
}

function generateCostReport(days = 30): CostReport {
  const usage = usageTracker.getUsageReport(days);

  // Cost per request (adjust based on your plan)
  const costPerRequest = 0.001;

  const byEndpoint: Record<string, { count: number; cost: number }> = {};
  Object.entries(usage.byEndpoint).forEach(([endpoint, count]) => {
    byEndpoint[endpoint] = {
      count: count as number,
      cost: (count as number) * costPerRequest,
    };
  });

  // Sort by cost descending
  const sortedEndpoints = Object.entries(byEndpoint)
    .sort((a, b) => b[1].cost - a[1].cost);

  const recommendations: string[] = [];

  // Top cost endpoint
  if (sortedEndpoints.length > 0) {
    const [topEndpoint, topUsage] = sortedEndpoints[0];
    recommendations.push(
      `Highest cost: ${topEndpoint} ($${topUsage.cost.toFixed(2)}) - ` +
      `Consider caching or webhooks`
    );
  }

  // Low cache hit rate
  const cacheHitRate = parseFloat(usage.cacheHitRate);
  if (cacheHitRate < 50) {
    const potentialSavings = usage.totalRequests * 0.5 * costPerRequest;
    recommendations.push(
      `Cache hit rate is ${cacheHitRate.toFixed(0)}% - ` +
      `Improving to 50% could save $${potentialSavings.toFixed(2)}`
    );
  }

  return {
    period: `${days} days`,
    totalRequests: usage.totalRequests,
    estimatedCost: usage.totalRequests * costPerRequest,
    byEndpoint,
    recommendations,
  };
}
```

## Output

- API usage tracking implemented
- Smart caching strategy
- Webhook-based sync instead of polling
- Request batching
- Cost dashboard and reports

## Cost Savings Summary

| Optimization | Before | After | Savings |
|-------------|--------|-------|---------|
| Caching | 10,000/day | 4,000/day | 60% |
| Webhooks vs polling | 2,880/day | 100/day | 97% |
| Batching | 500/day | 100/day | 80% |
| Total estimate | 13,380/day | 4,200/day | 69% |

## Resources

- [MaintainX Pricing](https://www.getmaintainx.com/pricing)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps

For architecture patterns, see `maintainx-reference-architecture`.
