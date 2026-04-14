---
name: shopify-security-basics
description: |
  Apply Shopify security best practices for API credentials, webhook HMAC validation,
  and access scope management.
  Use when securing API keys, validating webhook signatures,
  or auditing Shopify security configuration.
  Trigger with phrases like "shopify security", "shopify secrets",
  "secure shopify", "shopify HMAC", "shopify webhook verify".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Security Basics

## Overview

Security essentials for Shopify apps: credential management, webhook HMAC validation, request verification, and least-privilege access scopes.

## Prerequisites

- Shopify Partner account with app credentials
- Understanding of HMAC-SHA256 signatures
- Access to Shopify app configuration

## Instructions

### Step 1: Secure Credential Storage

```bash
# .env — NEVER commit
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret_key
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# .gitignore — add immediately
.env
.env.local
.env.*.local
*.pem
```

**Token format reference:**
| Token Type | Prefix | Length | Used For |
|-----------|--------|--------|----------|
| Admin API access token | `shpat_` | 38 chars | Server-side Admin API |
| Storefront API token | varies | varies | Client-safe storefront queries |
| API secret key | none | 32+ hex | Webhook HMAC, OAuth |

### Step 2: Webhook HMAC Verification

Shopify signs every webhook with your app's API secret using HMAC-SHA256. The signature is in the `X-Shopify-Hmac-Sha256` header. Use `crypto.timingSafeEqual` for comparison to prevent timing attacks. The middleware must use raw body parser (not JSON parser).

See [Webhook HMAC Verification](references/webhook-hmac-verification.md) for the complete implementation.

### Step 3: OAuth Request Verification

Verify that incoming OAuth requests from Shopify are authentic by checking the HMAC query parameter. The library handles this automatically, but the manual approach sorts params alphabetically, creates a query string, and compares HMAC hex digests.

See [OAuth Request Verification](references/oauth-request-verification.md) for the complete implementation.

### Step 4: Minimal Access Scopes

Only request the scopes your app actually needs:

| Use Case | Required Scopes |
|----------|----------------|
| Read-only product catalog | `read_products` |
| Product management | `read_products`, `write_products` |
| Order dashboard | `read_orders` |
| Fulfillment automation | `read_orders`, `write_fulfillments`, `read_fulfillments` |
| Customer loyalty app | `read_customers`, `write_customers` |
| Full admin app | Request scopes incrementally, not all at once |

```toml
# shopify.app.toml — start minimal, add as needed
[access_scopes]
scopes = "read_products"

# Use optional scopes for features that not all merchants need
[access_scopes.optional]
scopes = "write_products,read_orders"
```

### Step 5: Content Security Policy for Embedded Apps

```typescript
// Embedded apps must set proper CSP headers
app.use((req, res, next) => {
  const shop = req.query.shop as string;
  res.setHeader(
    "Content-Security-Policy",
    `frame-ancestors https://${shop} https://admin.shopify.com;`
  );
  next();
});
```

## Output

- Credentials securely stored in environment variables
- Webhook HMAC verification on all incoming webhooks
- OAuth request signatures validated
- Minimal access scopes configured
- CSP headers set for embedded apps

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in git history | `git log -p \| grep shpat_` | Rotate token immediately, use git-secrets |
| Invalid webhook HMAC | 401 responses in webhook handler | Verify API secret matches Partner Dashboard |
| Missing scope | 403 errors on API calls | Add scope to `shopify.app.toml` and re-auth |
| Token exposed in client JS | Browser devtools | Never send admin tokens to the browser |

## Examples

### Security Audit Checklist

- [ ] Access tokens in environment variables, never in code
- [ ] `.env` files in `.gitignore`
- [ ] Webhook HMAC verified on every incoming webhook
- [ ] OAuth HMAC verified on app installation requests
- [ ] Minimal scopes — only what the app needs
- [ ] CSP `frame-ancestors` set for embedded apps
- [ ] No admin tokens in client-side JavaScript
- [ ] Token rotation procedure documented
- [ ] `git-secrets` or similar pre-commit hook installed

### Install git-secrets to Prevent Token Leaks

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or: sudo apt install git-secrets  # Linux

# Add Shopify patterns
git secrets --add 'shpat_[a-f0-9]{32}'
git secrets --add 'shpss_[a-f0-9]{32}'

# Install hook
git secrets --install
```

## Resources

- [Shopify Webhook HMAC Verification](https://shopify.dev/docs/apps/build/webhooks/subscribe#step-5-verify-the-webhook)
- [Shopify API Authentication](https://shopify.dev/docs/api/usage/authentication)
- [Access Scopes Reference](https://shopify.dev/docs/api/usage/access-scopes)
- [Embedded App Security](https://shopify.dev/docs/apps/build/authentication-authorization)
