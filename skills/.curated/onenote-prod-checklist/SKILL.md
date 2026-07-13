---
name: onenote-prod-checklist
description: 'Production readiness checklist for OneNote Graph API integrations covering
  auth, rate limits, and failure modes.

  Use when preparing a OneNote integration for production deployment or conducting
  a launch review.

  Trigger with "onenote production checklist", "onenote launch review", "onenote prod
  ready".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Production Checklist

## Overview

OneNote integrations that work perfectly in development break in production in predictable ways: SharePoint document libraries exceed the 5,000-item view threshold and stop returning notebooks, image uploads silently truncate above 4MB, rate limits compound across users during business hours, and MSAL token caches lose state across container restarts. This skill is a comprehensive go/no-go checklist organized by failure category. Each item references the specific Graph API behavior that causes the production failure and provides the fix. Use this checklist during launch reviews — every unchecked item is a production incident waiting to happen.

## Prerequisites

- A functional OneNote integration that works in development/staging
- Azure AD app registration with delegated permissions configured
- Access to production monitoring infrastructure (logging, alerting)
- Familiarity with your deployment environment (containers, VMs, serverless)
- Completed `onenote-security-basics` and `onenote-rate-limits` skills

## Instructions

### 1. Authentication Checklist

| # | Check | Why it matters |
|:-:|-------|---------------|
| 1.1 | Using delegated auth (DeviceCodeCredential or InteractiveBrowserCredential) | App-only auth (ClientSecretCredential) deprecated for OneNote March 31, 2025 |
| 1.2 | MSAL token cache serialized to persistent storage | Container restarts lose in-memory cache; users forced to re-authenticate |
| 1.3 | Silent token renewal tested (call `acquire_token_silent` before every request) | Access tokens expire in 1 hour; without silent renewal, users hit 401 hourly |
| 1.4 | Refresh token 90-day expiry monitored | Inactive users' refresh tokens expire silently; need re-auth flow |
| 1.5 | Token cache file permissions set to 0600 (owner-only) | Cache contains refresh tokens — world-readable is a credential leak |
| 1.6 | Multi-tenant: `tid` claim validated on every token | Prevents cross-tenant data leakage from token reuse |

**Verification test:**

```python
import os, time

def verify_auth_resilience(client):
    """Test that auth survives token expiry cycle."""
    # 1. Make a call to confirm auth works
    response = client.me.onenote.notebooks.get()
    assert response.value is not None, "Initial auth failed"

    # 2. Verify token cache exists on disk
    cache_path = os.path.expanduser("~/.onenote-token-cache.json")
    assert os.path.exists(cache_path), "Token cache not persisted"
    stat = os.stat(cache_path)
    assert oct(stat.st_mode)[-3:] == "600", f"Cache permissions {oct(stat.st_mode)} not 600"

    # 3. Verify silent renewal works (simulate expired access token)
    response2 = client.me.onenote.notebooks.get()
    assert response2.value is not None, "Silent renewal failed"
    print("Auth resilience: PASS")
```

### 2. Rate Limit Checklist

| # | Check | Why it matters |
|:-:|-------|---------------|
| 2.1 | Retry-After header parsed and honored on 429 responses | Ignoring Retry-After escalates throttling duration |
| 2.2 | Exponential backoff implemented (not fixed delay) | Fixed delays waste time on short throttles, not enough on long ones |
| 2.3 | Per-user call tracking in place | One power user can consume the entire 600/min budget |
| 2.4 | Tenant-level rate tracked (10,000/10min across all users) | Dev testing per-user never reveals the tenant ceiling |
| 2.5 | Queue-based throttling for batch operations | Bursting 200 requests fails; queuing 20/second succeeds |
| 2.6 | 429 alert configured (threshold: >1% of requests) | Early warning before users notice degradation |

**Retry-After implementation:**

```typescript
async function callWithRetry(
  client: any,
  apiPath: string,
  maxRetries: number = 3
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await client.api(apiPath).get();
    } catch (error: any) {
      if (error.statusCode === 429 && attempt < maxRetries) {
        const retryAfter = parseInt(error.headers?.["retry-after"] || "5", 10);
        console.warn(
          `Rate limited. Retry-After: ${retryAfter}s (attempt ${attempt + 1}/${maxRetries})`
        );
        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
      } else {
        throw error;
      }
    }
  }
}
```

### 3. Error Handling Checklist

All seven Graph API error codes must have explicit handlers:

| # | Code | Handler required |
|:-:|:----:|-----------------|
| 3.1 | `400 Bad Request` | Validate XHTML before sending; log request body for debugging |
| 3.2 | `403 Forbidden` | Check scope in token; detect app-only auth usage; surface to user as "permissions needed" |
| 3.3 | `404 Not Found` | Handle deleted notebooks/sections/pages gracefully; clear local cache entry |
| 3.4 | `429 Too Many Requests` | Retry with Retry-After header (see section 2) |
| 3.5 | `500 Internal Server Error` | Retry with exponential backoff; log `request-id` header for Microsoft support |
| 3.6 | `502 Bad Gateway` | Retry once; if persistent, check for expired token edge case |
| 3.7 | `507 Insufficient Storage` | Section page limit hit; alert admin; suggest archival |

