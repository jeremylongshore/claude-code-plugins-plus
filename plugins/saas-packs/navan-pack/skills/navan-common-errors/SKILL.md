---
name: navan-common-errors
description: 'Diagnose and fix common Navan API errors with targeted fix procedures.

  Use when an API call returns an unexpected HTTP error or when debugging production
  failures.

  Trigger with "navan error", "fix navan", "debug navan", "navan 401", "navan 403",
  "navan 429".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Common Errors

## Overview

Diagnose and resolve Navan API errors using targeted fix procedures. All errors surface as raw HTTP status codes since Navan has **no public SDK** — this guide covers 401, 403, 404, 429, 500, and 503 with curl-based diagnostics.

**Purpose:** Identify the root cause of a Navan API error and apply the correct fix.

## Prerequisites

- Navan API credentials configured (see `navan-install-auth`)
- `curl` and `jq` available in your terminal
- Environment variables set: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`

## Instructions

### Error 401 — Unauthorized (Invalid or Expired OAuth Token)

**Root causes:**
1. OAuth token has expired (tokens have a limited `expires_in` window)
2. `client_secret` was rotated in the Navan dashboard but not updated in `.env`
3. Malformed `Authorization` header (missing `Bearer` prefix)
4. Token from a different Navan organization

**Diagnostic steps:**

```bash
# 1. Verify credentials can still obtain a token
curl -s -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('TOKEN OK' if 'access_token' in d else f'FAIL: {d}')"

# 2. Check if existing token is expired
echo "Token var length: ${#NAVAN_TOKEN}"
```

**Fix:** Re-run the token exchange. If that also returns 401, regenerate credentials at **Admin > Travel admin > Settings > Integrations > Navan API Credentials**.

### Error 403 — Forbidden (Insufficient Permissions)

**Root causes:**
1. API credentials lack required scopes for the endpoint
2. Account is on Business tier but endpoint requires Enterprise
3. Expense Transaction API not enabled (requires separate Navan support request)
4. User role lacks admin permissions for admin-only endpoints

**Diagnostic steps:**

```bash
# Test the bookings endpoint
TOKEN=$(curl -s -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Bookings:" && curl -s -o /dev/null -w "%{http_code}" \
  "https://api.navan.com/v1/bookings?page=0&size=1" -H "Authorization: Bearer $TOKEN"
```

**Fix:** If the bookings endpoint returns 403, your credentials lack the required scope. Contact Navan support. If the Expense API returns 403, it requires separate enablement — request it through your Navan account manager.

### Error 404 — Not Found (Invalid Endpoint)

**Root causes:**
1. Typo in endpoint path
2. Using a legacy or reverse-engineered endpoint that no longer exists
3. Referencing an endpoint not available on your Navan tier

**Known valid endpoints (from Airbyte connector source):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ta-auth/oauth/token` | POST | OAuth token exchange (client_credentials) |
| `/v1/bookings` | GET | Booking records (paginated with `page` + `size`) |

> **Note:** Older references to endpoints like `/get_user_trips`, `/get_admin_trips`, `/get_users` originate from Supergood's reverse-engineered browser automation and are not part of the official Navan REST API. Use `/v1/bookings` for booking data.

**Fix:** Verify the endpoint path against the table above. The Navan API uses `/v1/` prefixed paths at `https://api.navan.com`.

### Error 429 — Rate Limited

**Root causes:**
1. Exceeding the per-minute request limit
2. Automated scripts making rapid sequential calls without throttling
3. Multiple services sharing the same credentials

**Diagnostic steps:**

```bash
# Check rate limit headers in response
curl -s -D - "https://api.navan.com/v1/bookings?page=0&size=1" \
  -H "Authorization: Bearer $TOKEN" \
  -o /dev/null 2>&1 | grep -i "rate\|retry\|limit"
```

**Fix:** Implement exponential backoff. Start with a 2-second delay, doubling on each retry up to 3 attempts. Cache tokens to avoid redundant auth requests. If using multiple services, consider separate credentials per service.

```typescript
async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try { return await fn(); }
    catch (err: any) {
      if (err.status !== 429 || i === maxRetries - 1) throw err;
      await new Promise(r => setTimeout(r, Math.pow(2, i + 1) * 1000));
    }
  }
  throw new Error('Max retries exceeded');
}
```

### Error 500 — Internal Server Error

**Root causes:**
1. Navan backend service failure
2. Malformed request body causing server-side exception
3. Data inconsistency in your organization's records

**Diagnostic steps:**

```bash
# Test with minimal request to isolate
curl -s -w "\nHTTP %{http_code}" "https://api.navan.com/v1/bookings?page=0&size=1" \
  -H "Authorization: Bearer $TOKEN"
```

**Fix:** Retry after 30 seconds. If the error persists across multiple endpoints, it is likely a Navan-side outage. If only one endpoint fails, check your request body for malformed JSON. For persistent 500 errors, contact Navan support with the endpoint, timestamp, and request ID from the response headers.

### Error 503 — Service Unavailable (Maintenance)

**Root causes:**
1. Scheduled Navan maintenance window
2. Navan infrastructure scaling event
3. Regional AWS outage (Navan is AWS-hosted)

**Fix:** Wait and retry with exponential backoff. Check the Navan Help Center for maintenance announcements. 503 errors are typically transient and resolve within minutes. Implement circuit-breaker patterns for production systems to avoid cascading failures during extended outages.

## Output

This error reference delivers:
- Six HTTP error codes with Navan-specific root causes
- Copy-paste diagnostic curl commands for each error type
- Fix procedures ranked by likelihood
- A backoff implementation for automated retry handling

## Error Handling

| Error | Code | Most Likely Cause | First Action |
|-------|------|-------------------|--------------|
| Unauthorized | 401 | Expired OAuth token | Re-run token exchange |
| Forbidden | 403 | Tier or scope limitation | Check plan tier; contact Navan support |
| Not found | 404 | Wrong endpoint path | Verify against known endpoints table |
| Rate limited | 429 | No throttling in client code | Add exponential backoff |
| Server error | 500 | Navan backend issue | Retry after 30s; check request body |
| Maintenance | 503 | Navan downtime | Wait and retry; check help center |

## Examples

**Full diagnostic script:**

```bash
#!/bin/bash
echo "=== Navan API Diagnostic ==="
echo "1. Testing authentication..."
AUTH_RESULT=$(curl -s -w "\n%{http_code}" -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET")
AUTH_CODE=$(echo "$AUTH_RESULT" | tail -1)
echo "   Auth: HTTP $AUTH_CODE"

if [ "$AUTH_CODE" = "200" ]; then
  TOKEN=$(echo "$AUTH_RESULT" | head -1 | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  echo "2. Testing bookings (page 0)..."
  curl -s -o /dev/null -w "   Bookings: HTTP %{http_code}\n" \
    "https://api.navan.com/v1/bookings?page=0&size=1" -H "Authorization: Bearer $TOKEN"
else
  echo "   Auth failed — check NAVAN_CLIENT_ID and NAVAN_CLIENT_SECRET"
fi
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — announcements and maintenance notices
- [Navan TMC API Docs](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/navan-tmc-api-integration-documentation) — API reference
- [Navan Security & Compliance](https://navan.com/security) — SOC 2 Type II, ISO 27001, PCI DSS Level 1
- [Navan Integrations](https://navan.com/integrations) — partner ecosystem and integration options

## Next Steps

After resolving your error, see `navan-sdk-patterns` for production-grade error handling with automatic retries, or `navan-local-dev-loop` for request logging that captures errors for post-mortem analysis.
