---
name: bamboohr-common-errors
description: |
  Diagnose and fix BambooHR API errors and exceptions.
  Use when encountering BambooHR errors, debugging failed requests,
  or troubleshooting HTTP 400/401/403/404/429/500/503 responses.
  Trigger with phrases like "bamboohr error", "fix bamboohr",
  "bamboohr not working", "debug bamboohr", "bamboohr 401", "bamboohr 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, debugging]
compatible-with: claude-code
---

# BambooHR Common Errors

## Overview

Diagnostic reference for BambooHR REST API errors. BambooHR returns error details in the `X-BambooHR-Error-Message` response header for most 400-level and some 500-level errors.

## Prerequisites

- BambooHR API access configured
- Access to application logs or HTTP response headers

## Instructions

### Step 1: Read the Error Header

Always check `X-BambooHR-Error-Message` first — it contains BambooHR's specific error detail, which is more useful than generic HTTP status text.

```typescript
const res = await fetch(`${BASE}/employees/999/`, {
  headers: { Authorization: AUTH, Accept: 'application/json' },
});

if (!res.ok) {
  const errorDetail = res.headers.get('X-BambooHR-Error-Message');
  console.error(`HTTP ${res.status}: ${errorDetail || res.statusText}`);
}
```

### Step 2: Match Error to Solution

---

#### 401 Unauthorized — Invalid API Key

```
X-BambooHR-Error-Message: Invalid API key
```

**Cause:** API key is missing, expired, revoked, or malformed in the Basic Auth header.

**Solution:**

```bash
# Verify key is set
echo "Key length: ${#BAMBOOHR_API_KEY}"

# Test auth directly
curl -s -o /dev/null -w "%{http_code}" \
  -u "${BAMBOOHR_API_KEY}:x" \
  "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory"
```

**Common mistakes:**
- Using Bearer token instead of Basic Auth
- Putting the API key as the password instead of the username
- Missing the `:x` password part in Basic Auth encoding

---

#### 403 Forbidden — Insufficient Permissions

```
X-BambooHR-Error-Message: You do not have access to this resource
```

**Cause:** The API key's user account lacks permissions for the requested endpoint or employee.

**Solution:**
- Verify the user's access level in BambooHR (Account > Access Levels)
- Time-off management endpoints require manager or admin permissions
- Compensation table access requires admin permissions
- Some fields are restricted to specific access levels

---

#### 400 Bad Request — Invalid Fields or Payload

```
X-BambooHR-Error-Message: Invalid field: "jobTitl"
```

**Cause:** Misspelled field name, invalid date format, or malformed JSON body.

**Solution:**

```bash
# Verify field names against BambooHR's field list
curl -s -u "${BAMBOOHR_API_KEY}:x" \
  "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/0/?fields=firstName,lastName" \
  -H "Accept: application/json"
```

**Common field name mistakes:**
- `title` (wrong) vs `jobTitle` (correct)
- `email` (wrong) vs `workEmail` (correct)
- `name` (wrong) vs `firstName` + `lastName` (correct)
- Date format must be `YYYY-MM-DD`, not `MM/DD/YYYY`

---

#### 404 Not Found — Wrong Endpoint or ID

```
X-BambooHR-Error-Message: Employee not found
```

**Cause:** Employee ID does not exist, wrong company domain, or malformed URL path.

**Solution:**

```bash
# Verify company domain
echo "Domain: $BAMBOOHR_COMPANY_DOMAIN"

# Verify the base URL structure
# Correct:  /api/gateway.php/{domain}/v1/employees/{id}/
# Wrong:    /api/v1/employees/{id}/
# Wrong:    /api/gateway.php/{domain}/employees/{id}/  (missing /v1/)
```

---

#### 429 / 503 — Rate Limited

```
HTTP 503 with Retry-After: 30
```

**Cause:** Too many requests in a short period. BambooHR does not publish exact rate limits but returns 503 with a `Retry-After` header.

**Solution:**

```typescript
async function handleRateLimit(res: Response): Promise<void> {
  if (res.status === 503 || res.status === 429) {
    const retryAfter = parseInt(res.headers.get('Retry-After') || '30', 10);
    console.warn(`Rate limited. Waiting ${retryAfter}s...`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
  }
}
```

**Prevention:**
- Batch reads using custom reports instead of individual employee GETs
- Cache directory results (they change infrequently)
- Use `/employees/changed/?since=...` for incremental sync instead of full pulls

---

#### 500 / 502 — Server Errors

**Cause:** BambooHR internal error. Usually transient.

**Solution:**
1. Check [BambooHR Status Page](https://status.bamboohr.com) for outages
2. Retry with exponential backoff (see `bamboohr-rate-limits`)
3. If persistent, collect request details for BambooHR support

---

#### Content-Type Mismatch

**Cause:** Missing `Accept: application/json` header — BambooHR defaults to XML.

```bash
# Wrong — returns XML
curl -u "${BAMBOOHR_API_KEY}:x" \
  "${BASE}/employees/directory"

# Correct — returns JSON
curl -u "${BAMBOOHR_API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/employees/directory"
```

### Step 3: Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== BambooHR Diagnostic ==="
echo "Company: ${BAMBOOHR_COMPANY_DOMAIN}"
echo "Key set: ${BAMBOOHR_API_KEY:+YES}"
echo "Key length: ${#BAMBOOHR_API_KEY}"

BASE="https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1"

echo -n "Auth test: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "${BAMBOOHR_API_KEY}:x" \
  -H "Accept: application/json" "${BASE}/employees/directory")
echo "$STATUS"

echo -n "Status page: "
curl -s https://status.bamboohr.com | head -c 100
echo ""

if [ "$STATUS" -eq 200 ]; then
  echo "Connection OK"
elif [ "$STATUS" -eq 401 ]; then
  echo "FIX: Regenerate API key in BambooHR dashboard"
elif [ "$STATUS" -eq 403 ]; then
  echo "FIX: Upgrade API key user's access level"
elif [ "$STATUS" -eq 404 ]; then
  echo "FIX: Check BAMBOOHR_COMPANY_DOMAIN value"
else
  echo "FIX: Check status page and retry"
fi
```

## Output

- Identified error from HTTP status + `X-BambooHR-Error-Message` header
- Applied fix based on error category
- Verified resolution with diagnostic script

## Error Summary Table

| Status | Header | Root Cause | Fix |
|--------|--------|-----------|-----|
| 400 | Invalid field | Typo in field name | Check field list docs |
| 401 | Invalid API key | Bad credentials | Regenerate API key |
| 403 | No access | Insufficient permissions | Upgrade user access level |
| 404 | Not found | Wrong ID or domain | Verify URL components |
| 429/503 | `Retry-After` | Rate limited | Backoff and retry |
| 500/502 | — | Server error | Retry; check status page |

## Resources

- [BambooHR API Details](https://documentation.bamboohr.com/docs/api-details)
- [BambooHR Status Page](https://status.bamboohr.com)
- [BambooHR Field Names](https://documentation.bamboohr.com/docs/list-of-field-names)

## Next Steps

For comprehensive debugging, see `bamboohr-debug-bundle`.
