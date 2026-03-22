---
name: snowflake-prod-checklist
description: |
  Execute Snowflake production readiness checklist with monitoring and rollback.
  Use when deploying Snowflake pipelines to production, preparing for go-live,
  or validating production Snowflake configuration.
  Trigger with phrases like "snowflake production", "snowflake go-live",
  "snowflake launch checklist", "snowflake prod ready".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Production Checklist

## Overview

Complete checklist for deploying Snowflake data pipelines and integrations to production.

## Prerequisites

- Staging environment validated
- Production Snowflake account configured
- Resource monitors in place
- Monitoring infrastructure ready

## Pre-Deployment Checklist

### Authentication & Secrets
- [ ] Service accounts use key pair auth (not password)
- [ ] Private keys stored in secret manager (not files/env vars)
- [ ] Key rotation procedure documented and tested
- [ ] Network policy applied to production account
- [ ] Connection parameters use production account identifier

### Warehouse Configuration
- [ ] Production warehouses created with appropriate sizing
- [ ] Auto-suspend configured (60-300s based on workload)
- [ ] Auto-resume enabled
- [ ] Resource monitors with credit quotas and alerts
- [ ] Separate warehouses for ETL, analytics, and dashboard workloads

```sql
-- Production warehouse setup
CREATE WAREHOUSE IF NOT EXISTS PROD_ETL_WH
  WAREHOUSE_SIZE = 'LARGE'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;

CREATE WAREHOUSE IF NOT EXISTS PROD_ANALYTICS_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

-- Resource monitor with alerts
CREATE OR REPLACE RESOURCE MONITOR prod_monitor
  WITH CREDIT_QUOTA = 1000
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND
    ON 110 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE PROD_ETL_WH SET RESOURCE_MONITOR = prod_monitor;
ALTER WAREHOUSE PROD_ANALYTICS_WH SET RESOURCE_MONITOR = prod_monitor;
```

### Data Pipeline Readiness
- [ ] All tasks resumed and running on schedule
- [ ] Streams not stale (check with `SHOW STREAMS`)
- [ ] Snowpipe notifications configured and verified
- [ ] COPY INTO error handling set (`ON_ERROR = 'CONTINUE'` or `'SKIP_FILE'`)
- [ ] Data retention set appropriately (`DATA_RETENTION_TIME_IN_DAYS`)

### Query & Performance
- [ ] Critical queries tested at production data volume
- [ ] Clustering keys set on large tables (>1TB)
- [ ] Statement timeout configured per warehouse
- [ ] Result caching enabled (`USE_CACHED_RESULT = TRUE`)

```sql
-- Set statement timeout for production
ALTER WAREHOUSE PROD_ETL_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 3600;
ALTER WAREHOUSE PROD_ANALYTICS_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 600;

-- Enable query result caching (default is ON)
ALTER ACCOUNT SET USE_CACHED_RESULT = TRUE;
```

### Access Control
- [ ] RBAC hierarchy follows Snowflake best practices
- [ ] No users have ACCOUNTADMIN as default role
- [ ] Service accounts have minimal required privileges
- [ ] Object ownership assigned to functional roles

```sql
-- Verify no one defaults to ACCOUNTADMIN
SELECT name, default_role
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
WHERE default_role = 'ACCOUNTADMIN' AND disabled = 'false';
```

### Monitoring & Alerting
- [ ] Query failure alerts configured
- [ ] Warehouse credit consumption dashboards
- [ ] Task failure notifications
- [ ] Login failure monitoring

```sql
-- Create alert for task failures (Snowflake Alerts feature)
CREATE OR REPLACE ALERT task_failure_alert
  WAREHOUSE = PROD_ANALYTICS_WH
  SCHEDULE = '5 MINUTE'
  IF (EXISTS (
    SELECT *
    FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
      SCHEDULED_TIME_RANGE_START => DATEADD(minutes, -10, CURRENT_TIMESTAMP())
    ))
    WHERE state = 'FAILED'
  ))
  THEN
    CALL SYSTEM$SEND_EMAIL(
      'prod_notifications',
      'oncall@company.com',
      'Snowflake Task Failure',
      'One or more tasks failed in the last 10 minutes. Check TASK_HISTORY.'
    );

ALTER ALERT task_failure_alert RESUME;
```

### Disaster Recovery
- [ ] Time Travel retention set (Enterprise: up to 90 days)
- [ ] Database replication configured for critical databases
- [ ] Failover tested to secondary account/region
- [ ] Backup procedure documented

```sql
-- Enable 14-day Time Travel on production tables
ALTER TABLE prod_db.core.orders SET DATA_RETENTION_TIME_IN_DAYS = 14;

-- Enable database replication
ALTER DATABASE prod_db ENABLE REPLICATION TO ACCOUNTS myorg.secondary_account;
```

## Health Check Query

```sql
-- Run this before and after deployment
SELECT 'Warehouses' AS check_type,
       COUNT(*) AS count,
       COUNT_IF(state = 'STARTED') AS active
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSES())
UNION ALL
SELECT 'Tasks', COUNT(*), COUNT_IF(state = 'started')
FROM TABLE(INFORMATION_SCHEMA.TASKS())
UNION ALL
SELECT 'Streams', COUNT(*), COUNT_IF(stale = FALSE)
FROM TABLE(INFORMATION_SCHEMA.STREAMS())
UNION ALL
SELECT 'Pipes', COUNT(*), COUNT_IF(is_autoingest_enabled = 'true')
FROM TABLE(INFORMATION_SCHEMA.PIPES());
```

## Rollback Procedure

```sql
-- Use Time Travel to revert a table
CREATE OR REPLACE TABLE prod_db.core.orders
  CLONE prod_db.core.orders AT (TIMESTAMP => '2026-03-21 12:00:00'::TIMESTAMP_NTZ);

-- Suspend problematic tasks
ALTER TASK transform_orders SUSPEND;

-- Revert warehouse changes
ALTER WAREHOUSE PROD_ETL_WH SET WAREHOUSE_SIZE = 'MEDIUM';
```

## Error Handling

| Alert | Condition | Severity |
|-------|-----------|----------|
| Task failure | `state = 'FAILED'` in TASK_HISTORY | P1 |
| Stream stale | `stale = TRUE` in SHOW STREAMS | P1 |
| Credit quota >90% | Resource monitor trigger | P2 |
| Query queue >5min | `avg_queued_load > 0` sustained | P2 |
| Login failures spike | >10 failures/hour | P2 |

## Resources

- [Resource Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [Business Continuity](https://docs.snowflake.com/en/user-guide/replication-intro)
- [Access Control Best Practices](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)

## Next Steps

For version upgrades, see `snowflake-upgrade-migration`.
