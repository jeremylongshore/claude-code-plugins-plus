---
name: salesforce-core-workflow-a
description: |
  Execute Salesforce CRUD operations on standard sObjects with SOQL and REST API.
  Use when creating, reading, updating, or deleting Accounts, Contacts, Leads,
  or Opportunities via the Salesforce API.
  Trigger with phrases like "salesforce CRUD", "salesforce create record",
  "salesforce update account", "salesforce SOQL query", "salesforce REST API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Core Workflow A — CRUD & SOQL

## Overview
Primary workflow: perform CRUD operations on standard sObjects (Account, Contact, Lead, Opportunity) using SOQL queries, jsforce methods, and REST API endpoints.

## Prerequisites
- Completed `salesforce-install-auth` setup
- jsforce installed and connection configured
- Understanding of Salesforce sObject model

## Instructions

### Step 1: SOQL Queries (Read Operations)

```typescript
import { getConnection } from './salesforce/connection';

const conn = await getConnection();

// Basic query — all open opportunities closing this quarter
const opps = await conn.query(`
  SELECT Id, Name, Amount, StageName, CloseDate, Account.Name
  FROM Opportunity
  WHERE IsClosed = false
    AND CloseDate = THIS_QUARTER
  ORDER BY Amount DESC
  LIMIT 50
`);

// Relationship query — Accounts with their Contacts
const accountsWithContacts = await conn.query(`
  SELECT Id, Name, Industry,
    (SELECT Id, FirstName, LastName, Email FROM Contacts)
  FROM Account
  WHERE Industry = 'Technology'
  LIMIT 20
`);

// Aggregate query
const revByIndustry = await conn.query(`
  SELECT Industry, COUNT(Id) numAccounts, SUM(AnnualRevenue) totalRevenue
  FROM Account
  WHERE Industry != null
  GROUP BY Industry
  ORDER BY SUM(AnnualRevenue) DESC
`);

// SOSL search — full-text search across objects
const searchResults = await conn.search(
  `FIND {Acme} IN ALL FIELDS RETURNING
    Account(Id, Name, Industry),
    Contact(Id, FirstName, LastName, Email),
    Lead(Id, Name, Company, Status)`
);
```

### Step 2: Create Records

```typescript
// Single record create via sObject
const newLead = await conn.sobject('Lead').create({
  FirstName: 'Jane',
  LastName: 'Smith',
  Company: 'Acme Corp',
  Email: 'jane.smith@acme.example.com',
  Status: 'Open - Not Contacted',
  LeadSource: 'Web',
});
console.log('Lead ID:', newLead.id); // '00Qxx...'

// Create with relationship (Contact linked to Account)
const newContact = await conn.sobject('Contact').create({
  FirstName: 'John',
  LastName: 'Doe',
  Email: 'john.doe@example.com',
  AccountId: '001xxxxxxxxxxxx', // Existing Account ID
  Title: 'VP Engineering',
});

// Create Opportunity with all key fields
const newOpp = await conn.sobject('Opportunity').create({
  Name: 'Acme Corp — Enterprise License',
  AccountId: '001xxxxxxxxxxxx',
  StageName: 'Prospecting',
  CloseDate: '2026-06-30',
  Amount: 50000,
});
```

### Step 3: Bulk Create with sObject Collections

```typescript
// Create up to 200 records in a single API call (sObject Collections)
const contacts = [
  { FirstName: 'Alice', LastName: 'A', Email: 'alice@example.com', AccountId: '001xx' },
  { FirstName: 'Bob', LastName: 'B', Email: 'bob@example.com', AccountId: '001xx' },
  { FirstName: 'Carol', LastName: 'C', Email: 'carol@example.com', AccountId: '001xx' },
];

const results = await conn.sobject('Contact').create(contacts);
// Returns array: [{ id: '003xx', success: true }, ...]

// Check for partial failures
for (const result of results) {
  if (!result.success) {
    console.error('Failed:', result.errors);
  }
}
```

### Step 4: Update Records

```typescript
// Single update
await conn.sobject('Opportunity').update({
  Id: '006xxxxxxxxxxxx',
  StageName: 'Qualification',
  Amount: 75000,
  Description: 'Upgraded after demo call',
});

// Bulk update (up to 200)
const updates = [
  { Id: '003xx1', Title: 'Senior Engineer' },
  { Id: '003xx2', Title: 'Staff Engineer' },
  { Id: '003xx3', Title: 'Principal Engineer' },
];
await conn.sobject('Contact').update(updates);
```

### Step 5: Upsert (Insert or Update by External ID)

```typescript
// Upsert uses an External ID field to match existing records
// Requires a custom External ID field on the sObject
await conn.sobject('Account').upsert({
  External_ID__c: 'EXT-12345',  // Custom external ID field
  Name: 'Acme Corporation',
  Industry: 'Technology',
  Website: 'https://acme.example.com',
}, 'External_ID__c');  // Field to match on
```

### Step 6: Delete Records

```typescript
// Single delete
await conn.sobject('Lead').destroy('00Qxxxxxxxxxxxx');

// Bulk delete (up to 200)
const idsToDelete = ['00Qxx1', '00Qxx2', '00Qxx3'];
await conn.sobject('Lead').destroy(idsToDelete);
```

### Step 7: Direct REST API Calls

```typescript
// When jsforce doesn't wrap what you need, use raw REST
// GET — describe an sObject
const accountMeta = await conn.request(
  '/services/data/v59.0/sobjects/Account/describe'
);
console.log('Fields:', accountMeta.fields.map((f: any) => f.name));

// POST — create via REST
const created = await conn.request({
  method: 'POST',
  url: '/services/data/v59.0/sobjects/Account/',
  body: JSON.stringify({ Name: 'REST Created Account' }),
  headers: { 'Content-Type': 'application/json' },
});

// PATCH — update via REST
await conn.request({
  method: 'PATCH',
  url: `/services/data/v59.0/sobjects/Account/${created.id}`,
  body: JSON.stringify({ Industry: 'Consulting' }),
  headers: { 'Content-Type': 'application/json' },
});
```

## Output
- SOQL queries returning typed sObject records
- Single and bulk record creation
- Record updates and upserts by External ID
- Record deletion (single and bulk)
- Direct REST API calls for advanced use cases

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_FIELD` | Wrong field API name in SOQL | Use Object Manager to check field names |
| `REQUIRED_FIELD_MISSING` | Create missing required fields | Check Setup > Object Manager > Fields for required |
| `DUPLICATE_VALUE` | Unique field constraint violated | Check External ID or unique field values |
| `INSUFFICIENT_ACCESS_OR_READONLY` | Missing object/field permissions | Check Profile or Permission Set assignments |
| `UNABLE_TO_LOCK_ROW` | Concurrent update on same record | Retry with backoff — common in high-volume writes |
| `ENTITY_IS_DELETED` | Operating on deleted record | Query Recycle Bin or use `ALL ROWS` in SOQL |

## Resources
- [sObject CRUD (REST API)](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_sobject_create.htm)
- [sObject Collections](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite_sobjects_collections.htm)
- [SOQL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)
- [SOSL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm)

## Next Steps
For Bulk API and Composite API patterns, see `salesforce-core-workflow-b`.
