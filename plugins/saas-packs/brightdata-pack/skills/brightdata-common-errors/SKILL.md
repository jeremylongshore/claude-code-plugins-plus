---
name: brightdata-common-errors
description: |
  Diagnose and fix Bright Data common errors and exceptions.
  Use when encountering Bright Data errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "brightdata error", "fix brightdata",
  "brightdata not working", "debug brightdata".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Common Errors

## Overview

Diagnostic reference for the most common Bright Data proxy and API errors with real solutions and fix commands.

## Prerequisites

- Bright Data zone configured
- Proxy credentials available
- Access to error logs

## Instructions

### Step 1: Identify the Error

Check your proxy response status code or error message against the table below.

### Step 2: Apply the Fix

Follow the specific solution for your error code.

## Error Reference

### 407 Proxy Authentication Required

```
HTTP/1.1 407 Proxy Authentication Required
```

**Cause:** Username format is wrong or credentials are invalid.

**Fix:**
```bash
# Verify credential format — must be exactly:
# brd-customer-{CUSTOMER_ID}-zone-{ZONE_NAME}
echo "Username: brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}"

# Test with curl
curl -x "http://brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}:${BRIGHTDATA_ZONE_PASSWORD}@brd.superproxy.io:33335" \
  https://lumtest.com/myip.json
```

---

### 502 Bad Gateway

```
HTTP/1.1 502 Bad Gateway
X-Luminati-Error: target_site_blocked
```

**Cause:** Target site blocked the request despite Web Unlocker retries.

**Fix:**
- Increase timeout to 120s (Web Unlocker needs time to solve CAPTCHAs)
- Switch to Scraping Browser zone for JS-heavy sites
- Add `-country-us` to username for geo-specific content

---

### SSL Certificate Errors

```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Cause:** Missing Bright Data CA certificate for HTTPS proxying.

**Fix:**
```bash
# Download the Bright Data CA certificate
curl -sO https://brightdata.com/ssl/brd-ca.crt

# Node.js
export NODE_EXTRA_CA_CERTS=./brd-ca.crt

# Python requests
# requests.get(url, proxies=proxies, verify='./brd-ca.crt')
```

---

### ETIMEDOUT / Connection Timeout

```
Error: connect ETIMEDOUT brd.superproxy.io:33335
```

**Cause:** Firewall blocking outbound connections to Bright Data.

**Fix:**
```bash
# Test connectivity
nc -zv brd.superproxy.io 33335
# If blocked, allow outbound TCP to brd.superproxy.io:33335

# For Scraping Browser, also allow port 9222
nc -zv brd.superproxy.io 9222
```

---

### 403 Forbidden (Zone Inactive)

**Cause:** Zone is not active or has been paused.

**Fix:** Go to https://brightdata.com/cp, navigate to the zone, and click "Activate".

---

### 429 Too Many Requests

**Cause:** Exceeded concurrent request limit for your zone.

**Fix:**
```typescript
// Implement request queuing
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 10, interval: 1000, intervalCap: 20 });
const result = await queue.add(() => client.get(url));
```

---

### Empty Response Body

**Cause:** Target returned a CAPTCHA page that Web Unlocker couldn't solve, or wrong zone type for the target.

**Fix:**
- Check zone type matches target (Web Unlocker for static, Scraping Browser for JS)
- Verify target URL is accessible in a regular browser
- Try adding `&brd_json=1` for SERP API requests

---

### X-Luminati-Error Headers

Bright Data returns error details in response headers:

| Header Value | Meaning | Action |
|-------------|---------|--------|
| `target_site_blocked` | Site anti-bot blocked request | Use Scraping Browser |
| `ip_banned` | IP was banned by target | Retry (auto-rotates IP) |
| `captcha` | CAPTCHA challenge failed | Increase timeout |
| `connection_failed` | Could not reach target | Verify target URL |
| `auth_failed` | Credential error | Check username/password |

## Quick Diagnostic Commands

```bash
# Check Bright Data status
curl -s https://status.brightdata.com/api/v2/status.json | python3 -m json.tool

# Test proxy connectivity
curl -x "http://brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}:${BRIGHTDATA_ZONE_PASSWORD}@brd.superproxy.io:33335" \
  -o /dev/null -s -w "HTTP %{http_code} in %{time_total}s\n" \
  https://lumtest.com/myip.json

# Check zone credentials
curl -H "Authorization: Bearer ${BRIGHTDATA_API_TOKEN}" \
  https://api.brightdata.com/zone/get_active_zones
```

## Escalation Path

1. Collect request/response headers (including `X-Luminati-*` headers)
2. Run `brightdata-debug-bundle` to create diagnostic package
3. Check https://status.brightdata.com for outages
4. Contact support with zone name, error headers, and timestamps

## Resources

- [Bright Data Error Reference](https://docs.brightdata.com/general/account/troubleshooting)
- [Status Page](https://status.brightdata.com)
- [Support Portal](https://brightdata.com/cp/support)

## Next Steps

For comprehensive debugging, see `brightdata-debug-bundle`.
