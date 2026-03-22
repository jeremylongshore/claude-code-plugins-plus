---
name: clickhouse-common-errors
description: |
  Diagnose and fix ClickHouse common errors and exceptions.
  Use when encountering ClickHouse errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "clickhouse error", "fix clickhouse",
  "clickhouse not working", "debug clickhouse".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse Common Errors

## Overview
Quick reference for the top 10 most common ClickHouse errors and their solutions.

## Prerequisites
- ClickHouse SDK installed
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

### Authentication Failed
**Error Message:**
```
Authentication error: Invalid API key
```

**Cause:** API key is missing, expired, or invalid.

**Solution:**
```bash
# Verify API key is set
echo $CLICKHOUSE_API_KEY
```

---

### Rate Limit Exceeded
**Error Message:**
```
Rate limit exceeded. Please retry after X seconds.
```

**Cause:** Too many requests in a short period.

**Solution:**
Implement exponential backoff. See `clickhouse-rate-limits` skill.

---

### Network Timeout
**Error Message:**
```
Request timeout after 30000ms
```

**Cause:** Network connectivity or server latency issues.

**Solution:**
```typescript
// Increase timeout
const client = new Client({ timeout: 60000 });
```

## Examples

### Quick Diagnostic Commands
```bash
# Check ClickHouse status
curl -s https://status.clickhouse.com

# Verify API connectivity
curl -I https://api.clickhouse.com

# Check local configuration
env | grep CLICKHOUSE
```

### Escalation Path
1. Collect evidence with `clickhouse-debug-bundle`
2. Check ClickHouse status page
3. Contact support with request ID

## Resources
- [ClickHouse Status Page](https://status.clickhouse.com)
- [ClickHouse Support](https://docs.clickhouse.com/support)
- [ClickHouse Error Codes](https://docs.clickhouse.com/errors)

## Next Steps
For comprehensive debugging, see `clickhouse-debug-bundle`.