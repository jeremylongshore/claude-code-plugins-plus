---
name: shopify-data-handling
description: |
  Handle Shopify customer PII, implement GDPR/CCPA compliance, and manage data retention
  with Shopify's mandatory privacy webhooks.
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

Shopify **requires** three GDPR webhooks for App Store apps. Your app will be **rejected** without them.

```typescript
// 1. customers/data_request — Customer requests their data
// Shopify sends this when a customer asks the merchant for their data
async function handleCustomerDataRequest(payload: {
  shop_domain: string;
  customer: { id: number; email: string; phone: string };
  orders_requested: number[];
  data_request: { id: number };
}): Promise<void> {
  // Collect all data you store about this customer
  const customerData = await db.customerRecords.findMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyCustomerId: String(payload.customer.id),
    },
  });

  const orderData = await db.orderRecords.findMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyOrderId: { in: payload.orders_requested.map(String) },
    },
  });

  // You have 30 days to respond
  // Email the data to the merchant (or make it available via your app)
  await sendDataExport({
    requestId: payload.data_request.id,
    shop: payload.shop_domain,
    customer: customerData,
    orders: orderData,
  });
}

// 2. customers/redact — Delete specific customer's data
async function handleCustomerRedact(payload: {
  shop_domain: string;
  customer: { id: number; email: string; phone: string };
  orders_to_redact: number[];
}): Promise<void> {
  // Delete ALL personal data for this customer
  await db.customerRecords.deleteMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyCustomerId: String(payload.customer.id),
    },
  });

  // Anonymize order records (keep for accounting, remove PII)
  for (const orderId of payload.orders_to_redact) {
    await db.orderRecords.update({
      where: { shopifyOrderId: String(orderId) },
      data: {
        customerEmail: null,
        customerName: null,
        shippingAddress: null,
        // Keep: orderId, total, line items, timestamps
      },
    });
  }

  // Log the deletion (keep audit record)
  await db.auditLog.create({
    data: {
      action: "CUSTOMER_DATA_REDACTED",
      shop: payload.shop_domain,
      customerId: String(payload.customer.id),
      timestamp: new Date(),
    },
  });
}

// 3. shop/redact — Delete ALL data for a shop (48h after uninstall)
async function handleShopRedact(payload: {
  shop_id: number;
  shop_domain: string;
}): Promise<void> {
  // Delete EVERYTHING related to this shop
  await db.customerRecords.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });
  await db.orderRecords.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });
  await db.sessions.deleteMany({
    where: { shop: payload.shop_domain },
  });
  await db.appSettings.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });

  console.log(`All data deleted for ${payload.shop_domain}`);
}
```

### Step 3: Data Minimization in API Queries

```typescript
// BAD: Fetching all customer fields when you only need the name
const ALL_FIELDS = `{
  customer(id: $id) {
    id firstName lastName email phone
    addresses { address1 city province country zip phone }
    orders(first: 100) {
      edges { node { id name totalPrice shippingAddress { ... } } }
    }
    metafields(first: 20) { edges { node { key value } } }
  }
}`;

// GOOD: Only fetch what you actually use
const MINIMAL_FIELDS = `{
  customer(id: $id) {
    id
    displayName
    numberOfOrders
    amountSpent { amount currencyCode }
  }
}`;
```

### Step 4: PII Detection in Logs

```typescript
// Prevent customer PII from leaking into logs
const PII_PATTERNS = [
  { name: "email", pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { name: "phone", pattern: /\+?\d{10,15}/g },
  { name: "credit_card", pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g },
];

function redactPII(text: string): string {
  let result = text;
  for (const { name, pattern } of PII_PATTERNS) {
    result = result.replace(pattern, `[REDACTED:${name}]`);
  }
  return result;
}

// Use in logging middleware
function safeLog(message: string, data: any): void {
  const safeData = JSON.parse(redactPII(JSON.stringify(data)));
  console.log(message, safeData);
}
```

### Step 5: Data Retention Policy

```typescript
// Automatic cleanup — run daily via cron
async function enforceRetentionPolicy(): Promise<void> {
  const now = new Date();

  // Delete API request logs older than 30 days
  await db.apiLogs.deleteMany({
    where: { createdAt: { lt: new Date(now.getTime() - 30 * 86400000) } },
  });

  // Delete webhook event logs older than 90 days
  await db.webhookLogs.deleteMany({
    where: { createdAt: { lt: new Date(now.getTime() - 90 * 86400000) } },
  });

  // Keep audit logs for 7 years (regulatory requirement)
  // Never auto-delete audit records

  console.log("Retention policy enforced");
}
```

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

## Next Steps

For enterprise access control, see `shopify-enterprise-rbac`.
