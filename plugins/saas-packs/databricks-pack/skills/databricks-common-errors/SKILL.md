---
name: databricks-common-errors
description: |
  Diagnose and fix Databricks common errors and exceptions.
  Use when encountering Databricks errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "databricks error", "fix databricks",
  "databricks not working", "debug databricks".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Common Errors

## Overview

Quick reference for the most common Databricks errors: connection failures, query timeouts, permission issues, and schema problems.


## Prerequisites
- Databricks SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

### Connection Pool Exhausted
**Error Message:**
```
Error: too many clients already / connection pool timeout
```

**Cause:** All connections in the pool are in use. Common with serverless functions creating new pools on each invocation.

**Solution:**
```bash
# Use connection pooling (PgBouncer, built-in pooler)
# Set pool max to match your plan's connection limit
# Ensure connections are released after queries (finally blocks)

```

---

### Query Timeout
**Error Message:**
```
Error: canceling statement due to statement timeout (30000ms)
```

**Cause:** Query execution exceeded the statement_timeout setting. Usually a missing index or full table scan.

**Solution:**
# Analyze the query plan
EXPLAIN ANALYZE SELECT ...;
# Add covering index for common filter columns
CREATE INDEX CONCURRENTLY idx_name ON table(column);
# Increase timeout for one-off analytical queries only


---

### Relation Does Not Exist
**Error Message:**
```
ERROR: relation "events" does not exist
```

**Cause:** Table not created yet, wrong schema search path, or typo in table name.

**Solution:**
```typescript
# Check available tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
# Set search_path if using custom schemas
SET search_path TO myschema, public;

```


---

### Deadlock Detected
**Error Message:**
```
ERROR: deadlock detected — Process 12345 waits for ShareLock on transaction 67890
```

**Cause:** Two concurrent transactions waiting on each other's locks. Common with concurrent UPDATEs on same rows.

**Solution:**
Ensure consistent lock ordering across transactions. Use `SELECT ... FOR UPDATE SKIP LOCKED` for queue patterns. Reduce transaction scope and duration.


## Examples

### Quick Diagnostic Commands
```bash
# Check Databricks status
curl -s https://status.databricks.com

# Verify API connectivity
curl -I https://api.databricks.com

# Check local configuration
env | grep DATABRICKS
```

### Escalation Path
1. Collect evidence with `databricks-debug-bundle`
2. Check Databricks status page
3. Contact support with request ID

## Resources
- [Databricks Status Page](https://status.databricks.com)
- [Databricks Support](https://docs.databricks.com/support)
- [Databricks Error Codes](https://docs.databricks.com/errors)

## Next Steps
For comprehensive debugging, see `databricks-debug-bundle`.