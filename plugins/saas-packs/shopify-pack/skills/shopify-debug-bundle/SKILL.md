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

### Step 1: Create and Run Debug Bundle

The debug bundle script collects shop info, access scopes, supported API versions, GraphQL and REST rate limit state, environment details (Node/npm versions, SDK version, env vars), then packages everything into a tarball with tokens automatically redacted.

See [Debug Bundle Script](references/debug-bundle-script.md) for the complete bash script.

Set these environment variables before running:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="shpat_xxx"
export SHOPIFY_API_VERSION="2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning
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
  "https://$SHOPIFY_STORE/admin/api/2025-04/shop.json" \
  | jq '{name: .shop.name, plan: .shop.plan_name}' \
  && echo "HEALTHY" || echo "UNHEALTHY"
```

## Resources

- [Shopify API Response Codes](https://shopify.dev/docs/api/usage/response-codes)
- [Shopify Partner Support](https://help.shopify.com/en/partners)
- [Shopify Status Page](https://www.shopifystatus.com)
