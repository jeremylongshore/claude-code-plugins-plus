---
name: salesforce-core-workflow-b
description: |
  Execute Salesforce Bulk API 2.0 and Composite API operations for high-volume data.
  Use when importing/exporting large datasets, performing multi-object transactions,
  or chaining dependent API calls.
  Trigger with phrases like "salesforce bulk API", "salesforce composite",
  "salesforce batch", "salesforce mass import", "salesforce large data".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Core Workflow B — Bulk & Composite API

## Overview
High-volume data operations using Bulk API 2.0 (millions of records) and Composite API (multi-step transactions in a single call).

## Prerequisites
- Completed `salesforce-install-auth` setup
- Understanding of `salesforce-core-workflow-a` (standard CRUD)
- jsforce installed with connection configured

## Instructions

### Step 1: Bulk API 2.0 — Ingest (Insert/Update/Upsert/Delete)

```typescript
import { getConnection } from './salesforce/connection';
import fs from 'fs';

const conn = await getConnection();

// Create a bulk ingest job
const job = conn.bulk2.createJob({
  operation: 'insert',     // insert | update | upsert | delete
  object: 'Contact',
  // For upsert, specify: externalIdFieldName: 'External_ID__c'
});

// Upload CSV data
const csvData = `FirstName,LastName,Email,AccountId
Alice,Johnson,alice@example.com,001xxxxxxxxxxxx
Bob,Williams,bob@example.com,001xxxxxxxxxxxx
Carol,Davis,carol@example.com,001xxxxxxxxxxxx`;

// jsforce handles chunking automatically
const results = await conn.bulk2.loadAndWaitForResults({
  object: 'Contact',
  operation: 'insert',
  input: csvData,
});

console.log('Successful:', results.successfulResults.length);
console.log('Failed:', results.failedResults.length);

for (const failure of results.failedResults) {
  console.error(`Row ${failure.sf__Id}: ${failure.sf__Error}`);
}
```

### Step 2: Bulk API 2.0 — Query (Export)

```typescript
// Bulk query for large datasets (100K+ records)
const queryResults = await conn.bulk2.query(
  `SELECT Id, Name, Email, Account.Name
   FROM Contact
   WHERE CreatedDate >= LAST_N_DAYS:90`
);

// Stream results for memory efficiency
let recordCount = 0;
for await (const record of queryResults) {
  recordCount++;
  // Process each record
  console.log(`${record.Name} — ${record.Email}`);
}
console.log(`Total exported: ${recordCount}`);
```

### Step 3: Bulk API 2.0 — File-Based Upload

```typescript
// Upload from a CSV file (for very large datasets)
const csvStream = fs.createReadStream('contacts-import.csv');

const bulkResults = await conn.bulk2.loadAndWaitForResults({
  object: 'Contact',
  operation: 'upsert',
  externalIdFieldName: 'External_ID__c',
  input: csvStream,
  pollTimeout: 600000,   // 10 min timeout for large jobs
  pollInterval: 5000,    // Check every 5 seconds
});

console.log(`Processed: ${bulkResults.successfulResults.length} success, ${bulkResults.failedResults.length} failed`);
```

### Step 4: Composite API — Multiple Operations in One Call

```typescript
// Execute up to 25 subrequests in a single API call
// Each subrequest counts as a separate API call for limits
const compositeResult = await conn.request({
  method: 'POST',
  url: '/services/data/v59.0/composite',
  body: JSON.stringify({
    allOrNone: true,  // Rollback all if any fail
    compositeRequest: [
      {
        method: 'POST',
        url: '/services/data/v59.0/sobjects/Account/',
        referenceId: 'newAccount',
        body: { Name: 'Composite Corp', Industry: 'Technology' },
      },
      {
        method: 'POST',
        url: '/services/data/v59.0/sobjects/Contact/',
        referenceId: 'newContact',
        body: {
          FirstName: 'Jane',
          LastName: 'Doe',
          AccountId: '@{newAccount.id}',  // Reference previous result
          Email: 'jane@composite.example.com',
        },
      },
      {
        method: 'POST',
        url: '/services/data/v59.0/sobjects/Opportunity/',
        referenceId: 'newOpp',
        body: {
          Name: 'Composite Deal',
          AccountId: '@{newAccount.id}',
          StageName: 'Prospecting',
          CloseDate: '2026-12-31',
          Amount: 100000,
        },
      },
    ],
  }),
  headers: { 'Content-Type': 'application/json' },
});
```

