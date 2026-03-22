---
name: algolia-webhooks-events
description: |
  Implement Algolia Insights API for click/conversion tracking, search analytics,
  and real-time event-driven index updates via database change listeners.
  Trigger: "algolia events", "algolia analytics", "algolia insights",
  "algolia click tracking", "algolia conversion", "algolia event tracking".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Events & Insights

## Overview

Algolia doesn't use traditional webhooks. Instead, it provides the **Insights API** for sending user behavior events (clicks, conversions, views) back to Algolia, and the **Analytics API** for reading search performance data. For keeping your index in sync, you build event-driven pipelines from your database to Algolia.

## Prerequisites

- `algoliasearch` v5 installed (Insights client is included)
- Index with records and `queryID` enabled (for click analytics)
- `search-insights` npm package for frontend event tracking

## Instructions

### Step 1: Enable Click Analytics in Search

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Enable clickAnalytics to get queryID in search results
const { hits, queryID } = await client.searchSingleIndex({
  indexName: 'products',
  searchParams: {
    query: 'running shoes',
    clickAnalytics: true,  // Returns queryID for event correlation
  },
});
// queryID links this search to subsequent click/conversion events
```

### Step 2: Send Click and Conversion Events (Backend)

```typescript
// The Insights API is built into the algoliasearch client
// Events connect user behavior back to specific search queries

// Track a click on a search result
await client.pushEvents({
  events: [{
    eventType: 'click',
    eventName: 'Product Clicked',
    index: 'products',
    userToken: 'user-123',        // Unique user identifier
    queryID: queryID,              // From search response
    objectIDs: ['product-456'],    // What was clicked
    positions: [3],                // Position in results (1-indexed)
    timestamp: Date.now(),
  }],
});

// Track a conversion (purchase, add-to-cart)
await client.pushEvents({
  events: [{
    eventType: 'conversion',
    eventName: 'Product Purchased',
    index: 'products',
    userToken: 'user-123',
    queryID: queryID,
    objectIDs: ['product-456'],
    timestamp: Date.now(),
  }],
});

// Track a view (product page visit, no search context)
await client.pushEvents({
  events: [{
    eventType: 'view',
    eventName: 'Product Viewed',
    index: 'products',
    userToken: 'user-123',
    objectIDs: ['product-456'],
    timestamp: Date.now(),
  }],
});
```

### Step 3: Frontend Event Tracking with search-insights

```bash
npm install search-insights
```

```typescript
// Frontend: lightweight event tracking
import { default as aa } from 'search-insights';

aa('init', {
  appId: 'YourAppID',
  apiKey: 'YourSearchOnlyKey',  // Search-only key is fine for events
});

// Set user token (anonymous or authenticated)
aa('setUserToken', 'user-123');

// After user clicks a search result
aa('clickedObjectIDsAfterSearch', {
  eventName: 'Product Clicked',
  index: 'products',
  queryID: 'abc123',          // From search response
  objectIDs: ['product-456'],
  positions: [3],
});

// After user converts (purchases)
aa('convertedObjectIDsAfterSearch', {
  eventName: 'Product Purchased',
  index: 'products',
  queryID: 'abc123',
  objectIDs: ['product-456'],
});
```

### Step 4: Read Search Analytics

```typescript
// The analytics client is part of algoliasearch
const analyticsClient = client.initAnalytics({ region: 'us' });

// Top searches
const { searches } = await client.getTopSearches({
  index: 'products',
  startDate: '2025-01-01',
  endDate: '2025-01-31',
});
searches.forEach(s => console.log(`"${s.search}" — ${s.count} searches, ${s.nbHits} avg hits`));

// Searches with no results (critical for relevance tuning)
const { searches: noResults } = await client.getSearchesNoResults({
  index: 'products',
  startDate: '2025-01-01',
  endDate: '2025-01-31',
});
noResults.forEach(s => console.log(`"${s.search}" — ${s.count} times, 0 results`));

// Click-through rate and conversion rate
const { clickRate, conversionRate } = await client.getClickThroughRate({
  index: 'products',
});
console.log(`CTR: ${(clickRate * 100).toFixed(1)}%, CVR: ${(conversionRate * 100).toFixed(1)}%`);
```

### Step 5: Database-to-Algolia Sync Pipeline

```typescript
// Real-time index updates from your database change events
// Works with Prisma, Drizzle, Mongoose change streams, PostgreSQL LISTEN/NOTIFY

import { getClient } from './algolia/client';

// Prisma middleware example
prisma.$use(async (params, next) => {
  const result = await next(params);
  const client = getClient();

  if (params.model === 'Product') {
    switch (params.action) {
      case 'create':
      case 'update':
        await client.saveObject({
          indexName: 'products',
          body: {
            objectID: result.id,
            name: result.name,
            price: result.price,
            category: result.category,
          },
        });
        break;
      case 'delete':
        await client.deleteObject({
          indexName: 'products',
          objectID: params.args.where.id,
        });
        break;
    }
  }

  return result;
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `queryID` is null | `clickAnalytics: true` not set | Add to search params |
| Events not appearing in dashboard | Wrong `userToken` format | Use stable, non-empty string identifiers |
| Analytics shows 0 CTR | Events not correlated | Ensure `queryID` matches between search and click |
| Sync pipeline losing events | No retry on failure | Add dead-letter queue for failed updates |

## Resources

- [Insights API](https://www.algolia.com/doc/guides/sending-events/getting-started/)
- [Analytics API](https://www.algolia.com/doc/libraries/javascript/v5/methods/analytics/)
- [search-insights](https://www.npmjs.com/package/search-insights)
- [Click Analytics Guide](https://www.algolia.com/doc/guides/getting-analytics/search-analytics/out-of-the-box-analytics/)

## Next Steps

For performance optimization, see `algolia-performance-tuning`.
