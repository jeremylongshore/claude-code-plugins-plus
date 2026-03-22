---
name: salesforce-known-pitfalls
description: |
  Identify and avoid Salesforce anti-patterns including SOQL N+1, governor limit violations, and API waste.
  Use when reviewing Salesforce code for issues, onboarding new developers,
  or auditing existing Salesforce integrations for best practices violations.
  Trigger with phrases like "salesforce mistakes", "salesforce anti-patterns",
  "salesforce pitfalls", "salesforce what not to do", "salesforce code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Known Pitfalls

## Overview
The 10 most common and costly mistakes when integrating with Salesforce, with real error messages and correct patterns.

## Pitfall #1: SOQL N+1 Query Pattern (Most Common)

### Anti-Pattern
```typescript
// Query accounts, then query contacts for each = N+1 API calls
const accounts = await conn.query('SELECT Id, Name FROM Account LIMIT 100');
for (const account of accounts.records) {
  // 100 extra API calls! (plus 100 extra SOQL queries in Apex)
  const contacts = await conn.query(
    `SELECT Id, Name, Email FROM Contact WHERE AccountId = '${account.Id}'`
  );
}
// Total: 101 API calls for what should be 1
```

### Correct Pattern
```typescript
// Single relationship query — 1 API call
const accounts = await conn.query(`
  SELECT Id, Name,
    (SELECT Id, FirstName, LastName, Email FROM Contacts)
  FROM Account
  LIMIT 100
`);
// accounts.records[0].Contacts.records → child contacts
```

---

## Pitfall #2: Ignoring API Limits (Org-Wide Shared Pool)

### Anti-Pattern
```typescript
// This integration uses 80,000 API calls/day
// Sales team uses 60,000/day
// Total: 140,000 > 150,000 limit → everyone gets blocked
```

### Correct Pattern
```typescript
// 1. Check limits before batch operations
const limits = await conn.request('/services/data/v59.0/limits/');
if (limits.DailyApiRequests.Remaining < estimatedCalls) {
  throw new Error('Insufficient API calls remaining');
}

// 2. Use sObject Collections (1 call = 200 records)
await conn.sobject('Contact').create(contacts); // batch of up to 200

// 3. Use Bulk API for 10K+ (separate limit pool)
await conn.bulk2.loadAndWaitForResults({ object: 'Contact', operation: 'insert', input: csv });
```

---

## Pitfall #3: SOQL Injection

### Anti-Pattern
```typescript
// User input directly in SOQL — injectable
const name = req.query.name; // Could be: "'; SELECT Id FROM User; --"
await conn.query(`SELECT Id FROM Account WHERE Name = '${name}'`);
```

### Correct Pattern
```typescript
function escapeSoql(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
await conn.query(`SELECT Id FROM Account WHERE Name = '${escapeSoql(name)}'`);
```

---

## Pitfall #4: SELECT FIELDS(ALL) (Performance Killer)

### Anti-Pattern
```typescript
// Fetches ALL fields — 200+ columns on Account, massive payload
const result = await conn.query('SELECT FIELDS(ALL) FROM Account LIMIT 100');
```

### Correct Pattern
```typescript
// Select only what you need — 5-10x faster, much less data transfer
const result = await conn.query('SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 100');
```

---

## Pitfall #5: Hardcoded Salesforce Record IDs

### Anti-Pattern
```typescript
// IDs are different across sandbox and production!
const adminProfileId = '00e5f000001abc';     // Works in sandbox...
const queueId = '00G5f000002def';            // ...breaks in production
await conn.sobject('Case').create({ OwnerId: queueId, ProfileId: adminProfileId });
```

### Correct Pattern
```typescript
// Look up by name, not by ID
const queue = await conn.query("SELECT Id FROM Group WHERE Name = 'Support Queue' AND Type = 'Queue'");
const queueId = queue.records[0].Id;

const profile = await conn.query("SELECT Id FROM Profile WHERE Name = 'System Administrator'");
const profileId = profile.records[0].Id;
```

---

## Pitfall #6: Not Handling Partial Success in Bulk Operations

### Anti-Pattern
```typescript
const results = await conn.sobject('Contact').create(contacts);
console.log('Done!'); // Ignoring that some records may have failed
```

