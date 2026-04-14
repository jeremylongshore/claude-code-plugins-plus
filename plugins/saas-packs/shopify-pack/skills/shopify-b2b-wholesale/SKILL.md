---
name: shopify-b2b-wholesale
description: |
  Build Shopify Plus B2B features with companies, catalogs, and wholesale pricing.
  Use when setting up wholesale accounts, creating price lists,
  or configuring B2B checkout with purchase orders.
  Trigger with phrases like "shopify b2b", "shopify wholesale",
  "shopify company api", "shopify price lists", "shopify catalog api".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify B2B & Wholesale

## Overview

Shopify Plus B2B features let you create separate wholesale experiences with company accounts, custom catalogs, and tiered pricing. This skill covers the full B2B setup: companies, catalogs, price lists, and checkout configuration using the GraphQL Admin API. Requires a Shopify Plus plan.

## Prerequisites

- Shopify Plus plan (B2B features are Plus-only)
- Access scopes: `read_customers`, `write_customers`, `read_products`, `write_products`, `read_orders`
- B2B enabled in Shopify admin (Settings > B2B)
- API version 2023-10 or later (B2B mutations stabilized)

## Instructions

### Step 1: Create a B2B Company

Use `companyCreate` with `CompanyCreateInput` — requires `company` (name, note), `companyContact` (email, firstName, lastName), and `companyLocation` (name, billingAddress, shippingAddress):

```typescript
await client.request(COMPANY_CREATE, {
  variables: {
    input: {
      company: { name: "Acme Wholesale Inc", note: "Tier 1 partner" },
      companyContact: { email: "buyer@acme.com", firstName: "Jane", lastName: "Doe" },
      companyLocation: {
        name: "Headquarters",
        billingAddress: { address1: "123 Commerce St", city: "Austin", provinceCode: "TX", countryCode: "US", zip: "78701" },
        shippingAddress: { address1: "123 Commerce St", city: "Austin", provinceCode: "TX", countryCode: "US", zip: "78701" },
      },
    },
  },
});
// Always check userErrors in response — returns code like COMPANY_NOT_FOUND, INVALID
```

See [references/company-management.md](references/company-management.md) for the full mutation, additional contacts, locations, and roles.

### Step 2: Create a Catalog

Catalogs link products to specific companies. Use `catalogCreate` with a title, status, and `context.companyLocationIds`:

```typescript
await client.request(CATALOG_CREATE, {
  variables: {
    input: {
      title: "Wholesale Tier 1",
      status: "ACTIVE",
      context: { companyLocationIds: ["gid://shopify/CompanyLocation/123456"] },
    },
  },
});
```

### Step 3: Set Wholesale Pricing

Create a price list with `priceListCreate`. Use `PERCENTAGE_DECREASE` for blanket discounts or `priceListFixedPricesAdd` for per-variant overrides:

```typescript
// 30% off all products in this catalog
await client.request(PRICE_LIST_CREATE, {
  variables: {
    input: {
      name: "Wholesale 30% Off",
      currency: "USD",
      parent: { adjustment: { type: "PERCENTAGE_DECREASE", value: 30 } },
      catalogId: "gid://shopify/Catalog/789",
    },
  },
});
```

For fixed price overrides, volume pricing, and multi-currency, see [references/catalog-pricing.md](references/catalog-pricing.md).

### Step 4: B2B Checkout Configuration

B2B orders use `draftOrderCreate` with `purchaseOrder` number and `purchasingEntity` linking to the company. Key fields:

```typescript
await client.request(DRAFT_ORDER_CREATE, {
  variables: {
    input: {
      purchaseOrder: "PO-2026-0042",
      lineItems: [{ variantId: "gid://shopify/ProductVariant/123", quantity: 100 }],
      purchasingEntity: {
        purchasingCompany: {
          companyId: "gid://shopify/Company/456",
          companyContactId: "gid://shopify/CompanyContact/789",
          companyLocationId: "gid://shopify/CompanyLocation/012",
        },
      },
      paymentTerms: { paymentTermsTemplateId: "gid://shopify/PaymentTermsTemplate/1" },
    },
  },
});
```

Payment terms templates: Due on receipt, Net 15, Net 30, Net 45, Net 60, Net 90. Query available templates with `paymentTermsTemplates`.

See [references/b2b-checkout.md](references/b2b-checkout.md) for the full draft order flow, invoice sending, and vaulted payments.

## Output

- B2B company created with contact and billing/shipping addresses
- Catalog linked to specific company locations
- Wholesale price list with percentage or fixed pricing
- Draft orders with purchase order numbers and payment terms

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `COMPANY_NOT_FOUND` | Invalid company GID | Verify the company ID exists via `companyQuery` |
| `CATALOG_LIMIT_EXCEEDED` | Max catalogs per context reached | Remove unused catalogs or upgrade plan |
| `PRICE_LIST_NOT_FOUND` | Price list not linked to catalog | Ensure `catalogId` is set on price list |
| `B2B_NOT_ENABLED` | B2B feature not activated | Enable B2B in Shopify admin Settings > B2B (requires Plus) |
| `COMPANY_CONTACT_NOT_FOUND` | Contact not associated with company | Create contact via `companyContactCreate` first |
| `INVALID_PURCHASING_ENTITY` | Missing company/contact/location in draft order | All three IDs required in `purchasingCompany` |

## Examples

### Onboarding a New Wholesale Partner

Create a B2B company with multiple contacts, locations, and roles for a new wholesale account joining your program.

See [Company Management](references/company-management.md) for the full mutation and multi-contact setup.

### Setting Up Tiered Wholesale Pricing

Configure percentage-based discounts for standard wholesalers and fixed per-variant overrides for VIP partners using price lists.

See [Catalog Pricing](references/catalog-pricing.md) for percentage, fixed price, and volume pricing strategies.

### Processing a B2B Purchase Order

Create a draft order with a PO number, Net 30 payment terms, and company association for a wholesale buyer.

See [B2B Checkout](references/b2b-checkout.md) for the full draft order flow, invoice sending, and vaulted payments.

## Resources

- [B2B on Shopify](https://shopify.dev/docs/apps/build/b2b)
- [companyCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/companyCreate)
- [catalogCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/catalogCreate)
- [priceListCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/priceListCreate)
- [B2B Checkout](https://shopify.dev/docs/apps/build/b2b/checkout)
