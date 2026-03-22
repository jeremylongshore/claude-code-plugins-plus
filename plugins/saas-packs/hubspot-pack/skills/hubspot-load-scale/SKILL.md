---
name: hubspot-load-scale
description: |
  Load test HubSpot integrations and plan capacity around API rate limits.
  Use when running performance tests, planning for traffic growth,
  or sizing your HubSpot integration for production load.
  Trigger with phrases like "hubspot load test", "hubspot scale",
  "hubspot capacity", "hubspot benchmark", "hubspot traffic planning".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Load & Scale

## Overview

Load testing and capacity planning for HubSpot integrations, constrained by the 10 requests/second and 500,000 requests/day API limits.

## Prerequisites

- k6 or similar load testing tool
- HubSpot developer test account (never load test against production)
- Understanding of HubSpot rate limits

## Instructions

### Step 1: Understand HubSpot Rate Limit Constraints

Your integration's maximum throughput is bound by HubSpot's limits:

| Constraint | Limit | Impact |
|-----------|-------|--------|
| Per-second | 10 req/sec | 600 req/min maximum |
| Daily | 500,000/day | ~347 req/min sustained |
| Batch size | 100 records/batch | Each batch = 1 API call |
| Search results | 10,000 total | Cannot page past 10K |
| Associations | 500 per record | Hard limit |

**Effective throughput with batching:**
- Individual operations: 10 records/sec
- Batch operations: 1,000 records/sec (10 batches/sec x 100 records/batch)

### Step 2: k6 Load Test Script

```javascript
// hubspot-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('hubspot_errors');
const rateLimited = new Rate('hubspot_rate_limited');

export const options = {
  stages: [
    { duration: '1m', target: 2 },    // warm up (2 req/sec)
    { duration: '3m', target: 5 },    // moderate load
    { duration: '2m', target: 8 },    // approach limit
    { duration: '2m', target: 10 },   // at limit
    { duration: '1m', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],       // 95% under 2s
    hubspot_errors: ['rate<0.05'],           // <5% errors
    hubspot_rate_limited: ['rate<0.10'],     // <10% rate limited
  },
};

const BASE_URL = 'https://api.hubapi.com';
const TOKEN = __ENV.HUBSPOT_ACCESS_TOKEN;

export default function () {
  // Test: List contacts (GET)
  const listRes = http.get(
    `${BASE_URL}/crm/v3/objects/contacts?limit=10&properties=email,firstname`,
    { headers: { Authorization: `Bearer ${TOKEN}` } }
  );

  check(listRes, { 'list contacts: 200': (r) => r.status === 200 });
  errorRate.add(listRes.status >= 400 && listRes.status !== 429);
  rateLimited.add(listRes.status === 429);

  sleep(0.1); // 100ms between requests per VU

  // Test: Search contacts (POST)
  const searchRes = http.post(
    `${BASE_URL}/crm/v3/objects/contacts/search`,
    JSON.stringify({
      filterGroups: [{
        filters: [{
          propertyName: 'lifecyclestage',
          operator: 'EQ',
          value: 'lead',
        }],
      }],
      properties: ['email'],
      limit: 10,
      after: 0,
      sorts: [],
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${TOKEN}`,
      },
    }
  );

  check(searchRes, { 'search contacts: 200': (r) => r.status === 200 });
  errorRate.add(searchRes.status >= 400 && searchRes.status !== 429);
  rateLimited.add(searchRes.status === 429);

  sleep(0.1);
}
```

```bash
# Run against test account only
k6 run --env HUBSPOT_ACCESS_TOKEN=$HUBSPOT_TEST_TOKEN hubspot-load-test.js
```

### Step 3: Capacity Planning Calculator

```typescript
interface CapacityPlan {
  operationType: string;
  recordsPerDay: number;
  apiCallsPerDay: number;
  batchApiCallsPerDay: number;
  percentOfDailyQuota: number;
  feasible: boolean;
}

