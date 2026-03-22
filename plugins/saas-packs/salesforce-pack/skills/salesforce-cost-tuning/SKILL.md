---
name: salesforce-cost-tuning
description: |
  Optimize Salesforce costs through API call reduction, edition selection, and license management.
  Use when analyzing Salesforce costs, reducing API consumption,
  or choosing the right Salesforce edition for your integration needs.
  Trigger with phrases like "salesforce cost", "salesforce pricing",
  "reduce salesforce costs", "salesforce license", "salesforce API usage", "salesforce budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Cost Tuning

## Overview
Optimize Salesforce costs by reducing API call consumption, choosing the right edition, and monitoring API usage budgets. Salesforce charges per-user licenses (not per-API-call), but API limits are tied to edition + license count.

## Prerequisites
- Access to Salesforce Setup > Company Information
- Understanding of current API usage patterns
- Access to contract/license details

## Instructions

### Step 1: Understand Salesforce Pricing Model

| Edition | Per-User/Month | API Calls/Day (Base) | Per-User API Calls |
|---------|---------------|---------------------|-------------------|
| Developer | Free | 15,000 | N/A (1 user) |
| Essentials | ~$25 | 15,000 | +1,000/user |
| Professional | ~$80 | 15,000 | +1,000/user |
| Enterprise | ~$165 | 100,000 | +1,000/user |
| Unlimited | ~$330 | 100,000 | +5,000/user |
| API Add-on Pack | Varies | +200K-10M/day | Per org |

**Key insight:** API calls are per-org, not per-user. A 50-user Enterprise org gets 100,000 + (50 * 1,000) = 150,000 daily API calls. All integrations share this pool.

### Step 2: Monitor Current Usage

```typescript
const conn = await getConnection();
const limits = await conn.request('/services/data/v59.0/limits/');

const apiUsage = {
  daily: {
    used: limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining,
    remaining: limits.DailyApiRequests.Remaining,
    max: limits.DailyApiRequests.Max,
    percentUsed: ((limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining) / limits.DailyApiRequests.Max * 100).toFixed(1),
  },
  bulk: {
    ingestJobs: limits.DailyBulkV2QueryJobs,
    queryJobs: limits.DailyBulkV2QueryJobs,
  },
  storage: {
    dataMB: `${limits.DataStorageMB.Max - limits.DataStorageMB.Remaining}/${limits.DataStorageMB.Max} MB`,
    fileMB: `${limits.FileStorageMB.Max - limits.FileStorageMB.Remaining}/${limits.FileStorageMB.Max} MB`,
  },
};

console.log('API Usage:', JSON.stringify(apiUsage, null, 2));
```

### Step 3: Reduce API Call Count (Biggest Cost Lever)

```typescript
// BEFORE: 1 API call per record = expensive
for (const contact of contacts) {
  await conn.sobject('Contact').create(contact); // 1000 calls for 1000 records
}

// AFTER: Batch with sObject Collections = 5 calls for 1000 records
for (let i = 0; i < contacts.length; i += 200) {
  const batch = contacts.slice(i, i + 200);
  await conn.sobject('Contact').create(batch); // Max 200 per call
}

// AFTER: Use Bulk API for 10K+ records = 1 job regardless of count
await conn.bulk2.loadAndWaitForResults({
  object: 'Contact',
  operation: 'insert',
  input: csvData, // Can be millions of rows
});
// Bulk API has its own separate daily limit (15,000 jobs)

// Cache describe calls — saves 50+ calls/day if you describe objects frequently
const describeCache = new Map();
async function cachedDescribe(objectName: string) {
  if (!describeCache.has(objectName)) {
    describeCache.set(objectName, await conn.sobject(objectName).describe());
  }
  return describeCache.get(objectName);
}
```

### Step 4: API Call Budget Tracking

```typescript
class ApiCallBudget {
  private dailyBudget: number;
  private callsToday = 0;

  constructor(dailyBudget: number) {
    this.dailyBudget = dailyBudget;
  }

  async refreshFromOrg(conn: jsforce.Connection): Promise<void> {
    const limits = await conn.request('/services/data/v59.0/limits/');
    this.callsToday = limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining;
    // Note: this call itself costs 1 API call — don't check too frequently
  }

  canSpend(estimatedCalls: number): { allowed: boolean; reason?: string } {
    const projected = this.callsToday + estimatedCalls;

    if (projected > this.dailyBudget * 0.95) {
      return { allowed: false, reason: `Would exceed 95% of ${this.dailyBudget} daily budget` };
    }

    if (projected > this.dailyBudget * 0.80) {
      console.warn(`API budget warning: ${this.callsToday}/${this.dailyBudget} used`);
    }

    return { allowed: true };
  }
}
```

### Step 5: Edition Right-Sizing

```
Decision tree for Salesforce edition:

If API calls/day < 15,000:
  → Developer Edition (free) or Professional ($80/user/month)

If API calls/day 15,000-150,000:
  → Enterprise Edition ($165/user/month)

If API calls/day > 150,000:
  → Unlimited ($330/user/month) or API Add-on Pack
  → OR reduce calls with batching/caching (usually cheaper)

If you need just data sync:
  → Consider Heroku Connect ($$$) for automatic bi-directional sync
  → Eliminates most API calls — data syncs via Change Data Capture
```

## Output
- Current API usage analyzed
- Cost reduction strategies applied (batching, caching, Bulk API)
- API call budget tracking implemented
- Edition recommendation based on usage

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected API call spike | Unoptimized loop/query | Use Collections or Bulk API |
| Budget exceeded | Missing monitoring | Add budget tracking class |
| Storage limit | Too many records/files | Archive old data, delete test data |
| License overspend | Unused integration licenses | Audit active users quarterly |

## Resources
- [Salesforce Editions & Pricing](https://www.salesforce.com/editions-pricing/overview/)
- [API Request Limits by Edition](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)
- [Limits REST Resource](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm)

## Next Steps
For architecture patterns, see `salesforce-reference-architecture`.
