---
name: flexport-common-errors
description: |
  Diagnose and fix common Flexport API errors including HTTP status codes,
  webhook failures, and data validation issues.
  Trigger: "flexport error", "fix flexport", "flexport not working", "debug flexport API".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Common Errors

## Overview

Quick reference for the most common Flexport API v2 errors. The API returns standard HTTP codes with JSON error bodies containing `code`, `message`, and sometimes `details` fields.

## Error Reference

### 401 Unauthorized — Invalid or Missing API Key

```json
{ "error": { "code": "UNAUTHORIZED", "message": "Invalid API key" } }
```

**Causes:** Missing `Authorization` header, expired JWT token, revoked API key.

**Fix:**
```bash
# Verify key is set
echo $FLEXPORT_API_KEY | head -c 10
# Test with cURL
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1
```

### 403 Forbidden — Insufficient Permissions

**Causes:** API key lacks required scope, IP whitelist blocking, sandbox key used on production.

**Fix:** Check key permissions in Flexport Portal > Settings > Developer. Ensure key scope includes the endpoint you are calling.

### 404 Not Found — Resource Does Not Exist

```json
{ "error": { "code": "NOT_FOUND", "message": "Shipment shp_xxx not found" } }
```

**Causes:** Wrong ID format, resource deleted, using test ID in production.

**Fix:** List resources first to get valid IDs:
```bash
curl -s -H "Authorization: Bearer $FLEXPORT_API_KEY" \
     -H "Flexport-Version: 2" \
     https://api.flexport.com/shipments?per=1 | jq '.data.records[0].id'
```

### 422 Unprocessable Entity — Validation Failed

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Invalid port code", "details": [...] } }
```

**Common validation failures:**

| Field | Issue | Fix |
|-------|-------|-----|
| `origin_port.code` | Not a valid UN/LOCODE | Use `CNSHA`, `USLAX`, `DEHAM` format |
| `hs_code` | Wrong format | Use 6-10 digit codes like `8479.89` |
| `cargo_ready_date` | In the past | Use future ISO date |
| `freight_type` | Unsupported value | Use `ocean`, `air`, or `trucking` |
| `incoterm` | Invalid | Use `FOB`, `CIF`, `EXW`, `DDP` |

### 429 Too Many Requests — Rate Limited

```json
{ "error": { "code": "RATE_LIMITED", "message": "Rate limit exceeded" } }
```

**Fix:** Check response headers and back off:
```typescript
function handleRateLimit(res: Response): number {
  const retryAfter = res.headers.get('Retry-After');
  const remaining = res.headers.get('X-RateLimit-Remaining');
  console.log(`Rate limited. Remaining: ${remaining}. Retry after: ${retryAfter}s`);
  return parseInt(retryAfter || '60') * 1000;
}
```

### 500/502/503 — Server Errors

**Causes:** Flexport internal issue, maintenance window, upstream provider failure.

**Fix:**
```bash
# Check Flexport status page
curl -s https://status.flexport.com/api/v2/status.json | jq '.status'
```

Retry with exponential backoff for transient 5xx errors. See `flexport-rate-limits`.

## Diagnostic Script

```bash
#!/bin/bash
echo "=== Flexport Diagnostics ==="
echo "API Key set: ${FLEXPORT_API_KEY:+YES}"
echo "Key prefix: ${FLEXPORT_API_KEY:0:8}..."
echo -n "API status: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1
echo ""
echo -n "Status page: "
curl -s https://status.flexport.com/api/v2/status.json | jq -r '.status.description'
```

## Escalation Path

1. Run diagnostic script above
2. Collect request ID from response headers (`X-Request-Id`)
3. Check [Flexport Status](https://status.flexport.com)
4. Contact Flexport support with request ID and error details

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [Flexport Status Page](https://status.flexport.com)
- [Developer Portal](https://developers.flexport.com/)

## Next Steps

For comprehensive debugging, see `flexport-debug-bundle`.
