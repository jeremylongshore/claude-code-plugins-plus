---
name: shopify-debug-bundle
description: |
  Collect Shopify debug evidence including API versions, scopes, rate limit state, and request logs.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Shopify problems.
  Trigger with phrases like "shopify debug", "shopify support bundle",
  "collect shopify logs", "shopify diagnostic".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Debug Bundle

## Overview

Collect all diagnostic information needed for Shopify support tickets: API version compatibility, access scopes, rate limit state, recent errors, and connectivity checks.

## Prerequisites

- Shopify access token (`shpat_xxx`) available
- `curl` and `jq` installed
- Store domain known (`*.myshopify.com`)

## Instructions

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# shopify-debug-bundle.sh
set -euo pipefail

STORE="${SHOPIFY_STORE:-your-store.myshopify.com}"
TOKEN="${SHOPIFY_ACCESS_TOKEN}"
VERSION="${SHOPIFY_API_VERSION:-2024-10}"
BUNDLE_DIR="shopify-debug-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BUNDLE_DIR"

echo "=== Shopify Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Store: $STORE" | tee -a "$BUNDLE_DIR/summary.txt"
echo "API Version: $VERSION" | tee -a "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "---" | tee -a "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect API State

```bash
# Shop info and plan
echo "--- Shop Info ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json" \
  | jq '{name: .shop.name, plan: .shop.plan_name, domain: .shop.domain, timezone: .shop.iana_timezone}' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: shop.json" >> "$BUNDLE_DIR/summary.txt"

# Granted access scopes
echo "--- Access Scopes ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" \
  | jq '.access_scopes[].handle' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: scopes" >> "$BUNDLE_DIR/summary.txt"

# Supported API versions
echo "--- API Versions ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" \
  | jq '.supported_versions[] | {handle, display_name, latest, supported}' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: versions" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Test Rate Limit State

```bash
# GraphQL rate limit check — inspects cost headers
echo "--- Rate Limit State ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  "https://$STORE/admin/api/$VERSION/graphql.json" \
  | jq '.extensions.cost' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1

# REST rate limit check — inspect response headers
echo "--- REST Rate Limit Headers ---" >> "$BUNDLE_DIR/summary.txt"
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json" \
  | grep -iE "(x-shopify-shop-api-call-limit|retry-after|x-request-id)" \
  >> "$BUNDLE_DIR/summary.txt" 2>&1
```

### Step 4: Collect Environment Info

```bash
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- @shopify/shopify-api ---" >> "$BUNDLE_DIR/summary.txt"
npm list @shopify/shopify-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "not installed" >> "$BUNDLE_DIR/summary.txt"

# Environment variables (redacted)
echo "--- Env Vars (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_KEY: ${SHOPIFY_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_SECRET: ${SHOPIFY_API_SECRET:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_ACCESS_TOKEN: ${SHOPIFY_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_SCOPES: ${SHOPIFY_SCOPES:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_VERSION: ${SHOPIFY_API_VERSION:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 5: Package and Report

```bash
# Redact any leaked tokens from the bundle
find "$BUNDLE_DIR" -type f -exec sed -i 's/shpat_[a-f0-9]\{32\}/shpat_[REDACTED]/g' {} +

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents:"
ls -la "$BUNDLE_DIR/"
echo ""
echo "Review before sharing — check for sensitive data!"
```

## Output

- `shopify-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — shop info, scopes, API versions, rate limits, environment
  - All secrets automatically redacted

## Error Handling

| Diagnostic | What It Reveals | If It Fails |
|-----------|----------------|-------------|
| Shop info | Store name, plan, timezone | Token invalid or store unreachable |
| Access scopes | What your app can access | Token expired or revoked |
| API versions | Which versions the store supports | Network issue |
| Rate limit state | Current bucket fill level | Token or network issue |
| SDK version | Whether SDK needs updating | Package not installed |

## Examples

### Sensitive Data Checklist

**ALWAYS REDACT before sharing:**
- Access tokens (`shpat_xxx`)
- API keys and secrets
- Customer PII (emails, names, addresses)
- Order details with customer data

**Safe to include:**
- Store name and plan
- API version and scopes
- Error messages and X-Request-Id values
- Rate limit headers
- SDK/runtime versions

### Quick One-Liner Health Check

```bash
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/2024-10/shop.json" \
  | jq '{name: .shop.name, plan: .shop.plan_name}' \
  && echo "HEALTHY" || echo "UNHEALTHY"
```

## Resources

- [Shopify API Response Codes](https://shopify.dev/docs/api/usage/response-codes)
- [Shopify Partner Support](https://help.shopify.com/en/partners)
- [Shopify Status Page](https://www.shopifystatus.com)

## Next Steps

For rate limit issues, see `shopify-rate-limits`.
