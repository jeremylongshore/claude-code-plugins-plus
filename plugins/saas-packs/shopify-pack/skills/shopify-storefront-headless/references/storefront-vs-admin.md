Detailed comparison of Shopify Storefront API vs Admin API capabilities and access patterns.

## Authentication

| Aspect | Storefront API | Admin API |
|--------|---------------|-----------|
| Token type | Public access token | Private access token (`shpat_*`) |
| Safe in browser | Yes | Never (server-only) |
| Token source | Headless channel or custom app | Custom app or OAuth |
| Scopes | `unauthenticated_*` prefixed | Standard scopes (`read_products`, etc.) |

## Rate Limiting

| Aspect | Storefront API | Admin API |
|--------|---------------|-----------|
| Model | Request-based | Query cost-based |
| Limit | ~100 requests/second per IP | 1000 points/second per app |
| Burst | Allowed (no bucket) | 2000 point bucket |
| Header | `Retry-After` | `X-Shopify-Shop-Api-Call-Limit` |
| Strategy | Simple retry with backoff | Calculate query cost, throttle proactively |

## Data Access Comparison

| Resource | Storefront API | Admin API |
|----------|---------------|-----------|
| Products | Published products only | All products (draft, archived, active) |
| Variants | `availableForSale`, `price`, `selectedOptions` | Full variant data + inventory quantities |
| Collections | Published collections only | All collections |
| Orders | Customer's own orders (with token) | All orders |
| Customers | Self-service (create, login, address) | Full CRUD on all customers |
| Metafields | Only if `storefront` access enabled | All metafields |
| Metaobjects | Only if `storefront` access enabled | All metaobjects |
| Cart | Full cart lifecycle | No cart operations |
| Checkout | Via `checkoutUrl` redirect | Draft orders (not checkout) |
| Inventory | Not available | Full inventory management |
| Fulfillment | Not available | Full fulfillment management |
| Discounts | Apply via discount codes on cart | Create/manage discount rules |

## When to Use Each

### Use Storefront API When:
- Building a customer-facing storefront or mobile app
- Running code in the browser (public token is safe)
- Managing shopping cart and checkout flow
- Displaying product catalogs, collections, search
- Handling customer authentication (login, register, addresses)

### Use Admin API When:
- Managing products, inventory, or orders (back-office)
- Processing webhooks on your server
- Syncing data with external systems (ERP, warehouse)
- Building admin tools or dashboards
- Running bulk operations (imports, exports)
- Creating draft orders programmatically

### Use Both When:
- Full headless storefront: Storefront API for the frontend, Admin API for backend order processing
- Custom checkout: Storefront API for cart, Admin API for post-purchase fulfillment
- Loyalty programs: Storefront API for customer-facing UI, Admin API for managing customer metafields

## GraphQL Schema Differences

The two APIs have **different schemas**. Field names and structures differ:

```graphql
# Storefront API — product price
product {
  priceRange {
    minVariantPrice { amount currencyCode }
  }
}

# Admin API — product price
product {
  priceRangeV2 {
    minVariantPrice { amount currencyCode }
  }
}
```

```graphql
# Storefront API — variant fields
variant {
  price { amount currencyCode }        # MoneyV2 object
  availableForSale                      # Boolean
  selectedOptions { name value }
}

# Admin API — variant fields
variant {
  price                                 # String ("29.99")
  inventoryQuantity                     # Int (not on Storefront)
  selectedOptions { name value }
  sku                                   # Not on Storefront
}
```

Do not copy queries between APIs without adjusting field names and types.