### Step 5: Composite Batch — Independent Operations

```typescript
// Batch executes up to 25 independent subrequests
// Unlike composite, subrequests can't reference each other
const batchResult = await conn.request({
  method: 'POST',
  url: '/services/data/v59.0/composite/batch',
  body: JSON.stringify({
    batchRequests: [
      {
        method: 'GET',
        url: 'v59.0/sobjects/Account/001xxxxxxxxxxxx',
      },
      {
        method: 'GET',
        url: 'v59.0/query/?q=SELECT+Id,Name+FROM+Contact+LIMIT+5',
      },
      {
        method: 'PATCH',
        url: 'v59.0/sobjects/Account/001xxxxxxxxxxxx',
        richInput: { Industry: 'Software' },
      },
    ],
  }),
  headers: { 'Content-Type': 'application/json' },
});

// Check results
for (const result of batchResult.results) {
  console.log(`Status: ${result.statusCode}`, result.result);
}
```

### Step 6: Composite Graph — Complex Transaction Trees

```typescript
// Composite Graph: multiple independent composite operations
// Each graph is an all-or-none transaction
const graphResult = await conn.request({
  method: 'POST',
  url: '/services/data/v59.0/composite/graph',
  body: JSON.stringify({
    graphs: [
      {
        graphId: 'graph1',
        compositeRequest: [
          {
            method: 'POST',
            url: '/services/data/v59.0/sobjects/Account/',
            referenceId: 'acct1',
            body: { Name: 'Graph Corp' },
          },
          {
            method: 'POST',
            url: '/services/data/v59.0/sobjects/Contact/',
            referenceId: 'contact1',
            body: {
              LastName: 'Graph',
              AccountId: '@{acct1.id}',
            },
          },
        ],
      },
    ],
  }),
  headers: { 'Content-Type': 'application/json' },
});
```

## Bulk vs Composite Decision Guide

| Scenario | API | Why |
|----------|-----|-----|
| Import 10K+ records | Bulk API 2.0 | Handles millions, async processing |
| Export large datasets | Bulk API 2.0 Query | Streaming, no memory issues |
| Create Account + Contact + Opportunity | Composite | Single call, references between objects |
| Fetch 5 unrelated records | Composite Batch | Parallel fetches, 1 API call |
| Multi-object transaction | Composite Graph | All-or-none across object types |
| < 200 records CRUD | sObject Collections | Simpler, synchronous, from workflow-a |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `PROCESSING_HALTED` | Bulk job aborted | Check `failedResults` for row-level errors |
| `InvalidBatch` | CSV format error | Verify column headers match field API names |
| `ALL_OR_NONE_OPERATION_ROLLED_BACK` | Composite `allOrNone` failure | Check individual subrequest errors |
| `MAX_BATCH_SIZE_EXCEEDED` | Too many subrequests | Composite: max 25, Batch: max 25 |
| `EXCEEDED_ID_LIMIT` | Too many records in single bulk job | Split into multiple jobs (max 150M records/job) |

## Resources
- [Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/bulk_api_2_0.htm)
- [Composite Resources](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite.htm)
- [Composite Graph](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_graph_introduction.htm)
- [sObject Collections](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_sobjects_collections.htm)

## Next Steps
For common errors and debugging, see `salesforce-common-errors`.
