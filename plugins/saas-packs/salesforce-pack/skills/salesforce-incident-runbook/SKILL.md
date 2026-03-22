---
name: salesforce-incident-runbook
description: |
  Execute Salesforce incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Salesforce-related outages, investigating API errors,
  or running post-incident reviews for Salesforce integration failures.
  Trigger with phrases like "salesforce incident", "salesforce outage",
  "salesforce down", "salesforce on-call", "salesforce emergency", "salesforce broken".
allowed-tools: Read, Grep, Bash(sf:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Incident Runbook

## Overview
Rapid incident response procedures for Salesforce integration failures, covering Salesforce-side outages, API limit exhaustion, authentication failures, and data sync issues.

## Prerequisites
- Salesforce CLI authenticated (`sf org login`)
- Access to Salesforce Status API
- Monitoring dashboards configured (see `salesforce-observability`)
- Communication channels (Slack, PagerDuty)

## Quick Triage (Do This First)

```bash
# 1. Is Salesforce itself down?
curl -s https://api.status.salesforce.com/v1/incidents/active | jq '.[0:3]'
# If incidents returned → Salesforce-side issue, enable fallback mode

# 2. Check your org's instance status
# Find your instance at: https://status.salesforce.com
curl -s "https://api.status.salesforce.com/v1/instances/NA45/status" | jq '.status'

# 3. Check API limits — are we out of calls?
sf limits api display --target-org my-org --json | jq '.result[] | select(.name == "DailyApiRequests")'
# If remaining = 0 → API_LIMIT_EXCEEDED, see mitigation below

# 4. Check authentication
sf org display --target-org my-org --json | jq '.result.connectedStatus'
# If "RefreshTokenError" → re-authenticate

# 5. Check recent errors in your logs
sf apex log list --target-org my-org --json | jq '.result[0:5]'
```

## Decision Tree

```
Integration returning errors?
├── YES: Is status.salesforce.com showing incident?
│   ├── YES → Salesforce outage. Enable fallback mode. Monitor status page.
│   └── NO → Check error type below:
│       ├── INVALID_SESSION_ID (401) → Token expired. Re-authenticate.
│       ├── REQUEST_LIMIT_EXCEEDED (403) → API limit hit. Reduce calls.
│       ├── UNABLE_TO_LOCK_ROW (409) → Record contention. Retry with backoff.
│       ├── MALFORMED_QUERY / INVALID_FIELD → Code bug. Check SOQL.
│       └── 500/503 → Salesforce-side. Wait and retry.
└── NO: Is data syncing correctly?
    ├── YES → Likely resolved or intermittent. Monitor.
    └── NO → Check CDC subscription, query timestamps, bulk job status.
```

## Immediate Actions by Error Type

### REQUEST_LIMIT_EXCEEDED — API Limit Exhausted
```typescript
// This is a P1 — your integration is completely blocked

// 1. Check what's consuming API calls
const limits = await conn.request('/services/data/v59.0/limits/');
console.log('API calls:', limits.DailyApiRequests);
console.log('Bulk API:', limits.DailyBulkV2QueryJobs);
// Limits reset on a 24-hour rolling basis

// 2. Identify top consumers (Enterprise+ orgs with EventLogFile)
const topUsers = await conn.query(`
  SELECT UserId, COUNT(Id) callCount
  FROM EventLogFile
  WHERE EventType = 'API' AND LogDate = TODAY
  GROUP BY UserId
  ORDER BY COUNT(Id) DESC
  LIMIT 10
`);

// 3. Immediate mitigation: pause non-critical integrations
// Set env var: SF_CRITICAL_ONLY=true
// Only allow essential operations (auth, health check, critical writes)
```

### INVALID_SESSION_ID — Authentication Failure
```bash
# Token expired or revoked — re-authenticate
sf org login web --alias my-org --instance-url https://login.salesforce.com

# For CI/automated: re-auth with JWT
sf org login jwt \
  --client-id $SF_CLIENT_ID \
  --jwt-key-file server.key \
  --username $SF_USERNAME \
  --alias my-org

# Verify connection is restored
sf org display --target-org my-org
```

### Salesforce System Outage
```typescript
// Enable graceful degradation — serve stale data from cache
const FALLBACK_MODE = process.env.SF_FALLBACK_MODE === 'true';

async function queryWithFallback<T>(soql: string, cacheKey: string): Promise<T[]> {
  if (FALLBACK_MODE) {
    const cached = await redis.get(cacheKey);
    if (cached) {
      console.warn('SF FALLBACK: serving cached data');
      return JSON.parse(cached);
    }
    throw new Error('Salesforce unavailable and no cached data');
  }

  const conn = await getConnection();
  const result = await conn.query<T>(soql);

  // Always update cache for fallback
  await redis.set(cacheKey, JSON.stringify(result.records), 'EX', 3600);
  return result.records;
}
```

## Communication Templates

### Internal (Slack)
```
P1 INCIDENT: Salesforce Integration
Status: INVESTIGATING
Error: [REQUEST_LIMIT_EXCEEDED / INVALID_SESSION_ID / SF outage]
Impact: [Data sync paused / API calls failing / user-facing errors]
Current action: [Checking limits / re-authenticating / enabling fallback]
Next update: [time]
```

### Postmortem Template
```markdown
## Incident: Salesforce [Error Type]
**Date:** YYYY-MM-DD | **Duration:** X hours | **Severity:** P[1-4]

### Summary
[One sentence — e.g., "API limit exhausted due to unoptimized batch job"]

### Root Cause
[e.g., "New sync job ran SELECT * on Contact (3M records) using individual queries instead of Bulk API"]

### Impact
- API calls blocked for [duration]
- [N] users affected / [N] records not synced

### Timeline
- HH:MM — Alerts fired: REQUEST_LIMIT_EXCEEDED
- HH:MM — Triage: identified bulk sync as consumer
- HH:MM — Mitigated: paused sync job
- HH:MM — Resolved: API limit rolled over

### Action Items
- [ ] Migrate sync to Bulk API 2.0 — @owner — due date
- [ ] Add API budget guard (80% warning) — @owner — due date
- [ ] Set up EventLogFile monitoring for top consumers — @owner — due date
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status API | Network issue | Try https://status.salesforce.com manually |
| sf CLI auth expired | Token revoked | Re-authenticate with `sf org login` |
| Limits API returns 403 | Limit already exceeded | Wait for rolling 24hr reset |
| Bulk job stuck | Processing timeout | Abort and retry: `sf data bulk delete` |

## Resources
- [Salesforce Status API](https://api.status.salesforce.com/)
- [Salesforce Trust Site](https://status.salesforce.com)
- [API Limits Quick Reference](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm)

## Next Steps
For data handling, see `salesforce-data-handling`.
