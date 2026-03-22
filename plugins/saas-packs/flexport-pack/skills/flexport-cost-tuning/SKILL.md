---
name: flexport-cost-tuning
description: |
  Optimize Flexport API usage costs through efficient pagination, caching,
  webhook-driven updates, and monitoring API call volume.
  Trigger: "flexport costs", "flexport API usage", "reduce flexport calls", "flexport billing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Cost Tuning

## Overview

Reduce Flexport API costs by minimizing unnecessary calls. Key strategies: use webhooks instead of polling, cache aggressively, maximize page sizes, and batch operations.

## Instructions

### Strategy 1: Webhooks Over Polling

```typescript
// BAD: Polling every 5 minutes (288 API calls/day per shipment)
setInterval(async () => {
  const shipment = await flexport(`/shipments/${id}`);
  if (shipment.data.status !== lastStatus) updateDB(shipment);
}, 5 * 60 * 1000);

// GOOD: Webhook-driven (0 API calls — Flexport pushes updates)
app.post('/webhooks/flexport', (req, res) => {
  const event = req.body;
  if (event.type === 'shipment.milestone') {
    updateDB(event.data);  // Only processes real changes
  }
  res.sendStatus(200);
});
// Savings: 100 shipments * 288 calls/day = 28,800 calls/day eliminated
```

### Strategy 2: Maximize Page Size

```typescript
// BAD: Default pagination (per=25)
// 1000 shipments = 40 API calls

// GOOD: Max pagination (per=100)
// 1000 shipments = 10 API calls (75% reduction)
const shipments = await flexport('/shipments?per=100&page=1');
```

### Strategy 3: Cache with Smart TTLs

| Data Type | Change Frequency | Cache TTL | Impact |
|-----------|-----------------|-----------|--------|
| Products | Rarely | 1 hour | ~95% fewer calls |
| Shipment list | Every few hours | 5 minutes | ~90% fewer calls |
| Shipment detail | On milestones | Until webhook | ~99% fewer calls |
| Purchase orders | Daily | 15 minutes | ~85% fewer calls |
| Freight invoices | Monthly | 1 hour | ~95% fewer calls |

### Strategy 4: Monitor API Usage

```typescript
// Track API call volume per endpoint
const apiMetrics = new Map<string, { count: number; lastReset: Date }>();

function trackAPICall(endpoint: string) {
  const key = endpoint.split('?')[0];  // Strip query params
  const metric = apiMetrics.get(key) || { count: 0, lastReset: new Date() };
  metric.count++;
  apiMetrics.set(key, metric);
}

// Report daily usage
function reportUsage() {
  console.log('=== Flexport API Usage ===');
  for (const [endpoint, { count }] of apiMetrics) {
    console.log(`  ${endpoint}: ${count} calls`);
  }
}
```

## Cost Reduction Checklist

- [ ] Replace polling with webhooks for shipment tracking
- [ ] Use `per=100` on all list endpoints
- [ ] Cache product catalog (1hr TTL)
- [ ] Cache shipment data, invalidate on webhooks
- [ ] Eliminate duplicate calls in page loads
- [ ] Monitor API call volume weekly

## Resources

- [Flexport Webhook Endpoints](https://apidocs.flexport.com/v2/tag/Webhook-Endpoints/)
- [Flexport API Reference](https://apidocs.flexport.com/)

## Next Steps

For architecture design, see `flexport-reference-architecture`.
