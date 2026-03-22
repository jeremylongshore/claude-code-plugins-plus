---
name: customerio-common-errors
description: |
  Diagnose and fix Customer.io common errors.
  Use when troubleshooting API errors, delivery failures,
  campaign issues, or SDK exceptions.
  Trigger: "customer.io error", "customer.io not working",
  "debug customer.io", "customer.io 401", "customer.io 429".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, debugging, errors]

---
# Customer.io Common Errors

## Overview

Diagnose and fix the most frequent Customer.io integration errors: API status codes, SDK exceptions, delivery failures, campaign trigger issues, and transactional message problems.

## Prerequisites

- Access to Customer.io dashboard
- API credentials configured
- Access to application logs

## HTTP Status Code Reference

| Code | Meaning | Retryable | Action |
|------|---------|-----------|--------|
| `200` | Success | N/A | No action needed |
| `400` | Bad Request | No | Fix request payload — see details below |
| `401` | Unauthorized | No | Check API credentials |
| `403` | Forbidden | No | API key lacks permission for this endpoint |
| `404` | Not Found | No | Check endpoint URL or resource ID |
| `408` | Request Timeout | Yes | Retry with backoff |
| `422` | Unprocessable Entity | No | Validation error — check required fields |
| `429` | Rate Limited | Yes | Back off, respect `Retry-After` header |
| `500` | Internal Server Error | Yes | Retry with exponential backoff |
| `503` | Service Unavailable | Yes | Check status.customer.io, retry later |

## Instructions

### Error 1: Authentication Failures (401/403)

```typescript
// WRONG — mixing up API key types
import { TrackClient, APIClient, RegionUS } from "customerio-node";

// Track API uses Site ID + Track API Key (Basic Auth)
const cio = new TrackClient(siteId, trackApiKey, { region: RegionUS });

// App API uses App API Key (Bearer Auth) — DIFFERENT key
const api = new APIClient(appApiKey, { region: RegionUS });

// Common mistake: using Track API key for App API client
// const api = new APIClient(trackApiKey); // WRONG — will get 401
```

**Fix:** Verify you're using the right key type. Track API credentials are under "Tracking API Key" in Settings. App API key is under "App API Key" — it's a separate bearer token.

### Error 2: Timestamp Format (400)

```typescript
// WRONG — Customer.io expects Unix seconds, not milliseconds
await cio.identify("user-1", {
  created_at: Date.now(),              // 1704067200000 — TOO LARGE
});

// CORRECT — divide by 1000
await cio.identify("user-1", {
  created_at: Math.floor(Date.now() / 1000),  // 1704067200
});
```

Customer.io silently accepts millisecond timestamps but interprets them as dates thousands of years in the future, breaking segment conditions and campaign triggers.

### Error 3: Events Not Triggering Campaigns

```typescript
// WRONG — event name doesn't match dashboard
await cio.track("user-1", { name: "SignedUp", data: {} });
// Dashboard expects: "signed_up" (case-sensitive)

// CORRECT — exact match, snake_case
await cio.track("user-1", { name: "signed_up", data: {} });
```

**Checklist:**
1. Event name is case-sensitive — must match dashboard trigger exactly
2. User must be identified before tracking (call `identify()` first)
3. Campaign must be **Active** (not Draft or Paused)
4. User must match campaign's audience filter/segment
5. User must not be suppressed

### Error 4: Transactional Message Failures (422)

```typescript
import { APIClient, SendEmailRequest, RegionUS } from "customerio-node";

const api = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS,
});

// Common 422 errors:
// 1. Wrong transactional_message_id
const request = new SendEmailRequest({
  to: "user@example.com",
  transactional_message_id: "999",     // Must exist in dashboard
  message_data: { name: "Jane" },
  identifiers: { id: "user-123" },
});

// 2. Missing required message_data fields
// If template uses {{ data.reset_url }}, message_data must include reset_url

// 3. Invalid email address
// "to" must be a valid email format
```

### Error 5: Rate Limiting (429)

```typescript
// Implement backoff when you hit 429
async function withBackoff<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.statusCode === 429 && i < maxRetries) {
        // Respect Retry-After header if present, otherwise exponential backoff
        const retryAfter = err.headers?.["retry-after"];
        const delay = retryAfter
          ? parseInt(retryAfter) * 1000
          : Math.pow(2, i) * 1000 + Math.random() * 500;
        console.warn(`Rate limited. Retrying in ${delay}ms...`);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Max retries exceeded");
}

// Usage
await withBackoff(() => cio.identify("user-1", { email: "user@example.com" }));
```

### Error 6: EU Region Mismatch

```typescript
// WRONG — EU account hitting US endpoint
const cio = new TrackClient(siteId, apiKey, { region: RegionUS });
// Returns 401 because credentials are for EU workspace

// CORRECT
import { RegionEU } from "customerio-node";
const cio = new TrackClient(siteId, apiKey, { region: RegionEU });
```

### Error 7: User Not Receiving Email

**Diagnostic checklist:**
1. Does the user have an `email` attribute? (Check People > user profile)
2. Is the user suppressed? (Check suppression list)
3. Has the email bounced before? (Check user Activity tab)
4. Is the campaign Active? (Check Campaigns list)
5. Does the user match the segment? (Check segment membership)
6. Is the sending domain verified? (Settings > Sending Domains)

## Diagnostic Commands

```bash
# Test Track API authentication
curl -s -w "\nHTTP %{http_code}\n" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_TRACK_API_KEY" \
  -X PUT "https://track.customer.io/api/v1/customers/test-diag" \
  -H "Content-Type: application/json" \
  -d '{"email":"diag@example.com"}'

# Test App API authentication
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Bearer $CUSTOMERIO_APP_API_KEY" \
  "https://api.customer.io/v1/campaigns"

# Check Customer.io status
curl -s "https://status.customer.io/api/v2/status.json" | python3 -m json.tool
```

## Error Handling Pattern

```typescript
// Centralized error handler for Customer.io operations
async function safeCioCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T | null> {
  try {
    return await fn();
  } catch (err: any) {
    const code = err.statusCode ?? err.status ?? "unknown";
    console.error(`CIO ${operation} failed [${code}]:`, err.message);

    // Alert on auth errors — likely misconfiguration
    if (code === 401 || code === 403) {
      console.error("AUTH ERROR: Check API credentials immediately");
    }

    // Don't crash the app for tracking failures
    return null;
  }
}

// Usage — never crashes your app
await safeCioCall("identify", () =>
  cio.identify("user-1", { email: "user@example.com" })
);
```

## Resources

- [Track API Error Reference](https://docs.customer.io/integrations/api/track/)
- [Common Transactional API Errors](https://docs.customer.io/journeys/transactional-api-common-api-errors/)
- [Common Broadcast Errors](https://docs.customer.io/journeys/api-triggered-errors/)
- [Customer.io Status Page](https://status.customer.io/)

## Next Steps

After resolving errors, proceed to `customerio-debug-bundle` for comprehensive debug reports.
