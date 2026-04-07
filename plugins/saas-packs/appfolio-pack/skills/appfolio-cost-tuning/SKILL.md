---
name: appfolio-cost-tuning
description: |
  Optimize AppFolio API costs through efficient usage patterns.
  Trigger: "appfolio cost".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Cost Tuning

## Overview

AppFolio Stack API pricing is partner-agreement based, with costs scaling by API call volume per managed property. Property management portfolios generate high-frequency reads for tenant lookups, lease status checks, and maintenance requests. Each redundant API call erodes margin on per-unit revenue. Optimizing call patterns directly impacts operational profitability, especially for portfolios managing hundreds or thousands of units where even small per-call costs compound rapidly.

## Cost Breakdown

| Component | Cost Driver | Optimization |
|-----------|------------|--------------|
| Property/unit reads | Per-call pricing on tenant and unit endpoints | Cache with 10-15 min TTL; property data changes infrequently |
| Lease operations | Bulk lease queries across entire portfolio | Fetch all leases once, filter locally instead of per-unit calls |
| Maintenance requests | Polling for new work orders | Use webhooks to receive push notifications |
| Reporting exports | Large payload downloads for financial reports | Schedule off-peak, cache results for 24h |
| Vendor/owner lookups | Repeated lookups for the same contacts | Build a local lookup table, refresh daily |

## API Call Reduction

```typescript
class AppFolioCache {
  private cache = new Map<string, { data: any; expiry: number }>();

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry || Date.now() > entry.expiry) return null;
    return entry.data;
  }

  set(key: string, data: any, ttlMs = 600_000): void {
    this.cache.set(key, { data, expiry: Date.now() + ttlMs });
  }

  async fetchWithCache(endpoint: string, ttlMs?: number): Promise<any> {
    const cached = this.get(endpoint);
    if (cached) return cached;
    const response = await fetch(endpoint);
    const data = await response.json();
    this.set(endpoint, data, ttlMs);
    return data;
  }
}
```

## Usage Monitoring

```typescript
class AppFolioUsageMonitor {
  private calls: Array<{ endpoint: string; timestamp: number }> = [];
  private budgetLimit = 10_000; // daily call budget

  record(endpoint: string): void {
    this.calls.push({ endpoint, timestamp: Date.now() });
    const todayCalls = this.getTodayCount();
    if (todayCalls > this.budgetLimit * 0.8) {
      console.warn(`AppFolio API budget 80% consumed: ${todayCalls}/${this.budgetLimit}`);
    }
  }

  getTodayCount(): number {
    const startOfDay = new Date().setHours(0, 0, 0, 0);
    return this.calls.filter(c => c.timestamp > startOfDay).length;
  }
}
```

## Cost Optimization Checklist

- [ ] Cache property and unit data with 10-15 min TTL
- [ ] Replace polling loops with webhook-driven event handling
- [ ] Batch lease queries — fetch all, filter locally
- [ ] Use incremental sync with `modified_since` parameter
- [ ] Schedule report exports during off-peak hours
- [ ] Build local lookup tables for vendors and owners
- [ ] Set daily API call budget alerts at 80% threshold
- [ ] Audit unused integrations consuming API quota

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests | Exceeded rate limit | Implement exponential backoff with jitter |
| Stale cache serving old data | TTL too long for volatile data | Reduce TTL for maintenance/lease endpoints to 2-5 min |
| Budget alerts firing daily | Polling loop running on short interval | Switch to webhook-driven architecture |
| Duplicate API calls | Multiple services fetching same data | Centralize through shared cache layer |
| Large payload timeouts | Fetching full portfolio in single call | Paginate requests, process in batches of 100 |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-performance-tuning`.