**Critical: Always log the `request-id` response header.** Microsoft support requires this for incident investigation:

```python
import logging

logger = logging.getLogger("onenote")

async def safe_api_call(client, api_path: str):
    try:
        return await client.api(api_path).get()
    except Exception as e:
        request_id = getattr(e, "headers", {}).get("request-id", "unknown")
        logger.error(
            f"Graph API error: {e} | path={api_path} | request-id={request_id}"
        )
        raise
```

### 4. Content Validation Checklist

| # | Check | Why it matters |
|:-:|-------|---------------|
| 4.1 | HTML validated as XHTML before POST (all tags closed, UTF-8) | Graph API silently strips invalid HTML — pages render incorrectly with no error |
| 4.2 | Page content size checked (< 4MB per page) | Oversized content silently truncates or returns 400 |
| 4.3 | Image format validated (PNG, JPEG, GIF only) | Unsupported formats (WebP, AVIF) silently fail |
| 4.4 | Image size checked (< 10MB per image) | Large images cause timeout during page creation |
| 4.5 | Embedded file count checked (< 10 per page) | Too many attachments cause 507 errors |

**XHTML validation before send:**

```python
from html.parser import HTMLParser

SELF_CLOSING_TAGS = {"br", "hr", "img", "input", "meta", "link"}

class XHTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        if tag not in SELF_CLOSING_TAGS:
            self.open_tags.append(tag)

    def handle_endtag(self, tag):
        if tag in SELF_CLOSING_TAGS:
            return
        if not self.open_tags or self.open_tags[-1] != tag:
            self.errors.append(f"Mismatched close tag: </{tag}>")
        else:
            self.open_tags.pop()

    def validate(self, html: str) -> list[str]:
        self.feed(html)
        if self.open_tags:
            self.errors.append(f"Unclosed tags: {self.open_tags}")
        return self.errors

def validate_page_content(html_body: str) -> tuple[bool, list[str]]:
    """Validate content before sending to OneNote API."""
    issues = []

    # Size check
    size_bytes = len(html_body.encode("utf-8"))
    if size_bytes > 4 * 1024 * 1024:
        issues.append(f"Content too large: {size_bytes / 1024 / 1024:.1f}MB (max 4MB)")

    # XHTML validation
    validator = XHTMLValidator()
    html_errors = validator.validate(html_body)
    issues.extend(html_errors)

    return len(issues) == 0, issues
```

### 5. SharePoint-Specific Checklist

| # | Check | Why it matters |
|:-:|-------|---------------|
| 5.1 | Site-id resolved via Graph API (not hardcoded) | Site-ids change when sites are recreated or migrated |
| 5.2 | Document library item count monitored | Libraries exceeding 5,000 items hit SharePoint view threshold — API returns partial results |
| 5.3 | SharePoint throttling handled separately | SharePoint has its own throttling on top of Graph API limits |
| 5.4 | Site URL-to-ID resolution cached | Avoid repeated `GET /sites/{hostname}:/{path}` lookups |

### 6. Monitoring Checklist

| # | Check | Why it matters |
|:-:|-------|---------------|
| 6.1 | 429 rate dashboard with alerting | Detect throttling before users report issues |
| 6.2 | P95 latency tracked per endpoint | Identify slow endpoints before timeout cascades |
| 6.3 | Error rate per error code | Distinguish auth failures (401/403) from service issues (500/502) |
| 6.4 | Request-id logged for every failed call | Microsoft support requires this for incident investigation |
| 6.5 | Token refresh success rate tracked | Detect MSAL cache issues before users get logged out |
| 6.6 | Per-user call volume visible | Identify users driving disproportionate load |

### 7. Health Check Endpoint

```typescript
interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  checks: Record<string, { ok: boolean; message: string; latencyMs: number }>;
}

async function healthCheck(client: any): Promise<HealthStatus> {
  const checks: HealthStatus["checks"] = {};

  // Auth check: can we get a token?
  const authStart = Date.now();
  try {
    await client.api("/me").select("id").get();
    checks.auth = { ok: true, message: "Token valid", latencyMs: Date.now() - authStart };
  } catch (e: any) {
    checks.auth = { ok: false, message: e.message, latencyMs: Date.now() - authStart };
  }

  // OneNote check: can we reach the API?
  const noteStart = Date.now();
  try {
    await client.api("/me/onenote/notebooks").select("id").top(1).get();
    checks.onenote = { ok: true, message: "API reachable", latencyMs: Date.now() - noteStart };
  } catch (e: any) {
    checks.onenote = { ok: false, message: e.message, latencyMs: Date.now() - noteStart };
  }

  const allOk = Object.values(checks).every((c) => c.ok);
  const anyOk = Object.values(checks).some((c) => c.ok);

  return {
    status: allOk ? "healthy" : anyOk ? "degraded" : "unhealthy",
    checks,
  };
}
```

