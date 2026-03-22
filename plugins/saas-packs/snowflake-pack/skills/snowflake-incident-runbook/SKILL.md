---
name: snowflake-incident-runbook
description: |
  Execute Snowflake incident response with triage, rollback, and postmortem using real SQL diagnostics.
  Use when responding to Snowflake outages, investigating query failures,
  or running post-incident reviews for pipeline failures.
  Trigger with phrases like "snowflake incident", "snowflake outage",
  "snowflake down", "snowflake on-call", "snowflake emergency".
allowed-tools: Read, Grep, Bash(curl:*), Bash(snowsql:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Incident Runbook

## Overview

Rapid incident response procedures for Snowflake infrastructure, pipeline failures, and query issues.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | All queries failing, auth broken |
| P2 | Degraded service | < 1 hour | High latency, task failures |
| P3 | Minor impact | < 4 hours | Snowpipe delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps, cost anomalies |

## Quick Triage (First 5 Minutes)

### Step 1: Is Snowflake Itself Down?

```bash
# Check Snowflake status page
curl -s https://status.snowflake.com/api/v2/summary.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Status: {data['status']['description']}\")
for c in data['components']:
    if c['status'] != 'operational':
        print(f\"  DEGRADED: {c['name']} - {c['status']}\")
"
```

### Step 2: Can We Connect?

```sql
-- Quick connectivity test
SELECT CURRENT_TIMESTAMP(), CURRENT_ACCOUNT(), CURRENT_REGION();

-- If this fails, the issue is connectivity/auth, not query logic
```

### Step 3: What's Failing?

```sql
-- Recent failures (last 30 minutes)
SELECT error_code, error_message, COUNT(*) AS occurrences,
       MIN(start_time) AS first_seen, MAX(start_time) AS last_seen
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'FAIL'
  AND start_time >= DATEADD(minutes, -30, CURRENT_TIMESTAMP())
GROUP BY error_code, error_message
ORDER BY occurrences DESC;

-- Failed tasks
SELECT name, state, error_message, scheduled_time, completed_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
  SCHEDULED_TIME_RANGE_START => DATEADD(hours, -1, CURRENT_TIMESTAMP())
))
WHERE state = 'FAILED'
ORDER BY scheduled_time DESC;

-- Stale streams (data loss risk)
SHOW STREAMS;
-- Check STALE column — if TRUE, stream offset is beyond retention
```

## Decision Tree

```
Query failures?
├─ Auth errors (390100, 390144)
│   → Check credentials, key pair, network policy
├─ Object not found (002003)
│   → Wrong context? Permissions? Object dropped?
├─ Warehouse issues (000606)
│   → Warehouse suspended? Resource monitor hit?
├─ Timeout (100038)
│   → Query too slow? Warehouse too small?
└─ Snowflake platform issue (5xx, connectivity)
    → Check status.snowflake.com → enable fallback

Pipeline failures?
├─ Task failed
│   → Check TASK_HISTORY error_message
│   → Is source stream stale?
├─ Snowpipe not loading
│   → SYSTEM$PIPE_STATUS('pipe_name')
│   → Check S3 event notifications
└─ Dynamic table not refreshing
    → Check DYNAMIC_TABLE_REFRESH_HISTORY
```

## Immediate Actions

### Authentication Failure (P1)

```sql
-- Check login failures
SELECT user_name, client_ip, error_code, error_message, event_timestamp
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE is_success = 'NO'
  AND event_timestamp >= DATEADD(minutes, -30, CURRENT_TIMESTAMP())
ORDER BY event_timestamp DESC;

-- If key pair issue — verify public key assignment
DESC USER svc_etl;
-- Check RSA_PUBLIC_KEY and RSA_PUBLIC_KEY_2
```

### Warehouse Suspended by Resource Monitor (P1)

```sql
-- Check resource monitor status
SHOW RESOURCE MONITORS;

-- Temporarily increase quota
ALTER RESOURCE MONITOR prod_monitor SET CREDIT_QUOTA = 3000;

-- Or switch to a different warehouse
ALTER SESSION SET WAREHOUSE = BACKUP_WH;
```

### Pipeline Failure — Stale Stream (P1)

```sql
-- If stream is stale, data between old and new offset is lost
-- You must recreate the stream and backfill

-- Check stream status
SELECT * FROM TABLE(INFORMATION_SCHEMA.STREAMS())
WHERE stale = TRUE;

-- Recreate stream
DROP STREAM IF EXISTS orders_stream;
CREATE STREAM orders_stream ON TABLE raw_orders;

-- Backfill from Time Travel
INSERT INTO dim_orders
SELECT * FROM raw_orders
AT (TIMESTAMP => '<last_known_good_timestamp>'::TIMESTAMP_NTZ)
WHERE order_id NOT IN (SELECT order_id FROM dim_orders);
```

### Rollback a Bad Deployment (P2)

```sql
-- Use Time Travel to restore table to pre-deployment state
CREATE OR REPLACE TABLE prod_dw.silver.users
  CLONE prod_dw.silver.users
  AT (TIMESTAMP => '2026-03-22 08:00:00'::TIMESTAMP_NTZ);

-- Or use UNDROP for accidentally dropped objects
UNDROP TABLE prod_dw.silver.users;
UNDROP SCHEMA prod_dw.silver;
UNDROP DATABASE prod_dw;

-- Suspend problematic tasks
ALTER TASK transform_orders SUSPEND;
```

## Communication Templates

**Internal (Slack):**
```
P1 INCIDENT: Snowflake [Category]
Status: INVESTIGATING
Impact: [Describe user/pipeline impact]
Current action: [What you're doing now]
Next update: [Time]
Incident commander: @[name]
```

**Postmortem Template:**
```markdown
## Incident: [Title]
**Date:** YYYY-MM-DD | **Duration:** X hours | **Severity:** P[1-4]

### Summary
[1-2 sentences]

### Timeline (UTC)
- HH:MM — [Event/detection]
- HH:MM — [Response action]
- HH:MM — [Resolution]

### Root Cause
[Technical explanation referencing specific error codes and query IDs]

### Impact
- Pipelines affected: N
- Data freshness delay: X hours
- Credit overage: Y credits

### Action Items
- [ ] [Preventive measure] — Owner — Due date
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't query ACCOUNT_USAGE | Missing privileges | Use ACCOUNTADMIN or grant IMPORTED PRIVILEGES |
| Time Travel expired | Past retention period | Cannot recover; increase retention proactively |
| Task won't resume | Dependency chain issue | Resume children first, then parent |
| Snowpipe backlog | S3 notification gap | Check SQS queue, run `ALTER PIPE x REFRESH` |

## Resources

- [Snowflake Status](https://status.snowflake.com)
- [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
- [UNDROP](https://docs.snowflake.com/en/sql-reference/sql/undrop)
- [Snowflake Support](https://community.snowflake.com/s/article/How-To-Submit-a-Support-Case-in-Snowflake-Lodge)

## Next Steps

For data governance, see `snowflake-data-handling`.
