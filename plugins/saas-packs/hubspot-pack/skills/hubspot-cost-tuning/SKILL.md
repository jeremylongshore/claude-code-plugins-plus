---
name: hubspot-cost-tuning
description: |
  Optimize HubSpot costs through API call reduction, plan selection, and usage monitoring.
  Use when analyzing HubSpot API usage, reducing unnecessary calls,
  or implementing usage tracking and budget alerts.
  Trigger with phrases like "hubspot cost", "hubspot API usage",
  "reduce hubspot calls", "hubspot pricing", "hubspot budget", "hubspot quota".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Cost Tuning

## Overview

Optimize HubSpot integration costs by reducing API call volume, monitoring usage against daily limits, and choosing the right plan.

## Prerequisites

- Access to HubSpot account settings (Settings > Account > Usage & Limits)
- Understanding of current API usage patterns

## Instructions

### Step 1: Understand HubSpot API Pricing Model

HubSpot API calls are included with your subscription tier. There is no per-call billing, but exceeding limits results in `429 Too Many Requests` errors that block your integration.

| Plan | Daily API Limit | Per-Second Limit |
|------|----------------|-----------------|
| Free / Starter | 250,000 | 10 |
| Professional | 500,000 | 10 |
| Enterprise | 500,000 | 10 |
| API Limit Increase Add-on | 1,000,000 | 10 |

**Key insight:** The daily limit is per portal (shared across all apps). A poorly written integration can consume the entire quota and block all other apps.

### Step 2: Monitor Current Usage

```bash
# Check rate limit headers on any API call
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i ratelimit

# Output:
# X-HubSpot-RateLimit-Daily: 500000
# X-HubSpot-RateLimit-Daily-Remaining: 487234
# X-HubSpot-RateLimit-Secondly: 10
# X-HubSpot-RateLimit-Secondly-Remaining: 9
```

```typescript
// Programmatic usage tracking
class HubSpotUsageTracker {
  private dailyCalls = 0;
  private lastReset = new Date();

  track(): void {
    this.dailyCalls++;

    // Reset counter at midnight
    const now = new Date();
    if (now.getDate() !== this.lastReset.getDate()) {
      this.dailyCalls = 0;
      this.lastReset = now;
    }
  }

  getUsage(): { daily: number; percentUsed: number } {
    const limit = parseInt(process.env.HUBSPOT_DAILY_LIMIT || '500000');
    return {
      daily: this.dailyCalls,
      percentUsed: (this.dailyCalls / limit) * 100,
    };
  }

  shouldAlert(): boolean {
    return this.getUsage().percentUsed > 80;
  }
}
```

### Step 3: High-Impact Cost Reductions

#### Replace Individual Reads with Batch Reads

```typescript
// BEFORE: 100 API calls
for (const id of contactIds) {
  await client.crm.contacts.basicApi.getById(id, ['email']);
}

// AFTER: 1 API call (100x reduction)
await client.crm.contacts.batchApi.read({
  inputs: contactIds.map(id => ({ id })),
  properties: ['email'],
  propertiesWithHistory: [],
});
```

#### Use Search Instead of List + Filter

```typescript
// BEFORE: Fetch all, filter in memory (wastes API calls + bandwidth)
let after: string | undefined;
const matches = [];
do {
  const page = await client.crm.contacts.basicApi.getPage(100, after, ['lifecyclestage']);
  matches.push(...page.results.filter(c => c.properties.lifecyclestage === 'customer'));
  after = page.paging?.next?.after;
} while (after);  // Could be hundreds of pages

// AFTER: 1 search call with server-side filtering
const results = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'lifecyclestage', operator: 'EQ', value: 'customer' }],
  }],
  properties: ['email', 'firstname'],
  limit: 100, after: 0, sorts: [],
});
```

#### Cache Pipeline and Property Metadata

```typescript
// Pipelines and properties change rarely -- cache for 1 hour
// This saves 2 API calls per deal creation if you look up stage IDs

// BEFORE: 2 calls every time
const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
const properties = await client.crm.properties.coreApi.getAll('deals');

// AFTER: 2 calls per hour (from cache)
const pipelines = await getCachedPipelines('deals');  // see performance-tuning skill
```

#### Use Webhooks Instead of Polling

```typescript
// BEFORE: Poll for changes every 60 seconds (1,440 calls/day)
setInterval(async () => {
  const recent = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{
        propertyName: 'lastmodifieddate',
        operator: 'GTE',
        value: String(Date.now() - 60000),
      }],
    }],
    properties: ['email'], limit: 100, after: 0, sorts: [],
  });
  processChanges(recent.results);
}, 60000);

// AFTER: 0 polling calls (HubSpot pushes changes to you)
// Set up webhook subscription for contact.propertyChange
// See hubspot-webhooks-events skill
```

### Step 4: Usage Dashboard Query

```sql
-- Track API usage if you log calls to a database
SELECT
  DATE_TRUNC('hour', called_at) as hour,
  endpoint,
  COUNT(*) as calls,
  COUNT(*) FILTER (WHERE status_code = 429) as rate_limited,
  AVG(response_ms) as avg_latency_ms
FROM hubspot_api_log
WHERE called_at >= NOW() - INTERVAL '24 hours'
GROUP BY 1, 2
ORDER BY calls DESC;
```

## Output

- API call volume tracked and monitored
- Batch operations replacing individual calls (100x reduction)
- Search replacing list+filter patterns
- Webhooks replacing polling (1,440 calls/day saved)
- Metadata cached to avoid redundant lookups

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Daily limit hit | Unoptimized code | Apply batch + cache + webhook patterns |
| All apps blocked | Shared portal limit | Identify heaviest caller, optimize |
| No visibility | No tracking | Add usage counter middleware |
| Sudden spike | New feature deployed | Review new code for N+1 patterns |

## Resources

- [HubSpot API Usage Limits](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [HubSpot Pricing](https://www.hubspot.com/pricing)
- [Batch Operations Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)

## Next Steps

For architecture patterns, see `hubspot-reference-architecture`.
