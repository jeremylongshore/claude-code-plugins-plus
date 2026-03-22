---
name: bamboohr-cost-tuning
description: |
  Optimize BambooHR integration costs through request reduction, caching,
  and usage monitoring. Use when analyzing API usage patterns, reducing
  unnecessary calls, or implementing request budgets.
  Trigger with phrases like "bamboohr cost", "bamboohr usage",
  "reduce bamboohr calls", "bamboohr optimization", "bamboohr budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, optimization]
compatible-with: claude-code
---

# BambooHR Cost Tuning

## Overview

BambooHR pricing is per-employee-per-month (not per-API-call), but excessive API usage triggers rate limiting (503 errors) which causes sync failures and operational issues. This skill covers reducing API call volume, monitoring usage, and building efficient sync patterns.

## Prerequisites

- BambooHR integration in production
- Understanding of current API usage patterns
- Application logging capturing API calls

## Instructions

### Step 1: Understand BambooHR Pricing

BambooHR charges by **employee count**, not API calls:

| Plan | Pricing Model | API Access |
|------|--------------|------------|
| Essentials | Per employee/month | Full REST API |
| Advantage | Per employee/month | Full REST API + advanced reports |
| Custom/Enterprise | Negotiated | Full API + dedicated support |

**Key insight:** API call volume does not directly affect your bill, but hitting rate limits causes operational failures. Optimize for reliability, not cost.

### Step 2: Audit Current API Usage

```typescript
// Instrument your client to log all API calls
class InstrumentedBambooHRClient {
  private callLog: { endpoint: string; method: string; timestamp: number; durationMs: number }[] = [];

  async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const start = Date.now();
    const result = await this.innerClient.request<T>(method, path, body);
    this.callLog.push({
      endpoint: path.split('?')[0], // Strip query params
      method,
      timestamp: start,
      durationMs: Date.now() - start,
    });
    return result;
  }

  generateReport(): void {
    // Group by endpoint
    const byEndpoint = new Map<string, number>();
    for (const call of this.callLog) {
      const key = `${call.method} ${call.endpoint}`;
      byEndpoint.set(key, (byEndpoint.get(key) || 0) + 1);
    }

    console.log('\n=== BambooHR API Usage Report ===');
    console.log(`Total calls: ${this.callLog.length}`);
    console.log(`Time window: ${((Date.now() - this.callLog[0]?.timestamp || 0) / 1000 / 60).toFixed(1)} minutes`);
    console.log('\nBy endpoint:');
    for (const [endpoint, count] of [...byEndpoint.entries()].sort((a, b) => b[1] - a[1])) {
      const pct = ((count / this.callLog.length) * 100).toFixed(1);
      console.log(`  ${count.toString().padStart(5)} (${pct}%)  ${endpoint}`);
    }
  }
}
```

### Step 3: Eliminate Wasteful Patterns

**Pattern 1: Replace polling with webhooks**

```typescript
// BAD: Polling every 5 minutes (288 calls/day minimum)
setInterval(async () => {
  const dir = await client.getDirectory();
  checkForChanges(dir);
}, 5 * 60 * 1000);

// GOOD: Use webhooks for real-time changes (0 polling calls)
// See bamboohr-webhooks-events skill
// Only poll as a fallback safety net (once per hour)
setInterval(async () => {
  const changed = await client.request('GET',
    `/employees/changed/?since=${lastSync}`);
  // Only process if webhook missed something
}, 60 * 60 * 1000);
```

**Pattern 2: Request only needed fields**

```typescript
// BAD: Requesting all fields when you only need 3
const emp = await client.getEmployee(id, [
  'firstName', 'lastName', 'displayName', 'jobTitle', 'department',
  'division', 'location', 'workEmail', 'homeEmail', 'mobilePhone',
  'hireDate', 'payRate', 'payType', 'ssn', 'dateOfBirth', // ...etc
]);

// GOOD: Only request what you use
const emp = await client.getEmployee(id, ['firstName', 'lastName', 'workEmail']);
```

