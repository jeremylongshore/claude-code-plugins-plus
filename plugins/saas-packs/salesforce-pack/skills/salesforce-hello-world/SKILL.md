---
name: salesforce-hello-world
description: |
  Create a minimal working Salesforce example with SOQL queries and sObject CRUD.
  Use when starting a new Salesforce integration, testing your setup,
  or learning basic Salesforce API patterns.
  Trigger with phrases like "salesforce hello world", "salesforce example",
  "salesforce quick start", "first salesforce query", "salesforce SOQL".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Hello World

## Overview
Minimal working example: connect to Salesforce, run a SOQL query, and perform basic CRUD on standard sObjects (Account, Contact, Lead).

## Prerequisites
- Completed `salesforce-install-auth` setup
- jsforce installed (`npm install jsforce`)
- Valid credentials in environment variables

## Instructions

### Step 1: Connect and Query Accounts

```typescript
import jsforce from 'jsforce';

const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL || 'https://login.salesforce.com',
});

await conn.login(
  process.env.SF_USERNAME!,
  process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!
);

// Your first SOQL query — fetch 5 Accounts
const result = await conn.query(
  "SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 5"
);

console.log(`Total records: ${result.totalSize}`);
for (const account of result.records) {
  console.log(`  ${account.Name} — ${account.Industry ?? 'N/A'}`);
}
```

### Step 2: Create a Record

```typescript
// Create a new Account
const newAccount = await conn.sobject('Account').create({
  Name: 'Acme Corporation',
  Industry: 'Technology',
  Website: 'https://acme.example.com',
  NumberOfEmployees: 250,
});

console.log('Created Account ID:', newAccount.id);
console.log('Success:', newAccount.success);
```

### Step 3: Read a Record by ID

```typescript
// Retrieve specific fields by record ID
const account = await conn.sobject('Account').retrieve(newAccount.id);
console.log('Account Name:', account.Name);

// Or use SOQL for more control
const result = await conn.query(
  `SELECT Id, Name, Industry, CreatedDate
   FROM Account
   WHERE Id = '${newAccount.id}'`
);
```

### Step 4: Update a Record

```typescript
const updateResult = await conn.sobject('Account').update({
  Id: newAccount.id,
  Industry: 'Software',
  Description: 'Updated via jsforce API',
});
console.log('Updated:', updateResult.success);
```

### Step 5: Delete a Record

```typescript
const deleteResult = await conn.sobject('Account').destroy(newAccount.id);
console.log('Deleted:', deleteResult.success);
```

### Python Example

```python
from simple_salesforce import Salesforce
import os

sf = Salesforce(
    username=os.environ['SF_USERNAME'],
    password=os.environ['SF_PASSWORD'],
    security_token=os.environ['SF_SECURITY_TOKEN']
)

# SOQL query
result = sf.query("SELECT Id, Name, Industry FROM Account LIMIT 5")
for record in result['records']:
    print(f"  {record['Name']} — {record.get('Industry', 'N/A')}")

# Create
new_account = sf.Account.create({'Name': 'Acme Corp', 'Industry': 'Technology'})
print(f"Created: {new_account['id']}")

# Update
sf.Account.update(new_account['id'], {'Industry': 'Software'})

# Delete
sf.Account.delete(new_account['id'])
```

## Output
- Successful SOQL query returning Account records
- Created, read, updated, and deleted an Account sObject
- Console output confirming each operation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_FIELD` | Field name wrong in SOQL | Check field API names in Setup > Object Manager |
| `MALFORMED_QUERY` | SOQL syntax error | Verify quotes, field names, WHERE clause |
| `INVALID_TYPE` | sObject name wrong | Use API name (e.g., `Account`, not `Accounts`) |
| `REQUIRED_FIELD_MISSING` | Missing required field on create | Add required fields (e.g., `Name` for Account) |
| `ENTITY_IS_DELETED` | Record already deleted | Query with `isDeleted = true` to find in Recycle Bin |

## Resources
- [SOQL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)
- [sObject CRUD (REST API)](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_sobject_retrieve.htm)
- [Standard Objects Reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_list.htm)

## Next Steps
Proceed to `salesforce-local-dev-loop` for development workflow setup.