### Correct Pattern
```typescript
const results = await conn.sobject('Contact').create(contacts);
const failures = results.filter(r => !r.success);
if (failures.length > 0) {
  console.error(`${failures.length}/${results.length} records failed:`);
  for (const failure of failures) {
    console.error(`  ${failure.errors.map(e => `${e.statusCode}: ${e.message}`).join('; ')}`);
  }
}
```

---

## Pitfall #7: Using test.salesforce.com for Production

### Anti-Pattern
```typescript
// Sandbox login URL used for production — silently connects to sandbox
const conn = new jsforce.Connection({
  loginUrl: 'https://test.salesforce.com', // WRONG for production
});
```

### Correct Pattern
```typescript
const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL, // 'https://login.salesforce.com' for prod
  // OR: 'https://test.salesforce.com' for sandboxes
});
// Always use environment variables — never hardcode login URLs
```

---

## Pitfall #8: Not Using External IDs for Upsert

### Anti-Pattern
```typescript
// Without External ID: create duplicates on every sync run
await conn.sobject('Account').create({ Name: 'Acme Corp', Industry: 'Tech' });
// Run again → duplicate Account created!
```

### Correct Pattern
```typescript
// With External ID: upsert is idempotent — safe to retry
await conn.sobject('Account').upsert({
  External_ID__c: 'CRM-ACME-001',  // Custom External ID field
  Name: 'Acme Corp',
  Industry: 'Tech',
}, 'External_ID__c');
// Run again → updates existing record, no duplicate
```

---

## Pitfall #9: Missing Error Handling for UNABLE_TO_LOCK_ROW

### Anti-Pattern
```typescript
// Record locking is COMMON in Salesforce — this crashes on contention
await conn.sobject('Account').update({ Id: accountId, Name: 'New Name' });
// Error: UNABLE_TO_LOCK_ROW → unhandled, crashes the process
```

### Correct Pattern
```typescript
async function updateWithRetry(objectType: string, data: any, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await conn.sobject(objectType).update(data);
    } catch (error: any) {
      if (error.errorCode === 'UNABLE_TO_LOCK_ROW' && attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 1000 * attempt)); // Backoff
        continue;
      }
      throw error;
    }
  }
}
```

---

## Pitfall #10: Polling When CDC Is Available

### Anti-Pattern
```typescript
// Poll every 5 minutes — wastes 288 API calls/day even when nothing changed
cron.schedule('*/5 * * * *', async () => {
  const changes = await conn.query(`
    SELECT Id, Name FROM Account WHERE LastModifiedDate >= ${fiveMinAgo}
  `);
  // Usually returns 0 records — wasted API call
});
```

### Correct Pattern
```typescript
// CDC — only fires when data actually changes, zero wasted API calls
conn.streaming.topic('/data/AccountChangeEvent').subscribe((event) => {
  // Only called when an Account is actually created/updated/deleted
  handleAccountChange(event);
});
```

---

## Quick Reference Card

| Pitfall | Detection | Prevention |
|---------|-----------|------------|
| N+1 SOQL queries | High API call count, loop with `.query()` | Use relationship SOQL |
| API limit exhaustion | `REQUEST_LIMIT_EXCEEDED` | Monitor `/limits/`, use Bulk API |
| SOQL injection | String concatenation in `.query()` | Use `escapeSoql()` |
| SELECT FIELDS(ALL) | Slow queries, large payloads | Select only needed fields |
| Hardcoded IDs | Different behavior in sandbox vs prod | Query by Name, use External IDs |
| Partial failure ignored | Silent data loss | Check `.success` on every result |
| Wrong login URL | Connected to wrong org | Use `SF_LOGIN_URL` env var |
| No External ID | Duplicate records on re-sync | Add External_ID__c, use upsert |
| No retry for LOCK_ROW | Random crashes under load | Retry with exponential backoff |
| Polling over CDC | Wasted API calls | Use Change Data Capture |

## Resources
- [Salesforce Best Practices](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm)
- [SOQL Injection Prevention](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/pages_security_tips_soql_injection.htm)
- [Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm)
- [Change Data Capture](https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/)
