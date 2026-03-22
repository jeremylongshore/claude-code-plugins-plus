---
name: salesforce-debug-bundle
description: |
  Collect Salesforce debug evidence including API limits, debug logs, and org info for support tickets.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Salesforce problems.
  Trigger with phrases like "salesforce debug", "salesforce support bundle",
  "collect salesforce logs", "salesforce diagnostic", "salesforce debug log".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(sf:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Debug Bundle

## Overview
Collect all necessary diagnostic information for Salesforce issues: debug logs, API limits, org configuration, and error traces.

## Prerequisites
- Salesforce CLI authenticated (`sf org login web`)
- jsforce connection configured
- Access to Setup in your Salesforce org

## Instructions

### Step 1: Collect Org Info & API Limits
```typescript
import { getConnection } from './salesforce/connection';

const conn = await getConnection();

// Org limits — most critical diagnostic info
const limits = await conn.request('/services/data/v59.0/limits/');
console.log('=== API Limits ===');
console.log(`Daily API Requests: ${limits.DailyApiRequests.Remaining}/${limits.DailyApiRequests.Max}`);
console.log(`Daily Bulk API: ${limits.DailyBulkV2QueryJobs.Remaining}/${limits.DailyBulkV2QueryJobs.Max}`);
console.log(`Data Storage (MB): ${limits.DataStorageMB.Remaining}/${limits.DataStorageMB.Max}`);
console.log(`File Storage (MB): ${limits.FileStorageMB.Remaining}/${limits.FileStorageMB.Max}`);
console.log(`Single Email: ${limits.SingleEmail.Remaining}/${limits.SingleEmail.Max}`);

// Org identity
const identity = await conn.identity();
console.log(`\n=== Org Info ===`);
console.log(`Username: ${identity.username}`);
console.log(`Org ID: ${identity.organization_id}`);
console.log(`Instance: ${conn.instanceUrl}`);
console.log(`API Version: ${conn.version}`);
```

### Step 2: Enable & Retrieve Debug Logs
```bash
# Set up a trace flag for debug logging via SF CLI
sf apex log list --target-org my-org

# Get the most recent debug log
sf apex log get --number 1 --target-org my-org

# Or tail logs in real-time during testing
sf apex log tail --target-org my-org --debug-level SFDC_DevConsole
```

### Step 3: Query Recent API Events
```typescript
// EventLogFile — Enterprise+ orgs only
// Contains API usage data for the last 30 days
const eventLogs = await conn.query(`
  SELECT Id, EventType, LogDate, LogFileLength
  FROM EventLogFile
  WHERE EventType = 'API'
    AND LogDate >= LAST_N_DAYS:7
  ORDER BY LogDate DESC
  LIMIT 5
`);

for (const log of eventLogs.records) {
  console.log(`Event: ${log.EventType}, Date: ${log.LogDate}, Size: ${log.LogFileLength}`);
  // Download log content
  const content = await conn.request(`/services/data/v59.0/sobjects/EventLogFile/${log.Id}/LogFile`);
  console.log(content);
}
```

### Step 4: Create Debug Bundle Script
```bash
#!/bin/bash
# salesforce-debug-bundle.sh
BUNDLE_DIR="sf-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Salesforce Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"

# Org info
sf org display --target-org my-org --json > "$BUNDLE_DIR/org-info.json" 2>&1

# API limits
sf limits api display --target-org my-org --json > "$BUNDLE_DIR/api-limits.json" 2>&1

# Recent debug logs
sf apex log list --target-org my-org --json > "$BUNDLE_DIR/log-list.json" 2>&1
sf apex log get --number 5 --target-org my-org > "$BUNDLE_DIR/debug-logs.txt" 2>&1

# Node environment
echo "--- Node Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm list jsforce 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# Salesforce system status
curl -s "https://api.status.salesforce.com/v1/instances/$(sf org display --target-org my-org --json | jq -r '.result.instanceUrl' | sed 's|https://||;s|\..*||')/status" > "$BUNDLE_DIR/sf-status.json" 2>&1

# Redact secrets from .env
if [ -f .env ]; then
  cat .env | sed 's/=.*/=***REDACTED***/' > "$BUNDLE_DIR/config-redacted.txt"
fi

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 5: Check Salesforce System Status
```typescript
// Check if Salesforce itself is having issues
const statusResponse = await fetch('https://api.status.salesforce.com/v1/incidents/active');
const incidents = await statusResponse.json();

if (incidents.length > 0) {
  console.log('ACTIVE SALESFORCE INCIDENTS:');
  for (const incident of incidents) {
    console.log(`  ${incident.id}: ${incident.message.maintenanceType}`);
    console.log(`    Affected: ${incident.instanceKeys.join(', ')}`);
  }
} else {
  console.log('No active Salesforce incidents — issue is likely org-specific');
}
```

## Output
- `sf-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Environment and SDK versions
  - `org-info.json` — Org identity and configuration
  - `api-limits.json` — Current API usage vs limits
  - `debug-logs.txt` — Recent Apex debug logs
  - `sf-status.json` — Salesforce system status
  - `config-redacted.txt` — Configuration (secrets removed)

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| API limits | Check if limits are exhausted | Yes |
| Debug logs | Apex execution traces | Yes |
| Org info | Instance, edition, user | Yes |
| System status | Salesforce-side outages | Yes |
| Environment | Node.js, jsforce versions | Yes |

## Resources
- [Salesforce Status API](https://api.status.salesforce.com/)
- [Debug Log Levels](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm)
- [EventLogFile (Shield)](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm)
- [API Limits Resource](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm)

## Next Steps
For rate limit issues, see `salesforce-rate-limits`.