**Pattern 3: Cache the directory**

```typescript
// BAD: Fetching directory on every page load
app.get('/employees', async (req, res) => {
  const dir = await client.getDirectory(); // Called 1000x/day
  res.json(dir.employees);
});

// GOOD: Cache with webhook-based invalidation
let cachedDirectory: any = null;
let cacheTimestamp = 0;

async function getDirectory() {
  if (cachedDirectory && Date.now() - cacheTimestamp < 5 * 60 * 1000) {
    return cachedDirectory;
  }
  cachedDirectory = await client.getDirectory();
  cacheTimestamp = Date.now();
  return cachedDirectory;
}

// Invalidate on webhook
function onWebhookReceived() {
  cachedDirectory = null;
}
```

**Pattern 4: Use custom reports for bulk data**

```typescript
// BAD: 500 individual employee GETs
for (const id of employeeIds) {
  await client.getEmployee(id, ['firstName', 'department']);
}

// GOOD: 1 custom report
const all = await client.customReport(['firstName', 'lastName', 'department']);
```

### Step 4: Implement Request Budget

```typescript
class RequestBudget {
  private count = 0;
  private windowStart = Date.now();
  private readonly maxPerHour: number;

  constructor(maxPerHour = 500) {
    this.maxPerHour = maxPerHour;
  }

  async acquire(): Promise<void> {
    // Reset counter every hour
    if (Date.now() - this.windowStart > 3600_000) {
      this.count = 0;
      this.windowStart = Date.now();
    }

    if (this.count >= this.maxPerHour) {
      const waitMs = 3600_000 - (Date.now() - this.windowStart);
      console.warn(`Request budget exhausted. Waiting ${(waitMs / 1000).toFixed(0)}s`);
      await new Promise(r => setTimeout(r, waitMs));
      this.count = 0;
      this.windowStart = Date.now();
    }

    this.count++;
  }

  stats() {
    return {
      used: this.count,
      budget: this.maxPerHour,
      remaining: this.maxPerHour - this.count,
      windowResetIn: Math.max(0, 3600_000 - (Date.now() - this.windowStart)),
    };
  }
}

const budget = new RequestBudget(500);

// Wrap all BambooHR calls
async function budgetedRequest<T>(operation: () => Promise<T>): Promise<T> {
  await budget.acquire();
  return operation();
}
```

### Step 5: Usage Dashboard Query

```sql
-- If logging API calls to a database
SELECT
  DATE_TRUNC('hour', timestamp) AS hour,
  endpoint,
  COUNT(*) AS calls,
  AVG(duration_ms) AS avg_latency,
  COUNT(*) FILTER (WHERE status >= 400) AS errors,
  COUNT(*) FILTER (WHERE status = 503) AS rate_limits
FROM bamboohr_api_log
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY 1, 2
ORDER BY 1 DESC, calls DESC;
```

## Output

- API usage audit identifying wasteful patterns
- Polling replaced with webhooks where possible
- Request budget preventing rate limit hits
- Field-level optimization (request only needed data)
- Caching with webhook-based invalidation

## Optimization Impact Summary

| Optimization | Calls Before | Calls After | Reduction |
|-------------|-------------|-------------|-----------|
| Webhooks vs polling | 288/day | 24/day (safety net) | 92% |
| Custom reports vs N+1 | 501/sync | 1/sync | 99.8% |
| Directory caching | 1000/day | 12/day | 98.8% |
| Incremental sync | Full pull | Delta only | 90-99% |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Budget exhausted | High-traffic feature | Increase budget or add caching |
| Stale cached data | Cache TTL too long | Reduce TTL or invalidate on webhook |
| Webhook delivery gaps | BambooHR delivery failure | Keep hourly polling as fallback |
| Rate limit during sync | Too many parallel requests | Use queue with concurrency limit |

## Resources

- [BambooHR Pricing](https://www.bamboohr.com/pricing)
- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)

## Next Steps

For architecture patterns, see `bamboohr-reference-architecture`.
