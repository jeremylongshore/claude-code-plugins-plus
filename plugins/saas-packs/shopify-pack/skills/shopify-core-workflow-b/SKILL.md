---
name: shopify-core-workflow-b
description: |
  Manage Shopify orders, customers, and fulfillments using the GraphQL Admin API.
  Use when querying orders, processing fulfillments, managing customers,
  or building order management integrations.
  Trigger with phrases like "shopify orders", "shopify customers",
  "shopify fulfillment", "process shopify order", "shopify checkout".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Orders & Customer Management

## Overview

Secondary core workflow: manage orders, customers, and fulfillments. Query order data, process fulfillments, and handle customer records through the GraphQL Admin API.

## Prerequisites

- Completed `shopify-install-auth` setup
- Access scopes: `read_orders`, `write_orders`, `read_customers`, `write_customers`, `read_fulfillments`, `write_fulfillments`
- Familiarity with `shopify-core-workflow-a` (products)

## Instructions

### Step 1: Query Orders

Query orders with financial/fulfillment status filters, line items, customer data, and shipping addresses. Uses Shopify query syntax (`financial_status:paid`, `fulfillment_status:unfulfilled`, `name:#1001`, etc.).

See [Query Orders](references/query-orders.md) for the complete query with pagination and query syntax examples.

### Step 2: Create a Draft Order

Create draft orders with variant line items, custom line items, discounts, shipping addresses, and customer assignment.

See [Draft Order Create](references/draft-order-create.md) for the complete mutation and variables.

### Step 3: Process Fulfillment

Two-step process: first query fulfillment orders for an order to get line item IDs, then create the fulfillment with tracking information and customer notification.

See [Fulfillment Processing](references/fulfillment-processing.md) for both queries and the complete workflow.

### Step 4: Customer Management

Search customers by email, order count, total spent, tags, and state. Returns addresses and metafields.

See [Customer Search Query](references/customer-search-query.md) for the complete query and syntax examples.

## Output

- Orders queryable with financial and fulfillment status filters
- Draft orders created with line items, discounts, and shipping
- Fulfillments processed with tracking information
- Customer records searchable with spending and order filters

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Access denied for orders` | Missing `read_orders` scope | Add scope and re-auth |
| `Fulfillment order not found` | Wrong fulfillment order ID | Query fulfillment orders first |
| `Cannot fulfill: already fulfilled` | Order already shipped | Check `remainingQuantity > 0` |
| `Customer not found` | Invalid customer GID | Verify GID format `gid://shopify/Customer/1234567890` (numeric ID) |
| `Order is not editable` | Order already archived | Only draft/open orders are editable |
| `THROTTLED` | Rate limit exceeded | Implement backoff -- see `shopify-rate-limits` |

## Examples

### Order Analytics Query

```typescript
// Get order count and revenue for a date range
const ORDER_ANALYTICS = `
  query orderAnalytics {
    ordersCount(query: "created_at:>2024-01-01 AND created_at:<2024-02-01") {
      count
    }
    orders(first: 1, query: "created_at:>2024-01-01", sortKey: TOTAL_PRICE, reverse: true) {
      edges {
        node {
          name
          totalPriceSet { shopMoney { amount currencyCode } }
        }
      }
    }
  }
`;
```

### Refund an Order

Create a refund with line item restock and customer notification.

See [Refund Create](references/refund-create.md) for the complete mutation and variables.

## Resources

- [Orders Query](https://shopify.dev/docs/api/admin-graphql/latest/queries/orders)
- [FulfillmentCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/fulfillmentCreate)
- [Customer Object](https://shopify.dev/docs/api/admin-graphql/latest/objects/Customer)
- [Draft Orders](https://shopify.dev/docs/api/admin-graphql/latest/mutations/draftOrderCreate)
