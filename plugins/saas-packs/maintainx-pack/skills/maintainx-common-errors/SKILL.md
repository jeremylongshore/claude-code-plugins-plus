---
name: maintainx-common-errors
description: |
  Debug and resolve common MaintainX API errors.
  Use when encountering API errors, authentication issues,
  or unexpected responses from the MaintainX API.
  Trigger with phrases like "maintainx error", "maintainx 401",
  "maintainx api problem", "maintainx not working", "debug maintainx".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Common Errors

## Overview
Quick reference for diagnosing and resolving common MaintainX API errors with concrete solutions and diagnostic commands.

## Prerequisites
- `MAINTAINX_API_KEY` environment variable configured
- `curl` and `jq` available
- Access to application logs

## Instructions

### Step 1: Diagnostic Quick Check

Run this first to validate connectivity and auth:

```bash
# Test 1: Verify API key is valid
curl -s -o /dev/null -w "%{http_code}" \
  https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY"
# Expected: 200

# Test 2: Check API key is set
echo "Key length: ${#MAINTAINX_API_KEY}"
# Should be > 0

# Test 3: Verify DNS resolution
nslookup api.getmaintainx.com
# Should resolve to an IP
```

### Step 2: Identify the Error

## Error Handling

### 400 Bad Request

**Cause**: Invalid request body, missing required fields, or malformed JSON.

```bash
# Diagnose: Send a minimal valid request
curl -X POST https://api.getmaintainx.com/v1/workorders \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Diagnostic test order"}' -v 2>&1 | tail -5
```

**Common fixes**:
- Work orders require at minimum a `title` field
- Priority must be one of: `NONE`, `LOW`, `MEDIUM`, `HIGH`
- Status must be one of: `OPEN`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, `CLOSED`
- Dates must be ISO 8601 format: `2026-03-19T12:00:00Z`

### 401 Unauthorized

**Cause**: Missing, invalid, or expired API key.

```typescript
// Diagnostic wrapper
async function diagAuth() {
  try {
    const res = await fetch('https://api.getmaintainx.com/v1/users?limit=1', {
      headers: { Authorization: `Bearer ${process.env.MAINTAINX_API_KEY}` },
    });
    if (res.status === 401) {
      console.error('API key is invalid or expired.');
      console.error('Generate a new key: MaintainX > Settings > Integrations > New Key');
    } else {
      console.log('Auth OK - status:', res.status);
    }
  } catch (e) {
    console.error('Network error:', e);
  }
}
```

**Fixes**:
- Regenerate key in MaintainX: Settings > Integrations > Generate Key
- Check for whitespace: `echo "'$MAINTAINX_API_KEY'" | cat -A`
- Ensure `Bearer` prefix (not `Basic` or `Token`)

### 403 Forbidden

**Cause**: Valid key but insufficient permissions or wrong plan tier.

**Fixes**:
- Verify your plan supports API access (Professional or Enterprise)
- Check user role has permission for the requested operation
- For org-specific endpoints, include `X-Organization-Id` header

### 404 Not Found

**Cause**: Resource ID does not exist or wrong endpoint path.

```bash
# Verify a resource exists before referencing it
curl -s "https://api.getmaintainx.com/v1/workorders/99999" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.message // .title'
```

**Fixes**:
- Confirm the ID exists (GET the resource first)
- Use `api.getmaintainx.com/v1` (not `/v2` or missing version)
- Check for typos in endpoint path (`/workorders` not `/work-orders`)

### 422 Unprocessable Entity

**Cause**: Request is syntactically valid but semantically incorrect.

**Common triggers**:
- Invalid status transition (e.g., `CLOSED` to `IN_PROGRESS`)
- Referencing a non-existent `assetId` or `locationId`
- Invalid enum values for priority or category fields

### 429 Too Many Requests

**Cause**: Rate limit exceeded.

```typescript
// Auto-retry on 429
async function safeRequest(fn: () => Promise<any>, retries = 3) {
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err?.response?.status === 429 && i < retries) {
        const wait = parseInt(err.response.headers['retry-after'] || '5') * 1000;
        console.warn(`Rate limited. Waiting ${wait}ms...`);
        await new Promise(r => setTimeout(r, wait));
      } else {
        throw err;
      }
    }
  }
}
```

**Fixes**:
- Honor the `Retry-After` response header
- Implement exponential backoff (see `maintainx-rate-limits`)
- Reduce polling frequency; use webhooks instead

### 500 Internal Server Error

**Cause**: MaintainX server-side issue.

**Fixes**:
- Check [MaintainX Status Page](https://status.getmaintainx.com)
- Retry with exponential backoff (transient errors resolve themselves)
- If persistent, contact MaintainX support with request details

## Output
- Identified error root cause from HTTP status code and response body
- Applied the appropriate fix from the reference above
- Verified resolution with the diagnostic quick check commands

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Status Page](https://status.getmaintainx.com)
- [MaintainX Help Center](https://help.getmaintainx.com)

## Next Steps
For comprehensive debugging, see `maintainx-debug-bundle`.

## Examples

**Full diagnostic script**:

```bash
#!/bin/bash
echo "=== MaintainX API Diagnostics ==="
echo "Key set: $([ -n "$MAINTAINX_API_KEY" ] && echo 'YES' || echo 'NO')"
echo "Key length: ${#MAINTAINX_API_KEY}"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY")
echo "Auth status: $STATUS"

if [ "$STATUS" = "200" ]; then
  WO_COUNT=$(curl -s "https://api.getmaintainx.com/v1/workorders?limit=1" \
    -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.workOrders | length')
  echo "Work orders accessible: $WO_COUNT"
fi
```
