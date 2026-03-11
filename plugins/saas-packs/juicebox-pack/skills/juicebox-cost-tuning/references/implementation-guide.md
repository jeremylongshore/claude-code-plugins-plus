# Juicebox Cost Tuning - Implementation Guide

Detailed implementation examples and code patterns.

## Juicebox Pricing Model

| Tier | Monthly Cost | Searches | Enrichments | Support |
|------|--------------|----------|-------------|---------|
| Free | $0 | 500 | 100 | Community |
| Pro | $99 | 10,000 | 2,000 | Email |
| Business | $499 | 50,000 | 10,000 | Priority |
| Enterprise | Custom | Unlimited | Unlimited | Dedicated |

## Instructions

### Step 1: Track Usage
```typescript
// lib/usage-tracker.ts
interface UsageMetrics {
  searches: number;
  enrichments: number;
  apiCalls: number;
  dataTransfer: number;
}

export class UsageTracker {
  private metrics: UsageMetrics = {
    searches: 0,
    enrichments: 0,
    apiCalls: 0,
    dataTransfer: 0
  };

  private readonly limits: UsageMetrics;

  constructor(tier: 'free' | 'pro' | 'business') {
    this.limits = this.getLimits(tier);
  }

  trackSearch(): void {
    this.metrics.searches++;
    this.checkLimits();
  }

  trackEnrichment(): void {
    this.metrics.enrichments++;
    this.checkLimits();
  }

  getUsagePercentage(): Record<string, number> {
    return {
      searches: (this.metrics.searches / this.limits.searches) * 100,
      enrichments: (this.metrics.enrichments / this.limits.enrichments) * 100
    };
  }

  private checkLimits(): void {
    const usage = this.getUsagePercentage();
    if (usage.searches > 80 || usage.enrichments > 80) {
      this.sendAlert('Approaching usage limit');
    }
  }
}
```

### Step 2: Implement Smart Caching
```typescript
// lib/cost-aware-cache.ts
export class CostAwareCache {
  // Cache expensive operations longer
  private ttlByOperation: Record<string, number> = {
    'search': 5 * 60,           // 5 minutes
    'profile.basic': 60 * 60,   // 1 hour
    'profile.enriched': 24 * 60 * 60, // 24 hours (expensive)
    'export': 7 * 24 * 60 * 60  // 7 days (very expensive)
  };

  async getOrFetch<T>(
    operation: string,
    key: string,
    fetchFn: () => Promise<T>
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached) {
      metrics.increment('cache.hit', { operation });
      return cached;
    }

    metrics.increment('cache.miss', { operation });
    const result = await fetchFn();

    const ttl = this.ttlByOperation[operation] || 300;
    await this.set(key, result, ttl);

    return result;
  }
}
```

### Step 3: Deduplicate Requests
```typescript
// lib/request-deduplicator.ts
export class RequestDeduplicator {
  private inFlight = new Map<string, Promise<any>>();

  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const existing = this.inFlight.get(key);
    if (existing) {
      return existing as Promise<T>;
    }

    const promise = fn().finally(() => {
      this.inFlight.delete(key);
    });

    this.inFlight.set(key, promise);
    return promise;
  }
}

// Usage - prevents duplicate API calls
const deduplicator = new RequestDeduplicator();

async function getProfile(id: string): Promise<Profile> {
  return deduplicator.dedupe(`profile:${id}`, () =>
    client.profiles.get(id)
  );
}
```

### Step 4: Batch Operations
```typescript
// lib/cost-optimizer.ts
export class CostOptimizer {
  // Instead of individual enrichments, batch them
  async enrichProfiles(ids: string[]): Promise<Profile[]> {
    const BATCH_SIZE = 100; // API limit
    const results: Profile[] = [];

    for (let i = 0; i < ids.length; i += BATCH_SIZE) {
      const batch = ids.slice(i, i + BATCH_SIZE);
      // One API call for 100 profiles vs 100 calls
      const enriched = await client.profiles.batchEnrich(batch);
      results.push(...enriched);
    }

    return results;
  }

  // Selective enrichment - only enrich what you need
  async smartEnrich(profile: Profile, requiredFields: string[]): Promise<Profile> {
    const missingFields = requiredFields.filter(f => !profile[f]);

    if (missingFields.length === 0) {
      return profile; // No enrichment needed
    }

    return client.profiles.enrich(profile.id, {
      fields: missingFields // Only fetch missing data
    });
  }
}
```

### Step 5: Usage Dashboard
```typescript
// routes/usage.ts
router.get('/api/usage/dashboard', async (req, res) => {
  const usage = await juiceboxClient.usage.get();

  const dashboard = {
    currentPeriod: {
      searches: usage.searches,
      searchLimit: usage.limits.searches,
      searchPercentage: (usage.searches / usage.limits.searches) * 100,
      enrichments: usage.enrichments,
      enrichmentLimit: usage.limits.enrichments,
      enrichmentPercentage: (usage.enrichments / usage.limits.enrichments) * 100
    },
    projectedUsage: {
      searchesEndOfMonth: projectUsage(usage.searches, usage.periodStart),
      enrichmentsEndOfMonth: projectUsage(usage.enrichments, usage.periodStart)
    },
    costSavings: {
      cacheHitRate: await getCacheHitRate(),
      dedupeSavings: await getDedupeSavings(),
      batchingSavings: await getBatchingSavings()
    }
  };

  res.json(dashboard);
});
```

## Cost Optimization Checklist

```markdown

## Monthly Cost Review

### Caching
- [ ] Cache hit rate > 70%
- [ ] High-cost operations cached longer
- [ ] Cache invalidation working properly

### Request Optimization
- [ ] Deduplication enabled
- [ ] Batch operations used
- [ ] Selective field fetching

### Usage Patterns
- [ ] No unnecessary enrichments
- [ ] Search results paginated efficiently
- [ ] Exports scheduled off-peak

### Alerts
- [ ] 80% usage warning configured
- [ ] Anomaly detection enabled
- [ ] Budget alerts set up
```
