---
name: shopify-data-handling
description: |
  Handle Shopify customer PII, implement GDPR/CCPA compliance, and manage data retention
  with Shopify's mandatory privacy webhooks.
  Use when building apps that store customer data, preparing for App Store review, or implementing deletion workflows.
  Trigger with phrases like "shopify data", "shopify PII", "shopify GDPR",
  "shopify customer data", "shopify privacy", "shopify CCPA", "shopify data request".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Data Handling

## Overview

Handle customer PII correctly when building Shopify apps. Covers the mandatory GDPR webhooks, data minimization, and the specific privacy requirements Shopify enforces for App Store submission.

## Prerequisites

- Understanding of GDPR/CCPA requirements
- Shopify app with webhook handling configured
- Database for storing and deleting customer data

## Instructions

### Step 1: Understand What Data Shopify Shares

When a merchant grants your app access, you may receive:

| Data Type | Source | Sensitivity | Retention Obligation |
|-----------|--------|-------------|---------------------|
| Customer email, name, phone | `read_customers` scope | PII — encrypt at rest | Delete on `customers/redact` |
| Shipping addresses | `read_orders` scope | PII — encrypt at rest | Delete on `customers/redact` |
| Order details (amounts, items) | `read_orders` scope | Business data | Delete on `shop/redact` |
| Product data | `read_products` scope | Public | Delete on `shop/redact` |
| Shop owner email | `read_shop` scope | PII | Delete on `shop/redact` |

### Step 2: Implement Mandatory Privacy Webhooks

Shopify **requires** three GDPR webhooks for App Store apps. Your app will be **rejected** without them: `customers/data_request` (customer wants their data), `customers/redact` (delete a customer's PII), and `shop/redact` (delete all shop data 48h after uninstall).

See [GDPR Privacy Webhooks](references/gdpr-privacy-webhooks.md) for the complete implementation of all three handlers.

### Step 3: Data Minimization and PII Detection

Only fetch the fields you actually use in GraphQL queries. Add PII redaction middleware to prevent customer data from leaking into logs — detect emails, phone numbers, and credit card patterns.

See [Data Minimization and PII Detection](references/data-minimization-and-pii-detection.md) for query examples and redaction middleware.

### Step 4: Data Retention Policy

Automate cleanup with a daily cron job: delete API logs after 30 days, webhook logs after 90 days, and keep audit logs for 7 years (regulatory requirement).

See [Data Retention Policy](references/data-retention-policy.md) for the complete implementation.

## Output

- GDPR mandatory webhooks implemented and tested
- Data minimization in API queries
- PII redaction in all log output
- Retention policy with automatic cleanup

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| App Store rejection for GDPR | Missing webhook handlers | Implement all 3 mandatory webhooks |
| Customer data not found | Data already deleted | Return empty response (not an error) |
| shop/redact not received | App reinstalled before 48h | Shopify cancels redact if reinstalled |
| PII in logs | Missing redaction | Add redaction middleware to all loggers |

## Examples

### Test GDPR Webhooks

```bash
# Simulate a customers/data_request webhook locally
curl -X POST http://localhost:3000/webhooks/gdpr/data-request \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Topic: customers/data_request" \
  -H "X-Shopify-Shop-Domain: test.myshopify.com" \
  -d '{
    "shop_domain": "test.myshopify.com",
    "customer": {"id": 123, "email": "test@example.com", "phone": "+1234567890"},
    "orders_requested": [1001, 1002],
    "data_request": {"id": 999}
  }'
```

## Resources

- [Shopify Privacy Law Compliance](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)
- [GDPR Webhook Requirements](https://shopify.dev/changelog/apps-now-need-to-use-gdpr-webhooks)
- [Data Protection Best Practices](https://shopify.dev/docs/apps/build/compliance)
