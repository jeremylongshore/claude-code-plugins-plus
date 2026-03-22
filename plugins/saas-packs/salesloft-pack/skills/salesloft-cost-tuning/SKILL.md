---
name: salesloft-cost-tuning
description: |
  Optimize SalesLoft API costs by reducing request volume and deep pagination.
  Use when analyzing API usage, reducing rate limit consumption,
  or planning capacity for bulk operations.
  Trigger: "salesloft cost", "salesloft billing", "reduce salesloft API usage".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Cost Tuning

## Overview

SalesLoft API cost is rate-limit-based (600 cost points/minute), not dollar-based. The primary cost driver is deep pagination -- pages beyond 100 cost 3-30x more. Optimize by using incremental sync, caching, and avoiding full table scans.

## Cost Model

### Rate Limit Cost Structure

| Page Range | Cost per Request | Notes |
|------------|-----------------|-------|
| 1-100 | 1 point | Standard |
| 101-150 | 3 points | 3x multiplier |
| 151-250 | 8 points | 8x multiplier |
| 251-500 | 10 points | 10x multiplier |
| 501+ | 30 points | 30x multiplier |

**Budget: 600 points/minute.** This is the ceiling regardless of SalesLoft plan tier.

### Cost Calculator

```typescript
function calculateSyncCost(totalRecords: number, perPage = 100) {
  const pages = Math.ceil(totalRecords / perPage);
  let cost = 0;
  for (let p = 1; p <= pages; p++) {
    if (p <= 100) cost += 1;
    else if (p <= 150) cost += 3;
    else if (p <= 250) cost += 8;
    else if (p <= 500) cost += 10;
    else cost += 30;
  }
  const minutes = Math.ceil(cost / 600);
  return { pages, cost, minutes, pointsPerMinute: 600 };
}

// Examples:
// 1,000 records = 10 pages = 10 points = instant
// 10,000 records = 100 pages = 100 points = instant
// 25,000 records = 250 pages = 100 + 150 + 800 = 1050 points = ~2 min
// 50,000 records = 500 pages = 100 + 150 + 800 + 2500 = 3550 points = ~6 min
```

## Cost Reduction Strategies

### Strategy 1: Incremental Sync (Biggest Win)

```typescript
// Full sync of 25k people: 1050 points
// Incremental sync of last hour's changes: ~1-5 points
const { data } = await api.get('/people.json', {
  params: {
    updated_at: { gt: lastSyncTime }, // Only changed records
    per_page: 100,
    page: 1,
  },
});
```

### Strategy 2: Cache Frequently Accessed Data

```typescript
// Cadence list rarely changes -- cache for 5 minutes
const cadences = await cachedGet('/cadences.json', { per_page: 100 }, 300_000);

// Person lookup by email -- cache for 1 minute
const person = await cachedGet('/people.json', { email_addresses: [email] }, 60_000);
```

### Strategy 3: Webhook-Driven Instead of Polling

```typescript
// EXPENSIVE: Poll every minute for changes
setInterval(() => api.get('/people.json', { params: { updated_at: { gt: lastCheck } }}), 60_000);

// FREE: Receive webhooks for changes (0 API cost)
app.post('/webhooks/salesloft', (req, res) => {
  handlePersonUpdate(req.body.data);
  res.status(200).send();
});
```

### Strategy 4: Request Consolidation

```typescript
// EXPENSIVE: 3 separate requests = 3 points
const person = await api.get(`/people/${id}.json`);
const cadences = await api.get('/cadences.json');
const activities = await api.get('/activities/emails.json');

// CHEAPER: Parallel but still 3 points -- at least saves wall-clock time
const [person, cadences, activities] = await Promise.all([...]);
```

## Usage Monitoring

```typescript
class ApiCostTracker {
  private costs: { timestamp: number; endpoint: string; cost: number }[] = [];

  track(endpoint: string, page: number) {
    let cost = 1;
    if (page > 500) cost = 30;
    else if (page > 250) cost = 10;
    else if (page > 150) cost = 8;
    else if (page > 100) cost = 3;

    this.costs.push({ timestamp: Date.now(), endpoint, cost });
  }

  lastMinuteCost(): number {
    const cutoff = Date.now() - 60_000;
    return this.costs.filter(c => c.timestamp > cutoff).reduce((sum, c) => sum + c.cost, 0);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Frequent 429s | Deep pagination or polling | Switch to incremental sync + webhooks |
| Sync takes hours | Full table scan nightly | Switch to incremental with 5-min intervals |
| Rate limit exhausted | Multiple integrations sharing key | Use separate OAuth apps |

## Resources

- [SalesLoft Rate Limits](https://developers.salesloft.com/docs/platform/api-basics/rate-limits/)
- [SalesLoft Pricing](https://salesloft.com/pricing)

## Next Steps

For architecture patterns, see `salesloft-reference-architecture`.
