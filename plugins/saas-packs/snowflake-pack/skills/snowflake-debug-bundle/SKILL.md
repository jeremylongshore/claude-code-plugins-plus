---
name: snowflake-debug-bundle
description: |
  Collect Snowflake debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support cases,
  or collecting diagnostic information from QUERY_HISTORY and ACCOUNT_USAGE.
  Trigger with phrases like "snowflake debug", "snowflake support bundle",
  "snowflake diagnostic", "snowflake query history", "snowflake troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Debug Bundle

## Overview

Collect diagnostic information from Snowflake's ACCOUNT_USAGE views, QUERY_HISTORY, and driver logs for support tickets and troubleshooting.

## Prerequisites

- Role with access to `SNOWFLAKE.ACCOUNT_USAGE` schema (typically ACCOUNTADMIN)
- Access to application logs
- Permission to collect environment info

## Instructions

### Step 1: Query-Level Diagnostics

```sql
-- Find the problematic query by ID
SELECT query_id, query_text, execution_status, error_code, error_message,
       start_time, end_time, total_elapsed_time / 1000 AS elapsed_seconds,
       bytes_scanned, rows_produced, compilation_time, execution_time,
       warehouse_name, warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_id = '<paste-query-id-here>';

-- Recent failed queries
SELECT query_id, query_text, error_code, error_message,
       start_time, user_name, role_name, warehouse_name
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'FAIL'
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 20;

-- Slow queries (> 60 seconds)
SELECT query_id, query_text, total_elapsed_time / 1000 AS seconds,
       bytes_scanned / 1e9 AS gb_scanned, partitions_scanned, partitions_total,
       warehouse_name, warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE total_elapsed_time > 60000
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 10;
```

### Step 2: Connection and Session Diagnostics

```sql
-- Active sessions
SELECT session_id, user_name, created_on,
       client_application_id, client_environment
FROM TABLE(INFORMATION_SCHEMA.SESSIONS())
ORDER BY created_on DESC;

-- Login history (auth failures)
SELECT event_timestamp, user_name, client_ip, reported_client_type,
       error_code, error_message, is_success
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE event_timestamp >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND is_success = 'NO'
ORDER BY event_timestamp DESC;
```

### Step 3: Warehouse and Resource Diagnostics

```sql
-- Warehouse load (queued queries = undersized)
SELECT warehouse_name, start_time,
       avg_running, avg_queued_load, avg_queued_provisioning, avg_blocked
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_LOAD_HISTORY(
  DATE_RANGE_START => DATEADD(hours, -4, CURRENT_TIMESTAMP())
))
ORDER BY start_time DESC;

-- Credit consumption by warehouse
SELECT warehouse_name, SUM(credits_used) AS credits,
       SUM(credits_used_compute) AS compute_credits,
       SUM(credits_used_cloud_services) AS cloud_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(days, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY credits DESC;
```

### Step 4: Create Debug Bundle Script

```bash
#!/bin/bash
# snowflake-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="snowflake-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Snowflake Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"

# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || true
python3 --version >> "$BUNDLE_DIR/summary.txt" 2>&1 || true
echo "SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"
echo "SNOWFLAKE_WAREHOUSE: ${SNOWFLAKE_WAREHOUSE:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"

# Driver versions
echo "--- Driver Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list snowflake-sdk 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "Node driver: N/A" >> "$BUNDLE_DIR/summary.txt"
pip show snowflake-connector-python 2>/dev/null | grep -E "Name|Version" >> "$BUNDLE_DIR/summary.txt" || echo "Python connector: N/A" >> "$BUNDLE_DIR/summary.txt"

# Recent application logs (redacted)
if [ -f "logs/app.log" ]; then
  grep -i "snowflake\|error\|timeout\|connection" logs/app.log 2>/dev/null \
    | tail -100 \
    | sed -E 's/(password|token|key)=[^ ]*/\1=***REDACTED***/gi' \
    > "$BUNDLE_DIR/app-logs-redacted.txt"
fi

# Configuration (redacted)
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
fi

# Network test
echo "--- Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" \
  "https://${SNOWFLAKE_ACCOUNT:-unknown}.snowflakecomputing.com/" \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "Connectivity test failed" >> "$BUNDLE_DIR/summary.txt"

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 5: Submit to Snowflake Support

1. Go to [Snowflake Support](https://community.snowflake.com/s/article/How-To-Submit-a-Support-Case-in-Snowflake-Lodge)
2. Include: account identifier, query IDs, error codes, timestamps (UTC)
3. Attach debug bundle (ensure no credentials included)
4. Reference the specific error code from `QUERY_HISTORY`

## Sensitive Data Handling

**ALWAYS REDACT:** passwords, private keys, OAuth tokens, PII
**SAFE TO INCLUDE:** error codes, query IDs, query text (if no PII), timestamps, warehouse names

## Error Handling

| Item | Purpose | Source |
|------|---------|--------|
| Query ID | Pinpoint exact failure | `QUERY_HISTORY` |
| Error code | Classify issue type | Error message |
| Warehouse load | Identify resource contention | `WAREHOUSE_LOAD_HISTORY` |
| Login history | Auth failure pattern | `LOGIN_HISTORY` |
| Driver version | Version-specific bugs | `npm list` / `pip show` |

## Resources

- [QUERY_HISTORY View](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [Account Usage](https://docs.snowflake.com/en/sql-reference/account-usage)
- [Snowflake Support](https://community.snowflake.com/s/article/How-To-Submit-a-Support-Case-in-Snowflake-Lodge)

## Next Steps

For concurrency and warehouse sizing, see `snowflake-rate-limits`.
