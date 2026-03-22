---
name: salesforce-load-scale
description: |
  Implement Salesforce load testing, API limit capacity planning, and Bulk API scaling.
  Use when running performance tests against Salesforce, planning API consumption,
  or scaling high-volume Salesforce integrations.
  Trigger with phrases like "salesforce load test", "salesforce scale",
  "salesforce performance test", "salesforce capacity planning", "salesforce high volume".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(sf:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Load & Scale

## Overview
Load testing, scaling strategies, and capacity planning for Salesforce integrations. Focus on API limit budgeting, Bulk API throughput, and handling Salesforce's unique constraint: org-wide shared limits.

## Prerequisites
- k6 or Artillery load testing tool
- Sandbox or Developer org for testing (never load test production)
- Understanding of your org's API limit allocation
- Monitoring configured (see `salesforce-observability`)

## Instructions

### Step 1: Calculate API Limit Budget

```typescript
const conn = await getConnection();
const limits = await conn.request('/services/data/v59.0/limits/');

const budget = {
  dailyMax: limits.DailyApiRequests.Max,
  currentlyUsed: limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining,
  remaining: limits.DailyApiRequests.Remaining,
  // Budget allocation
  integrationA: Math.floor(limits.DailyApiRequests.Max * 0.40), // 40% for primary sync
  integrationB: Math.floor(limits.DailyApiRequests.Max * 0.20), // 20% for secondary
  salesUsers: Math.floor(limits.DailyApiRequests.Max * 0.30),   // 30% for Salesforce UI users
  headroom: Math.floor(limits.DailyApiRequests.Max * 0.10),     // 10% buffer
};

console.table(budget);
// Example (Enterprise, 50 users): 150,000 daily calls
// Integration A: 60,000 | Integration B: 30,000 | Users: 45,000 | Buffer: 15,000
```

### Step 2: Load Test with k6 (against Sandbox)

```javascript
// salesforce-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const SF_TOKEN = __ENV.SF_ACCESS_TOKEN;
const SF_INSTANCE = __ENV.SF_INSTANCE_URL;

export const options = {
  stages: [
    { duration: '1m', target: 5 },    // Ramp up
    { duration: '3m', target: 5 },    // Steady state
    { duration: '1m', target: 20 },   // Peak load
    { duration: '3m', target: 20 },   // Sustained peak
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],  // SF API calls are slower than typical SaaS
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  // SOQL query
  const queryRes = http.get(
    `${SF_INSTANCE}/services/data/v59.0/query/?q=SELECT+Id,Name+FROM+Account+LIMIT+10`,
    { headers: { Authorization: `Bearer ${SF_TOKEN}` } }
  );
  check(queryRes, { 'query 200': (r) => r.status === 200 });

  // sObject retrieve
  const retrieveRes = http.get(
    `${SF_INSTANCE}/services/data/v59.0/sobjects/Account/describe`,
    { headers: { Authorization: `Bearer ${SF_TOKEN}` } }
  );
  check(retrieveRes, { 'describe 200': (r) => r.status === 200 });

  // Check rate limit headers
  const limitInfo = queryRes.headers['Sforce-Limit-Info'];
  if (limitInfo) {
    const [used, max] = limitInfo.replace('api-usage=', '').split('/');
    if (parseInt(used) / parseInt(max) > 0.8) {
      console.warn(`API usage at ${used}/${max}`);
    }
  }

  sleep(1); // Respect rate limits
}
```

```bash
# Get access token for load test
SF_ACCESS_TOKEN=$(sf org display --target-org my-sandbox --json | jq -r '.result.accessToken')
SF_INSTANCE_URL=$(sf org display --target-org my-sandbox --json | jq -r '.result.instanceUrl')

# Run load test (ONLY against sandbox)
k6 run \
  --env SF_ACCESS_TOKEN=$SF_ACCESS_TOKEN \
  --env SF_INSTANCE_URL=$SF_INSTANCE_URL \
  salesforce-load-test.js
```

### Step 3: Bulk API Throughput Testing

```typescript
// Bulk API 2.0 can process millions of records per job
// Key limits:
// - 15,000 Bulk API jobs/day
// - 150,000,000 records per 24hr rolling period
// - 10 concurrent Bulk API jobs

// Generate test data
function generateTestCsv(count: number): string {
  const lines = ['FirstName,LastName,Email,External_ID__c'];
  for (let i = 0; i < count; i++) {
    lines.push(`Test${i},User${i},test${i}@loadtest.example.com,LOAD-${i}`);
  }
  return lines.join('\n');
}

// Measure Bulk API throughput
const startTime = Date.now();
const results = await conn.bulk2.loadAndWaitForResults({
  object: 'Contact',
  operation: 'upsert',
  externalIdFieldName: 'External_ID__c',
  input: generateTestCsv(50000),
  pollInterval: 5000,
});

const duration = (Date.now() - startTime) / 1000;
const throughput = results.successfulResults.length / duration;

console.log({
  records: results.successfulResults.length,
  failures: results.failedResults.length,
  durationSeconds: duration.toFixed(1),
  recordsPerSecond: throughput.toFixed(1),
});
// Typical: 1,000-5,000 records/second depending on triggers and validation rules
```

### Step 4: Scaling Strategies

```typescript
// Strategy 1: Use Bulk API for large datasets (separate limit pool)
// Regular API: shared daily limit
// Bulk API: 15,000 jobs/day, unlimited records per job

// Strategy 2: Batch with sObject Collections (200 records/call)
// 100,000 API calls * 200 records/call = 20M records/day via REST

// Strategy 3: Reduce describe/metadata calls (cache aggressively)
// A single describe call can return 500+ fields — cache for hours

// Strategy 4: Use Composite API (25 operations per call)
// Replaces 25 individual calls with 1

// Strategy 5: Off-peak scheduling
// Run bulk jobs during business hours when sales users are active
// This ensures API limit usage is spread across the day
```

### Step 5: Capacity Planning Table

| Operation | Records/Day | API Calls Required | Strategy |
|-----------|------------|-------------------|----------|
| Account sync | 10,000 | 50 (Collections) | sObject Collections, 200/call |
| Contact sync | 100,000 | 1 (Bulk job) | Bulk API 2.0 |
| Opportunity queries | 5,000 | 25 (SOQL) | Relationship queries, cache |
| Real-time updates | 500 | 500 | REST API, individual calls |
| Metadata/describe | Constant | 10 (cached) | Cache with 1-hour TTL |
| **Total** | **115,500** | **586** | **Well within limits** |

## Output
- API limit budget allocated across integrations
- Load test script targeting sandbox
- Bulk API throughput benchmarked
- Scaling strategies documented
- Capacity planning table for production

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `REQUEST_LIMIT_EXCEEDED` during test | Wrong org (testing production) | ONLY test against sandbox |
| Bulk job timeout | Too many triggers firing | Disable non-essential triggers in sandbox |
| Low throughput | Validation rules, workflows | Test with rules disabled, then enabled |
| Inconsistent results | Concurrent jobs contending | Run one test at a time |

## Resources
- [API Limits by Edition](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)
- [Bulk API 2.0 Limits](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/bulk_api_2_0.htm)
- [k6 Documentation](https://k6.io/docs/)

## Next Steps
For reliability patterns, see `salesforce-reliability-patterns`.
