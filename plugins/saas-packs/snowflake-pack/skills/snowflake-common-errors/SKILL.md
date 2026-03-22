---
name: snowflake-common-errors
description: |
  Diagnose and fix common Snowflake errors and SQL compilation failures.
  Use when encountering Snowflake error codes, failed queries,
  authentication issues, or warehouse/connection problems.
  Trigger with phrases like "snowflake error", "fix snowflake",
  "snowflake not working", "snowflake SQL error", "snowflake 002003".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Common Errors

## Overview

Quick reference for the most common Snowflake error codes, SQL compilation errors, and driver issues with real solutions.

## Error Reference

### 002003 (42S02): Object Does Not Exist

```
SQL compilation error: Object 'MY_DB.MY_SCHEMA.USERS' does not exist or not authorized.
```

**Causes:** Table doesn't exist, wrong database/schema context, or role lacks privileges.

**Solutions:**
```sql
-- Check current context
SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE();

-- Verify object exists
SHOW TABLES LIKE 'USERS' IN SCHEMA MY_DB.MY_SCHEMA;

-- Grant access if needed
GRANT SELECT ON TABLE MY_DB.MY_SCHEMA.USERS TO ROLE MY_ROLE;

-- Use fully-qualified names to avoid context issues
SELECT * FROM MY_DB.MY_SCHEMA.USERS;
```

### 000606: No Active Warehouse

```
SQL execution error: No active warehouse selected in the current session.
```

**Solutions:**
```sql
-- Set warehouse for session
USE WAREHOUSE COMPUTE_WH;

-- Or set in connection config
-- warehouse: 'COMPUTE_WH' in createConnection()

-- Check warehouse state
SHOW WAREHOUSES LIKE 'COMPUTE_WH';
-- If SUSPENDED, it auto-resumes if AUTO_RESUME = TRUE
```

### 390100: Incorrect Username or Password

```
Incorrect username or password was specified.
```

**Solutions:**
```bash
# Verify credentials are set
echo $SNOWFLAKE_ACCOUNT  # Should be 'orgname-accountname'
echo $SNOWFLAKE_USER

# Test with SnowSQL
snowsql -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER

# Check account format — common mistake:
# Wrong: myaccount.us-east-1.snowflakecomputing.com
# Right: myorg-myaccount
```

### 390144: JWT Token Invalid (Key Pair Auth)

```
JWT token is invalid.
```

**Solutions:**
```bash
# Verify public key is assigned
# Run in Snowflake:
# DESC USER my_user;
# Check RSA_PUBLIC_KEY column

# Regenerate if needed
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Re-assign (remove headers/newlines from pub key first)
# ALTER USER my_user SET RSA_PUBLIC_KEY='MIIBIj...';
```

### 001003: SQL Compilation Error

```
SQL compilation error: syntax error line X at position Y unexpected 'TOKEN'.
```

**Common causes:**
```sql
-- Missing semicolons in multi-statement mode
-- Wrong: SELECT 1 SELECT 2
-- Right: SELECT 1; SELECT 2;

-- Reserved word used as identifier
-- Wrong: SELECT order FROM orders
-- Right: SELECT "order" FROM orders

-- Wrong function syntax
-- Wrong: DATEADD('day', 1, col)
-- Right: DATEADD(day, 1, col)  -- no quotes on date part
```

### 100038: Statement Timeout

```
Statement reached its statement or warehouse timeout of X second(s).
```

**Solutions:**
```sql
-- Increase statement timeout (seconds)
ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 3600;

-- Or per-warehouse
ALTER WAREHOUSE COMPUTE_WH SET STATEMENT_TIMEOUT_IN_SECONDS = 3600;

-- Check if query needs optimization
SELECT query_id, query_text, execution_status, error_message,
       total_elapsed_time / 1000 AS seconds
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE execution_status = 'FAIL'
ORDER BY start_time DESC LIMIT 10;
```

### 100035: Out of Memory / Result Too Large

```
Results exceed the allowed data size.
```

**Solutions:**
```typescript
// Use streaming in Node.js instead of fetching all rows
connection.execute({
  sqlText: 'SELECT * FROM large_table',
  streamResult: true,  // Don't buffer all rows in memory
  complete: (err, stmt) => {
    const stream = stmt.streamRows();
    stream.on('data', (row) => processRow(row));
    stream.on('end', () => console.log('Done'));
  },
});
```
```python
# Use fetchmany() in Python
cursor.execute("SELECT * FROM large_table")
while True:
    rows = cursor.fetchmany(10000)
    if not rows:
        break
    process_batch(rows)
```

### Node.js Driver: Network / Connection Errors

```
Error: connect ECONNREFUSED
Error: getaddrinfo ENOTFOUND
```

**Solutions:**
```typescript
// Wrong account identifier format
// Wrong: 'myaccount.us-east-1.snowflakecomputing.com'
// Right: 'myorg-myaccount'

// Check for proxy/firewall
// Snowflake requires outbound HTTPS to *.snowflakecomputing.com

// Enable connection diagnostics
snowflake.configure({ logLevel: 'DEBUG' });
```

### Python Connector: OperationalError

```python
# Common: snowflake.connector.errors.OperationalError
# 250001: Could not connect to Snowflake backend

# Check connectivity
import snowflake.connector
snowflake.connector.connect(
    account='myorg-myaccount',
    user='test',
    password='test',
    login_timeout=10,  # Fail fast for testing
)
```

## Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== Snowflake Diagnostic ==="
echo "Account: ${SNOWFLAKE_ACCOUNT:-NOT SET}"
echo "User: ${SNOWFLAKE_USER:-NOT SET}"
echo "Password: ${SNOWFLAKE_PASSWORD:+SET (hidden)}"
echo "Warehouse: ${SNOWFLAKE_WAREHOUSE:-NOT SET}"
echo ""
echo "Connectivity test:"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s" \
  "https://${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/session/v1/login-request" || echo "FAILED"
echo ""
echo "Driver versions:"
npm list snowflake-sdk 2>/dev/null || echo "Node.js driver: not installed"
pip show snowflake-connector-python 2>/dev/null | grep Version || echo "Python connector: not installed"
```

## Error Handling

| Error Code | Category | Quick Fix |
|-----------|----------|-----------|
| `002003` | Object not found | Check context, grant access |
| `000606` | No warehouse | `USE WAREHOUSE x;` |
| `390100` | Auth failure | Check account format, credentials |
| `390144` | JWT invalid | Regenerate key pair |
| `001003` | SQL syntax | Check reserved words, function syntax |
| `100038` | Timeout | Increase timeout or optimize query |
| `100035` | Too large | Use streaming or pagination |

## Resources

- [Error Messages](https://docs.snowflake.com/en/user-guide/client-connectivity-troubleshooting/error-messages)
- [Key Pair Troubleshooting](https://docs.snowflake.com/en/user-guide/key-pair-auth-troubleshooting)
- [Connection Troubleshooting](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-use)

## Next Steps

For comprehensive debugging, see `snowflake-debug-bundle`.