function planCapacity(operations: Array<{
  type: string;
  recordsPerDay: number;
  batchable: boolean;
}>): CapacityPlan[] {
  const DAILY_LIMIT = 500_000;
  let totalCalls = 0;

  const plans = operations.map(op => {
    const apiCallsPerDay = op.batchable
      ? Math.ceil(op.recordsPerDay / 100) // batch: 100 per call
      : op.recordsPerDay;                  // individual: 1 per call

    totalCalls += apiCallsPerDay;

    return {
      operationType: op.type,
      recordsPerDay: op.recordsPerDay,
      apiCallsPerDay: op.batchable ? op.recordsPerDay : apiCallsPerDay,
      batchApiCallsPerDay: apiCallsPerDay,
      percentOfDailyQuota: (apiCallsPerDay / DAILY_LIMIT) * 100,
      feasible: apiCallsPerDay < DAILY_LIMIT * 0.5, // leave 50% headroom
    };
  });

  console.log(`\nTotal daily API calls: ${totalCalls.toLocaleString()} / ${DAILY_LIMIT.toLocaleString()}`);
  console.log(`Quota utilization: ${((totalCalls / DAILY_LIMIT) * 100).toFixed(1)}%`);

  if (totalCalls > DAILY_LIMIT) {
    console.warn('WARNING: Exceeds daily limit! Optimize with batching or reduce volume.');
  }

  return plans;
}

// Example capacity plan
planCapacity([
  { type: 'Sync contacts (read)', recordsPerDay: 50000, batchable: true },
  { type: 'Create deals', recordsPerDay: 500, batchable: true },
  { type: 'Search contacts', recordsPerDay: 10000, batchable: false },
  { type: 'Webhook processing', recordsPerDay: 5000, batchable: false },
]);
// Total: 500 + 5 + 10000 + 5000 = 15,505 API calls
// Quota: 3.1% -- very feasible
```

### Step 4: Scaling Patterns for High Volume

```typescript
// Pattern 1: Queue-based rate limiting
import PQueue from 'p-queue';

const hubspotQueue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10, // HubSpot's 10/sec limit
});

// Pattern 2: Batch aggregation
class BatchAggregator<T> {
  private buffer: T[] = [];
  private timer: NodeJS.Timeout | null = null;

  constructor(
    private maxBatch: number,
    private maxWaitMs: number,
    private flush: (items: T[]) => Promise<void>
  ) {}

  add(item: T): void {
    this.buffer.push(item);
    if (this.buffer.length >= this.maxBatch) {
      this.flushNow();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flushNow(), this.maxWaitMs);
    }
  }

  private async flushNow(): Promise<void> {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.buffer.length === 0) return;
    const batch = this.buffer.splice(0, this.maxBatch);
    await this.flush(batch);
  }
}

// Usage: aggregate individual creates into batch creates
const contactAggregator = new BatchAggregator(
  100,   // max batch size (HubSpot limit)
  5000,  // flush every 5 seconds max
  async (contacts) => {
    await client.crm.contacts.batchApi.create({
      inputs: contacts.map(c => ({ properties: c, associations: [] })),
    });
  }
);
```

## Output

- Understanding of HubSpot rate limit constraints
- k6 load test script for realistic testing
- Capacity planning calculator for daily operations
- Queue-based rate limiting for production use
- Batch aggregation pattern for high-volume writes

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Load test hits 429 immediately | Testing against shared portal | Use dedicated test account |
| k6 results inconsistent | HubSpot API latency varies | Run multiple iterations |
| Capacity plan exceeds limit | Too many individual calls | Convert to batch operations |
| Batch aggregator data loss | App crash before flush | Add persistence to buffer |

## Resources

- [HubSpot API Usage Guidelines](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [k6 Documentation](https://grafana.com/docs/k6/)
- [p-queue npm](https://github.com/sindresorhus/p-queue)

## Next Steps

For reliability patterns, see `hubspot-reliability-patterns`.
