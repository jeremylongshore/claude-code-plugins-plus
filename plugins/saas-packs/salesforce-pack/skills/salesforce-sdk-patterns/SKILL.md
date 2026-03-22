---
name: salesforce-sdk-patterns
description: |
  Apply production-ready Salesforce jsforce patterns for TypeScript and Python.
  Use when implementing Salesforce integrations, refactoring SDK usage,
  or establishing team coding standards for Salesforce.
  Trigger with phrases like "salesforce SDK patterns", "jsforce best practices",
  "salesforce code patterns", "idiomatic salesforce", "salesforce typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce SDK Patterns

## Overview
Production-ready patterns for jsforce (Node.js) and simple-salesforce (Python) — singleton connections, typed queries, error handling, and token refresh.

## Prerequisites
- Completed `salesforce-install-auth` setup
- Familiarity with async/await and TypeScript generics
- Understanding of Salesforce sObject model

## Instructions

### Step 1: Singleton Connection with Auto-Refresh

```typescript
// src/salesforce/connection.ts
import jsforce from 'jsforce';

let conn: jsforce.Connection | null = null;

export async function getConnection(): Promise<jsforce.Connection> {
  if (conn?.accessToken) {
    // Test if token is still valid
    try {
      await conn.identity();
      return conn;
    } catch {
      conn = null; // Token expired, reconnect
    }
  }

  conn = new jsforce.Connection({
    loginUrl: process.env.SF_LOGIN_URL || 'https://login.salesforce.com',
    version: '59.0', // Pin API version for stability
  });

  await conn.login(
    process.env.SF_USERNAME!,
    process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!
  );

  return conn;
}
```

### Step 2: Typed sObject Interfaces

```typescript
// src/salesforce/types.ts

/** Standard Salesforce sObject base fields */
interface SObjectBase {
  Id: string;
  CreatedDate: string;
  LastModifiedDate: string;
  SystemModstamp: string;
  IsDeleted: boolean;
}

export interface Account extends SObjectBase {
  Name: string;
  Industry?: string;
  AnnualRevenue?: number;
  NumberOfEmployees?: number;
  Website?: string;
  Phone?: string;
  BillingCity?: string;
  BillingState?: string;
  OwnerId: string;
}

export interface Contact extends SObjectBase {
  FirstName?: string;
  LastName: string;
  Email?: string;
  Phone?: string;
  AccountId?: string;
  Title?: string;
  Department?: string;
}

export interface Opportunity extends SObjectBase {
  Name: string;
  Amount?: number;
  StageName: string;
  CloseDate: string;
  AccountId?: string;
  Probability?: number;
  ForecastCategory?: string;
}

export interface Lead extends SObjectBase {
  FirstName?: string;
  LastName: string;
  Company: string;
  Email?: string;
  Status: string;
  IsConverted: boolean;
}
```

### Step 3: Type-Safe Query Builder

```typescript
// src/salesforce/queries.ts
import { getConnection } from './connection';
import type { Account, Contact, Opportunity } from './types';

export async function queryAccounts(
  filters?: { industry?: string; minRevenue?: number }
): Promise<Account[]> {
  const conn = await getConnection();

  let soql = `
    SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees,
           Website, Phone, BillingCity, BillingState, OwnerId
    FROM Account
  `;

  const conditions: string[] = [];
  if (filters?.industry) {
    conditions.push(`Industry = '${filters.industry.replace(/'/g, "\\'")}'`);
  }
  if (filters?.minRevenue) {
    conditions.push(`AnnualRevenue >= ${filters.minRevenue}`);
  }

  if (conditions.length > 0) {
    soql += ` WHERE ${conditions.join(' AND ')}`;
  }

  soql += ' ORDER BY Name ASC LIMIT 200';

  const result = await conn.query<Account>(soql);
  return result.records;
}

export async function queryContactsByAccount(
  accountId: string
): Promise<Contact[]> {
  const conn = await getConnection();
  const result = await conn.query<Contact>(
    `SELECT Id, FirstName, LastName, Email, Phone, Title, Department
     FROM Contact
     WHERE AccountId = '${accountId}'
     ORDER BY LastName ASC`
  );
  return result.records;
}

export async function queryOpenOpportunities(): Promise<Opportunity[]> {
  const conn = await getConnection();
  const result = await conn.query<Opportunity>(
    `SELECT Id, Name, Amount, StageName, CloseDate, AccountId, Probability
     FROM Opportunity
     WHERE IsClosed = false AND CloseDate >= TODAY
     ORDER BY CloseDate ASC`
  );
  return result.records;
}
```

### Step 4: Error Handling Wrapper

```typescript
// src/salesforce/errors.ts
export class SalesforceError extends Error {
  constructor(
    message: string,
    public readonly errorCode: string,
    public readonly statusCode?: number,
    public readonly fields?: string[]
  ) {
    super(message);
    this.name = 'SalesforceError';
  }
}

export async function safeSfCall<T>(
  operation: () => Promise<T>,
  context?: string
): Promise<T> {
  try {
    return await operation();
  } catch (err: any) {
    const errorCode = err.errorCode || err.name || 'UNKNOWN_ERROR';
    const fields = err.fields || [];

    // Map Salesforce error codes to actionable messages
    const messages: Record<string, string> = {
      'INVALID_FIELD': `Invalid field name in query. Fields: ${fields.join(', ')}`,
      'MALFORMED_QUERY': 'SOQL syntax error — check field names and WHERE clause',
      'INVALID_TYPE': 'sObject type does not exist — use API names like Account, not Accounts',
      'INSUFFICIENT_ACCESS_OR_READONLY': 'User lacks permission for this operation',
      'ENTITY_IS_DELETED': 'Record has been deleted — check Recycle Bin',
      'DUPLICATE_VALUE': 'Duplicate external ID or unique field value',
      'FIELD_INTEGRITY_EXCEPTION': 'Field validation rule failed',
      'STRING_TOO_LONG': 'Field value exceeds max length',
      'REQUEST_LIMIT_EXCEEDED': 'Daily API limit exhausted — check org limits',
    };

    throw new SalesforceError(
      messages[errorCode] || err.message || 'Unknown Salesforce error',
      errorCode,
      err.statusCode,
      fields
    );
  }
}
```

### Step 5: Retry Logic for Transient Errors

```typescript
const RETRYABLE_ERRORS = [
  'REQUEST_LIMIT_EXCEEDED',
  'SERVER_UNAVAILABLE',
  'UNABLE_TO_LOCK_ROW',
];

export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      const errorCode = err.errorCode || err.name;
      if (attempt === maxRetries || !RETRYABLE_ERRORS.includes(errorCode)) {
        throw err;
      }
      const delay = baseDelayMs * Math.pow(2, attempt - 1);
      console.warn(`Retryable error ${errorCode}, attempt ${attempt}/${maxRetries}, waiting ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Output
- Type-safe jsforce connection singleton with auto-refresh
- Typed sObject interfaces for Account, Contact, Opportunity, Lead
- SOQL query builders with parameterized filters
- Error handling mapped to Salesforce error codes
- Retry logic for transient failures

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeSfCall()` wrapper | All API calls | Maps error codes to human messages |
| `withRetry()` | Transient failures (`UNABLE_TO_LOCK_ROW`) | Automatic recovery |
| Typed queries | All SOQL | Catches field mismatches at compile time |
| Token refresh | Long-running processes | Prevents session expiration |

## Resources
- [jsforce API Reference](https://jsforce.github.io/document/)
- [Salesforce Error Codes](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm)
- [SOQL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm)

## Next Steps
Apply patterns in `salesforce-core-workflow-a` for CRUD operations at scale.