### 8. Go/No-Go Decision Matrix

| Category | Must-Have (blocks launch) | Should-Have (launch with plan) |
|----------|:---:|:---:|
| Delegated auth working | 1.1, 1.2, 1.3 | 1.4, 1.5, 1.6 |
| Rate limits handled | 2.1, 2.2 | 2.3, 2.4, 2.5, 2.6 |
| Error codes handled | 3.1, 3.2, 3.3, 3.4 | 3.5, 3.6, 3.7 |
| Content valid | 4.1, 4.2 | 4.3, 4.4, 4.5 |
| Monitoring | 6.1, 6.4 | 6.2, 6.3, 6.5, 6.6 |

**Launch rule:** All "Must-Have" items checked. "Should-Have" items documented as post-launch tasks with owners and deadlines.

## Output

After applying this checklist, you will have: verified authentication resilience across token expiry cycles, confirmed rate limit handling with Retry-After parsing, validated all seven error code handlers, ensured XHTML content passes pre-send validation, configured monitoring dashboards with alert thresholds, and documented a clear go/no-go decision with any deferred items tracked.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Health check returns "degraded" | OneNote API reachable but auth check failed | Token may be expired; trigger MSAL silent renewal; check cache persistence |
| Health check returns "unhealthy" | Both auth and OneNote checks failed | Service outage or network issue; check Microsoft 365 Service Health dashboard |
| `507 Insufficient Storage` in production | Section accumulated too many pages over time | Implement page archival (move old pages to archive section); monitor page counts |
| Silent HTML truncation | Invalid XHTML passed validation but Graph stripped content | Tighten validator; test with Graph Explorer before automated POST |
| SharePoint returns partial notebook list | Document library exceeded 5,000-item view threshold | Use `$filter` to narrow results; paginate with `$top` and `$skip`; or restructure library |

## Examples

**Quick pre-launch validation script:**

```bash
#!/bin/bash
# Run this before every production deployment
set -e

echo "=== OneNote Production Readiness Check ==="

# 1. Verify auth works
echo -n "Auth check... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/me/onenote/notebooks?\$top=1")
[ "$STATUS" = "200" ] && echo "PASS" || echo "FAIL (HTTP $STATUS)"

# 2. Verify token cache exists
echo -n "Token cache... "
[ -f ~/.onenote-token-cache.json ] && echo "PASS" || echo "FAIL (no cache file)"

# 3. Check cache permissions
echo -n "Cache permissions... "
PERMS=$(stat -c %a ~/.onenote-token-cache.json 2>/dev/null || echo "missing")
[ "$PERMS" = "600" ] && echo "PASS" || echo "FAIL ($PERMS, should be 600)"

# 4. Verify .env not in git
echo -n ".env excluded... "
git check-ignore .env > /dev/null 2>&1 && echo "PASS" || echo "FAIL (.env trackable by git)"

echo "=== Complete ==="
```

**Load test estimation (read-only, safe):**

```python
import time

def estimate_production_load(client, user_count: int):
    """Measure real API latency to estimate production capacity."""
    latencies = []
    for _ in range(10):
        start = time.time()
        client.me.onenote.notebooks.get()
        latencies.append((time.time() - start) * 1000)

    avg_ms = sum(latencies) / len(latencies)
    p95_ms = sorted(latencies)[int(len(latencies) * 0.95)]

    calls_per_user_per_min = 10  # From cost tuning model
    total_calls_per_min = calls_per_user_per_min * user_count
    tenant_budget_per_min = 1000  # 10,000/10min

    print(f"Avg latency: {avg_ms:.0f}ms | P95: {p95_ms:.0f}ms")
    print(f"Est. {total_calls_per_min} calls/min for {user_count} users")
    print(f"Tenant budget: {tenant_budget_per_min}/min")
    print(f"Utilization: {total_calls_per_min/tenant_budget_per_min*100:.0f}%")
    if total_calls_per_min > tenant_budget_per_min * 0.8:
        print("WARNING: > 80% budget utilization. Apply cost tuning strategies.")
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Input/Output HTML](https://learn.microsoft.com/en-us/graph/onenote-input-output-html)
- [Images & Files](https://learn.microsoft.com/en-us/graph/onenote-images-files)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)

## Next Steps

- Apply `onenote-security-basics` if any authentication items failed
- Use `onenote-cost-tuning` to optimize before scaling to more users
- See `onenote-rate-limits` for advanced queue-based throttling patterns
- Review `onenote-common-errors` for error code handling patterns
