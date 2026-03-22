---
name: brightdata-prod-checklist
description: |
  Execute Bright Data production deployment checklist and rollback procedures.
  Use when deploying Bright Data integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "brightdata production", "deploy brightdata",
  "brightdata go-live", "brightdata launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Production Checklist

## Overview

Complete checklist for deploying Bright Data scraping integrations to production with zone verification, monitoring, and rollback procedures.

## Prerequisites

- Staging environment tested
- Production zone credentials in secrets vault
- Monitoring and alerting configured

## Instructions

### Step 1: Zone and Credential Verification

- [ ] Production zone active in Bright Data CP
- [ ] Zone password stored in secrets vault (not `.env`)
- [ ] API token scoped to production zone only
- [ ] SSL certificate (`brd-ca.crt`) deployed
- [ ] Separate zone from development/staging

```bash
# Verify production zone is active
curl -s -H "Authorization: Bearer ${BRIGHTDATA_API_TOKEN}" \
  https://api.brightdata.com/zone/get_active_zones \
  | python3 -c "import sys,json; zones=json.load(sys.stdin); print([z['name'] for z in zones])"

# Test production proxy connectivity
curl -x "http://brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}:${BRIGHTDATA_ZONE_PASSWORD}@brd.superproxy.io:33335" \
  -s -w "HTTP %{http_code} in %{time_total}s\n" \
  https://lumtest.com/myip.json
```

### Step 2: Code Quality

- [ ] No hardcoded credentials (grep for passwords, tokens)
- [ ] Retry logic with exponential backoff (see `brightdata-rate-limits`)
- [ ] Request queuing with concurrency limits (p-queue)
- [ ] Response validation (check for CAPTCHA pages, empty responses)
- [ ] Timeout set to 60-120s for Web Unlocker
- [ ] Error logging includes `X-Luminati-Error` headers

### Step 3: Infrastructure

- [ ] Health check endpoint tests proxy connectivity
- [ ] Monitoring tracks proxy response times, error rates
- [ ] Budget alerts configured in Bright Data CP
- [ ] Circuit breaker for proxy failures

```typescript
// Health check endpoint
export async function healthCheck() {
  const start = Date.now();
  try {
    const client = getBrightDataClient();
    const res = await client.get('https://lumtest.com/myip.json');
    return {
      status: 'healthy',
      proxy_ip: res.data.ip,
      latency_ms: Date.now() - start,
    };
  } catch (error: any) {
    return {
      status: 'degraded',
      error: error.response?.headers?.['x-luminati-error'] || error.message,
      latency_ms: Date.now() - start,
    };
  }
}
```

### Step 4: Monitoring and Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Proxy down | 5xx errors > 10/min | P1 |
| High latency | p99 > 30s | P2 |
| Budget spike | Daily cost > 2x average | P2 |
| Auth failures | 407 errors > 0 | P1 |
| Target blocked | `target_site_blocked` > 20% | P3 |

### Step 5: Gradual Rollout

```bash
# Pre-flight
curl -s https://status.brightdata.com/api/v2/status.json | python3 -c "import sys,json; s=json.load(sys.stdin); print(f'Status: {s[\"status\"][\"description\"]}')"

# Deploy with canary
kubectl apply -f k8s/production.yaml
kubectl rollout status deployment/scraper --timeout=300s

# Verify scraping works post-deploy
curl -s http://localhost:8080/health | python3 -m json.tool
```

## Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/scraper
kubectl rollout status deployment/scraper

# If zone compromised, pause in Bright Data CP immediately
```

## Output

- Verified production zone and credentials
- Health check endpoint monitoring proxy connectivity
- Alert rules for proxy errors and budget spikes
- Documented rollback procedure

## Resources

- [Bright Data Status](https://status.brightdata.com)
- [Zone Management](https://brightdata.com/cp/zones)
- [Usage Dashboard](https://brightdata.com/cp/usage)

## Next Steps

For version upgrades, see `brightdata-upgrade-migration`.
