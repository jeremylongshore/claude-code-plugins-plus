---
name: salesforce-advanced-troubleshooting
description: |
  Apply Salesforce advanced debugging with debug logs, SOQL query plans, and EventLogFile analysis.
  Use when standard troubleshooting fails, investigating SOQL performance issues,
  or analyzing Apex governor limit violations.
  Trigger with phrases like "salesforce hard bug", "salesforce debug log",
  "salesforce governor limit", "salesforce query plan", "salesforce deep debug", "SOQL slow".
allowed-tools: Read, Grep, Bash(sf:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Advanced Troubleshooting

## Overview
Deep debugging techniques for complex Salesforce issues: Apex debug log analysis, SOQL query plan optimization, governor limit diagnosis, and EventLogFile forensics.

## Prerequisites
- Salesforce CLI authenticated
- Access to Setup > Debug Logs
- Understanding of Apex governor limits
- Enterprise+ for EventLogFile access

## Instructions

### Step 1: Enable Debug Logging

```bash
# Set up debug logging for a specific user
sf apex log list --target-org my-org

# Create a trace flag for detailed logging
# Setup > Debug Logs > New Trace Flag
# - Traced Entity: your integration user
# - Debug Level: SFDC_DevConsole (or create custom)
# - Start: now, Expiration: +2 hours

# Tail logs in real-time
sf apex log tail --target-org my-org --debug-level SFDC_DevConsole
```

### Step 2: Analyze Debug Log for Governor Limits

```typescript
// Key governor limits to watch in debug logs:
const GOVERNOR_LIMITS = {
  'Number of SOQL queries':          { limit: 100, trigger: 'per transaction' },
  'Number of query rows':            { limit: 50000, trigger: 'per transaction' },
  'Number of DML statements':        { limit: 150, trigger: 'per transaction' },
  'Number of DML rows':              { limit: 10000, trigger: 'per transaction' },
  'Maximum CPU time':                { limit: 10000, trigger: 'ms per transaction' },
  'Maximum heap size':               { limit: 6000000, trigger: 'bytes (sync), 12MB (async)' },
  'Number of callouts':              { limit: 100, trigger: 'per transaction' },
  'Number of future calls':          { limit: 50, trigger: 'per transaction' },
};

// Parse debug log for limit consumption
// Look for lines like:
// Number of SOQL queries: 45 out of 100
// Number of query rows: 23456 out of 50000
// Maximum CPU time on the Salesforce servers: 8500 out of 10000
```

```bash
# Download and analyze debug log
sf apex log get --number 1 --target-org my-org > debug.log

# Search for limit warnings
grep -n "LIMIT_USAGE_FOR_NS" debug.log
grep -n "out of" debug.log | tail -20

# Search for slow SOQL
grep -n "SOQL_EXECUTE_BEGIN" debug.log
grep -n "SOQL_EXECUTE_END" debug.log
# Compare timestamps — queries > 1000ms need optimization
```

### Step 3: SOQL Query Plan Analysis

```typescript
// Use the Query Plan tool in Developer Console:
// Developer Console > Query Editor > Query Plan button

// Or via REST API (Tooling API)
const conn = await getConnection();

const queryPlan = await conn.request({
  method: 'GET',
  url: `/services/data/v59.0/query/?explain=SELECT Id, Name FROM Account WHERE Industry = 'Technology'`,
});

// Analyze the plan
for (const plan of queryPlan.plans) {
  console.log({
    cardinality: plan.cardinality,         // Estimated result rows
    fields: plan.fields,                    // Fields used in filter
    leadingOperationType: plan.leadingOperationType, // Index | TableScan
    relativeCost: plan.relativeCost,        // Lower is better (0-1)
    spikeError: plan.spikeError,            // True if selective threshold exceeded
  });
}

// GOOD: leadingOperationType = "Index" and relativeCost < 0.3
// BAD: leadingOperationType = "TableScan" — needs index or different filter

// Selective filters (use indexed fields):
// - Id, Name, OwnerId (always indexed)
// - CreatedDate, LastModifiedDate, SystemModstamp
// - Lookup/Master-Detail fields
// - Custom fields marked as External ID or Unique
// - Custom indexes (request via Salesforce Support)
```

### Step 4: Diagnose UNABLE_TO_LOCK_ROW

```typescript
// UNABLE_TO_LOCK_ROW occurs when:
// 1. Multiple processes update the same record simultaneously
// 2. Bulk operations trigger cascading updates via triggers/flows
// 3. Parent record locked by child DML (implicit lock)

// Diagnostic query — find records with heavy automation
const triggers = await conn.query(`
  SELECT Name, TableEnumOrId, Body
  FROM ApexTrigger
  WHERE Status = 'Active'
  ORDER BY TableEnumOrId
`);

console.log('Active triggers:', triggers.records.map(
  (t: any) => `${t.Name} on ${t.TableEnumOrId}`
));

// Mitigation: Use Bulk API with serial mode
await conn.bulk2.loadAndWaitForResults({
  object: 'Account',
  operation: 'update',
  input: csvData,
  lineEnding: 'LF',
  // Bulk API processes in parallel by default
  // For lock issues, reduce concurrency or use smaller batches
});
```

### Step 5: EventLogFile Forensics (Enterprise+)

```typescript
// EventLogFile stores detailed API usage data for 30 days
const conn = await getConnection();

// Find heavy API consumers
const apiEvents = await conn.query(`
  SELECT Id, EventType, LogDate, LogFileLength
  FROM EventLogFile
  WHERE EventType = 'API'
    AND LogDate >= LAST_N_DAYS:1
  ORDER BY LogFileLength DESC
  LIMIT 5
`);

for (const event of apiEvents.records) {
  // Download the CSV log file
  const csvContent = await conn.request(
    `/services/data/v59.0/sobjects/EventLogFile/${event.Id}/LogFile`
  );

  // CSV columns include:
  // TIMESTAMP, USER_ID, URI, METHOD, STATUS_CODE, RUN_TIME, CPU_TIME, DB_TOTAL_TIME
  // Parse to find slow queries, high CPU operations, etc.
  console.log(`${event.EventType} log (${event.LogDate}): ${event.LogFileLength} bytes`);
}

// Login forensics
const loginEvents = await conn.query(`
  SELECT Id, LogDate, LogFileLength
  FROM EventLogFile
  WHERE EventType = 'Login'
    AND LogDate >= LAST_N_DAYS:7
`);
```

### Step 6: Minimal Reproduction

```typescript
// Strip to absolute minimum to isolate the issue
async function minimalRepro(): Promise<void> {
  const conn = new jsforce.Connection({
    loginUrl: process.env.SF_LOGIN_URL,
    version: '59.0', // Pin version
  });

  await conn.login(process.env.SF_USERNAME!, process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!);

  // Test with simplest possible operation
  try {
    // 1. Can we query at all?
    const result = await conn.query('SELECT Id FROM Account LIMIT 1');
    console.log('Basic query works:', result.totalSize);

    // 2. Can we create?
    const created = await conn.sobject('Account').create({ Name: 'Debug Test' });
    console.log('Create works:', created.success);

    // 3. Clean up
    await conn.sobject('Account').destroy(created.id);
    console.log('Delete works');
  } catch (error: any) {
    console.error('FAILURE:', {
      errorCode: error.errorCode,
      message: error.message,
      fields: error.fields,
    });
  }
}
```

## Output
- Debug logging enabled with trace flags
- Governor limit consumption identified
- SOQL query plan analyzed for performance issues
- EventLogFile data retrieved for API forensics
- Minimal reproduction created for support escalation

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No debug logs appearing | Trace flag expired or wrong user | Recreate trace flag in Setup |
| `SOQL_EXECUTE_LIMIT` | 100+ queries in one transaction | Consolidate queries, use collections |
| Query plan shows TableScan | Non-selective filter | Add indexed field to WHERE clause |
| EventLogFile empty | Not Enterprise+ edition | Use instrumented client logging instead |

## Resources
- [Debug Log Reference](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm)
- [SOQL Query Plan](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_query_plan.htm)
- [Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm)
- [EventLogFile](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)

## Next Steps
For load testing, see `salesforce-load-scale`.
