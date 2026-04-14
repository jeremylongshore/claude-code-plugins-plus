---
name: shopify-prod-checklist
description: |
  Execute Shopify app production deployment checklist covering App Store requirements,
  mandatory webhooks, API versioning, and rollback procedures.
  Use when preparing a Shopify app for production launch, submitting to the App Store,
  or auditing an existing deployment for compliance gaps.
  Trigger with phrases like "shopify production", "deploy shopify",
  "shopify go-live", "shopify launch checklist", "shopify app store submit".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Production Checklist

## Overview

Complete pre-launch checklist for deploying Shopify apps to production and submitting to the Shopify App Store.

## Prerequisites

- Staging environment tested and verified
- Shopify Partner account with app configured
- All development and staging tests passing

## Instructions

### Step 1: API and Authentication

- [ ] Using a recent stable API version (e.g., 2025-04), not `unstable`
- [ ] Access token stored in secure environment variables (never in code)
- [ ] API secret stored securely for webhook HMAC verification
- [ ] OAuth flow tested with a fresh install on a clean dev store
- [ ] Session persistence implemented (database or Redis, not in-memory)
- [ ] Token refresh/re-auth handled for expired sessions
- [ ] `APP_UNINSTALLED` webhook handler cleans up sessions

### Step 2: Mandatory GDPR Compliance

- [ ] `customers/data_request` webhook handler implemented
- [ ] `customers/redact` webhook handler implemented
- [ ] `shop/redact` webhook handler implemented (fires 48h after uninstall)
- [ ] All three configured in `shopify.app.toml`
- [ ] Handlers respond with HTTP 200 within 5 seconds
- [ ] Customer data deletion actually works (test it!)

### Step 3: Webhook Security

- [ ] All webhooks verify `X-Shopify-Hmac-Sha256` using HMAC-SHA256
- [ ] Using `crypto.timingSafeEqual()` for signature comparison
- [ ] Webhook endpoints use raw body parsing (not JSON middleware)
- [ ] Idempotency: duplicate webhook deliveries handled gracefully

### Step 4: Rate Limit Resilience

- [ ] GraphQL queries optimized (check `requestedQueryCost` with debug header)
- [ ] Retry logic with exponential backoff for 429 / THROTTLED responses
- [ ] Bulk operations used for large data exports instead of paginated queries
- [ ] No unbounded loops that could exhaust rate limits

### Step 5: Error Handling

- [ ] All GraphQL mutations check `userErrors` array (200 with errors!)
- [ ] HTTP 4xx/5xx errors caught and logged with `X-Request-Id`
- [ ] Graceful degradation when Shopify is unavailable
- [ ] No PII logged (customer emails, addresses, phone numbers)

### Step 6: App Store Submission Requirements

- [ ] App listing has clear name, description, and screenshots
- [ ] Privacy policy URL provided
- [ ] App has proper onboarding flow for new merchants
- [ ] Embedded app uses App Bridge for navigation (no full-page redirects)
- [ ] CSP headers set: `frame-ancestors https://*.myshopify.com https://admin.shopify.com`
- [ ] App works on both desktop and mobile admin
- [ ] Loading states shown during API calls (no blank screens)

### Step 7: API Version Management

```bash
# Check which API versions your store supports
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" \
  | jq '.supported_versions[] | select(.supported == true) | .handle'

# Shopify deprecates versions ~12 months after release
# Set a calendar reminder to upgrade quarterly
```

### Step 8: Health Check Endpoint

Express endpoint that tests Shopify API connectivity and database availability, returning structured status with latency metrics.

See [Health Check Endpoint](references/health-check-endpoint.md) for the complete implementation.

## Output

- All checklist items verified
- Health check endpoint operational
- GDPR compliance webhooks functional
- App ready for production traffic or App Store submission

## Error Handling

| Alert | Condition | Severity |
|-------|-----------|----------|
| Shopify API down | 5xx errors > 5/min | P1 - Critical |
| Auth failures | 401 errors > 0 | P1 - Token may be revoked |
| Rate limited | THROTTLED > 5/min | P2 - Reduce query cost |
| High latency | p95 > 3000ms | P2 - Check query complexity |
| Webhook failures | Delivery success < 95% | P2 - Check endpoint health |

## Examples

### Pre-Deploy Smoke Test

Bash script that validates Shopify auth and API scopes before deploying to production.

See [Pre-Deploy Smoke Test](references/pre-deploy-smoke-test.md) for the complete script.

## Resources

- [Shopify App Store Review Requirements](https://shopify.dev/docs/apps/launch/app-requirements)
- [GDPR Compliance Webhooks](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)
- [API Versioning](https://shopify.dev/docs/api/usage/versioning)
- [Shopify Status Page](https://www.shopifystatus.com)
