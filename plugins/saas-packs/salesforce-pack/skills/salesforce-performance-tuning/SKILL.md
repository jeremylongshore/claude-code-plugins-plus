---
name: salesforce-performance-tuning
description: |
  Optimize Salesforce API performance with SOQL tuning, Composite API batching, and caching.
  Use when experiencing slow API responses, optimizing SOQL queries,
  or reducing API call count for Salesforce integrations.
  Trigger with phrases like "salesforce performance", "optimize salesforce",
  "salesforce latency", "salesforce caching", "salesforce slow", "SOQL optimization".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Performance Tuning

## Overview
Optimize Salesforce API performance: tune SOQL queries, minimize API calls using Composite/Collections APIs, implement metadata caching, and handle large result sets efficiently.

## Prerequisites
- jsforce connection configured
- Understanding of SOQL query plans
- Redis or in-memory cache available (optional)
- Access to Setup > API usage monitoring

## Instructions

### Step 1: SOQL Query Optimization

```typescript
// BAD: SELECT * equivalent — fetches all fields
const result = await conn.query('SELECT FIELDS(ALL) FROM Account LIMIT 100');

// GOOD: Only select fields you need
const result = await conn.query(`
  SELECT Id, Name, Industry, AnnualRevenue
  FROM Account
  WHERE Industry = 'Technology'
  LIMIT 100
`);

// BAD: Non-selective WHERE clause (full table scan)
const result = await conn.query("SELECT Id FROM Contact WHERE Title LIKE '%Engineer%'");

// GOOD: Use indexed fields in WHERE (Id, Name, CreatedDate, RecordType, lookup fields)
const result = await conn.query(`
  SELECT Id, Name, Title
  FROM Contact
  WHERE AccountId = '001xxxxxxxxxxxx'
    AND CreatedDate >= LAST_N_DAYS:30
  LIMIT 200
`);

// Use relationship queries to avoid N+1 pattern
// BAD: Query Accounts, then query Contacts for each (N+1 API calls)
const accounts = await conn.query('SELECT Id FROM Account LIMIT 50');
for (const acct of accounts.records) {
  await conn.query(`SELECT Id FROM Contact WHERE AccountId = '${acct.Id}'`);
  // 50 extra API calls!
}

// GOOD: Single relationship query (1 API call)
const accountsWithContacts = await conn.query(`
  SELECT Id, Name,
    (SELECT Id, FirstName, LastName, Email FROM Contacts LIMIT 20)
  FROM Account
  WHERE Industry = 'Technology'
  LIMIT 50
`);
```

### Step 2: Reduce API Call Count

```typescript
// STRATEGY 1: sObject Collections — 200 records per API call
// Instead of 100 individual creates = 100 API calls
const contacts = Array.from({ length: 100 }, (_, i) => ({
  FirstName: `User${i}`,
  LastName: `Test`,
  Email: `user${i}@test.com`,
}));
await conn.sobject('Contact').create(contacts); // 1 API call

// STRATEGY 2: Composite API — 25 mixed operations per API call
// Create Account + Contact + Opportunity = 1 API call instead of 3
// See salesforce-core-workflow-b

// STRATEGY 3: queryMore for pagination — FREE (doesn't count as extra call)
let result = await conn.query('SELECT Id, Name FROM Contact');
let allRecords = [...result.records];
while (!result.done) {
  result = await conn.queryMore(result.nextRecordsUrl!);
  allRecords.push(...result.records);
}
```

### Step 3: Cache Metadata (Describe Calls)

```typescript
import { LRUCache } from 'lru-cache';

// Describe calls are expensive and metadata rarely changes
const describeCache = new LRUCache<string, any>({
  max: 50,                // Cache up to 50 sObject describes
  ttl: 1000 * 60 * 60,   // 1 hour TTL (metadata changes are rare)
});

async function cachedDescribe(sObjectType: string) {
  const cached = describeCache.get(sObjectType);
  if (cached) return cached;

  const conn = await getConnection();
  const describe = await conn.sobject(sObjectType).describe();
  describeCache.set(sObjectType, describe);
  return describe;
}

// Cache SOQL query results for frequently-accessed reference data
const queryCache = new LRUCache<string, any>({
  max: 100,
  ttl: 1000 * 60 * 5,    // 5 minute TTL for query results
});

async function cachedQuery<T>(soql: string): Promise<T[]> {
  const cached = queryCache.get(soql);
  if (cached) return cached;

  const conn = await getConnection();
  const result = await conn.query<T>(soql);
  queryCache.set(soql, result.records);
  return result.records;
}
```

### Step 4: Stream Large Result Sets

```typescript
// For large exports (100K+ records), use Bulk API 2.0 query
// Streams results to avoid loading everything into memory

const queryResults = await conn.bulk2.query(
  'SELECT Id, Name, Email FROM Contact WHERE CreatedDate >= LAST_YEAR'
);

// Process as async iterator — constant memory usage
let count = 0;
for await (const record of queryResults) {
  await processContact(record);
  count++;
  if (count % 10000 === 0) {
    console.log(`Processed ${count} records...`);
  }
}
```

### Step 5: Connection Optimization

```typescript
// Reuse connections across requests (singleton pattern)
// jsforce handles keep-alive internally

// Pin API version to avoid version negotiation overhead
const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL,
  version: '59.0',         // Skip version detection call
  maxRequest: 10,           // Max concurrent requests
});
```

## Performance Benchmarks

| Operation | Typical Latency | Optimization |
|-----------|----------------|--------------|
| Single SOQL query | 100-300ms | Use selective filters on indexed fields |
| sObject Create (single) | 150-400ms | Batch with Collections (up to 200) |
| Describe call | 200-500ms | Cache for 1 hour |
| Bulk API job creation | 500ms-2s | Use for 10K+ records |
| Composite (25 subrequests) | 500ms-3s | Replaces 25 individual calls |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `NON_SELECTIVE_QUERY` | WHERE clause too broad | Add indexed field filters |
| `QUERY_TOO_COMPLICATED` | Too many joins/subqueries | Simplify or split into multiple queries |
| `50,001 row limit` | Too many results | Add LIMIT, or use Bulk API for exports |
| Cache stampede | TTL expired, all threads miss | Use stale-while-revalidate pattern |

## Resources
- [SOQL Performance Best Practices](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_VLSQ.htm)
- [Query Plan Tool](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_query_plan.htm)
- [sObject Collections](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_sobjects_collections.htm)

## Next Steps
For cost optimization, see `salesforce-cost-tuning`.
