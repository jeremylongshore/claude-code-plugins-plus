---
name: shopify-prod-checklist
description: |
  Execute Shopify app production deployment checklist covering App Store requirements,
  mandatory webhooks, API versioning, and rollback procedures.
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

- [ ] Using a stable API version (e.g., `2024-10`), not `unstable`
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

```typescript
app.get("/health", async (req, res) => {
  const checks: Record<string, any> = {};

  // Test Shopify connectivity
  try {
    const start = Date.now();
    await client.request("{ shop { name } }");
    checks.shopify = { status: "ok", latencyMs: Date.now() - start };
  } catch (err) {
    checks.shopify = { status: "error", message: (err as Error).message };
  }

  // Test database
  try {
    await db.query("SELECT 1");
    checks.database = { status: "ok" };
  } catch (err) {
    checks.database = { status: "error" };
  }

  const allHealthy = Object.values(checks).every((c: any) => c.status === "ok");
  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? "healthy" : "degraded",
    checks,
    timestamp: new Date().toISOString(),
  });
});
```

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

```bash
#!/bin/bash
echo "=== Shopify Pre-Deploy Smoke Test ==="
STORE="$SHOPIFY_STORE"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
PASS=0; FAIL=0

# Auth test
if curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/2024-10/shop.json" > /dev/null; then
  echo "PASS: Auth"; ((PASS++))
else
  echo "FAIL: Auth"; ((FAIL++))
fi

# Scopes test
SCOPES=$(curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" | jq -r '.access_scopes[].handle')
for required in read_products read_orders; do
  if echo "$SCOPES" | grep -q "$required"; then
    echo "PASS: Scope $required"; ((PASS++))
  else
    echo "FAIL: Missing scope $required"; ((FAIL++))
  fi
done

echo "---"
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "READY FOR DEPLOY" || echo "FIX FAILURES FIRST"
```

## Resources

- [Shopify App Store Review Requirements](https://shopify.dev/docs/apps/launch/app-requirements)
- [GDPR Compliance Webhooks](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)
- [API Versioning](https://shopify.dev/docs/api/usage/versioning)
- [Shopify Status Page](https://www.shopifystatus.com)

## Next Steps

For version upgrades, see `shopify-upgrade-migration`.
