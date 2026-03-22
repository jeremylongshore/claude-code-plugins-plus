---
name: hubspot-performance-tuning
description: |
  Optimize HubSpot API performance with caching, batching, and search optimization.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for HubSpot CRM operations.
  Trigger with phrases like "hubspot performance", "optimize hubspot",
  "hubspot slow", "hubspot caching", "hubspot batch", "hubspot latency".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Performance Tuning

## Overview

Optimize HubSpot API performance through batch operations, caching, search optimization, and request minimization.

## Prerequisites

- `@hubspot/api-client` installed
- Understanding of your access patterns (read-heavy vs write-heavy)
- Optional: Redis for distributed caching

## Instructions

### Step 1: Use Batch APIs Everywhere

The single biggest performance win: batch operations reduce API calls by up to 100x.

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

// BAD: 100 API calls for 100 contacts
async function getContactsSlow(ids: string[]) {
  return Promise.all(ids.map(id =>
    client.crm.contacts.basicApi.getById(id, ['email', 'firstname'])
  ));
}

// GOOD: 1 API call for 100 contacts
async function getContactsFast(ids: string[], properties: string[]) {
  // POST /crm/v3/objects/contacts/batch/read
  const result = await client.crm.contacts.batchApi.read({
    inputs: ids.map(id => ({ id })),
    properties,
    propertiesWithHistory: [],
  });
  return result.results;
}

// For more than 100 records, chunk:
async function getContactsChunked(ids: string[], properties: string[]) {
  const results = [];
  for (let i = 0; i < ids.length; i += 100) {
    const chunk = ids.slice(i, i + 100);
    const batch = await getContactsFast(chunk, properties);
    results.push(...batch);
  }
  return results;
}
```

### Step 2: Request Only Needed Properties

```typescript
// BAD: Returns ALL default properties (slow, large payload)
const contact = await client.crm.contacts.basicApi.getById(id);

// GOOD: Only request what you need (fast, small payload)
const contact = await client.crm.contacts.basicApi.getById(
  id,
  ['email', 'firstname', 'lastname', 'lifecyclestage'] // specific properties
);
```

### Step 3: Cache Frequently Accessed Data

```typescript
import { LRUCache } from 'lru-cache';

const contactCache = new LRUCache<string, any>({
  max: 5000,              // max entries
  ttl: 5 * 60 * 1000,     // 5 minute TTL
  updateAgeOnGet: true,
});

async function getCachedContact(id: string, properties: string[]) {
  const cacheKey = `contact:${id}`;
  const cached = contactCache.get(cacheKey);
  if (cached) return cached;

  const contact = await client.crm.contacts.basicApi.getById(id, properties);
  contactCache.set(cacheKey, contact);
  return contact;
}

// Invalidate on webhook events
function invalidateContactCache(contactId: string): void {
  contactCache.delete(`contact:${contactId}`);
}
```

### Step 4: Optimize Search Queries

```typescript
// BAD: Overly broad search, returns too much data
const bad = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [],  // no filters = scan entire DB
  properties: [],    // returns default properties
  limit: 100,
  after: 0,
  sorts: [],
});

// GOOD: Specific filters, minimal properties, sorted
const good = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [
      { propertyName: 'lifecyclestage', operator: 'EQ', value: 'customer' },
      { propertyName: 'createdate', operator: 'GTE', value: String(Date.now() - 86400000) },
    ],
  }],
  properties: ['email', 'firstname'],  // only what you need
  limit: 50,
  after: 0,
  sorts: [{ propertyName: 'createdate', direction: 'DESCENDING' }],
});

// Search limits: max 5 filterGroups, 6 filters per group, 18 filters total
// Search returns max 10,000 results total (pagination limit)
```

### Step 5: Pipeline and Property Caching

Pipeline stages and custom properties rarely change -- cache them aggressively:

```typescript
let pipelineCache: Map<string, any> | null = null;
let pipelineCacheExpiry = 0;

async function getCachedPipelines(objectType: 'deals' | 'tickets') {
  if (pipelineCache && Date.now() < pipelineCacheExpiry) {
    return pipelineCache.get(objectType);
  }

  const pipelines = await client.crm.pipelines.pipelinesApi.getAll(objectType);
  if (!pipelineCache) pipelineCache = new Map();
  pipelineCache.set(objectType, pipelines.results);
  pipelineCacheExpiry = Date.now() + 3600000; // 1 hour cache
  return pipelines.results;
}

// Same pattern for properties
let propertyCache: Map<string, any> | null = null;

async function getCachedProperties(objectType: string) {
  if (propertyCache?.has(objectType)) {
    return propertyCache.get(objectType);
  }
  const props = await client.crm.properties.coreApi.getAll(objectType);
  if (!propertyCache) propertyCache = new Map();
  propertyCache.set(objectType, props.results);
  return props.results;
}
```

### Step 6: Pagination with Async Generators

```typescript
// Memory-efficient streaming for large exports
async function* streamAllContacts(properties: string[]) {
  let after: string | undefined;
  do {
    const page = await client.crm.contacts.basicApi.getPage(
      100,    // max page size
      after,
      properties
    );
    yield* page.results;
    after = page.paging?.next?.after;
  } while (after);
}

// Process millions of records without running out of memory
let count = 0;
for await (const contact of streamAllContacts(['email', 'firstname'])) {
  await processContact(contact);
  count++;
  if (count % 1000 === 0) console.log(`Processed ${count} contacts`);
}
```

## Output

- Batch operations reducing API calls by 100x
- Property-specific requests reducing payload size
- LRU caching for frequently accessed records
- Optimized search queries with proper filters
- Streaming pagination for large datasets

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Batch returns `207 Multi-Status` | Some records failed | Check individual `status` in response |
| Cache stale data | TTL too long | Invalidate on webhook events |
| Search returns max 10,000 | HubSpot search limit | Use `getPage` pagination instead |
| Memory pressure | Caching too much | Set `max` entries on LRU cache |

## Resources

- [Batch Operations Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)
- [CRM Search Guide](https://developers.hubspot.com/docs/guides/api/crm/search)
- [lru-cache npm](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `hubspot-cost-tuning`.
