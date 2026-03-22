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

```typescript
const QUERY_ORDERS = `
  query orders($first: Int!, $query: String, $after: String) {
    orders(first: $first, query: $query, after: $after, sortKey: CREATED_AT, reverse: true) {
      edges {
        node {
          id
          name                    # "#1001"
          createdAt
          displayFinancialStatus  # PAID, PENDING, REFUNDED, etc.
          displayFulfillmentStatus # FULFILLED, UNFULFILLED, PARTIALLY_FULFILLED
          totalPriceSet {
            shopMoney { amount currencyCode }
          }
          customer {
            id
            displayName
            email
          }
          lineItems(first: 10) {
            edges {
              node {
                title
                quantity
                variant {
                  id
                  sku
                  price
                }
                originalTotalSet {
                  shopMoney { amount currencyCode }
                }
              }
            }
          }
          shippingAddress {
            address1
            city
            province
            country
            zip
          }
        }
        cursor
      }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

// Shopify order query syntax:
// "financial_status:paid"
// "fulfillment_status:unfulfilled"
// "created_at:>2024-01-01"
// "name:#1001"
// "email:customer@example.com"
// "tag:rush"
const data = await client.request(QUERY_ORDERS, {
  variables: {
    first: 25,
    query: "financial_status:paid AND fulfillment_status:unfulfilled",
  },
});
```

### Step 2: Create a Draft Order

```typescript
const CREATE_DRAFT_ORDER = `
  mutation draftOrderCreate($input: DraftOrderInput!) {
    draftOrderCreate(input: $input) {
      draftOrder {
        id
        name
        totalPriceSet {
          shopMoney { amount currencyCode }
        }
        invoiceUrl
      }
      userErrors {
        field
        message
      }
    }
  }
`;

await client.request(CREATE_DRAFT_ORDER, {
  variables: {
    input: {
      lineItems: [
        {
          variantId: "gid://shopify/ProductVariant/12345",
          quantity: 2,
        },
        {
          title: "Custom Engraving", // Custom line item (no variant)
          originalUnitPrice: "15.00",
          quantity: 1,
        },
      ],
      customerId: "gid://shopify/Customer/67890",
      note: "Rush order — ship priority",
      tags: ["wholesale", "rush"],
      shippingAddress: {
        address1: "123 Main St",
        city: "Portland",
        provinceCode: "OR",
        countryCode: "US",
        zip: "97201",
      },
      appliedDiscount: {
        title: "Wholesale 10%",
        value: 10.0,
        valueType: "PERCENTAGE",
      },
    },
  },
});
```

### Step 3: Process Fulfillment

```typescript
// Step 3a: Get fulfillment orders for an order
const GET_FULFILLMENT_ORDERS = `
  query fulfillmentOrders($orderId: ID!) {
    order(id: $orderId) {
      fulfillmentOrders(first: 10) {
        edges {
          node {
            id
            status  # OPEN, IN_PROGRESS, CLOSED, CANCELLED
            assignedLocation {
              name
            }
            lineItems(first: 20) {
              edges {
                node {
                  id
                  totalQuantity
                  remainingQuantity
                }
              }
            }
          }
        }
      }
    }
  }
`;

// Step 3b: Create fulfillment with tracking
const CREATE_FULFILLMENT = `
  mutation fulfillmentCreate($fulfillment: FulfillmentInput!) {
    fulfillmentCreate(fulfillment: $fulfillment) {
      fulfillment {
        id
        status
        trackingInfo {
          number
          url
          company
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(CREATE_FULFILLMENT, {
  variables: {
    fulfillment: {
      lineItemsByFulfillmentOrder: [
        {
          fulfillmentOrderId: "gid://shopify/FulfillmentOrder/99999",
          fulfillmentOrderLineItems: [
            {
              id: "gid://shopify/FulfillmentOrderLineItem/11111",
              quantity: 2,
            },
          ],
        },
      ],
      trackingInfo: {
        number: "1Z999AA10123456784",
        url: "https://www.ups.com/track?tracknum=1Z999AA10123456784",
        company: "UPS",
      },
      notifyCustomer: true,
    },
  },
});
```

### Step 4: Customer Management

```typescript
// Query customers
const SEARCH_CUSTOMERS = `
  query customers($query: String!, $first: Int!) {
    customers(first: $first, query: $query) {
      edges {
        node {
          id
          displayName
          email
          phone
          numberOfOrders
          amountSpent { amount currencyCode }
          tags
          addresses(first: 3) {
            address1
            city
            province
            country
          }
          metafields(first: 5) {
            edges {
              node {
                namespace
                key
                value
                type
              }
            }
          }
        }
      }
    }
  }
`;

// Customer query examples:
// "email:john@example.com"
// "orders_count:>5"
// "total_spent:>100"
// "tag:vip"
// "state:enabled"
const customers = await client.request(SEARCH_CUSTOMERS, {
  variables: {
    query: "orders_count:>5 AND total_spent:>100",
    first: 20,
  },
});
```

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
| `Customer not found` | Invalid customer GID | Verify GID format `gid://shopify/Customer/{id}` |
| `Order is not editable` | Order already archived | Only draft/open orders are editable |
| `THROTTLED` | Rate limit exceeded | Implement backoff — see `shopify-rate-limits` |

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

```typescript
const REFUND_CREATE = `
  mutation refundCreate($input: RefundInput!) {
    refundCreate(input: $input) {
      refund {
        id
        totalRefundedSet { shopMoney { amount currencyCode } }
      }
      userErrors { field message }
    }
  }
`;

await client.request(REFUND_CREATE, {
  variables: {
    input: {
      orderId: "gid://shopify/Order/12345",
      note: "Customer requested return",
      notify: true,
      refundLineItems: [
        {
          lineItemId: "gid://shopify/LineItem/67890",
          quantity: 1,
          restockType: "RETURN",
        },
      ],
    },
  },
});
```

## Resources

- [Orders Query](https://shopify.dev/docs/api/admin-graphql/latest/queries/orders)
- [FulfillmentCreate Mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/fulfillmentCreate)
- [Customer Object](https://shopify.dev/docs/api/admin-graphql/latest/objects/Customer)
- [Draft Orders](https://shopify.dev/docs/api/admin-graphql/latest/mutations/draftOrderCreate)

## Next Steps

For common errors, see `shopify-common-errors`.
