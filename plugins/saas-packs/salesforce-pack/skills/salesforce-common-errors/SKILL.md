---
name: salesforce-common-errors
description: |
  Diagnose and fix Salesforce common errors, SOQL issues, and API exceptions.
  Use when encountering Salesforce errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "salesforce error", "fix salesforce",
  "salesforce not working", "debug salesforce", "SOQL error", "salesforce exception".
allowed-tools: Read, Grep, Bash(curl:*), Bash(sf:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Common Errors

## Overview
Quick reference for the most common Salesforce API errors with real error codes, messages, and solutions.

## Prerequisites
- Salesforce connection established (jsforce or simple-salesforce)
- Access to Setup in your Salesforce org
- Familiarity with sObject field API names

## Instructions

### Step 1: Identify the Error
Check the `errorCode` field in the API response or the exception from jsforce.

### Step 2: Match to Error Below

---

### INVALID_LOGIN — Authentication Failed
```
[{"message":"INVALID_LOGIN: Invalid username, password, security token; or user locked out.","errorCode":"INVALID_LOGIN"}]
```
**Cause:** Wrong credentials or security token.
**Solution:**
```bash
# Reset security token: Setup > My Personal Information > Reset My Security Token
# Append token to password: password + securityToken
# Verify IP is whitelisted or token is appended
echo "Password format: ${SF_PASSWORD}${SF_SECURITY_TOKEN}"
```

---

### INVALID_FIELD — Wrong Field Name in SOQL
```
[{"message":"SELECT Id, FullName FROM Account\n                ^\nERROR: No such column 'FullName' on entity 'Account'","errorCode":"INVALID_FIELD"}]
```
**Cause:** Field API name does not exist on the sObject.
**Solution:**
```typescript
// Check available fields via describe
const meta = await conn.sobject('Account').describe();
const fieldNames = meta.fields.map(f => f.name);
console.log('Available fields:', fieldNames.join(', '));
// Common mistake: "FullName" vs "Name", "Email" on Account (doesn't exist — it's on Contact)
```

---

### MALFORMED_QUERY — SOQL Syntax Error
```
[{"message":"unexpected token: 'FORM'","errorCode":"MALFORMED_QUERY"}]
```
**Cause:** Typo in SOQL keywords or missing quotes.
**Solution:**
```sql
-- Wrong: SELECT Id FORM Account (typo)
-- Right: SELECT Id FROM Account

-- Wrong: WHERE Name = Acme (missing quotes)
-- Right: WHERE Name = 'Acme'

-- Wrong: WHERE CreatedDate > 2026-01-01 (needs literal format)
-- Right: WHERE CreatedDate > 2026-01-01T00:00:00Z
```

---

### REQUIRED_FIELD_MISSING — Missing Required Fields on Create
```
[{"message":"Required fields are missing: [LastName]","errorCode":"REQUIRED_FIELD_MISSING","fields":["LastName"]}]
```
**Cause:** Create/update missing a required field.
**Solution:**
```typescript
// Check required fields
const meta = await conn.sobject('Contact').describe();
const required = meta.fields
  .filter(f => !f.nillable && !f.defaultedOnCreate && f.createable)
  .map(f => f.name);
console.log('Required for create:', required);
// Contact requires: LastName
// Lead requires: LastName, Company
// Opportunity requires: Name, StageName, CloseDate
```

---

### INSUFFICIENT_ACCESS_OR_READONLY — Permission Issue
```
[{"message":"Insufficient access rights on cross-reference id","errorCode":"INSUFFICIENT_ACCESS_OR_READONLY"}]
```
**Cause:** User profile lacks CRUD permission or field-level security blocks access.
**Solution:** In Setup, check:
1. Profile > Object Permissions > verify CRUD for the sObject
2. Profile > Field-Level Security > verify field access
3. Sharing Rules if record-level access is denied
4. Organization-Wide Defaults (OWD) for the object

---

### REQUEST_LIMIT_EXCEEDED — API Limit Hit
```
[{"message":"TotalRequests Limit exceeded.","errorCode":"REQUEST_LIMIT_EXCEEDED"}]
```
**Cause:** Org exceeded the 24-hour rolling API call limit.
**Solution:**
```typescript
// Check remaining API calls
const limits = await conn.request('/services/data/v59.0/limits/');
console.log('Daily API:', limits.DailyApiRequests);
// { Max: 100000, Remaining: 45230 }

// Enterprise Edition base: 100,000/24hr + 1,000 per user license
// Check: Setup > Company Information > API Requests, Last 24 Hours
```

---

### UNABLE_TO_LOCK_ROW — Record Locking Conflict
```
[{"message":"unable to obtain exclusive access to this record","errorCode":"UNABLE_TO_LOCK_ROW"}]
```
**Cause:** Another process is updating the same record simultaneously.
**Solution:** Retry with exponential backoff — this is transient.
```typescript
// This commonly occurs with triggers, workflows, or parallel bulk jobs
// Retry 3 times with increasing delay
await withRetry(() => conn.sobject('Account').update({ Id: id, Name: 'New Name' }));
```

---

### DUPLICATES_DETECTED — Duplicate Rule Triggered
```
[{"message":"Use one of these records?","errorCode":"DUPLICATES_DETECTED"}]
```
**Cause:** Salesforce Duplicate Rules matched existing records.
**Solution:**
```typescript
// Allow duplicates by setting header
const result = await conn.sobject('Lead').create(
  { LastName: 'Smith', Company: 'Acme', Email: 'smith@acme.com' },
  { headers: { 'Sforce-Duplicate-Rule-Header': 'allowSave=true' } }
);
```

---

### FIELD_CUSTOM_VALIDATION_EXCEPTION — Validation Rule Failed
```
[{"message":"Phone number must be 10 digits","errorCode":"FIELD_CUSTOM_VALIDATION_EXCEPTION"}]
```
**Cause:** A validation rule on the sObject rejected the data.
**Solution:** Check Setup > Object Manager > [Object] > Validation Rules to see active rules and fix your data accordingly.

---

### ENTITY_IS_DELETED — Record in Recycle Bin
```
[{"message":"entity is deleted","errorCode":"ENTITY_IS_DELETED"}]
```
**Cause:** Record was soft-deleted and is in the Recycle Bin.
**Solution:**
```sql
-- Query deleted records with ALL ROWS
SELECT Id, Name, IsDeleted FROM Account WHERE Id = '001xx' ALL ROWS

-- Undelete via API
```
```typescript
await conn.sobject('Account').undelete('001xxxxxxxxxxxx');
```

## Quick Diagnostic Commands
```bash
# Check Salesforce system status
curl -s https://api.status.salesforce.com/v1/instances | jq '.[0]'

# Check org API limits via sf CLI
sf org display --target-org my-org

# List recent API errors in debug log
sf apex log list --target-org my-org
sf apex log get --log-id 07Lxx --target-org my-org
```

## Error Handling
| HTTP Status | Error Code | Retryable? |
|------------|------------|------------|
| 400 | MALFORMED_QUERY, INVALID_FIELD | No — fix query |
| 401 | INVALID_SESSION_ID | Yes — refresh token |
| 403 | REQUEST_LIMIT_EXCEEDED | Yes — wait and retry |
| 404 | NOT_FOUND | No — wrong ID or sObject |
| 409 | UNABLE_TO_LOCK_ROW | Yes — retry with backoff |
| 500 | UNKNOWN_EXCEPTION | Maybe — check SF status |

## Resources
- [Salesforce Status API](https://api.status.salesforce.com/)
- [REST API Error Responses](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm)
- [SOQL Date Literals](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm)
- [Salesforce Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)

## Next Steps
For comprehensive debugging, see `salesforce-debug-bundle`.
