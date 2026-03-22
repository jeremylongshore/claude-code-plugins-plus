---
name: salesforce-rate-limits
description: |
  Implement Salesforce API limit management, backoff, and quota monitoring.
  Use when handling REQUEST_LIMIT_EXCEEDED errors, implementing retry logic,
  or optimizing API request throughput for Salesforce.
  Trigger with phrases like "salesforce rate limit", "salesforce API limit",
  "salesforce 403", "salesforce retry", "salesforce governor limits", "API quota".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Rate Limits

## Overview
Handle Salesforce API limits gracefully. Salesforce uses a 24-hour rolling limit (not per-minute), plus concurrent request limits and Bulk API quotas.

## Prerequisites
- jsforce connection configured
- Understanding of your org's edition and license count
- Access to Setup > Company Information

## Instructions

### Step 1: Understand Salesforce API Limits

| Limit Type | Calculation | Example (Enterprise, 50 users) |
|-----------|-------------|-------------------------------|
| Daily API Requests | Base + (per-user * licenses) | 100,000 + (1,000 * 50) = 150,000 |
| Concurrent API (long-running) | 25 per org | 25 |
| Bulk API 2.0 Ingest Jobs | 15,000/day | 15,000 |
| Bulk API 2.0 Query Jobs | 15,000/day | 15,000 |
| Composite Subrequests | 25 per call | 25 |
| SOQL Query Row Limit | 50,000 per query | 50,000 |
| sObject Collections | 200 records per call | 200 |

**Key difference from most SaaS APIs:** Salesforce limits are per-org, not per-user or per-key. All integrations sharing the same org share the same pool.

### Step 2: Monitor Remaining Quota

```typescript
import { getConnection } from './salesforce/connection';

async function checkApiLimits(): Promise<{
  used: number;
  remaining: number;
  max: number;
  percentUsed: number;
}> {
  const conn = await getConnection();
  const limits = await conn.request('/services/data/v59.0/limits/');

  const daily = limits.DailyApiRequests;
  const used = daily.Max - daily.Remaining;
  const percentUsed = (used / daily.Max) * 100;

  return {
    used,
    remaining: daily.Remaining,
    max: daily.Max,
    percentUsed: Math.round(percentUsed * 10) / 10,
  };
}

// Also available in every REST API response header:
// Sforce-Limit-Info: api-usage=135/150000
```

### Step 3: Implement Backoff for REQUEST_LIMIT_EXCEEDED

```typescript
async function withSalesforceRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 2000, maxDelayMs: 60000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const errorCode = error.errorCode || error.name;

      // Only retry on transient/limit errors
      const retryable = [
        'REQUEST_LIMIT_EXCEEDED',
        'SERVER_UNAVAILABLE',
        'UNABLE_TO_LOCK_ROW',
      ];

      if (attempt === config.maxRetries || !retryable.includes(errorCode)) {
        throw error;
      }

      // Exponential backoff with jitter
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * 1000;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.warn(`${errorCode}: retry ${attempt + 1}/${config.maxRetries} in ${Math.round(delay)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Pre-Flight Limit Check

```typescript
class SalesforceQuotaGuard {
  private warningThreshold = 0.8; // Warn at 80%
  private blockThreshold = 0.95;  // Block at 95%

  async canMakeRequest(estimatedCalls: number = 1): Promise<{
    allowed: boolean;
    remaining: number;
    reason?: string;
  }> {
    const { remaining, max, percentUsed } = await checkApiLimits();

    if (remaining < estimatedCalls) {
      return {
        allowed: false,
        remaining,
        reason: `Only ${remaining} API calls remain (need ${estimatedCalls})`,
      };
    }

    if (percentUsed / 100 >= this.blockThreshold) {
      return {
        allowed: false,
        remaining,
        reason: `API usage at ${percentUsed}% — blocking to preserve quota`,
      };
    }

    if (percentUsed / 100 >= this.warningThreshold) {
      console.warn(`API usage at ${percentUsed}% (${remaining} remaining)`);
    }

    return { allowed: true, remaining };
  }
}
```

### Step 5: Reduce API Call Count

```typescript
// STRATEGY 1: Use sObject Collections (1 call = 200 records)
// Instead of 200 individual creates...
const records = contacts.map(c => ({ FirstName: c.first, LastName: c.last, Email: c.email }));
await conn.sobject('Contact').create(records); // 1 API call, not 200

// STRATEGY 2: Use Composite API (1 call = 25 operations)
// See salesforce-core-workflow-b

// STRATEGY 3: Use Bulk API for 10K+ records (1 job = unlimited records)
// Bulk API has its own separate limit pool

// STRATEGY 4: Cache describe calls — metadata rarely changes
const describeCache = new Map<string, any>();
async function cachedDescribe(sObjectType: string) {
  if (!describeCache.has(sObjectType)) {
    describeCache.set(sObjectType, await conn.sobject(sObjectType).describe());
  }
  return describeCache.get(sObjectType);
}

// STRATEGY 5: Use queryMore for pagination (doesn't count as extra API call)
let result = await conn.query('SELECT Id, Name FROM Contact');
while (!result.done) {
  result = await conn.queryMore(result.nextRecordsUrl!);
  // Process result.records
}
```

## Output
- API limit monitoring with threshold alerts
- Automatic retry with exponential backoff for limit errors
- Pre-flight quota checks before batch operations
- Strategies to reduce API call consumption

## Error Handling
| Error Code | HTTP Status | Meaning | Action |
|-----------|-------------|---------|--------|
| `REQUEST_LIMIT_EXCEEDED` | 403 | Daily API limit exceeded | Wait for 24hr window to reset |
| `CONCURRENT_LIMIT_EXCEEDED` | 403 | Too many concurrent requests | Queue and throttle |
| `SERVER_UNAVAILABLE` | 503 | Salesforce temporarily down | Retry with backoff |
| `UNABLE_TO_LOCK_ROW` | 409-equivalent | Record contention | Retry with backoff |

## Resources
- [API Request Limits](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)
- [Limits REST Resource](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm)
- [Apex Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm)

## Next Steps
For security configuration, see `salesforce-security-basics`.
